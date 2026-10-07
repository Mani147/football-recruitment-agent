from typing import List
from backend.app.schemas.dossier import RankedCandidate, CriticVerificationReport
from backend.app.agents.tools import tools

class RecruitmentCriticAgent:
    def __init__(self):
        self.role_name = "Recruitment Critic Agent"

    def verify_top_candidates(self, candidates: List[RankedCandidate], budget_max: float) -> List[CriticVerificationReport]:
        reports = []
        for c in candidates:
            res = tools.verify_candidate(
                candidate_id=c.player.id,
                claimed_metrics=c.player.raw_metrics.model_dump(),
                budget_max=budget_max
            )
            reports.append(CriticVerificationReport(**res))
        return reports

critic_agent = RecruitmentCriticAgent()
