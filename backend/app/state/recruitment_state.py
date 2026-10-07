from typing import Dict, List, Optional, Any
import time
from pydantic import BaseModel
from backend.app.schemas.player import PlayerProfile
from backend.app.schemas.recruitment import RecruitmentProfile
from backend.app.schemas.dossier import (
    WorkflowMilestone,
    RankedCandidate,
    CriticVerificationReport,
    SquadImpactProxy,
    FinalRecruitmentDossier
)

class RecruitmentState(BaseModel):
    session_id: str
    club: str = "Arsenal FC"
    objective: str
    transfer_budget_eur: float = 50_000_000.0
    wage_cap_eur_pw: float = 120_000.0
    recruitment_profile: Optional[RecruitmentProfile] = None
    candidate_pool: List[PlayerProfile] = []
    ranked_candidates: List[RankedCandidate] = []
    critic_verifications: List[CriticVerificationReport] = []
    squad_impact_simulations: List[SquadImpactProxy] = []
    final_dossier: Optional[FinalRecruitmentDossier] = None
    event_milestones: List[WorkflowMilestone] = []

    def add_milestone(self, agent: str, action_type: str, message: str, details: Optional[Dict[str, Any]] = None) -> WorkflowMilestone:
        milestone = WorkflowMilestone(
            timestamp_ms=int(time.time() * 1000),
            agent=agent,
            action_type=action_type,
            message=message,
            details=details
        )
        self.event_milestones.append(milestone)
        return milestone
