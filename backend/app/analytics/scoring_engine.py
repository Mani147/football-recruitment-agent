from typing import List, Dict, Tuple
from backend.app.schemas.player import PlayerProfile, NormalizedPlayerPercentiles
from backend.app.schemas.recruitment import RecruitmentProfile, TargetPercentiles, PriorityWeights
from backend.app.schemas.dossier import RankedCandidate, TacticalMetricMatch
from backend.app.analytics.league_adjustment import adjust_percentiles_for_league, get_league_coefficient
from backend.app.analytics.reliability import calculate_reliability_score
from backend.app.analytics.financial_model import evaluate_financial_fit, calculate_amortization_and_cost

def calculate_tactical_match(
    player_adj_pct: NormalizedPlayerPercentiles,
    target_pct: TargetPercentiles,
    weights: PriorityWeights
) -> Tuple[float, List[TacticalMetricMatch]]:
    """
    Computes TacticalFit = sum(w_i * M(p_i, t_i)) / sum(w_i) * 100
    where M(p_i, t_i) = 1.0 if p_i >= t_i else 1.0 - (t_i - p_i)/100.0
    Also returns a transparent, auditable breakdown for every metric.
    """
    def match(p: float, t: float) -> Tuple[float, str]:
        if p >= t:
            return 1.0, "Strong Match"
        diff = t - p
        m_val = max(0.0, 1.0 - diff / 100.0)
        status = "Moderate Match" if diff <= 15.0 else "Deficit"
        return m_val, status
        
    m_prog_pass, s_prog_pass = match(player_adj_pct.progressive_passes, target_pct.progressive_passes)
    m_prog_carry, s_prog_carry = match(player_adj_pct.progressive_carries, target_pct.progressive_carries)
    m_tackles, s_tackles = match(player_adj_pct.tackles_interceptions, target_pct.tackles_interceptions)
    m_recoveries, s_recoveries = match(player_adj_pct.ball_recoveries_pressures, target_pct.ball_recoveries_pressures)
    m_aerial, s_aerial = match(player_adj_pct.aerial_dominance, target_pct.aerial_dominance)
    m_xa, s_xa = match(player_adj_pct.chance_creation_xa, target_pct.chance_creation_xa)
    m_retention, s_retention = match(player_adj_pct.possession_retention, target_pct.possession_retention)
    m_xg, s_xg = match(player_adj_pct.goal_threat_xg, target_pct.goal_threat_xg)
    
    breakdown = [
        TacticalMetricMatch(metric_name="Progressive Passing", player_league_adj_pct=player_adj_pct.progressive_passes, target_pct=target_pct.progressive_passes, match_factor=round(m_prog_pass, 2), status=s_prog_pass),
        TacticalMetricMatch(metric_name="Progressive Carries", player_league_adj_pct=player_adj_pct.progressive_carries, target_pct=target_pct.progressive_carries, match_factor=round(m_prog_carry, 2), status=s_prog_carry),
        TacticalMetricMatch(metric_name="Tackles & Interceptions", player_league_adj_pct=player_adj_pct.tackles_interceptions, target_pct=target_pct.tackles_interceptions, match_factor=round(m_tackles, 2), status=s_tackles),
        TacticalMetricMatch(metric_name="Pressures & Recoveries", player_league_adj_pct=player_adj_pct.ball_recoveries_pressures, target_pct=target_pct.ball_recoveries_pressures, match_factor=round(m_recoveries, 2), status=s_recoveries),
        TacticalMetricMatch(metric_name="Aerial Dominance", player_league_adj_pct=player_adj_pct.aerial_dominance, target_pct=target_pct.aerial_dominance, match_factor=round(m_aerial, 2), status=s_aerial),
        TacticalMetricMatch(metric_name="Chance Creation (xA)", player_league_adj_pct=player_adj_pct.chance_creation_xa, target_pct=target_pct.chance_creation_xa, match_factor=round(m_xa, 2), status=s_xa),
        TacticalMetricMatch(metric_name="Possession Retention", player_league_adj_pct=player_adj_pct.possession_retention, target_pct=target_pct.possession_retention, match_factor=round(m_retention, 2), status=s_retention),
        TacticalMetricMatch(metric_name="Goal Threat (xG)", player_league_adj_pct=player_adj_pct.goal_threat_xg, target_pct=target_pct.goal_threat_xg, match_factor=round(m_xg, 2), status=s_xg),
    ]

    cat_progression = 0.5 * (m_prog_pass + m_prog_carry)
    cat_defensive = 0.5 * (m_tackles + m_aerial)
    cat_pressing = m_recoveries
    cat_possession = m_retention
    cat_creation = 0.5 * (m_xa + m_xg)
    
    w_sum = (weights.progression + weights.defensive + weights.pressing_recovery + 
             weights.possession_retention + weights.creation_goal)
    if w_sum <= 0:
        w_sum = 1.0
        
    score = (
        weights.progression * cat_progression +
        weights.defensive * cat_defensive +
        weights.pressing_recovery * cat_pressing +
        weights.possession_retention * cat_possession +
        weights.creation_goal * cat_creation
    ) / w_sum * 100.0
    
    return round(min(100.0, max(0.0, score)), 1), breakdown

