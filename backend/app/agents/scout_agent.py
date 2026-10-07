from typing import List, Tuple
from backend.app.schemas.player import PlayerProfile, position_matches
from backend.app.schemas.recruitment import RecruitmentProfile, POSITION_GROUPS
from backend.app.schemas.dossier import RankedCandidate
from backend.app.agents.tools import tools
from backend.app.analytics.scoring_engine import rank_candidates

CLARIFICATION_MESSAGE = """
⚠️ Recruitment Position Unclear

The Director could not determine a supported tactical position from your mandate.

Supported positions:
  • Goalkeeper           → "goalkeeper", "GK", "sweeper keeper"
  • Fullback             → "fullback", "left back", "right back", "LB", "RB", "wing back"
  • Center Back          → "center back", "centre-back", "CB", "central defender"
  • Defensive Midfielder → "defensive midfielder", "DM", "holding midfielder", "pivot", "ball winner"
  • Central Midfielder   → "central midfielder", "CM", "box-to-box", "number 8"
  • Attacking Midfielder → "attacking midfielder", "AM", "playmaker", "number 10"
  • Winger               → "winger", "LW", "RW", "left winger", "right winger"
  • Striker              → "striker", "ST", "CF", "centre forward", "number 9"

Please rephrase your mandate using one of the above position terms.
""".strip()


class PlayerScoutAgent:
    def __init__(self):
        self.role_name = "Player Scout Agent"

    def retrieve_and_rank_candidates(
        self,
        profile: RecruitmentProfile,
        query_context: str
    ) -> Tuple[List[PlayerProfile], List[RankedCandidate]]:
        """
        Hybrid retrieval workflow:
        1. Guard against UNKNOWN position — never silently default to DM.
        2. SQL Hard constraint filtering using position_family expansion.
        3. Semantic similarity matching on tactical narrative.
        4. Centralized position_matches() gate before combining pools.
        5. Deterministic Python multi-criteria scoring and ranking.
        """

        # --- Guard: Do NOT proceed with an unknown position ---
        if profile.position_family.upper() == "UNKNOWN" or profile.position.upper() == "UNKNOWN":
            raise ValueError(CLARIFICATION_MESSAGE)

        # --- Step 1: SQL Filter with position_family expansion ---
        sql_results = tools.search_candidates_sql(
            position_family=profile.position_family,
            position=profile.position,
            max_age=profile.age_max,
            max_budget_eur=profile.budget_max_eur,
            max_wage_eur_pw=profile.wage_cap_eur_pw,
            min_minutes=profile.min_minutes_played
        )

        # If too few results, relax constraints slightly (but keep position strict)
        if len(sql_results) < 2:
            sql_results = tools.search_candidates_sql(
                position_family=profile.position_family,
                position=profile.position,
                max_age=profile.age_max + 2,
                max_budget_eur=profile.budget_max_eur * 1.30,
                min_minutes=500
            )

        candidate_pool = [PlayerProfile(**m) for m in sql_results]
        candidate_ids = {p.id for p in candidate_pool}

        # --- Step 2: Semantic vector match, gated by centralized position_matches() ---
        semantic_matches = tools.search_semantic_profiles(query_text=query_context, top_k=8)
        semantic_pool = []
        for m in semantic_matches:
            if m["player"]["id"] in candidate_ids:
                continue
            player = PlayerProfile(**m["player"])
            # Centralized position check — handles FB → LB/RB/LWB/RWB expansion
            if position_matches(player, profile.position_family, profile.position):
                semantic_pool.append(player)

        combined_pool = candidate_pool + semantic_pool

        # --- Step 3: Deterministic Ranking ---
        ranked_candidates = rank_candidates(combined_pool, profile)

        return combined_pool, ranked_candidates


scout_agent = PlayerScoutAgent()

