import re
from typing import Optional
from backend.app.schemas.recruitment import (
    RecruitmentProfile,
    TargetPercentiles,
    PriorityWeights,
    PositionFamily,
    POSITION_GROUPS
)

def has_word(text: str, *words: str) -> bool:
    """
    True if ANY of `words` appears as a whole word (or phrase) in `text`.
    Uses regex word boundaries to prevent substring false-positives
    (e.g. 'am' inside 'team', 'st' inside 'assist', 'cm' inside 'become').
    """
    for w in words:
        pattern = r'(?<![a-z])' + re.escape(w) + r'(?![a-z])'
        if re.search(pattern, text):
            return True
    return False


CLUBS_MAP = {
    "bayern": "Bayern Munich",
    "bayern munich": "Bayern Munich",
    "arsenal": "Arsenal FC",
    "arsenal fc": "Arsenal FC",
    "real madrid": "Real Madrid",
    "barcelona": "FC Barcelona",
    "barca": "FC Barcelona",
    "man city": "Manchester City",
    "manchester city": "Manchester City",
    "chelsea": "Chelsea FC",
    "liverpool": "Liverpool FC",
    "psg": "Paris Saint-Germain",
    "juventus": "Juventus",
    "inter": "Inter Milan",
    "milan": "AC Milan",
    "dortmund": "Borussia Dortmund",
    "bayer leverkusen": "Bayer Leverkusen",
    "leverkusen": "Bayer Leverkusen",
    "tottenham": "Tottenham Hotspur",
    "spurs": "Tottenham Hotspur",
    "man utd": "Manchester United",
    "manchester united": "Manchester United"
}

def extract_target_club(prompt: str, default_club: str = "Arsenal FC") -> str:
    lower = prompt.lower()
    for key, name in CLUBS_MAP.items():
        # Match 'for Bayern', 'at Bayern', 'by Bayern' or bare club mentions
        pattern = rf'\b(?:for|at|with|by|to)?\s*{re.escape(key)}\b'
        if re.search(pattern, lower):
            return name
    return default_club

