from typing import List, Dict, Any
from backend.app.schemas.dossier import RankedCandidate
from backend.app.agents.tools import tools

class FinancialAnalystAgent:
    def __init__(self):
        self.role_name = "Financial Analyst Agent"

    def assess_candidates_finances(self, candidates: List[RankedCandidate], budget_max: float, wage_cap_pw: float) -> List[Dict[str, Any]]:
        assessments = []
        for c in candidates:
            res = tools.evaluate_financial_profile(
                player_id=c.player.id,
                budget_max=budget_max,
                wage_cap_pw=wage_cap_pw
            )
            assessments.append(res)
        return assessments

financial_agent = FinancialAnalystAgent()
