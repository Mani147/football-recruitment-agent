"""
Seed database — 2025/26 Season Benchmark Dataset
Data Vintage  : Summer 2026 (pre-season estimates)
Sources       : StatsBomb-style metrics (illustrative), market values via
                Transfermarkt benchmark (estimated), contract data via public
                press reports. All values are labeled as estimated benchmarks.
NOTE          : This is an illustrative dataset for portfolio demonstration.
                A production deployment would ingest live StatsBomb / Opta /
                Transfermarkt API feeds.
"""
from backend.app.schemas.player import PlayerProfile, RawPlayerMetrics, NormalizedPlayerPercentiles
from backend.app.data.sqlite_db import db
from backend.app.data.vector_store import vector_store

PLAYERS_2526: list[PlayerProfile] = [

    # ══════════════════════════════════════════════════════════════════
    # FULLBACKS / WING-BACKS  (LB · RB · LWB · RWB)
    # ══════════════════════════════════════════════════════════════════

    PlayerProfile(
        id="fb_frimpong",
        name="Jeremie Frimpong",
        age=25,                                  # +1 from 2024/25
        primary_position="RB", secondary_positions=["RWB", "RM"],
        club="Bayer Leverkusen", league="Bundesliga", nationality="Netherlands",
        preferred_foot="Right", height_cm=171,
        market_value_eur=55_000_000.0,           # risen after another strong season
        weekly_wage_eur=100_000.0,
        contract_expiry_year=2028,
        release_clause_eur=45_000_000.0,
        raw_metrics=RawPlayerMetrics(
            minutes_played=2480, matches_played=30,
            goals_per90=0.40, assists_per90=0.34,
            xg_per90=0.37, xa_per90=0.30,
            progressive_passes_per90=5.1, progressive_carries_per90=9.4,
            tackles_per90=1.7, interceptions_per90=1.2,
            pressures_recoveries_per90=6.0,
            aerial_duels_won_pct=41.0, key_passes_per90=2.2,
            turnovers_per90=2.0, pass_completion_pct=83.8,
        ),
        normalized_percentiles=NormalizedPlayerPercentiles(
            progressive_passes=78.0, progressive_carries=99.0,
            tackles_interceptions=70.0, ball_recoveries_pressures=74.0,
            aerial_dominance=39.0, chance_creation_xa=95.0,
            possession_retention=82.0, goal_threat_xg=97.0,
        ),
        scouting_narrative=(
            "Ultra-offensive right wing-back with unmatched sprint speed, "
            "high-volume penalty-box entries, and a remarkable goals+assists "
            "return for a defender — the best attacking right-back in the Bundesliga."
        ),
    ),

    PlayerProfile(
        id="fb_udogie",
        name="Destiny Udogie",
        age=24,
        primary_position="LB", secondary_positions=["LWB"],
        club="Tottenham Hotspur", league="Premier League", nationality="Italy",
        preferred_foot="Left", height_cm=188,
        market_value_eur=55_000_000.0,
        weekly_wage_eur=95_000.0,
        contract_expiry_year=2030,
        release_clause_eur=None,
        raw_metrics=RawPlayerMetrics(
            minutes_played=2250, matches_played=27,
            goals_per90=0.12, assists_per90=0.20,
            xg_per90=0.10, xa_per90=0.18,
            progressive_passes_per90=5.5, progressive_carries_per90=6.8,
            tackles_per90=3.2, interceptions_per90=1.6,
            pressures_recoveries_per90=8.1,
            aerial_duels_won_pct=66.0, key_passes_per90=1.5,
            turnovers_per90=1.3, pass_completion_pct=86.5,
        ),
        normalized_percentiles=NormalizedPlayerPercentiles(
            progressive_passes=83.0, progressive_carries=91.0,
            tackles_interceptions=91.0, ball_recoveries_pressures=89.0,
            aerial_dominance=70.0, chance_creation_xa=77.0,
            possession_retention=86.0, goal_threat_xg=57.0,
        ),
        scouting_narrative=(
            "Physically imposing inverted left-back commanding the Premier League "
            "for aggressive ground duels, underlapping interior runs, and elite "
            "transition-phase pressing — one of England's best left-backs."
        ),
    ),

    PlayerProfile(
        id="fb_lewis_skelly",
        name="Myles Lewis-Skelly",
        age=19,                                  # NEW — Arsenal's breakout 2025/26 LB
        primary_position="LB", secondary_positions=["DM", "LWB"],
        club="Arsenal FC", league="Premier League", nationality="England",
        preferred_foot="Left", height_cm=183,
        market_value_eur=40_000_000.0,
        weekly_wage_eur=50_000.0,
        contract_expiry_year=2029,
        release_clause_eur=None,
        raw_metrics=RawPlayerMetrics(
            minutes_played=1950, matches_played=24,
            goals_per90=0.09, assists_per90=0.14,
            xg_per90=0.08, xa_per90=0.13,
            progressive_passes_per90=6.2, progressive_carries_per90=5.9,
            tackles_per90=3.4, interceptions_per90=2.0,
            pressures_recoveries_per90=8.8,
            aerial_duels_won_pct=58.0, key_passes_per90=1.3,
            turnovers_per90=1.1, pass_completion_pct=87.2,
        ),
        normalized_percentiles=NormalizedPlayerPercentiles(
            progressive_passes=86.0, progressive_carries=87.0,
            tackles_interceptions=93.0, ball_recoveries_pressures=91.0,
            aerial_dominance=60.0, chance_creation_xa=72.0,
            possession_retention=87.0, goal_threat_xg=50.0,
        ),
        scouting_narrative=(
            "Extraordinary 19-year-old left-back — equally comfortable as a "
            "holding midfielder — with elite press resistance, aggressive "
            "ball-winning, and composed progressive distribution beyond his years."
        ),
    ),

    PlayerProfile(
        id="fb_kayode",
        name="Michael Kayode",
        age=22,
        primary_position="RB", secondary_positions=["RWB"],
        club="Fiorentina", league="Serie A", nationality="Italy",
        preferred_foot="Right", height_cm=181,
        market_value_eur=30_000_000.0,
        weekly_wage_eur=35_000.0,
        contract_expiry_year=2028,
        release_clause_eur=None,
        raw_metrics=RawPlayerMetrics(
            minutes_played=2050, matches_played=26,
            goals_per90=0.06, assists_per90=0.14,
            xg_per90=0.05, xa_per90=0.12,
            progressive_passes_per90=5.1, progressive_carries_per90=6.2,
            tackles_per90=3.3, interceptions_per90=1.9,
            pressures_recoveries_per90=7.9,
            aerial_duels_won_pct=70.0, key_passes_per90=1.1,
            turnovers_per90=1.0, pass_completion_pct=84.0,
        ),
        normalized_percentiles=NormalizedPlayerPercentiles(
            progressive_passes=76.0, progressive_carries=87.0,
            tackles_interceptions=92.0, ball_recoveries_pressures=86.0,
            aerial_dominance=74.0, chance_creation_xa=65.0,
            possession_retention=81.0, goal_threat_xg=44.0,
        ),
        scouting_narrative=(
            "Athletic, defensively dominant right-back leading Serie A for "
            "aerial duels and 1v1 isolation wins — an undervalued option at "
            "€30M with a strong upside trajectory."
        ),
    ),

    # ══════════════════════════════════════════════════════════════════
    # DEFENSIVE MIDFIELDERS  (DM)
    # ══════════════════════════════════════════════════════════════════

    PlayerProfile(
        id="dm_zubimendi",
        name="Martín Zubimendi",
        age=26,
        primary_position="DM", secondary_positions=["CM"],
        club="Real Sociedad", league="La Liga", nationality="Spain",
        preferred_foot="Right", height_cm=181,
        market_value_eur=55_000_000.0,
        weekly_wage_eur=85_000.0,
        contract_expiry_year=2027,
        release_clause_eur=60_000_000.0,
        raw_metrics=RawPlayerMetrics(
            minutes_played=2500, matches_played=30,
            goals_per90=0.08, assists_per90=0.12,
            xg_per90=0.06, xa_per90=0.10,
            progressive_passes_per90=7.8, progressive_carries_per90=2.5,
            tackles_per90=2.5, interceptions_per90=2.0,
            pressures_recoveries_per90=8.9,
            aerial_duels_won_pct=65.0, key_passes_per90=1.3,
            turnovers_per90=0.7, pass_completion_pct=89.2,
        ),
        normalized_percentiles=NormalizedPlayerPercentiles(
            progressive_passes=92.0, progressive_carries=74.0,
            tackles_interceptions=86.0, ball_recoveries_pressures=90.0,
            aerial_dominance=69.0, chance_creation_xa=64.0,
            possession_retention=92.0, goal_threat_xg=44.0,
        ),
        scouting_narrative=(
            "Spain's first-choice pivot — elite spatial awareness, flawless press "
            "resistance, and masterclass progressive distribution from deep. "
            "Release clause intact at €60M; one of Europe's best sixes."
        ),
    ),

    PlayerProfile(
        id="dm_neves",
        name="João Neves",
        age=21,
        primary_position="DM", secondary_positions=["CM"],
        club="Paris Saint-Germain", league="Ligue 1", nationality="Portugal",
        preferred_foot="Right", height_cm=174,
        market_value_eur=80_000_000.0,            # risen significantly
        weekly_wage_eur=120_000.0,
        contract_expiry_year=2029,
        release_clause_eur=None,
        raw_metrics=RawPlayerMetrics(
            minutes_played=2300, matches_played=28,
            goals_per90=0.09, assists_per90=0.16,
            xg_per90=0.07, xa_per90=0.15,
            progressive_passes_per90=8.4, progressive_carries_per90=3.4,
            tackles_per90=3.6, interceptions_per90=2.2,
            pressures_recoveries_per90=10.6,
            aerial_duels_won_pct=56.0, key_passes_per90=1.6,
            turnovers_per90=1.0, pass_completion_pct=90.1,
        ),
        normalized_percentiles=NormalizedPlayerPercentiles(
            progressive_passes=94.0, progressive_carries=86.0,
            tackles_interceptions=95.0, ball_recoveries_pressures=98.0,
            aerial_dominance=53.0, chance_creation_xa=76.0,
            possession_retention=89.0, goal_threat_xg=49.0,
        ),
        scouting_narrative=(
            "Arguably the best young defensive midfielder in world football — "
            "leads PSG and Ligue 1 for ball recovery volume, combines relentless "
            "press intensity with elite vertical passing vision."
        ),
    ),

    PlayerProfile(
        id="dm_wharton",
        name="Adam Wharton",
        age=22,
        primary_position="DM", secondary_positions=["CM"],
        club="Crystal Palace", league="Premier League", nationality="England",
        preferred_foot="Left", height_cm=182,
        market_value_eur=52_000_000.0,
        weekly_wage_eur=75_000.0,
        contract_expiry_year=2029,
        release_clause_eur=None,
        raw_metrics=RawPlayerMetrics(
            minutes_played=2100, matches_played=25,
            goals_per90=0.06, assists_per90=0.20,
            xg_per90=0.05, xa_per90=0.18,
            progressive_passes_per90=8.8, progressive_carries_per90=2.3,
            tackles_per90=3.0, interceptions_per90=1.9,
            pressures_recoveries_per90=8.3,
            aerial_duels_won_pct=59.0, key_passes_per90=1.7,
            turnovers_per90=0.9, pass_completion_pct=87.0,
        ),
        normalized_percentiles=NormalizedPlayerPercentiles(
            progressive_passes=95.0, progressive_carries=70.0,
            tackles_interceptions=89.0, ball_recoveries_pressures=83.0,
            aerial_dominance=62.0, chance_creation_xa=80.0,
            possession_retention=85.0, goal_threat_xg=39.0,
        ),
        scouting_narrative=(
            "Left-footed progressive passing phenom — the highest pass-completion "
            "line-breaker in the Premier League for his position. England "
            "international with calm decisiveness and outstanding football IQ."
        ),
    ),

    PlayerProfile(
        id="dm_baleba",
        name="Carlos Baleba",
        age=22,
        primary_position="DM", secondary_positions=["CM"],
        club="Brighton & Hove Albion", league="Premier League", nationality="Cameroon",
        preferred_foot="Left", height_cm=179,
        market_value_eur=42_000_000.0,
        weekly_wage_eur=50_000.0,
        contract_expiry_year=2028,
        release_clause_eur=None,
        raw_metrics=RawPlayerMetrics(
            minutes_played=1850, matches_played=24,
            goals_per90=0.07, assists_per90=0.07,
            xg_per90=0.06, xa_per90=0.08,
            progressive_passes_per90=6.1, progressive_carries_per90=4.2,
            tackles_per90=3.2, interceptions_per90=1.7,
            pressures_recoveries_per90=9.1,
            aerial_duels_won_pct=62.0, key_passes_per90=0.9,
            turnovers_per90=1.2, pass_completion_pct=86.0,
        ),
        normalized_percentiles=NormalizedPlayerPercentiles(
            progressive_passes=76.0, progressive_carries=93.0,
            tackles_interceptions=87.0, ball_recoveries_pressures=91.0,
            aerial_dominance=66.0, chance_creation_xa=56.0,
            possession_retention=80.0, goal_threat_xg=43.0,
        ),
        scouting_narrative=(
            "Physically commanding ball-carrier capable of evading first-press "
            "traps and driving through midfield lines. Leads Brighton in duels "
            "won and turnover creation in transition."
        ),
    ),

    PlayerProfile(
        id="dm_joao_gomes",
        name="João Gomes",
        age=24,                                  # NEW — Wolves DM, solid Premier League performer
        primary_position="DM", secondary_positions=["CM"],
        club="Wolverhampton Wanderers", league="Premier League", nationality="Brazil",
        preferred_foot="Right", height_cm=177,
        market_value_eur=35_000_000.0,
        weekly_wage_eur=60_000.0,
        contract_expiry_year=2028,
        release_clause_eur=None,
        raw_metrics=RawPlayerMetrics(
            minutes_played=2600, matches_played=31,
            goals_per90=0.05, assists_per90=0.09,
            xg_per90=0.04, xa_per90=0.08,
            progressive_passes_per90=5.8, progressive_carries_per90=2.6,
            tackles_per90=4.1, interceptions_per90=2.3,
            pressures_recoveries_per90=11.2,
            aerial_duels_won_pct=58.0, key_passes_per90=0.8,
            turnovers_per90=0.8, pass_completion_pct=85.5,
        ),
        normalized_percentiles=NormalizedPlayerPercentiles(
            progressive_passes=74.0, progressive_carries=72.0,
            tackles_interceptions=97.0, ball_recoveries_pressures=99.0,
            aerial_dominance=60.0, chance_creation_xa=52.0,
            possession_retention=83.0, goal_threat_xg=36.0,
        ),
        scouting_narrative=(
            "Premier League's most relentless pressing DM — leads the division "
            "in tackles+interceptions combined for the second consecutive season. "
            "Undervalued at €35M given consistent elite defensive metrics."
        ),
    ),

    PlayerProfile(
        id="dm_musiala_cm",
        name="Jamal Musiala",
        age=23,                                  # NEW — Bayern CM/AM, elite technical profile
        primary_position="CM", secondary_positions=["AM", "LW"],
        club="Bayern Munich", league="Bundesliga", nationality="Germany",
        preferred_foot="Left", height_cm=180,
        market_value_eur=130_000_000.0,
        weekly_wage_eur=200_000.0,
        contract_expiry_year=2026,               # contract situation uncertain
        release_clause_eur=None,
        raw_metrics=RawPlayerMetrics(
            minutes_played=2350, matches_played=28,
            goals_per90=0.42, assists_per90=0.38,
            xg_per90=0.38, xa_per90=0.35,
            progressive_passes_per90=6.8, progressive_carries_per90=10.2,
            tackles_per90=1.4, interceptions_per90=0.8,
            pressures_recoveries_per90=5.5,
            aerial_duels_won_pct=42.0, key_passes_per90=3.1,
            turnovers_per90=2.4, pass_completion_pct=84.5,
        ),
        normalized_percentiles=NormalizedPlayerPercentiles(
            progressive_passes=90.0, progressive_carries=99.0,
            tackles_interceptions=52.0, ball_recoveries_pressures=62.0,
            aerial_dominance=40.0, chance_creation_xa=97.0,
            possession_retention=85.0, goal_threat_xg=96.0,
        ),
        scouting_narrative=(
            "One of the world's most complete attacking midfielders — magical "
            "dribbler, elite chance creator, and consistent finisher. Contract "
            "situation in 2026 makes him one of the most discussed potential "
            "free agents in the sport."
        ),
    ),

    # ══════════════════════════════════════════════════════════════════
    # CENTER BACKS  (CB)
    # ══════════════════════════════════════════════════════════════════

    PlayerProfile(
        id="cb_scalvini",
        name="Giorgio Scalvini",
        age=23,
        primary_position="CB", secondary_positions=["DM"],
        club="Atalanta", league="Serie A", nationality="Italy",
        preferred_foot="Right", height_cm=194,
        market_value_eur=55_000_000.0,
        weekly_wage_eur=65_000.0,
        contract_expiry_year=2028,
        release_clause_eur=None,
        raw_metrics=RawPlayerMetrics(
            minutes_played=2200, matches_played=27,
            goals_per90=0.10, assists_per90=0.09,
            xg_per90=0.09, xa_per90=0.07,
            progressive_passes_per90=5.7, progressive_carries_per90=3.0,
            tackles_per90=2.6, interceptions_per90=2.5,
            pressures_recoveries_per90=7.0,
            aerial_duels_won_pct=73.0, key_passes_per90=0.7,
            turnovers_per90=0.5, pass_completion_pct=88.5,
        ),
        normalized_percentiles=NormalizedPlayerPercentiles(
            progressive_passes=88.0, progressive_carries=89.0,
            tackles_interceptions=93.0, ball_recoveries_pressures=85.0,
            aerial_dominance=90.0, chance_creation_xa=57.0,
            possession_retention=90.0, goal_threat_xg=57.0,
        ),
        scouting_narrative=(
            "Italy's most complete young center-back — imposing aerial presence "
            "(194cm, 73% duel wins), capable of stepping into the double pivot, "
            "and a clean ball-player under pressure. Coveted across Europe."
        ),
    ),

    PlayerProfile(
        id="cb_hincapie",
        name="Piero Hincapié",
        age=24,
        primary_position="CB", secondary_positions=["LB"],
        club="Bayer Leverkusen", league="Bundesliga", nationality="Ecuador",
        preferred_foot="Left", height_cm=184,
        market_value_eur=50_000_000.0,
        weekly_wage_eur=75_000.0,
        contract_expiry_year=2028,               # extended after Leverkusen title run
        release_clause_eur=None,
        raw_metrics=RawPlayerMetrics(
            minutes_played=2150, matches_played=26,
            goals_per90=0.06, assists_per90=0.10,
            xg_per90=0.05, xa_per90=0.09,
            progressive_passes_per90=6.2, progressive_carries_per90=3.1,
            tackles_per90=2.7, interceptions_per90=2.0,
            pressures_recoveries_per90=7.3,
            aerial_duels_won_pct=64.0, key_passes_per90=0.7,
            turnovers_per90=0.6, pass_completion_pct=89.0,
        ),
        normalized_percentiles=NormalizedPlayerPercentiles(
            progressive_passes=87.0, progressive_carries=88.0,
            tackles_interceptions=90.0, ball_recoveries_pressures=86.0,
            aerial_dominance=71.0, chance_creation_xa=64.0,
            possession_retention=89.0, goal_threat_xg=46.0,
        ),
        scouting_narrative=(
            "Dynamic left-sided defender with superb recovery pace and "
            "aggressive front-foot tackling. Comfortable as a left-back "
            "in build-up phases — left-footed and capable of diagonal switches."
        ),
    ),

    PlayerProfile(
        id="cb_inacio",
        name="Gonçalo Inácio",
        age=24,
        primary_position="CB", secondary_positions=["LB"],
        club="Sporting CP", league="Liga Portugal", nationality="Portugal",
        preferred_foot="Left", height_cm=186,
        market_value_eur=50_000_000.0,
        weekly_wage_eur=55_000.0,
        contract_expiry_year=2027,
        release_clause_eur=60_000_000.0,
        raw_metrics=RawPlayerMetrics(
            minutes_played=2450, matches_played=29,
            goals_per90=0.08, assists_per90=0.11,
            xg_per90=0.07, xa_per90=0.09,
            progressive_passes_per90=7.2, progressive_carries_per90=3.8,
            tackles_per90=2.4, interceptions_per90=1.8,
            pressures_recoveries_per90=6.5,
            aerial_duels_won_pct=68.0, key_passes_per90=0.9,
            turnovers_per90=0.7, pass_completion_pct=90.1,
        ),
        normalized_percentiles=NormalizedPlayerPercentiles(
            progressive_passes=91.0, progressive_carries=90.0,
            tackles_interceptions=86.0, ball_recoveries_pressures=80.0,
            aerial_dominance=74.0, chance_creation_xa=62.0,
            possession_retention=92.0, goal_threat_xg=48.0,
        ),
        scouting_narrative=(
            "Portugal's outstanding left-footed center-back with elite distribution "
            "range and high defensive line comfort. Champions League-proven, "
            "release clause at €60M — genuinely elite ball-playing defender."
        ),
    ),

    PlayerProfile(
        id="cb_murillo",
        name="Murillo",
        age=23,                                  # NEW — Nottm Forest CB, breakout Premier League season
        primary_position="CB", secondary_positions=[],
        club="Nottingham Forest", league="Premier League", nationality="Brazil",
        preferred_foot="Right", height_cm=186,
        market_value_eur=40_000_000.0,
        weekly_wage_eur=55_000.0,
        contract_expiry_year=2028,
        release_clause_eur=None,
        raw_metrics=RawPlayerMetrics(
            minutes_played=2700, matches_played=31,
            goals_per90=0.04, assists_per90=0.04,
            xg_per90=0.04, xa_per90=0.04,
            progressive_passes_per90=5.0, progressive_carries_per90=2.2,
            tackles_per90=3.1, interceptions_per90=2.6,
            pressures_recoveries_per90=7.8,
            aerial_duels_won_pct=72.0, key_passes_per90=0.5,
            turnovers_per90=0.5, pass_completion_pct=85.5,
        ),
        normalized_percentiles=NormalizedPlayerPercentiles(
            progressive_passes=78.0, progressive_carries=80.0,
            tackles_interceptions=94.0, ball_recoveries_pressures=88.0,
            aerial_dominance=80.0, chance_creation_xa=48.0,
            possession_retention=84.0, goal_threat_xg=38.0,
        ),
        scouting_narrative=(
            "Aggressive, physically dominant Brazilian center-back who excelled in "
            "Nottingham Forest's low-block defensive structure — leads the Premier "
            "League for defensive actions and aerial duels won."
        ),
    ),

    # ══════════════════════════════════════════════════════════════════
    # STRIKERS / CENTER FORWARDS  (ST · CF)
    # ══════════════════════════════════════════════════════════════════

    PlayerProfile(
        id="st_sesko",
        name="Benjamin Šeško",
        age=23,
        primary_position="ST", secondary_positions=["CF"],
        club="RB Leipzig", league="Bundesliga", nationality="Slovenia",
        preferred_foot="Right", height_cm=195,
        market_value_eur=65_000_000.0,           # risen after another prolific season
        weekly_wage_eur=90_000.0,
        contract_expiry_year=2029,
        release_clause_eur=65_000_000.0,
        raw_metrics=RawPlayerMetrics(
            minutes_played=2200, matches_played=28,
            goals_per90=0.68, assists_per90=0.20,
            xg_per90=0.63, xa_per90=0.16,
            progressive_passes_per90=3.5, progressive_carries_per90=4.4,
            tackles_per90=0.9, interceptions_per90=0.4,
            pressures_recoveries_per90=4.5,
            aerial_duels_won_pct=70.0, key_passes_per90=1.3,
            turnovers_per90=1.8, pass_completion_pct=77.5,
        ),
        normalized_percentiles=NormalizedPlayerPercentiles(
            progressive_passes=68.0, progressive_carries=84.0,
            tackles_interceptions=49.0, ball_recoveries_pressures=62.0,
            aerial_dominance=88.0, chance_creation_xa=70.0,
            possession_retention=79.0, goal_threat_xg=97.0,
        ),
        scouting_narrative=(
            "Generational physical specimen — 195cm with explosive pace and "
            "clinical finishing. Led the Bundesliga in headed goals for a second "
            "consecutive season. Release clause at €65M is widely considered "
            "below true market value."
        ),
    ),

    PlayerProfile(
        id="st_ramos",
        name="Gonçalo Ramos",
        age=24,                                  # NEW — PSG/loan striker
        primary_position="ST", secondary_positions=["CF"],
        club="Paris Saint-Germain", league="Ligue 1", nationality="Portugal",
        preferred_foot="Right", height_cm=183,
        market_value_eur=60_000_000.0,
        weekly_wage_eur=110_000.0,
        contract_expiry_year=2028,
        release_clause_eur=None,
        raw_metrics=RawPlayerMetrics(
            minutes_played=1950, matches_played=27,
            goals_per90=0.55, assists_per90=0.22,
            xg_per90=0.50, xa_per90=0.20,
            progressive_passes_per90=4.2, progressive_carries_per90=5.8,
            tackles_per90=1.0, interceptions_per90=0.5,
            pressures_recoveries_per90=5.2,
            aerial_duels_won_pct=55.0, key_passes_per90=1.6,
            turnovers_per90=1.9, pass_completion_pct=79.5,
        ),
        normalized_percentiles=NormalizedPlayerPercentiles(
            progressive_passes=72.0, progressive_carries=88.0,
            tackles_interceptions=50.0, ball_recoveries_pressures=65.0,
            aerial_dominance=62.0, chance_creation_xa=82.0,
            possession_retention=80.0, goal_threat_xg=93.0,
        ),
        scouting_narrative=(
            "Intelligent, mobile Portuguese center-forward who links play "
            "brilliantly and scores at an elite rate. Champions League pedigree — "
            "hat-trick on his CL debut for Benfica remains iconic."
        ),
    ),

    # ══════════════════════════════════════════════════════════════════
    # GOALKEEPERS  (GK)
    # ══════════════════════════════════════════════════════════════════

    PlayerProfile(
        id="gk_costa",
        name="Diogo Costa",
        age=26,
        primary_position="GK", secondary_positions=[],
        club="FC Porto", league="Liga Portugal", nationality="Portugal",
        preferred_foot="Right", height_cm=186,
        market_value_eur=50_000_000.0,
        weekly_wage_eur=65_000.0,
        contract_expiry_year=2027,
        release_clause_eur=75_000_000.0,
        raw_metrics=RawPlayerMetrics(
            minutes_played=2700, matches_played=30,
            goals_per90=0.0, assists_per90=0.02,
            xg_per90=0.0, xa_per90=0.02,
            progressive_passes_per90=7.1, progressive_carries_per90=1.3,
            tackles_per90=0.5, interceptions_per90=0.9,
            pressures_recoveries_per90=4.5,
            aerial_duels_won_pct=93.0, key_passes_per90=0.4,
            turnovers_per90=0.3, pass_completion_pct=84.8,
        ),
        normalized_percentiles=NormalizedPlayerPercentiles(
            progressive_passes=93.0, progressive_carries=57.0,
            tackles_interceptions=62.0, ball_recoveries_pressures=72.0,
            aerial_dominance=95.0, chance_creation_xa=37.0,
            possession_retention=91.0, goal_threat_xg=10.0,
        ),
        scouting_narrative=(
            "Elite sweeper-keeper and penalty specialist — saved three penalties "
            "at Euro 2024 to send Portugal through. World-class distribution and "
            "commanding box presence make him the benchmark modern goalkeeper."
        ),
    ),

    PlayerProfile(
        id="gk_flekken",
        name="Mark Flekken",
        age=31,                                  # experienced option — Brentford
        primary_position="GK", secondary_positions=[],
        club="Brentford", league="Premier League", nationality="Netherlands",
        preferred_foot="Right", height_cm=194,
        market_value_eur=20_000_000.0,
        weekly_wage_eur=55_000.0,
        contract_expiry_year=2027,
        release_clause_eur=None,
        raw_metrics=RawPlayerMetrics(
            minutes_played=2700, matches_played=30,
            goals_per90=0.0, assists_per90=0.01,
            xg_per90=0.0, xa_per90=0.01,
            progressive_passes_per90=8.2, progressive_carries_per90=1.1,
            tackles_per90=0.4, interceptions_per90=0.7,
            pressures_recoveries_per90=3.9,
            aerial_duels_won_pct=91.0, key_passes_per90=0.3,
            turnovers_per90=0.2, pass_completion_pct=86.5,
        ),
        normalized_percentiles=NormalizedPlayerPercentiles(
            progressive_passes=96.0, progressive_carries=52.0,
            tackles_interceptions=58.0, ball_recoveries_pressures=65.0,
            aerial_dominance=93.0, chance_creation_xa=32.0,
            possession_retention=93.0, goal_threat_xg=8.0,
        ),
        scouting_narrative=(
            "Tall, commanding Premier League goalkeeper who leads the division "
            "for long-pass accuracy — exceptional ball-playing GK for "
            "possession-based systems needing a high-line sweeper."
        ),
    ),

    # ══════════════════════════════════════════════════════════════════
    # WINGERS & ATTACKING MIDFIELDERS  (RW · LW · AM)
    # ══════════════════════════════════════════════════════════════════

    PlayerProfile(
        id="w_yamal",
        name="Lamine Yamal",
        age=18,                                  # NEW — the defining player of 2025/26
        primary_position="RW", secondary_positions=["AM", "LW"],
        club="FC Barcelona", league="La Liga", nationality="Spain",
        preferred_foot="Left", height_cm=178,
        market_value_eur=180_000_000.0,          # highest teenage valuation in history
        weekly_wage_eur=180_000.0,
        contract_expiry_year=2030,
        release_clause_eur=1_000_000_000.0,      # 1B clause
        raw_metrics=RawPlayerMetrics(
            minutes_played=2600, matches_played=32,
            goals_per90=0.45, assists_per90=0.52,
            xg_per90=0.40, xa_per90=0.48,
            progressive_passes_per90=5.8, progressive_carries_per90=11.2,
            tackles_per90=1.2, interceptions_per90=0.5,
            pressures_recoveries_per90=4.8,
            aerial_duels_won_pct=35.0, key_passes_per90=3.8,
            turnovers_per90=2.5, pass_completion_pct=82.0,
        ),
        normalized_percentiles=NormalizedPlayerPercentiles(
            progressive_passes=88.0, progressive_carries=99.0,
            tackles_interceptions=48.0, ball_recoveries_pressures=58.0,
            aerial_dominance=30.0, chance_creation_xa=99.0,
            possession_retention=83.0, goal_threat_xg=95.0,
        ),
        scouting_narrative=(
            "Generational talent — arguably the most exciting teenager in the "
            "history of the game. Leads La Liga in dribble completion, chance "
            "creation, and progressive carries at just 18. Release clause of €1B "
            "means he is informational only at this valuation."
        ),
    ),

    PlayerProfile(
        id="w_barcola",
        name="Bradley Barcola",
        age=24,
        primary_position="LW", secondary_positions=["RW", "CF"],
        club="Paris Saint-Germain", league="Ligue 1", nationality="France",
        preferred_foot="Right", height_cm=186,
        market_value_eur=80_000_000.0,           # risen sharply
        weekly_wage_eur=110_000.0,
        contract_expiry_year=2028,
        release_clause_eur=None,
        raw_metrics=RawPlayerMetrics(
            minutes_played=2250, matches_played=29,
            goals_per90=0.52, assists_per90=0.40,
            xg_per90=0.46, xa_per90=0.37,
            progressive_passes_per90=4.3, progressive_carries_per90=7.2,
            tackles_per90=1.5, interceptions_per90=0.7,
            pressures_recoveries_per90=5.1,
            aerial_duels_won_pct=43.0, key_passes_per90=2.5,
            turnovers_per90=2.0, pass_completion_pct=82.5,
        ),
        normalized_percentiles=NormalizedPlayerPercentiles(
            progressive_passes=77.0, progressive_carries=97.0,
            tackles_interceptions=64.0, ball_recoveries_pressures=70.0,
            aerial_dominance=41.0, chance_creation_xa=93.0,
            possession_retention=81.0, goal_threat_xg=96.0,
        ),
        scouting_narrative=(
            "Established himself as one of Europe's elite left-wingers — "
            "blistering pace, devastating 1v1 take-ons, and clinical cutback "
            "deliveries now backed by consistent 20+ goal seasons."
        ),
    ),

    PlayerProfile(
        id="w_cherki",
        name="Rayan Cherki",
        age=22,
        primary_position="AM", secondary_positions=["RW", "LW"],
        club="Borussia Dortmund",                # UPDATED: moved from Lyon in 2025
        league="Bundesliga",
        nationality="France",
        preferred_foot="Both", height_cm=177,
        market_value_eur=45_000_000.0,           # risen after Bundesliga move
        weekly_wage_eur=75_000.0,
        contract_expiry_year=2029,
        release_clause_eur=None,
        raw_metrics=RawPlayerMetrics(
            minutes_played=1900, matches_played=26,
            goals_per90=0.28, assists_per90=0.48,
            xg_per90=0.24, xa_per90=0.50,
            progressive_passes_per90=7.2, progressive_carries_per90=8.0,
            tackles_per90=1.0, interceptions_per90=0.5,
            pressures_recoveries_per90=4.0,
            aerial_duels_won_pct=38.0, key_passes_per90=3.3,
            turnovers_per90=2.6, pass_completion_pct=80.5,
        ),
        normalized_percentiles=NormalizedPlayerPercentiles(
            progressive_passes=93.0, progressive_carries=98.0,
            tackles_interceptions=46.0, ball_recoveries_pressures=52.0,
            aerial_dominance=36.0, chance_creation_xa=99.0,
            possession_retention=82.0, goal_threat_xg=78.0,
        ),
        scouting_narrative=(
            "Magical ambipedal creator now proving himself in the Bundesliga at "
            "Dortmund — league-leading expected assist rate and unpredictable "
            "dribbling that defenders simply cannot plan for."
        ),
    ),

    PlayerProfile(
        id="w_tel",
        name="Mathys Tel",
        age=20,                                  # NEW — Bayern / on-loan versatile attacker
        primary_position="RW", secondary_positions=["LW", "ST"],
        club="Bayern Munich", league="Bundesliga", nationality="France",
        preferred_foot="Left", height_cm=181,
        market_value_eur=50_000_000.0,
        weekly_wage_eur=80_000.0,
        contract_expiry_year=2029,
        release_clause_eur=None,
        raw_metrics=RawPlayerMetrics(
            minutes_played=1700, matches_played=25,
            goals_per90=0.38, assists_per90=0.28,
            xg_per90=0.34, xa_per90=0.26,
            progressive_passes_per90=4.5, progressive_carries_per90=8.8,
            tackles_per90=1.1, interceptions_per90=0.5,
            pressures_recoveries_per90=4.4,
            aerial_duels_won_pct=40.0, key_passes_per90=2.0,
            turnovers_per90=2.2, pass_completion_pct=80.0,
        ),
        normalized_percentiles=NormalizedPlayerPercentiles(
            progressive_passes=72.0, progressive_carries=98.0,
            tackles_interceptions=50.0, ball_recoveries_pressures=60.0,
            aerial_dominance=38.0, chance_creation_xa=88.0,
            possession_retention=80.0, goal_threat_xg=91.0,
        ),
        scouting_narrative=(
            "Explosive versatile attacker capable across all three forward "
            "positions — elite dribbler with rapid acceleration, elite xG "
            "generation, and a superb left foot that makes him dangerous "
            "cutting inside from the right."
        ),
    ),
]


