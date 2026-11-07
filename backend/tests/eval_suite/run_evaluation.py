"""Report observed outcomes without treating empty results or stress cases as passes."""
import argparse
import json
from pathlib import Path
from time import perf_counter

from backend.app.agents.orchestrator import director_orchestrator
from backend.app.analytics.eligibility import eligibility_failures
from backend.app.data.bootstrap import initialize_data
from backend.app.schemas.dossier import FinalRecruitmentDossier


def evaluate_dossier(dossier, scenario):
    profile = dossier.recruitment_profile
    rows = []
    for candidate in dossier.top_candidates:
        player = candidate.player
        # Independently check supplied benchmark limits as well as the parsed brief.
        scenario_ok = (player.age <= scenario['max_age']
                       and player.market_value_eur <= scenario['max_budget']
                       and player.weekly_wage_eur <= scenario.get('wage_cap_pw', 120_000))
        rows.append({'player_id':player.id,
                     'effective_constraints_pass':not eligibility_failures(player, profile),
                     'scenario_limits_pass':scenario_ok})
    positions = [scenario['target_position'] in [c.player.primary_position, *c.player.secondary_positions]
                 for c in dossier.top_candidates[:3]]
    return {'status':dossier.status, 'candidate_count':len(rows), 'candidates':rows,
            'position_match_at_1':bool(positions and positions[0]),
            'position_precision_at_3':sum(positions)/len(positions) if positions else 0}


def run_evaluation_suite(benchmark_path=None):
    initialize_data()
    benchmark_path = benchmark_path or Path(__file__).with_name('benchmark_queries.json')
    queries = json.loads(Path(benchmark_path).read_text(encoding='utf-8-sig'))
    runs, durations = [], []
    for q in queries:
        start = perf_counter()
        try:
            _, dossier = director_orchestrator.execute_recruitment_workflow(
                objective=q['objective'], budget_eur=q['max_budget'],
                wage_cap_pw=q.get('wage_cap_pw', 120_000))
            FinalRecruitmentDossier.model_validate(dossier.model_dump())
            durations.append((perf_counter()-start)*1000)
            runs.append(dict(id=q['id'], category=q['category'], **evaluate_dossier(dossier,q)))
        except Exception as exc:
            runs.append({'id':q['id'], 'category':q['category'], 'status':'error', 'error':str(exc),
                         'candidates':[], 'candidate_count':0, 'position_match_at_1':False,
                         'position_precision_at_3':0})
    candidates = [c for r in runs for c in r['candidates']]
    def pct(n, total):
        return round(100*n/total, 1) if total else None
    results = {
        'total_scenarios_evaluated':len(runs),
        'schema_valid_response_rate_pct':pct(sum(r['status'] != 'error' for r in runs), len(runs)),
        'runs_with_candidates':sum(r['candidate_count'] > 0 for r in runs),
        'no_match_runs':sum(r['status'] == 'no_matches' for r in runs),
        'clarification_runs':sum(r['status'] == 'needs_clarification' for r in runs),
        'error_runs':sum(r['status'] == 'error' for r in runs),
        'candidates_checked':len(candidates),
        'effective_constraint_satisfaction_pct':pct(sum(c['effective_constraints_pass'] for c in candidates),len(candidates)),
        'scenario_limit_satisfaction_pct':pct(sum(c['scenario_limits_pass'] for c in candidates),len(candidates)),
        'position_match_at_1_pct_all_scenarios':pct(sum(r['position_match_at_1'] for r in runs),len(runs)),
        'position_precision_at_3_pct_all_scenarios':pct(sum(r['position_precision_at_3'] for r in runs),len(runs)),
        'pipeline_latency_mean_ms':round(sum(durations)/len(durations),2) if durations else None,
        'interpretation':'Position agreement is not recruitment quality. Empty results and clarification runs remain in the position-metric denominator; no candidate-compliance rate is reported when no candidates exist. Scenario limits are checked separately from the parsed profile. Text-only preferences not represented in a profile are not measured.',
        'runs':runs,
    }
    print(json.dumps(results, indent=2))
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    results = run_evaluation_suite()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(results, indent=2),encoding='utf-8')
