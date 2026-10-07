from typing import Tuple
from backend.app.schemas.player import PlayerProfile
from backend.app.analytics.league_adjustment import get_league_coefficient

def calculate_reliability_score(player: PlayerProfile) -> Tuple[float, str]:
    minutes = player.raw_metrics.minutes_played
    r_minutes = min(1.0, max(0.0, minutes / 1800.0)) * 100.0
    matches = max(1, player.raw_metrics.matches_played)
    avg_mins = minutes / matches
    r_consistency = min(100.0, max(40.0, (avg_mins / 90.0) * 100.0))
    r_completeness = 100.0
    coef = get_league_coefficient(player.league)
    r_league = coef * 100.0
    r_total = (0.45 * r_minutes) + (0.25 * r_consistency) + (0.20 * r_completeness) + (0.10 * r_league)
    r_score = round(min(100.0, max(0.0, r_total)), 1)
    
    flags = []
    if minutes < 900:
        flags.append(f"Small sample warning: only {minutes} mins played")
    elif minutes < 1400:
        flags.append(f"Moderate sample size ({minutes} mins played)")
    else:
        flags.append(f"Robust full-season sample ({minutes} mins played)")
        
    if coef < 0.85:
        flags.append(f"Non-Tier 1 League ({player.league})")
        
    summary = " | ".join(flags)
    return r_score, summary
