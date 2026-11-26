from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from .player import PlayerProfile, NormalizedPlayerPercentiles
from .recruitment import RecruitmentProfile

class WorkflowMilestone(BaseModel):
    timestamp_ms: int
    agent: str
    action_type: str
    message: str
    details: Optional[Dict[str, Any]] = None

class TacticalMetricMatch(BaseModel):
    metric_name: str
    player_league_adj_pct: float
    target_pct: float
    match_factor: float
    status: str

class RankedCandidate(BaseModel):
    player: PlayerProfile
    rank: int
    fit_score: float
    tactical_fit_score: float
    stat_fit_score: float
    financial_fit_score: float
    age_potential_score: float
    reliability_score: float
    reliability_summary: str
    league_adjusted_percentiles: NormalizedPlayerPercentiles
    estimated_annual_cost_eur: float
    why_recommended: List[str]
    risk_factors: List[str]
    tactical_strengths: List[str]
    tactical_breakdown: List[TacticalMetricMatch] = []

class CriticVerificationReport(BaseModel):
    candidate_id: str
    candidate_name: str
    is_verified: bool
    groundedness_score: float = 100.0
    verified_claims: List[str] = []
    flagged_caveats: List[str] = []
    budget_compliance_verified: bool = True
    sample_size_flag: Optional[str] = None
    wage_compliance_verified: bool = False
    checked_claim_count: int = 0
    matched_claim_count: int = 0

class SquadImpactProxy(BaseModel):
    candidate_id: str
    candidate_name: str
    baseline_club: str = "Arsenal FC"
    baseline_is_fallback: bool = False
    baseline_squad_defense: float = 72.0
    projected_squad_defense: float = 78.5
    baseline_squad_progression: float = 74.0
    projected_squad_progression: float = 80.2
    role_overlap_penalty: float = 0.5
    net_improvement_index: float = 6.2
    summary: str

class FinalRecruitmentDossier(BaseModel):
    club: str
    objective: str
    recruitment_profile: RecruitmentProfile
    top_candidates: List[RankedCandidate]
    verifications: List[CriticVerificationReport]
    impact_simulations: List[SquadImpactProxy]
    director_executive_summary: str
    status: str = "complete"
    eligible_candidate_count: int = 0
    dataset_notice: str = "Illustrative 2025/26 demo data. Fees, wages and performance metrics are estimates, not live scouting feeds."
    limitations: List[str] = [
        "Rule-based text parsing and TF-IDF narrative retrieval; no live LLM calls.",
        "Fit is a weighted comparison, not a probability of transfer success.",
        "Reliability describes the stored sample, not independent data accuracy.",
        "Squad impact is an unvalidated heuristic using an Arsenal baseline; it is not a forecast."
    ]
    created_at_iso: str
