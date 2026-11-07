import json
import os
import asyncio
from typing import Literal
from contextlib import asynccontextmanager
from backend.app.data.bootstrap import initialize_data
from backend.app.agents.tactical_agent import tactical_agent, extract_target_club
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ValidationError

from backend.app.config import settings
from backend.app.data.sqlite_db import db
from backend.app.agents.orchestrator import director_orchestrator

@asynccontextmanager
async def lifespan(app):
    await asyncio.to_thread(initialize_data)
    yield

app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs"
)

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"status": "ok", "project": settings.PROJECT_NAME}

class ScoutRequest(BaseModel):
    objective: str = Field(min_length=3, max_length=2000, pattern=r"\S")
    club: str = Field(default="Arsenal FC", min_length=1, max_length=100, pattern=r"\S")
    budget_eur: float = Field(default=50_000_000, gt=0, le=1_000_000_000, allow_inf_nan=False)
    wage_cap_pw: float = Field(default=120_000, gt=0, le=10_000_000, allow_inf_nan=False)
    age_max: int | None = Field(default=None, ge=18, le=60)
    min_minutes: int = Field(default=800, ge=0, le=10000)
    preferred_foot: Literal["Left", "Right", "Either"] | None = None

def effective_profile(req: ScoutRequest):
    try:
        profile = tactical_agent.generate_profile(req.objective, extract_target_club(req.club, req.club), req.budget_eur, req.wage_cap_pw)
        if req.age_max is not None:
            profile.age_max = req.age_max
        profile.min_minutes_played = req.min_minutes
        if req.preferred_foot is not None:
            profile.preferred_foot = None if req.preferred_foot == "Either" else req.preferred_foot
        if profile.age_max < profile.age_min:
            raise ValueError("Adult recruitment only: set a maximum age of at least 18.")
        return profile
    except (ValueError, ValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.post("/api/scout/profile")
def preview_profile(req: ScoutRequest):
    profile = effective_profile(req)
    return {"profile": profile.model_dump(), "needs_clarification": profile.position_family == "UNKNOWN",
            "notice": "Only the displayed constraints are enforced. Text is interpreted by rules; review before searching."}

@app.get("/api/health")
def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME, "version": "2.0.0", "player_count": len(db.get_all_players()), "mode": "illustrative_demo"}

@app.get("/api/players")
def list_players():
    players = db.get_all_players()
    return {"count": len(players), "players": [p.model_dump() for p in players]}

@app.get("/api/players/{player_id}")
def get_player(player_id: str):
    player = db.get_player_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player.model_dump()

@app.post("/api/scout/search")
def search_scout_mandate(req: ScoutRequest):
    state, dossier = director_orchestrator.execute_recruitment_workflow(
        objective=req.objective,
        club=req.club,
        budget_eur=req.budget_eur,
        wage_cap_pw=req.wage_cap_pw,
        profile=effective_profile(req)
    )
    return {
        "session_id": state.session_id,
        "dossier": dossier.model_dump(),
        "milestones": [m.model_dump() for m in state.event_milestones]
    }

@app.get("/api/scout/stream")
async def stream_scout_mandate(
    objective: str = Query(..., min_length=3, max_length=2000, pattern=r"\S"),
    club: str = Query("Arsenal FC", min_length=1, max_length=100, pattern=r"\S"),
    budget: float = Query(50_000_000, gt=0, le=1_000_000_000, allow_inf_nan=False),
    wage_cap: float = Query(120_000, gt=0, le=10_000_000, allow_inf_nan=False),
    age_max: int | None = Query(None, ge=18, le=60),
    min_minutes: int = Query(800, ge=0, le=10000),
    preferred_foot: Literal["Left", "Right", "Either"] | None = Query(None),
):
    req = ScoutRequest(objective=objective, club=club, budget_eur=budget, wage_cap_pw=wage_cap,
                       age_max=age_max, min_minutes=min_minutes, preferred_foot=preferred_foot)
    profile = effective_profile(req)
    async def event_generator():
        queue = asyncio.Queue()
        loop = asyncio.get_running_loop()
        def emit(milestone):
            loop.call_soon_threadsafe(queue.put_nowait, {"event": "milestone", "data": milestone.model_dump()})
        async def execute():
            try:
                state, dossier = await asyncio.to_thread(
                    director_orchestrator.execute_recruitment_workflow,
                    objective=req.objective, club=req.club, budget_eur=req.budget_eur,
                    wage_cap_pw=req.wage_cap_pw, profile=profile, on_milestone=emit)
                await queue.put({"event": "complete", "data": {
                    "session_id": state.session_id, "dossier": dossier.model_dump()}})
            except Exception:
                import logging
                logging.getLogger(__name__).exception("Recruitment search failed")
                await queue.put({"event": "error", "data": {"message": "Search failed. Please try again."}})
        task = asyncio.create_task(execute())
        try:
            while True:
                payload = await queue.get()
                yield f"data: {json.dumps(payload)}\n\n"
                if payload["event"] in ("complete", "error"):
                    break
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    return StreamingResponse(event_generator(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.post("/api/simulate")
def simulate_transfer(candidate_id: str, club: str = "Arsenal FC"):
    player = db.get_player_by_id(candidate_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    from backend.app.analytics.scoring_engine import rank_candidates
    from backend.app.schemas.recruitment import RecruitmentProfile
    from backend.app.analytics.transfer_simulator import simulate_squad_impact
    profile = RecruitmentProfile(target_club=None, position_family=player.primary_position, position=player.primary_position,
                                 tactical_role_name="Individual player simulation", age_max=max(25, player.age),
                                 budget_max_eur=max(1, player.market_value_eur),
                                 wage_cap_eur_pw=max(1, player.weekly_wage_eur), min_minutes_played=0)
    candidates = rank_candidates([player], profile)
    if not candidates:
        raise HTTPException(status_code=422, detail="Player is outside the supported adult demo range.")
    return simulate_squad_impact(candidates[0], club=club).model_dump()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
