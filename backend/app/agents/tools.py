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
    def verify_candidate(candidate_id: str, claimed_metrics: Dict[str, Any], budget_max: float,
                         wage_cap_pw: Optional[float] = None) -> Dict[str, Any]:
        """Check supplied raw-metric claims against the stored demo record, not external truth."""
        import math
        player = db.get_player_by_id(candidate_id)
        if not player:
            return CriticVerificationReport(
                candidate_id=candidate_id, candidate_name="Unknown player", is_verified=False,
                groundedness_score=0, budget_compliance_verified=False,
                wage_compliance_verified=False, flagged_caveats=["Player record missing."]
            ).model_dump()
        actual = player.raw_metrics.model_dump()
        verified, caveats = [], []
        matched = 0
        for key, value in claimed_metrics.items():
            expected = actual.get(key)
            valid = (key in actual and isinstance(value, (int, float)) and not isinstance(value, bool)
                     and math.isfinite(value) and math.isclose(value, expected, rel_tol=1e-6, abs_tol=1e-6))
            if valid:
                matched += 1
                verified.append(f"{key}: {expected} matches the stored record.")
            else:
                caveats.append(f"Unsupported or mismatched claim: {key}.")
        if not claimed_metrics:
            caveats.append("No metric claims supplied for verification.")
        budget_ok = player.market_value_eur <= budget_max
        wage_ok = wage_cap_pw is not None and player.weekly_wage_eur <= wage_cap_pw
        if not budget_ok:
            caveats.append("Estimated fee exceeds the effective budget.")
        if not wage_ok:
            caveats.append("Weekly wage exceeds the cap or no wage cap was supplied.")
        sample_flag = None
        if player.raw_metrics.minutes_played < 1000:
            sample_flag = f"Small sample: {player.raw_metrics.minutes_played} league minutes."
            caveats.append(sample_flag)
        checked = len(claimed_metrics)
        return CriticVerificationReport(
            candidate_id=player.id, candidate_name=player.name,
            is_verified=bool(checked) and matched == checked and budget_ok and wage_ok,
            groundedness_score=round(100 * matched / checked, 1) if checked else 0,
            checked_claim_count=checked, matched_claim_count=matched,
            verified_claims=verified, flagged_caveats=caveats,
            budget_compliance_verified=budget_ok, wage_compliance_verified=wage_ok,
            sample_size_flag=sample_flag
        ).model_dump()

    @staticmethod
    def run_squad_impact_sim(ranked_candidate_data: Dict[str, Any], club: str = "Arsenal FC") -> Dict[str, Any]:
        candidate = RankedCandidate(**ranked_candidate_data)
        sim = simulate_squad_impact(candidate, club=club)
        return sim.model_dump()

tools = RecruitmentTools()
