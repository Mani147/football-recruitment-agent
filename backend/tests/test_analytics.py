import pytest
from backend.app.schemas.player import PlayerProfile, RawPlayerMetrics, NormalizedPlayerPercentiles
from backend.app.schemas.recruitment import RecruitmentProfile, TargetPercentiles, PriorityWeights
from backend.app.analytics.league_adjustment import get_league_coefficient, adjust_percentiles_for_league
from backend.app.analytics.reliability import calculate_reliability_score
from backend.app.analytics.financial_model import calculate_amortization_and_cost, evaluate_financial_fit
from backend.app.analytics.scoring_engine import calculate_tactical_match, rank_candidates
from backend.app.analytics.transfer_simulator import simulate_squad_impact

@pytest.fixture
def sample_player():
    return PlayerProfile(
        id="p1",
        name="Martín Zubimendi",
        age=25,
        primary_position="DM",
        secondary_positions=["CM"],
        club="Real Sociedad",
        league="La Liga",
        nationality="Spain",
        preferred_foot="Right",
        height_cm=181,
        market_value_eur=45_000_000.0,
        weekly_wage_eur=75_000.0,
        contract_expiry_year=2027,
        raw_metrics=RawPlayerMetrics(
            minutes_played=2100,
            matches_played=26,
            goals_per90=0.08,
            assists_per90=0.12,
            xg_per90=0.06,
            xa_per90=0.10,
            progressive_passes_per90=7.2,
            progressive_carries_per90=2.4,
            tackles_per90=2.3,
            interceptions_per90=1.8,
            pressures_recoveries_per90=8.4,
            aerial_duels_won_pct=62.5,
            key_passes_per90=1.1,
            turnovers_per90=0.9,
            pass_completion_pct=88.4
        ),
        normalized_percentiles=NormalizedPlayerPercentiles(
            progressive_passes=88.0,
            progressive_carries=72.0,
            tackles_interceptions=84.0,
            ball_recoveries_pressures=89.0,
            aerial_dominance=68.0,
            chance_creation_xa=62.0,
            possession_retention=86.0,
            goal_threat_xg=45.0
        ),
        scouting_narrative="Composed deep-lying controller and ball winner with elite progressive distribution."
    )

@pytest.fixture
def recruitment_profile():
    return RecruitmentProfile(
        position_family="DM",
        position="DM",
        tactical_role_name="Deep-Lying Controller & Ball Winner",
        age_min=18,
        age_max=26,
        budget_max_eur=60_000_000.0,
        wage_cap_eur_pw=100_000.0,
        min_minutes_played=900,
        target_percentiles=TargetPercentiles(
            progressive_passes=80.0,
            progressive_carries=65.0,
            tackles_interceptions=80.0,
            ball_recoveries_pressures=85.0,
            aerial_dominance=60.0,
            chance_creation_xa=50.0,
            possession_retention=80.0,
            goal_threat_xg=30.0
        ),
        priority_weights=PriorityWeights(
            defensive=0.35,
            progression=0.35,
            pressing_recovery=0.20,
            possession_retention=0.10,
            creation_goal=0.0
        )
    )

def test_league_adjustment(sample_player):
    coef = get_league_coefficient("La Liga")
    assert coef == 0.93
    adj = adjust_percentiles_for_league(sample_player.normalized_percentiles, sample_player.league)
    assert adj.progressive_passes == round(88.0 * 0.93, 1)
    assert 0.0 <= adj.progressive_passes <= 100.0

def test_reliability_score(sample_player):
    score, summary = calculate_reliability_score(sample_player)
    assert 0.0 <= score <= 100.0
    assert score >= 80.0  # Full 2100 mins should yield high reliability
    assert "Robust full-season sample" in summary

def test_financial_amortization(sample_player):
    res = calculate_amortization_and_cost(sample_player, contract_years=5)
    assert res["transfer_fee_eur"] == 45_000_000.0
    assert res["annual_amortization_eur"] == 9_000_000.0
    assert res["annual_gross_salary_eur"] == 75_000.0 * 52.0
    assert res["total_annual_book_cost_eur"] == 9_000_000.0 + (75_000.0 * 52.0)

def test_financial_fit(sample_player, recruitment_profile):
    fit_score, status = evaluate_financial_fit(
        sample_player,
        recruitment_profile.budget_max_eur,
        recruitment_profile.wage_cap_eur_pw
    )
    assert 0.0 <= fit_score <= 100.0
    assert status == "Within Budget Headroom"

def test_ranking_engine(sample_player, recruitment_profile):
    ranked = rank_candidates([sample_player], recruitment_profile)
    assert len(ranked) == 1
    top = ranked[0]
    assert top.rank == 1
    assert 0.0 <= top.fit_score <= 100.0
    assert 0.0 <= top.tactical_fit_score <= 100.0
    assert len(top.why_recommended) > 0
    assert len(top.risk_factors) > 0

def test_squad_impact_simulator(sample_player, recruitment_profile):
    ranked = rank_candidates([sample_player], recruitment_profile)[0]
    sim = simulate_squad_impact(ranked, club="Arsenal FC")
    assert sim.candidate_id == "p1"
    assert sim.projected_squad_defense >= 70.0
    assert sim.projected_squad_progression >= 70.0
    assert "Projected squad impact (Proxy)" in sim.summary
