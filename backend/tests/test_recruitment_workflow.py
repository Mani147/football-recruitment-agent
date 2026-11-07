import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from backend.app.agents.tactical_agent import tactical_agent
from backend.app.agents.scout_agent import scout_agent
from backend.app.agents.tools import tools
from backend.app.analytics.eligibility import eligibility_failures
from backend.app.analytics.scoring_engine import rank_candidates
from backend.app.data.bootstrap import initialize_data
from backend.app.data.sqlite_db import FootballDatabase
from backend.app.data.vector_store import SemanticScoutVectorStore
from backend.app.main import app
from backend.app.schemas.recruitment import RecruitmentProfile


@pytest.fixture
def database(tmp_path):
    return FootballDatabase(str(tmp_path / 'fresh.db'))


@pytest.fixture
def client(database, monkeypatch):
    # Isolate API and all agent reads from persistent application data.
    import backend.app.main as main
    import backend.app.data.bootstrap as bootstrap
    import backend.app.agents.tools as tools_module
    index = SemanticScoutVectorStore()
    monkeypatch.setattr(main, 'db', database)
    monkeypatch.setattr(bootstrap, 'db', database)
    monkeypatch.setattr(bootstrap, 'vector_store', index)
    monkeypatch.setattr(tools_module, 'db', database)
    monkeypatch.setattr(tools_module, 'vector_store', index)
    with TestClient(app) as api:
        yield api


def test_bootstrap_seeds_once_and_indexes_existing_data(database):
    index = SemanticScoutVectorStore()
    count = initialize_data(database, index)
    assert count > 0 and index.is_fitted
    restarted_index = SemanticScoutVectorStore()
    assert initialize_data(database, restarted_index) == count
    assert restarted_index.search_similar_profiles('progressive midfielder')


@pytest.mark.parametrize('prompt', ['Find a fast player', 'Find the best prospect', 'Need an assistant'])
def test_unknown_is_not_a_striker_substring(prompt):
    assert tactical_agent.generate_profile(prompt).position_family == 'UNKNOWN'


@pytest.mark.parametrize('prompt,budget,age', [
    ('Find a striker under 23 years for under €40M', 40_000_000, 22),
    ('Find a U24 DM under 35.5 million', 35_500_000, 23),
    ('Find a CB with under 1000 minutes', 50_000_000, 25),
    ('Find a ST under €40000000', 40_000_000, 25),
    ('Find a striker under €75M', 50_000_000, 25),
])
def test_budget_and_age_are_separate(prompt, budget, age):
    p = tactical_agent.generate_profile(prompt)
    assert p.budget_max_eur == budget
    assert p.age_max == age


def test_semantic_candidates_cannot_bypass_limits(client, monkeypatch):
    players = client.get('/api/players').json()['players']
    eligible = next(p for p in players if p['primary_position'] == 'DM')
    invalid = dict(eligible, id='invalid', age=40, weekly_wage_eur=9999999,
                   market_value_eur=999999999)
    monkeypatch.setattr(tools, 'search_candidates_sql', lambda **kwargs: [])
    monkeypatch.setattr(tools, 'search_semantic_profiles', lambda **kwargs: [{'player':invalid, 'similarity_score':1}])
    p = RecruitmentProfile(position_family='DM', position='DM', tactical_role_name='Test')
    pool, ranked = scout_agent.retrieve_and_rank_candidates(p, 'DM')
    assert pool == ranked == []


def test_ranker_enforces_every_constraint(client):
    from backend.app.schemas.player import PlayerProfile
    player = PlayerProfile(**client.get('/api/players').json()['players'][0])
    profile = RecruitmentProfile(position_family=player.primary_position, position=player.primary_position,
        tactical_role_name='Test', age_max=60, budget_max_eur=1e9, wage_cap_eur_pw=1e7, min_minutes_played=0)
    assert rank_candidates([player], profile)
    changes = [dict(age_max=18), dict(budget_max_eur=1), dict(wage_cap_eur_pw=1),
               dict(min_minutes_played=10000), dict(preferred_foot='Left' if player.preferred_foot == 'Right' else 'Right')]
    for change in changes:
        assert not rank_candidates([player], profile.model_copy(update=change)), change


