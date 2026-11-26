import uuid
import datetime
from typing import Generator, Dict, Any, Tuple, Optional, Callable
from backend.app.schemas.recruitment import RecruitmentProfile
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
        wage_cap_pw: float = 120_000.0,
        profile: Optional[RecruitmentProfile] = None,
        on_milestone: Optional[Callable] = None,
    ) -> Tuple[RecruitmentState, FinalRecruitmentDossier]:
        session_id = str(uuid.uuid4())[:8]
        state = RecruitmentState(
            session_id=session_id,
            club=club,
            objective=objective,
            transfer_budget_eur=budget_eur,
            wage_cap_eur_pw=wage_cap_pw
        )

        def emit(**kwargs):
            milestone = state.add_milestone(**kwargs)
            if on_milestone:
                on_milestone(milestone)
            return milestone

        # Milestone 1: Objective Received
        emit(
            agent=self.role_name,
            action_type="INITIATE_MANDATE",
            message=f"Initiated recruitment mandate for {club}: '{objective}'"
        )

        # Milestone 2: Tactical Profile Generation
        profile = profile or tactical_agent.generate_profile(
            user_prompt=objective,
            club=club,
            budget_eur=budget_eur,
            wage_cap_pw=wage_cap_pw
        )
        state.recruitment_profile = profile
        club = profile.target_club or club
        budget_eur = profile.budget_max_eur
        wage_cap_pw = profile.wage_cap_eur_pw
        state.club = club
        state.transfer_budget_eur = budget_eur
        state.wage_cap_eur_pw = wage_cap_pw

        # --- Guard: UNKNOWN position → return structured clarification, never default to DM ---
        if profile.position_family.upper() == "UNKNOWN":
            emit(
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
                status="needs_clarification",
                top_candidates=[],
                verifications=[],
                impact_simulations=[],
                director_executive_summary=(
                    "⚠️ Recruitment mandate could not be processed — target position unclear. "
                    "Please include a recognised position term (e.g. 'fullback', 'centre-back', 'striker', 'winger')."
                ),
                created_at_iso=datetime.datetime.now(datetime.timezone.utc).isoformat()
            )
            state.final_dossier = clarification_dossier
            return state, clarification_dossier

        emit(
            agent=tactical_agent.role_name,
            action_type="GENERATE_PROFILE",
            message=f"Formulated {profile.tactical_role_name} ({profile.position_family}/{profile.position}) profile. Target club: {profile.target_club}.",
            details={"tactical_role": profile.tactical_role_name, "position_family": profile.position_family, "position": profile.position, "budget_cap": profile.budget_max_eur}
        )

        # Milestone 3: Candidate Retrieval & Deterministic Ranking
        candidate_pool, ranked_candidates = scout_agent.retrieve_and_rank_candidates(profile, query_context=objective)
        state.candidate_pool = candidate_pool
        state.ranked_candidates = ranked_candidates
        emit(
            agent=scout_agent.role_name,
            action_type="RETRIEVE_CANDIDATES",
            message=f"Retrieved {len(candidate_pool)} {profile.position_family} candidates meeting all effective constraints; deterministic engine ranked the eligible pool.",
            details={"candidates_found": len(candidate_pool), "top_candidate": ranked_candidates[0].player.name if ranked_candidates else None}
        )

        # Milestone 4: Financial Amortization & Budget Fit
        top_candidates = ranked_candidates[:5]
        financial_agent.assess_candidates_finances(top_candidates, budget_max=budget_eur, wage_cap_pw=wage_cap_pw)
        emit(
            agent=financial_agent.role_name,
            action_type="FINANCIAL_ASSESSMENT",
            message=f"Calculated 5-year fee amortization and wage cap compatibility across top {len(top_candidates)} candidates."
        )

        # Milestone 5: Critic Adversarial Verification
        verifications = critic_agent.verify_top_candidates(top_candidates, budget_max=budget_eur, wage_cap_pw=wage_cap_pw)
        state.critic_verifications = verifications
        flagged_count = sum(1 for v in verifications if v.flagged_caveats)
        emit(
            agent=critic_agent.role_name,
            action_type="CRITIC_VERIFICATION",
            message=f"Checked {len(verifications)} stored records ({flagged_count} with caveats). This is not external fact verification.",
            details={"flagged_count": flagged_count}
        )

        # Milestone 6: Squad Impact Proxy Simulation
        impact_sims = []
        for c in top_candidates:
            sim_res = tools.run_squad_impact_sim(c.model_dump(), club=club)
            impact_sims.append(sim_res)
        state.squad_impact_simulations = impact_sims
        emit(
            agent="Squad Impact Simulator",
            action_type="SIMULATE_IMPACT",
            message="Calculated an illustrative squad impact proxy using the available Arsenal reference baseline."
        )

        # Milestone 7: Final Executive Synthesis
        top_name = top_candidates[0].player.name if top_candidates else "N/A"
        summary = (
            f"Demo recruitment comparison for {club}. Target archetype: {profile.tactical_role_name} ({profile.position_family}). "
            f"Top recommendation is {top_name} (Fit Score: {top_candidates[0].fit_score if top_candidates else 0}/100, "
            f"Reliability: {top_candidates[0].reliability_score if top_candidates else 0}/100) based on reproducible "
            f"league-adjusted performance metrics and financial compatibility."
        )

        if not top_candidates:
            summary = ("No players in the demo dataset meet every constraint. "
                       "Review the effective brief, then explicitly adjust budget, age, foot or minutes and search again.")

        dossier = FinalRecruitmentDossier(
            status="complete" if top_candidates else "no_matches",
            eligible_candidate_count=len(ranked_candidates),
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

        emit(
            agent=self.role_name,
            action_type="FINAL_DOSSIER_READY",
            message=f"Scouting Dossier finalized. Top recommendation: {top_name}."
        )

        return state, dossier

director_orchestrator = DirectorOfFootballOrchestrator()
