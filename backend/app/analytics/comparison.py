"""Position groups for browsing stored players, independent of recruitment limits."""
POSITION_COMPARISON_GROUPS = {
    'goalkeepers': {'label':'Goalkeepers', 'positions':['GK'], 'metrics':['progressive_passes','possession_retention','aerial_dominance']},
    'fullbacks': {'label':'Fullback / wingback', 'positions':['LB','RB','LWB','RWB'], 'metrics':['progressive_passes','progressive_carries','tackles_interceptions','ball_recoveries_pressures','chance_creation_xa','possession_retention']},
    'centrebacks': {'label':'Centrebacks', 'positions':['CB'], 'metrics':['progressive_passes','progressive_carries','tackles_interceptions','aerial_dominance','possession_retention']},
    'midfielders': {'label':'Midfielders', 'positions':['DM','CM','AM'], 'metrics':['progressive_passes','progressive_carries','tackles_interceptions','ball_recoveries_pressures','chance_creation_xa','possession_retention','goal_threat_xg']},
    'wingers': {'label':'Wingers', 'positions':['LW','RW'], 'metrics':['progressive_passes','progressive_carries','chance_creation_xa','possession_retention','goal_threat_xg']},
    'strikers': {'label':'Strikers', 'positions':['ST','CF'], 'metrics':['aerial_dominance','progressive_carries','chance_creation_xa','possession_retention','goal_threat_xg']},
}

def matches_comparison_group(player, group, include_secondary=True):
    positions = [player.primary_position]
    if include_secondary:
        positions += player.secondary_positions
    return bool({p.upper() for p in positions} & set(POSITION_COMPARISON_GROUPS[group]['positions']))