def test_audit_rejects_mismatch_unknown_empty_and_financial_failure(client):
    player = client.get('/api/players').json()['players'][0]
    args = dict(candidate_id=player['id'], budget_max=1e9, wage_cap_pw=1e7)
    claims = player['raw_metrics']
    good = tools.verify_candidate(claimed_metrics=claims, **args)
    assert good['is_verified'] and good['matched_claim_count'] == len(claims)
    for bad in [dict(claims, minutes_played=-999), dict(claims, invented_stat=1), {}]:
        result = tools.verify_candidate(claimed_metrics=bad, **args)
        assert not result['is_verified'] and result['groundedness_score'] < 100
    assert not tools.verify_candidate(claimed_metrics=claims, **dict(args, budget_max=1))['is_verified']
    assert not tools.verify_candidate(claimed_metrics=claims, **dict(args, wage_cap_pw=1))['is_verified']
    assert not tools.verify_candidate('missing', claims, 1e9, 1e7)['is_verified']


def test_preview_and_search_use_identical_constraints(client):
    body = dict(objective='Find a left-footed CB under €30M for Bayern', budget_eur=40e6,
                wage_cap_pw=80000, age_max=24, min_minutes=1000, preferred_foot='Left')
    preview = client.post('/api/scout/profile', json=body)
    search = client.post('/api/scout/search', json=body)
    assert preview.status_code == search.status_code == 200
    dossier = search.json()['dossier']
    assert dossier['recruitment_profile'] == preview.json()['profile']
    assert dossier['club'] == 'Bayern Munich'
    profile = RecruitmentProfile(**dossier['recruitment_profile'])
    from backend.app.schemas.player import PlayerProfile
    for c in dossier['top_candidates']:
        assert not eligibility_failures(PlayerProfile(**c['player']), profile)
    assert all(s['baseline_is_fallback'] and s['baseline_club'] == 'Arsenal FC' for s in dossier['impact_simulations'])


def test_no_matches_unknown_and_invalid_inputs(client):
    d = client.post('/api/scout/search', json={'objective':'Find a DM', 'budget_eur':1}).json()['dossier']
    assert d['status'] == 'no_matches' and not d['top_candidates']
    d = client.post('/api/scout/search', json={'objective':'Find a fast player'}).json()['dossier']
    assert d['status'] == 'needs_clarification' and not d['top_candidates']
    for body in [{'objective':' '}, {'objective':'Find a DM', 'budget_eur':0},
                 {'objective':'Find a DM', 'wage_cap_pw':-1}, {'objective':'Find a DM', 'age_max':17},
                 {'objective':'Find a DM under £40M'}]:
        assert client.post('/api/scout/search', json=body).status_code == 422
    assert client.get('/api/scout/stream', params={'objective':'Find a DM', 'budget':0}).status_code == 422


def test_sided_positions_remain_strict(client):
    from backend.app.schemas.player import PlayerProfile, position_matches
    right_winger = PlayerProfile(**next(p for p in client.get('/api/players').json()['players']
                                       if p['primary_position'] == 'RW'))
    left_only = right_winger.model_copy(update={'primary_position':'LW', 'secondary_positions':[]})
    assert not position_matches(left_only, 'WINGER', 'RW')
    assert position_matches(left_only, 'WINGER', 'WINGER')
    left_back = right_winger.model_copy(update={'primary_position':'LB', 'secondary_positions':[]})
    assert not position_matches(left_back, 'RB', 'RB')


def test_stream_events_are_real_ordered_and_complete(client):
    response = client.get('/api/scout/stream', params={'objective':'Find a DM under €40M'})
    assert response.status_code == 200
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[0]['data']['action_type'] == 'INITIATE_MANDATE'
    assert events[-1]['event'] == 'complete'
    assert events[-2]['data']['action_type'] == 'FINAL_DOSSIER_READY'
    assert events[-1]['data']['dossier']['top_candidates']


