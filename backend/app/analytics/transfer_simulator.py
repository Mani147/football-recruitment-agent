from typing import Dict
from backend.app.schemas.player import PlayerProfile
from backend.app.schemas.dossier import RankedCandidate, SquadImpactProxy

SQUAD_BASELINES = {
    "Arsenal FC": {
        "defense_index": 73.5,
        "progression_index": 75.2,
        "pressing_index": 78.0,
        "retention_index": 76.5
    }
}

def simulate_squad_impact(candidate: RankedCandidate, club: str = "Arsenal FC", expected_minutes_share: float = 0.70) -> SquadImpactProxy:
    base = SQUAD_BASELINES.get(club, SQUAD_BASELINES["Arsenal FC"])
    adj_pct = candidate.league_adjusted_percentiles
    
    player_def = (adj_pct.tackles_interceptions + adj_pct.ball_recoveries_pressures + adj_pct.aerial_dominance) / 3.0
    player_prog = (adj_pct.progressive_passes + adj_pct.progressive_carries + adj_pct.possession_retention) / 3.0
    
    delta_def = (player_def - base["defense_index"]) * expected_minutes_share * 0.25
    delta_prog = (player_prog - base["progression_index"]) * expected_minutes_share * 0.25
    
    overlap_penalty = 0.4 if player_def > 80.0 and base["defense_index"] > 75.0 else 0.2
    
    proj_def = round(base["defense_index"] + delta_def - overlap_penalty, 1)
    proj_prog = round(base["progression_index"] + delta_prog - overlap_penalty, 1)
    
    net_improvement = round(((proj_def - base["defense_index"]) + (proj_prog - base["progression_index"])), 1)
    
    summary = (
        f"Projected squad impact (Proxy): Defense {base['defense_index']} -> {proj_def} "
        f"(+{round(proj_def - base['defense_index'], 1)}), Progression {base['progression_index']} -> {proj_prog} "
        f"(+{round(proj_prog - base['progression_index'], 1)}). Role overlap penalty: -{overlap_penalty}."
    )
    
    return SquadImpactProxy(
        candidate_id=candidate.player.id,
        candidate_name=candidate.player.name,
        baseline_squad_defense=base["defense_index"],
        projected_squad_defense=proj_def,
        baseline_squad_progression=base["progression_index"],
        projected_squad_progression=proj_prog,
        role_overlap_penalty=overlap_penalty,
        net_improvement_index=net_improvement,
        summary=summary
    )