class TacticalRequirementsAgent:
    def __init__(self):
        self.role_name = "Tactical Analyst Agent"

    def generate_profile(
        self,
        user_prompt: str,
        club: str = "Arsenal FC",
        budget_eur: float = 50_000_000.0,
        wage_cap_pw: float = 120_000.0
    ) -> RecruitmentProfile:
        lower = user_prompt.lower()
        target_club = extract_target_club(user_prompt, default_club=club)

        # 1. FULLBACK / WINGBACK (FB) - Checked BEFORE generic defender/CB
        if has_word(lower,
            "fullback", "full back", "full-back",
            "left back", "left-back", "lwb",
            "right back", "right-back", "rwb",
            "wing back", "wing-back", "overlapping back"
        ) or (has_word(lower, "lb") and has_word(lower, "back", "fullback", "defender")) \
          or (has_word(lower, "rb") and has_word(lower, "back", "fullback", "defender")):
            is_left = has_word(lower, "left", "lwb") or (has_word(lower, "lb") and not has_word(lower, "rb"))
            is_right = has_word(lower, "right", "rwb") or (has_word(lower, "rb") and not has_word(lower, "lb"))
            specific_pos = "LB" if is_left else ("RB" if is_right else "LB")
            # Use sided subgroup so SQL only returns left-side or right-side players
            pos_family = "LB" if is_left else ("RB" if is_right else "FB")

            role = f"Dynamic Overlapping {'Left' if is_left else ('Right' if is_right else '')} Fullback"
            if "invert" in lower:
                role = f"Inverted {'Left' if is_left else ('Right' if is_right else '')} Fullback"

            target_pct = TargetPercentiles(
                progressive_passes=78.0,
                progressive_carries=85.0 if "carry" in lower or "overlap" in lower else 75.0,
                tackles_interceptions=80.0,
                ball_recoveries_pressures=82.0,
                aerial_dominance=55.0,
                chance_creation_xa=70.0 if "cross" in lower or "attack" in lower else 60.0,
                possession_retention=82.0,
                goal_threat_xg=45.0
            )
            weights = PriorityWeights(
                defensive=0.30,
                progression=0.35,
                pressing_recovery=0.15,
                possession_retention=0.10,
                creation_goal=0.10
            )

        # 2. GOALKEEPER (GK)
        elif has_word(lower, "goalkeeper", "keeper", "gk", "shot stopper", "sweeper keeper"):
            pos_family = "GK"
            specific_pos = "GK"
            role = "Sweeper Keeper & Modern Distributor"
            target_pct = TargetPercentiles(
                progressive_passes=75.0,
                progressive_carries=40.0,
                tackles_interceptions=50.0,
                ball_recoveries_pressures=60.0,
                aerial_dominance=85.0,
                chance_creation_xa=30.0,
                possession_retention=88.0,
                goal_threat_xg=10.0
            )
            weights = PriorityWeights(
                defensive=0.45,
                progression=0.30,
                pressing_recovery=0.10,
                possession_retention=0.15,
                creation_goal=0.0
            )

        # 3. CENTER BACK (CB)
        elif has_word(lower,
            "center back", "centre back", "center-back", "centre-back",
            "cb", "central defender", "high line defender", "stopper"
        ):
            pos_family = "CB"
            specific_pos = "CB"
            role = "Ball-Playing High-Line Center Back"
            target_pct = TargetPercentiles(
                progressive_passes=80.0,
                progressive_carries=75.0,
                tackles_interceptions=88.0,
                ball_recoveries_pressures=80.0,
                aerial_dominance=80.0 if "aerial" in lower or "tall" in lower else 70.0,
                chance_creation_xa=45.0,
                possession_retention=88.0,
                goal_threat_xg=40.0
            )
            weights = PriorityWeights(
                defensive=0.40,
                progression=0.30,
                pressing_recovery=0.15,
                possession_retention=0.15,
                creation_goal=0.0
            )

        # 4. DEFENSIVE MIDFIELDER (DM)
        elif has_word(lower,
            "defensive midfielder", "dm", "holding midfielder", "pivot",
            "ball winner", "ball-winner", "no 6", "number 6", "number six", "regista", "destroyer"
        ):
            pos_family = "DM"
            specific_pos = "DM"
            role = "Box-to-Box Ball Winner & Press Resister" if "press" in lower or "recover" in lower else "Deep-Lying Controller"
            target_pct = TargetPercentiles(
                progressive_passes=85.0 if "pass" in lower or "progress" in lower else 75.0,
                progressive_carries=75.0 if "carry" in lower or "dribbl" in lower else 65.0,
                tackles_interceptions=85.0,
                ball_recoveries_pressures=90.0 if "press" in lower else 80.0,
                aerial_dominance=65.0,
                chance_creation_xa=55.0,
                possession_retention=85.0,
                goal_threat_xg=35.0
            )
            weights = PriorityWeights(
                defensive=0.35,
                progression=0.30,
                pressing_recovery=0.20,
                possession_retention=0.15,
                creation_goal=0.0
            )

        # 5. CENTRAL MIDFIELDER (CM)
        elif has_word(lower,
            "central midfielder", "cm", "box to box", "box-to-box",
            "no 8", "number 8", "number eight", "mezzala"
        ):
            pos_family = "CM"
            specific_pos = "CM"
            role = "All-Action Central Midfield Engine"
            target_pct = TargetPercentiles(
                progressive_passes=82.0,
                progressive_carries=80.0,
                tackles_interceptions=75.0,
                ball_recoveries_pressures=82.0,
                aerial_dominance=60.0,
                chance_creation_xa=70.0,
                possession_retention=84.0,
                goal_threat_xg=55.0
            )
            weights = PriorityWeights(
                defensive=0.25,
                progression=0.30,
                pressing_recovery=0.20,
                possession_retention=0.15,
                creation_goal=0.10
            )

        # 6. ATTACKING MIDFIELDER (AM)
        elif has_word(lower,
            "attacking midfielder", "am", "no 10", "number 10", "number ten",
            "playmaker", "advanced playmaker", "cam"
        ):
            pos_family = "AM"
            specific_pos = "AM"
            role = "Creative Advanced Playmaker (No. 10)"
            target_pct = TargetPercentiles(
                progressive_passes=88.0,
                progressive_carries=88.0,
                tackles_interceptions=45.0,
                ball_recoveries_pressures=55.0,
                aerial_dominance=40.0,
                chance_creation_xa=92.0,
                possession_retention=82.0,
                goal_threat_xg=75.0
            )
            weights = PriorityWeights(
                defensive=0.05,
                progression=0.35,
                pressing_recovery=0.10,
                possession_retention=0.15,
                creation_goal=0.35
            )

        # 7. WINGER (LW / RW)
        elif has_word(lower,
            "winger", "right winger", "left winger",
            "wide attacker", "wide forward", "rw", "lw"
        ):
            pos_family = "WINGER"
            is_left = has_word(lower, "left", "lw")
            is_right = has_word(lower, "right", "rw")
            specific_pos = "LW" if is_left else ("RW" if is_right else "RW")
            role = f"Explosive 1v1 Inverted {'Left' if is_left else 'Right'} Winger"
            target_pct = TargetPercentiles(
                progressive_passes=75.0,
                progressive_carries=92.0,
                tackles_interceptions=55.0,
                ball_recoveries_pressures=60.0,
                aerial_dominance=40.0,
                chance_creation_xa=85.0,
                possession_retention=78.0,
                goal_threat_xg=85.0
            )
            weights = PriorityWeights(
                defensive=0.05,
                progression=0.35,
                pressing_recovery=0.10,
                possession_retention=0.15,
                creation_goal=0.35
            )

        # 8. STRIKER / CENTER FORWARD (ST)
        elif any(w in lower for w in [
            "striker", "st", "cf", "centre forward", "center forward",
            "number 9", "number nine", "no 9", "target man", "goalscorer"
        ]):
            pos_family = "ST"
            specific_pos = "ST"
            role = "Clinical Complete Center Forward"
            target_pct = TargetPercentiles(
                progressive_passes=65.0,
                progressive_carries=80.0,
                tackles_interceptions=40.0,
                ball_recoveries_pressures=55.0,
                aerial_dominance=75.0 if "aerial" in lower or "target" in lower else 60.0,
                chance_creation_xa=70.0,
                possession_retention=78.0,
                goal_threat_xg=92.0
            )
            weights = PriorityWeights(
                defensive=0.05,
                progression=0.20,
                pressing_recovery=0.10,
                possession_retention=0.15,
                creation_goal=0.50
            )

        # 9. UNKNOWN / AMBIGUOUS - Never silently fallback to DM!
        else:
            pos_family = "UNKNOWN"
            specific_pos = "UNKNOWN"
            role = "Ambiguous Recruitment Position"
            target_pct = TargetPercentiles()
            weights = PriorityWeights()

        # Parse Age
        age_max = 25
        match_u = re.search(r'\bu(\d{2})\b', lower)
        match_under = re.search(r'under\s+(\d{2})\s+years?', lower)
        match_age = re.search(r'age\s*(?:<=|<|under)?\s*(\d{2})', lower)
        if match_u:
            age_max = int(match_u.group(1))
        elif match_under:
            age_max = int(match_under.group(1))
        elif match_age:
            age_max = int(match_age.group(1))

        # Parse Budget
        custom_budget = budget_eur
        m_b = re.search(r'(?:under|budget of|max|for|below)\s*(?:€|\$|£)?\s*(\d+)\s*(?:m|million)?', lower)
        if m_b:
            custom_budget = float(m_b.group(1)) * 1_000_000.0

        preferred_foot = "Left" if "left-footed" in lower or "left foot" in lower else ("Right" if "right-footed" in lower or "right foot" in lower else None)

        return RecruitmentProfile(
            target_club=target_club,
            position_family=pos_family,
            position=specific_pos,
            tactical_role_name=role,
            age_min=18,
            age_max=age_max,
            budget_max_eur=custom_budget,
            wage_cap_eur_pw=wage_cap_pw,
            min_minutes_played=800,
            target_percentiles=target_pct,
            priority_weights=weights,
            preferred_foot=preferred_foot,
            tactical_notes=f"Formulated for {target_club} from mandate: '{user_prompt}'"
        )

tactical_agent = TacticalRequirementsAgent()
