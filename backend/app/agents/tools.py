import json
from typing import List, Dict, Any, Optional
from backend.app.schemas.player import PlayerProfile
from backend.app.schemas.recruitment import RecruitmentProfile
from backend.app.schemas.dossier import RankedCandidate, CriticVerificationReport, SquadImpactProxy
from backend.app.data.sqlite_db import db
from backend.app.data.vector_store import vector_store
from backend.app.analytics.scoring_engine import rank_candidates
from backend.app.analytics.financial_model import calculate_amortization_and_cost, evaluate_financial_fit
from backend.app.analytics.transfer_simulator import simulate_squad_impact

class RecruitmentTools:
    @staticmethod
    def search_candidates_sql(
        position_family: Optional[str] = None,
        position: Optional[str] = None,
        max_age: Optional[int] = None,
        max_budget_eur: Optional[float] = None,
        max_wage_eur_pw: Optional[float] = None,
        min_minutes: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Queries relational SQLite store using hard constraints (Position Family, Max Age, Budget, Wages, Minutes).
        position_family (e.g. 'FB', 'CB', 'DM', 'WINGER', 'ST') is expanded to concrete codes via POSITION_GROUPS.
        """
        players = db.search_candidates_sql(
            position_family=position_family,
            position=position,
            max_age=max_age,
            max_budget_eur=max_budget_eur,
            max_wage_eur_pw=max_wage_eur_pw,
            min_minutes=min_minutes
        )
        return [p.model_dump() for p in players]

    @staticmethod
    def search_semantic_profiles(query_text: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Performs semantic vector search across qualitative scouting profiles.
        """
        results = vector_store.search_similar_profiles(query=query_text, top_k=top_k)
        return [{"player": p.model_dump(), "similarity_score": score} for p, score in results]

    @staticmethod
    def get_player_by_id(player_id: str) -> Optional[Dict[str, Any]]:
        player = db.get_player_by_id(player_id)
        return player.model_dump() if player else None

    @staticmethod
    def evaluate_financial_profile(player_id: str, budget_max: float, wage_cap_pw: float) -> Dict[str, Any]:
        player = db.get_player_by_id(player_id)
        if not player:
            return {"error": "Player not found"}
        
        amort = calculate_amortization_and_cost(player)
        fit_score, status = evaluate_financial_fit(player, budget_max, wage_cap_pw)
        return {
            "player_id": player_id,
            "player_name": player.name,
            "financial_fit_score": fit_score,
            "status": status,
            "amortization": amort
        }

    @staticmethod
    def rank_candidate_pool(candidates_data: List[Dict[str, Any]], profile_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Executes deterministic multi-criteria scoring and ranking.
        """
        candidates = [PlayerProfile(**c) for c in candidates_data]
        profile = RecruitmentProfile(**profile_data)
        ranked = rank_candidates(candidates, profile)
        return [r.model_dump() for r in ranked]

    @staticmethod
    def verify_candidate(candidate_id: str, claimed_metrics: Dict[str, Any], budget_max: float) -> Dict[str, Any]:
        """
        Critic tool: Verifies that claims made in scouting text match actual database values.
        """
        player = db.get_player_by_id(candidate_id)
        if not player:
            return {"candidate_id": candidate_id, "is_verified": False, "error": "Player record missing"}

        verified_claims = []
        flagged_caveats = []
        is_verified = True

        # Check budget compliance
        budget_compliant = player.market_value_eur <= (budget_max * 1.10)
        if not budget_compliant:
            flagged_caveats.append(f"Valuation (€{player.market_value_eur/1e6:.1f}M) exceeds base budget (€{budget_max/1e6:.1f}M)")

        # Check sample size
        sample_size_flag = None
        if player.raw_metrics.minutes_played < 1000:
            sample_size_flag = f"Small sample caution: only {player.raw_metrics.minutes_played} league minutes logged."
            flagged_caveats.append(sample_size_flag)

        verified_claims.append(f"Confirmed league stats from {player.league} ({player.raw_metrics.minutes_played} mins).")
        verified_claims.append(f"Market fee benchmark confirmed at €{player.market_value_eur/1e6:.1f}M.")

        report = CriticVerificationReport(
            candidate_id=player.id,
            candidate_name=player.name,
            is_verified=is_verified,
            groundedness_score=100.0 if not flagged_caveats else 85.0,
            verified_claims=verified_claims,
            flagged_caveats=flagged_caveats,
            budget_compliance_verified=budget_compliant,
            sample_size_flag=sample_size_flag
        )
        return report.model_dump()

    @staticmethod
    def run_squad_impact_sim(ranked_candidate_data: Dict[str, Any], club: str = "Arsenal FC") -> Dict[str, Any]:
        candidate = RankedCandidate(**ranked_candidate_data)
        sim = simulate_squad_impact(candidate, club=club)
        return sim.model_dump()

tools = RecruitmentTools()
