import json
import os
import asyncio
from typing import Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.app.config import settings
from backend.app.data.sqlite_db import db
from backend.app.agents.orchestrator import director_orchestrator
from backend.app.agents.tools import tools
from backend.app.schemas.dossier import FinalRecruitmentDossier

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    objective: str
    club: str = "Arsenal FC"
    budget_eur: float = 50_000_000.0
    wage_cap_pw: float = 120_000.0

@app.get("/api/health")
def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME, "version": "1.0.0"}

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
        wage_cap_pw=req.wage_cap_pw
    )
    return {
        "session_id": state.session_id,
        "dossier": dossier.model_dump(),
        "milestones": [m.model_dump() for m in state.event_milestones]
    }

@app.get("/api/scout/stream")
async def stream_scout_mandate(
    objective: str = Query(..., description="Recruitment requirement"),
    club: str = Query("Arsenal FC"),
    budget: float = Query(50_000_000.0),
    wage_cap: float = Query(120_000.0)
):
    async def event_generator():
        state, dossier = director_orchestrator.execute_recruitment_workflow(
            objective=objective,
            club=club,
            budget_eur=budget,
            wage_cap_pw=wage_cap
        )

        for m in state.event_milestones:
            payload = {
                "event": "milestone",
                "data": m.model_dump()
            }
            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(0.3)

        final_payload = {
            "event": "complete",
            "data": {
                "session_id": state.session_id,
                "dossier": dossier.model_dump()
            }
        }
        yield f"data: {json.dumps(final_payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/simulate")
def simulate_transfer(candidate_id: str, club: str = "Arsenal FC"):
    player = db.get_player_by_id(candidate_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    from backend.app.schemas.dossier import RankedCandidate
    from backend.app.analytics.league_adjustment import adjust_percentiles_for_league
    from backend.app.analytics.transfer_simulator import simulate_squad_impact

    adj_pct = adjust_percentiles_for_league(player.normalized_percentiles, player.league)
    ranked = RankedCandidate(
        player=player,
        rank=1,
        fit_score=85.0,
        tactical_fit_score=85.0,
        stat_fit_score=85.0,
        financial_fit_score=80.0,
        age_potential_score=85.0,
        reliability_score=90.0,
        reliability_summary="Robust sample",
        league_adjusted_percentiles=adj_pct,
        estimated_annual_cost_eur=player.market_value_eur / 5.0 + (player.weekly_wage_eur * 52.0),
        why_recommended=["Target tactical profile match"],
        risk_factors=["None detected"],
        tactical_strengths=["Ball Progression", "Duel Dominance"]
    )
    sim = simulate_squad_impact(ranked, club=club)
    return sim.model_dump()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