def calculate_age_potential_score(age: int) -> float:
    if age <= 21:
        return 95.0
    elif age <= 23:
        return 90.0
    elif age <= 25:
        return 82.0
    elif age <= 27:
        return 74.0
    elif age <= 29:
        return 65.0
    else:
        return 50.0

def rank_candidates(candidates: List[PlayerProfile], profile: RecruitmentProfile) -> List[RankedCandidate]:
    ranked_list = []
    
    for player in candidates:
        adj_pct = adjust_percentiles_for_league(player.normalized_percentiles, player.league)
        s_tactical, breakdown = calculate_tactical_match(adj_pct, profile.target_percentiles, profile.priority_weights)
        s_stat = round((adj_pct.progressive_passes + adj_pct.progressive_carries + 
                        adj_pct.tackles_interceptions + adj_pct.ball_recoveries_pressures + 
                        adj_pct.possession_retention) / 5.0, 1)
                        
        s_fin, fin_status = evaluate_financial_fit(player, profile.budget_max_eur, profile.wage_cap_eur_pw)
        s_age = calculate_age_potential_score(player.age)
        r_score, r_summary = calculate_reliability_score(player)
        
        composite = round(
            0.40 * s_tactical + 
            0.25 * s_stat + 
            0.20 * s_fin + 
            0.15 * s_age,
            1
        )
        
        amort = calculate_amortization_and_cost(player)
        
        why_rec = []
        if s_tactical >= 85:
            why_rec.append(f"Elite tactical fit ({s_tactical}/100) matching {profile.tactical_role_name} requirements.")
        if adj_pct.ball_recoveries_pressures >= 80:
            why_rec.append(f"High-volume pressing and recoveries ({adj_pct.ball_recoveries_pressures}th league-adj percentile).")
        if adj_pct.progressive_passes >= 80:
            why_rec.append(f"Outstanding ball progression ({adj_pct.progressive_passes}th percentile).")
        if player.age <= 23:
            why_rec.append(f"Prime developmental age ({player.age} yrs) with long-term contract resale value.")
        if not why_rec:
            why_rec.append(f"Balanced statistical profile across domestic campaign ({player.league}).")
            
        risks = []
        if player.raw_metrics.minutes_played < 1200:
            risks.append(f"Sample size warning: only {player.raw_metrics.minutes_played} league minutes logged.")
        if player.market_value_eur > profile.budget_max_eur:
            risks.append(f"Budget deficit caveat: valuation (€{player.market_value_eur/1e6:.1f}M) exceeds requested budget (€{profile.budget_max_eur/1e6:.1f}M).")
        elif player.market_value_eur > profile.budget_max_eur * 0.85:
            risks.append(f"High fee utilization (€{player.market_value_eur/1e6:.1f}M near €{profile.budget_max_eur/1e6:.1f}M cap).")
        if get_league_coefficient(player.league) < 0.85:
            risks.append(f"League translation risk: coming from {player.league}.")
        if not risks:
            risks.append("No immediate statistical or financial red flags detected.")
            
        strengths = []
        if adj_pct.tackles_interceptions >= 75:
            strengths.append("Tackles & Interceptions")
        if adj_pct.ball_recoveries_pressures >= 75:
            strengths.append("Pressures & Recoveries")
        if adj_pct.progressive_passes >= 75:
            strengths.append("Progressive Passing")
        if adj_pct.progressive_carries >= 75:
            strengths.append("Ball Carrying & Driving")
        if adj_pct.aerial_dominance >= 70:
            strengths.append("Aerial Presence")
        if not strengths:
            strengths.append("Tactical Versatility")
            
        ranked_candidate = RankedCandidate(
            player=player,
            rank=1,
            fit_score=composite,
            tactical_fit_score=s_tactical,
            stat_fit_score=s_stat,
            financial_fit_score=s_fin,
            age_potential_score=s_age,
            reliability_score=r_score,
            reliability_summary=r_summary,
            league_adjusted_percentiles=adj_pct,
            estimated_annual_cost_eur=amort["total_annual_book_cost_eur"],
            why_recommended=why_rec,
            risk_factors=risks,
            tactical_strengths=strengths,
            tactical_breakdown=breakdown
        )
        ranked_list.append(ranked_candidate)
        
    ranked_list.sort(key=lambda x: x.fit_score, reverse=True)
    for idx, c in enumerate(ranked_list):
        c.rank = idx + 1
        
    return ranked_list
