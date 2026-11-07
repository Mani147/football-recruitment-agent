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
from backend.app.data import real_data

# Demo mode is an explicit test fixture; the public workspace uses real season data.
DATASET_MODE = os.getenv('TOUCHLINE_DATASET', 'statsbomb')

@asynccontextmanager
async def lifespan(app):
    if DATASET_MODE == 'demo':
        await asyncio.to_thread(initialize_data)
    else:
        await asyncio.to_thread(real_data.snapshot)
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
    if DATASET_MODE != 'demo':
        return FileResponse(os.path.join(static_dir, 'research.html'))
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"status": "ok", "project": settings.PROJECT_NAME}

@app.get("/compare")
def serve_comparison():
    return FileResponse(os.path.join(static_dir, "compare.html"))


@app.get("/api/compare/players")
def comparison_players(
    group: Literal['goalkeepers','fullbacks','centrebacks','midfielders','wingers','strikers'] = 'midfielders',
    include_secondary: bool = True,
    min_minutes: int = Query(900,ge=0,le=3420),
):
    if DATASET_MODE != 'demo':
        return real_data.comparison(group,include_secondary,min_minutes)
    from backend.app.analytics.comparison import POSITION_COMPARISON_GROUPS, matches_comparison_group
    from backend.app.analytics.league_adjustment import adjust_percentiles_for_league
    from backend.app.analytics.reliability import calculate_reliability_score
    players = db.get_all_players()
    pool = sorted((p for p in players if matches_comparison_group(p,group,include_secondary)), key=lambda p:(p.name.casefold(),p.id))
    records = []
    for player in pool:
        score, summary = calculate_reliability_score(player)
        records.append({'player':player.model_dump(),
                        'league_adjusted_percentiles':adjust_percentiles_for_league(player.normalized_percentiles,player.league).model_dump(),
                        'reliability_score':score, 'reliability_summary':summary})
    return {'group':group, 'include_secondary':include_secondary, 'players':records,
            'groups':{key:dict(value,count=sum(matches_comparison_group(p,key,include_secondary) for p in players))
                      for key,value in POSITION_COMPARISON_GROUPS.items()},
            'dataset_count':len(players),
            'dataset_notice':'Illustrative demo records, not independently verified or live scouting data. Percentiles were hand-authored, not computed from a documented position-specific population.'}


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
    if DATASET_MODE != 'demo':
        try:
            profile, group = real_data.interpret(req)
            return {'profile':real_data.profile_payload(profile,group),'needs_clarification':not group,
                    'notice':'Historical performance-only search. Age, foot, fees and wages cannot be verified. Minimum 900 regulation minutes.'}
        except ValueError as exc:
            raise HTTPException(422,str(exc)) from exc
    profile = effective_profile(req)
    return {"profile": profile.model_dump(), "needs_clarification": profile.position_family == "UNKNOWN",
            "notice": "Only the displayed constraints are enforced. Text is interpreted by rules; review before searching."}

@app.get("/api/dataset")
def dataset_metadata():
    return real_data.metadata() if DATASET_MODE != 'demo' else {'mode':'illustrative_demo'}


@app.get("/api/health")
def health_check():
    if DATASET_MODE != 'demo':
        return {'status':'ok','project':settings.PROJECT_NAME,'version':'3.0.0','player_count':len(real_data.snapshot()['players']),
                'mode':'statsbomb','season':'2015/16','matches':380}
    return {"status": "ok", "project": settings.PROJECT_NAME, "version": "2.0.0", "player_count": len(db.get_all_players()), "mode": "illustrative_demo"}

@app.get("/api/players")
def list_players():
    if DATASET_MODE != 'demo':
        players=real_data.snapshot()['players']
        return {'count':len(players),'players':players,'metadata':real_data.metadata()}
    players = db.get_all_players()
    return {"count": len(players), "players": [p.model_dump() for p in players]}

@app.get("/api/players/{player_id}")
def get_player(player_id: str):
    if DATASET_MODE != 'demo':
        player=next((p for p in real_data.snapshot()['players'] if p['id']==player_id),None)
        if not player:
            raise HTTPException(404,'Player not found')
        return player
    player = db.get_player_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player.model_dump()

@app.post("/api/scout/search")
def search_scout_mandate(req: ScoutRequest):
    if DATASET_MODE != 'demo':
        try:
            return real_data.search(req)
        except ValueError as exc:
            raise HTTPException(422,str(exc)) from exc
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
    if DATASET_MODE != 'demo':
        try:
            if budget != 50_000_000 or wage_cap != 120_000:
                raise ValueError('Fee and wage constraints are unavailable in the historical dataset.')
            req = ScoutRequest(objective=objective,club=club,min_minutes=min_minutes,age_max=age_max,preferred_foot=preferred_foot)
            result = await asyncio.to_thread(real_data.search,req)
        except ValueError as exc:
            raise HTTPException(422,str(exc)) from exc
        async def real_events():
            yield f"data: {json.dumps({'event':'complete','data':result})}\n\n"
        return StreamingResponse(real_events(),media_type='text/event-stream')
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
    if DATASET_MODE != 'demo':
        raise HTTPException(422,'Squad impact predictions are not supported by this historical dataset.')
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
