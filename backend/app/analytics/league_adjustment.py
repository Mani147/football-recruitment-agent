from backend.app.schemas.player import NormalizedPlayerPercentiles

LEAGUE_STRENGTH_COEFFICIENTS = {
    'Premier League': 1.00,
    'La Liga': 0.93,
    'Bundesliga': 0.93,
    'Serie A': 0.90,
    'Ligue 1': 0.89,
    'Eredivisie': 0.82,
    'Liga Portugal': 0.81,
    'Championship': 0.78,
    'Other': 0.75
}

def get_league_coefficient(league: str) -> float:
    return LEAGUE_STRENGTH_COEFFICIENTS.get(league, LEAGUE_STRENGTH_COEFFICIENTS['Other'])

def adjust_percentiles_for_league(percentiles: NormalizedPlayerPercentiles, league: str) -> NormalizedPlayerPercentiles:
    coef = get_league_coefficient(league)
    def scale(val: float) -> float:
        return round(min(100.0, max(0.0, val * coef)), 1)
        
    return NormalizedPlayerPercentiles(
        progressive_passes=scale(percentiles.progressive_passes),
        progressive_carries=scale(percentiles.progressive_carries),
        tackles_interceptions=scale(percentiles.tackles_interceptions),
        ball_recoveries_pressures=scale(percentiles.ball_recoveries_pressures),
        aerial_dominance=scale(percentiles.aerial_dominance),
        chance_creation_xa=scale(percentiles.chance_creation_xa),
        possession_retention=scale(percentiles.possession_retention),
        goal_threat_xg=scale(percentiles.goal_threat_xg)
    )
