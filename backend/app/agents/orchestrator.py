import uuid
import datetime
from typing import Generator, Dict, Any, Tuple, Optional
from backend.app.state.recruitment_state import RecruitmentState
from backend.app.schemas.dossier import FinalRecruitmentDossier, WorkflowMilestone
from backend.app.agents.tactical_agent import tactical_agent
from backend.app.agents.scout_agent import scout_agent
from backend.app.agents.financial_agent import financial_agent
from backend.app.agents.critic_agent import critic_agent
from backend.app.agents.tools import tools

class DirectorOfFootballOrchestrator:
    def __init__(self):
        self.role_name = "Director of Football (Lead Orchestrator)"

    def execute_recruitment_workflow(
        self,
        objective: str,
        club: str = "Arsenal FC",
        budget_eur: float = 50_000_000.0,
        wage_cap_pw: float = 120_000.0
    ) -> Tuple[RecruitmentState, FinalRecruitmentDossier]:
        session_id = str(uuid.uuid4())[:8]
        state = RecruitmentState(
            session_id=session_id,
            club=club,
            objective=objective,
            transfer_budget_eur=budget_eur,
            wage_cap_eur_pw=wage_cap_pw
        )

        # Milestone 1: Objective Received
        state.add_milestone(
            agent=self.role_name,
            action_type="INITIATE_MANDATE",
            message=f"Initiated recruitment mandate for {club}: '{objective}'"
        )

        # Milestone 2: Tactical Profile Generation
        profile = tactical_agent.generate_profile(
            user_prompt=objective,
            club=club,
            budget_eur=budget_eur,
            wage_cap_pw=wage_cap_pw
        )
        state.recruitment_profile = profile

        # --- Guard: UNKNOWN position → return structured clarification, never default to DM ---
        if profile.position_family.upper() == "UNKNOWN":
            state.add_milestone(
                agent=tactical_agent.role_name,
                action_type="POSITION_UNCLEAR",
                message=(
                    "Could not determine a supported recruitment position from your mandate. "
                    "Supported positions: GK, Fullback (LB/RB), CB, DM, CM, AM, Winger (LW/RW), ST/CF. "
                    "Please rephrase using a recognised position term."
                ),
            )
            clarification_dossier = FinalRecruitmentDossier(
                club=club,
                objective=objective,
                recruitment_profile=profile,
                top_candidates=[],
                verifications=[],
                impact_simulations=[],
                director_executive_summary=(
                    "⚠️ Recruitment mandate could not be processed — target position unclear. "
                    "Please include a recognised position term (e.g. 'fullback', 'centre-back', 'striker', 'winger')."
                ),
                created_at_iso=datetime.datetime.now(datetime.timezone.utc).isoformat()
            )
            return state, clarification_dossier

        state.add_milestone(
            agent=tactical_agent.role_name,
            action_type="GENERATE_PROFILE",
            message=f"Formulated {profile.tactical_role_name} ({profile.position_family}/{profile.position}) profile. Target club: {profile.target_club}.",
            details={"tactical_role": profile.tactical_role_name, "position_family": profile.position_family, "position": profile.position, "budget_cap": profile.budget_max_eur}
        )

        # Milestone 3: Candidate Retrieval & Deterministic Ranking
        candidate_pool, ranked_candidates = scout_agent.retrieve_and_rank_candidates(profile, query_context=objective)
        state.candidate_pool = candidate_pool
        state.ranked_candidates = ranked_candidates
        state.add_milestone(
            agent=scout_agent.role_name,
            action_type="RETRIEVE_CANDIDATES",
            message=f"Retrieved {len(candidate_pool)} {profile.position_family} candidates via SQL family expansion + semantic vector search; Deterministic Engine ranked all.",
            details={"candidates_found": len(candidate_pool), "top_candidate": ranked_candidates[0].player.name if ranked_candidates else None}
        )

        # Milestone 4: Financial Amortization & Budget Fit
        top_candidates = ranked_candidates[:5]
        financial_evals = financial_agent.assess_candidates_finances(top_candidates, budget_max=budget_eur, wage_cap_pw=wage_cap_pw)
        state.add_milestone(
            agent=financial_agent.role_name,
            action_type="FINANCIAL_ASSESSMENT",
            message=f"Calculated 5-year fee amortization and wage cap compatibility across top {len(top_candidates)} candidates."
        )

        # Milestone 5: Critic Adversarial Verification
        verifications = critic_agent.verify_top_candidates(top_candidates, budget_max=budget_eur)
        state.critic_verifications = verifications
        flagged_count = sum(1 for v in verifications if v.flagged_caveats)
        state.add_milestone(
            agent=critic_agent.role_name,
            action_type="CRITIC_VERIFICATION",
            message=f"Audited claims against ground-truth database. Verified {len(verifications)} dossiers ({flagged_count} caveats flagged).",
            details={"flagged_count": flagged_count}
        )

        # Milestone 6: Squad Impact Proxy Simulation
        impact_sims = []
        for c in top_candidates:
            sim_res = tools.run_squad_impact_sim(c.model_dump(), club=club)
            impact_sims.append(sim_res)
        state.squad_impact_simulations = impact_sims
        state.add_milestone(
            agent="Squad Impact Simulator",
            action_type="SIMULATE_IMPACT",
            message=f"Simulated counterfactual squad metric deltas for top candidates in {club} tactical structure."
        )

        # Milestone 7: Final Executive Synthesis
        top_name = top_candidates[0].player.name if top_candidates else "N/A"
        summary = (
            f"Recruitment Dossier signed off for {club}. Target archetype: {profile.tactical_role_name} ({profile.position_family}). "
            f"Top recommendation is {top_name} (Fit Score: {top_candidates[0].fit_score if top_candidates else 0}/100, "
            f"Reliability: {top_candidates[0].reliability_score if top_candidates else 0}/100) based on reproducible "
            f"league-adjusted performance metrics and financial compatibility."
        )

        dossier = FinalRecruitmentDossier(
            club=club,
            objective=objective,
            recruitment_profile=profile,
            top_candidates=top_candidates,
            verifications=verifications,
            impact_simulations=impact_sims,
            director_executive_summary=summary,
            created_at_iso=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )
        state.final_dossier = dossier

        state.add_milestone(
            agent=self.role_name,
            action_type="FINAL_DOSSIER_READY",
            message=f"Scouting Dossier finalized. Top recommendation: {top_name}."
        )

        return state, dossier

director_orchestrator = DirectorOfFootballOrchestrator()