def test_stream_reports_execution_error(client, monkeypatch):
    from backend.app.agents.orchestrator import director_orchestrator
    def fail(**kwargs):
        raise RuntimeError('private internal failure')
    monkeypatch.setattr(director_orchestrator, 'execute_recruitment_workflow', fail)
    response = client.get('/api/scout/stream', params={'objective':'Find a DM'})
    assert '"event": "error"' in response.text
    assert 'private internal failure' not in response.text


def test_concurrent_searches_keep_profiles_separate(client):
    def search(body):
        return client.post('/api/scout/search', json=body).json()['dossier']
    briefs = [{'objective':'Find a DM', 'budget_eur':1}, {'objective':'Find a right back', 'budget_eur':50e6}]
    with ThreadPoolExecutor(max_workers=2) as pool:
        a, b = list(pool.map(search, briefs))
    assert not a['top_candidates'] and a['recruitment_profile']['budget_max_eur'] == 1
    assert b['recruitment_profile']['position_family'] == 'RB'


@pytest.mark.parametrize('prompt,position', [
    ('Find a left-footed right winger', 'RW'),
    ('Find a right-footed left winger', 'LW'),
    ('Find a left-footed right back', 'RB'),
    ('Find a right-footed left back', 'LB'),
])
def test_preferred_foot_does_not_change_side(prompt,position):
    assert tactical_agent.generate_profile(prompt).position == position


def test_money_formats_and_wages_do_not_corrupt_fee():
    assert tactical_agent.generate_profile('Find a DM under €40,000,000').budget_max_eur == 40e6
    assert tactical_agent.generate_profile('Find a DM under €30000/wk and €25M fee').budget_max_eur == 25e6


def test_current_club_is_not_a_transfer_target(client):
    from backend.app.schemas.player import PlayerProfile
    player = PlayerProfile(**client.get('/api/players').json()['players'][0])
    profile = RecruitmentProfile(target_club=player.club, position_family=player.primary_position,
                                 position=player.primary_position, tactical_role_name='Test')
    assert 'already at recruiting club' in eligibility_failures(player,profile)
    assert not rank_candidates([player], profile)
    response = client.post('/api/simulate',params={'candidate_id':player.id,'club':player.club})
    assert response.status_code == 200


def test_benchmark_does_not_whitelist_stress_cases(client):
    from backend.tests.eval_suite.run_evaluation import evaluate_dossier
    from backend.app.schemas.dossier import FinalRecruitmentDossier
    data = client.post('/api/scout/search',json={'objective':'Find a DM under €50M'}).json()['dossier']
    dossier = FinalRecruitmentDossier(**data)
    assert dossier.top_candidates
    metrics = evaluate_dossier(dossier,dict(target_position='DM',max_age=18,max_budget=1,category='budget_stress'))
    assert not any(c['scenario_limits_pass'] for c in metrics['candidates'])


def test_goal_threat_changes_attacking_statistical_score(client):
    from backend.app.schemas.player import PlayerProfile
    player = PlayerProfile(**next(p for p in client.get('/api/players').json()['players']
                                 if p['primary_position'] == 'ST'))
    profile = tactical_agent.generate_profile('Find a striker',budget_eur=1e9,wage_cap_pw=1e7)
    profile.age_max = 60
    profile.min_minutes_played = 0
    profile.target_club = None
    weak = player.model_copy(deep=True)
    weak.normalized_percentiles.goal_threat_xg = 0
    strong = player.model_copy(deep=True)
    strong.normalized_percentiles.goal_threat_xg = 100
    a = rank_candidates([weak],profile)[0]
    b = rank_candidates([strong],profile)[0]
    assert b.stat_fit_score > a.stat_fit_score
    assert b.fit_score > a.fit_score