# ──────────────────────────────────────────────────────────────────────
# DATA PROVENANCE NOTICE
# ──────────────────────────────────────────────────────────────────────
DATASET_METADATA = {
    "vintage": "2025/26 Season",
    "compiled": "Summer 2026 (Pre-Season)",
    "stat_source": "StatsBomb-style event metrics (illustrative benchmark)",
    "valuation_source": "Transfermarkt benchmark estimates (as of Summer 2026)",
    "contract_source": "Public press reports / club announcements",
    "note": (
        "All market values, wages, and contract lengths are estimated benchmarks "
        "for portfolio demonstration purposes. A production deployment would "
        "integrate live StatsBomb / Opta / Transfermarkt API feeds with daily refresh."
    ),
}


def seed_data():
    print(f"\nSeeding {len(PLAYERS_2526)} players — {DATASET_METADATA['vintage']} Benchmark Dataset")
    print(f"Data vintage  : {DATASET_METADATA['compiled']}")
    print(f"Stat source   : {DATASET_METADATA['stat_source']}")
    print(f"Note          : {DATASET_METADATA['note'][:80]}...\n")

    for p in PLAYERS_2526:
        db.insert_player(p)

    print("Fitting Vector Store with qualitative scouting narratives...")
    all_players = db.get_all_players()
    vector_store.fit(all_players)

    positions = sorted(set(p.primary_position for p in all_players))
    print(f"\nSuccessfully seeded and indexed {len(all_players)} players")
    print(f"Position families in DB: {positions}")
    print()


if __name__ == "__main__":
    seed_data()
