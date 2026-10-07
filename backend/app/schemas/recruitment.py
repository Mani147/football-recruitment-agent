from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class Position(str, Enum):
    GK = "GK"
    CB = "CB"
    LB = "LB"
    RB = "RB"
    LWB = "LWB"
    RWB = "RWB"
    DM = "DM"
    CM = "CM"
    AM = "AM"
    LW = "LW"
    RW = "RW"
    ST = "ST"
    CF = "CF"

class PositionFamily(str, Enum):
    GK = "GK"
    FB = "FB"
    CB = "CB"
    DM = "DM"
    CM = "CM"
    AM = "AM"
    WINGER = "WINGER"
    ST = "ST"
    UNKNOWN = "UNKNOWN"

POSITION_GROUPS: Dict[str, List[str]] = {
    "GK":     ["GK"],
    "LB":     ["LB", "LWB"],   # sided left-back subgroup
    "RB":     ["RB", "RWB"],   # sided right-back subgroup
    "FB":     ["LB", "RB", "LWB", "RWB"],  # generic fullback (unsided)
    "CB":     ["CB"],
    "DM":     ["DM"],
    "CM":     ["CM"],
    "AM":     ["AM"],
    "WINGER": ["LW", "RW"],
    "ST":     ["ST", "CF"],
}

def get_positions_for_family(family: str) -> List[str]:
    return POSITION_GROUPS.get(family.upper(), [family.upper()])

class PriorityWeights(BaseModel):
    defensive: float = 0.30
    progression: float = 0.30
    pressing_recovery: float = 0.20
    possession_retention: float = 0.10
    creation_goal: float = 0.10

class TargetPercentiles(BaseModel):
    progressive_passes: float = 75.0
    progressive_carries: float = 70.0
    tackles_interceptions: float = 75.0
    ball_recoveries_pressures: float = 80.0
    aerial_dominance: float = 65.0
    chance_creation_xa: float = 50.0
    possession_retention: float = 70.0
    goal_threat_xg: float = 40.0

class RecruitmentProfile(BaseModel):
    target_club: Optional[str] = Field(default="Arsenal FC", description="Club initiating the recruitment mandate")
    position_family: str = Field(description="Target tactical position family, e.g. FB, CB, DM, WINGER, ST, GK")
    position: str = Field(description="Primary specific position code or representative label, e.g. LB, RB, DM, CB, RW")
    tactical_role_name: str = Field(description="Role archetype, e.g. 'Inverted Attacking Fullback', 'Box-to-Box Ball Winner'")
    age_min: int = 18
    age_max: int = 25
    budget_max_eur: float = 50_000_000.0
    wage_cap_eur_pw: float = 120_000.0
    min_minutes_played: int = 800
    target_percentiles: TargetPercentiles = TargetPercentiles()
    priority_weights: PriorityWeights = PriorityWeights()
    preferred_foot: Optional[str] = None
    tactical_notes: str = ""
