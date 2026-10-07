from typing import List, Optional
from pydantic import BaseModel, Field
from backend.app.schemas.recruitment import POSITION_GROUPS

class RawPlayerMetrics(BaseModel):
    minutes_played: int = Field(default=0, description="Domestic league minutes")
    matches_played: int = Field(default=0)
    goals_per90: float = 0.0
    assists_per90: float = 0.0
    xg_per90: float = 0.0
    xa_per90: float = 0.0
    progressive_passes_per90: float = 0.0
    progressive_carries_per90: float = 0.0
    tackles_per90: float = 0.0
    interceptions_per90: float = 0.0
    pressures_recoveries_per90: float = 0.0
    aerial_duels_won_pct: float = 0.0
    key_passes_per90: float = 0.0
    turnovers_per90: float = 0.0
    pass_completion_pct: float = 0.0

class NormalizedPlayerPercentiles(BaseModel):
    progressive_passes: float = Field(default=50.0, ge=0.0, le=100.0)
    progressive_carries: float = Field(default=50.0, ge=0.0, le=100.0)
    tackles_interceptions: float = Field(default=50.0, ge=0.0, le=100.0)
    ball_recoveries_pressures: float = Field(default=50.0, ge=0.0, le=100.0)
    aerial_dominance: float = Field(default=50.0, ge=0.0, le=100.0)
    chance_creation_xa: float = Field(default=50.0, ge=0.0, le=100.0)
    possession_retention: float = Field(default=50.0, ge=0.0, le=100.0)
    goal_threat_xg: float = Field(default=50.0, ge=0.0, le=100.0)

class PlayerProfile(BaseModel):
    id: str
    name: str
    age: int
    primary_position: str
    secondary_positions: List[str] = []
    club: str
    league: str
    nationality: str
    preferred_foot: str = "Right"
    height_cm: Optional[int] = None
    market_value_eur: float
    weekly_wage_eur: float
    contract_expiry_year: int = 2027
    release_clause_eur: Optional[float] = None
    raw_metrics: RawPlayerMetrics
    normalized_percentiles: NormalizedPlayerPercentiles
    scouting_narrative: str

def position_matches(player: PlayerProfile, position_family: str, specific_pos: Optional[str] = None) -> bool:
    """
    Centralized position verification function.
    Checks whether a player satisfies a requested position_family (e.g. 'FB', 'CB', 'DM', 'ST', 'WINGER')
    or specific position (e.g. 'LB', 'RB').
    """
    player_positions = [player.primary_position.upper()] + [p.upper() for p in player.secondary_positions]
    
    if specific_pos and specific_pos.upper() in player_positions:
        return True
        
    allowed_positions = POSITION_GROUPS.get(position_family.upper(), [position_family.upper()])
    return any(p in allowed_positions for p in player_positions)
