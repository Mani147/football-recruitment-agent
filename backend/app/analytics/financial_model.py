from typing import Dict, Tuple
from backend.app.schemas.player import PlayerProfile

def calculate_amortization_and_cost(player: PlayerProfile, contract_years: int = 5) -> Dict[str, float]:
    fee = player.market_value_eur
    annual_salary = player.weekly_wage_eur * 52.0
    annual_amortization = fee / float(max(1, contract_years))
    total_annual_book_cost = annual_amortization + annual_salary
    
    return {
        "transfer_fee_eur": fee,
        "weekly_wage_eur": player.weekly_wage_eur,
        "annual_gross_salary_eur": annual_salary,
        "annual_amortization_eur": annual_amortization,
        "total_annual_book_cost_eur": total_annual_book_cost
    }

def evaluate_financial_fit(player: PlayerProfile, budget_max: float, wage_cap_pw: float) -> Tuple[float, str]:
    fee = player.market_value_eur
    wage = player.weekly_wage_eur
    
    if fee > budget_max:
        fee_ratio = fee / budget_max
        fee_score = max(0.0, 100.0 - (fee_ratio - 1.0) * 150.0)
    else:
        headroom_ratio = (budget_max - fee) / budget_max
        fee_score = 70.0 + (headroom_ratio * 30.0)
        
    if wage > wage_cap_pw:
        wage_ratio = wage / wage_cap_pw
        wage_score = max(0.0, 100.0 - (wage_ratio - 1.0) * 150.0)
    else:
        wage_headroom = (wage_cap_pw - wage) / wage_cap_pw
        wage_score = 70.0 + (wage_headroom * 30.0)
        
    total_score = round(0.60 * fee_score + 0.40 * wage_score, 1)
    status = "Within Budget Headroom" if fee <= budget_max and wage <= wage_cap_pw else "Exceeds Budget/Wage Cap"
    return min(100.0, max(0.0, total_score)), status
