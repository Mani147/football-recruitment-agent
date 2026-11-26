"""One eligibility gate for SQL, semantic retrieval and final ranking."""
from backend.app.schemas.player import PlayerProfile, position_matches
from backend.app.schemas.recruitment import RecruitmentProfile

def eligibility_failures(player: PlayerProfile, profile: RecruitmentProfile) -> list[str]:
    failures = []
    if profile.target_club and player.club.casefold().strip() == profile.target_club.casefold().strip():
        failures.append("already at recruiting club")
    if not position_matches(player, profile.position_family, profile.position):
        failures.append("position")
    if not profile.age_min <= player.age <= profile.age_max:
        failures.append("age")
    if player.market_value_eur > profile.budget_max_eur:
        failures.append("fee")
    if player.weekly_wage_eur > profile.wage_cap_eur_pw:
        failures.append("wage")
    if player.raw_metrics.minutes_played < profile.min_minutes_played:
        failures.append("minutes")
    if profile.preferred_foot and player.preferred_foot.casefold() != profile.preferred_foot.casefold():
        failures.append("preferred foot")
    return failures
