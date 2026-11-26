from collections import Counter
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from backend.app.data import real_data
from backend.app.data.import_statsbomb import aggregate_match, raw_rates, clock, build
from backend.app.main import app


@pytest.fixture
def real_fixture(monkeypatch):
    """Invented records are confined to tests; no provider data is redistributed in CI."""
    players=[]
    for group,position in [('goalkeepers','GK'),('fullbacks','RB'),('centrebacks','CB'),('midfielders','CM'),('wingers','RW'),('strikers','ST')]:
        for i in range(12):
            counts=dict(passes=300,completed_passes=220+i,progressive_passes=i,progressive_carries=i,tackles=i,
                        interceptions=i,recoveries=i,pressures=i,aerial_won=i+2,aerial_lost=20,
                        xg=i/10,xa=i/20,shots_on_target_faced=40,saves=20+i,keeper_claims=i,keeper_sweeps=i)
            players.append(dict(id=f'{group}-{i}',name=f'{group} Player {i:02d}',primary_position=position,
                secondary_positions=[],club='Fixture Club',league='Premier League',season='2015/16',age=None,
                preferred_foot=None,market_value_eur=None,weekly_wage_eur=None,counts=counts,
                raw_metrics=dict(minutes_played=1000,matches_played=12,**raw_rates(counts,1000))))
    meta=dict(source='StatsBomb Open Data',competition='Premier League',season='2015/16',
              upstream_revision='fixture',source_url='https://github.com/hudl/open-data',match_count=380,
              team_count=20,player_count=len(players),complete_fixture_list=True,minutes_definition='Fixture definition',financial_data_available=False)
    data={'players':players,'metadata':meta}
    monkeypatch.setattr(real_data,'snapshot',lambda:data)
    real_data.cohort.cache_clear()
    import backend.app.main as main
    monkeypatch.setattr(main,'DATASET_MODE','statsbomb')
    yield data
    real_data.cohort.cache_clear()


def test_percentiles_have_documented_endpoints_ties_and_missing_denominators(real_fixture):
    assert real_data.percentile(0,list(range(12)))==0
    assert real_data.percentile(11,list(range(12)))==100
    assert real_data.percentile(5,[5]*12)==50
    assert real_data.percentile(0,list(range(9))) is None
    assert real_data.percentile(None,list(range(12))) is None
    p=real_fixture['players'][0]
    p['counts']['shots_on_target_faced']=0
    assert real_data.metric_value(p,'save_pct') is None
    p['counts']['passes']=10
    assert real_data.metric_value(p,'possession_retention') is None
    p['counts']['aerial_won']=0;p['counts']['aerial_lost']=0
    assert real_data.metric_value(p,'aerial_dominance') is None


@pytest.mark.parametrize('group',list(real_data.GROUPS))
def test_real_position_comparison_has_calculated_values_no_financial_fiction(real_fixture,group):
    data=real_data.comparison(group)
    assert len(data['players'])==12
    assert data['metadata']['season']=='2015/16'
    first,last=data['players'][0],data['players'][-1]
    metric='progressive_carries' if group=='strikers' else 'progressive_passes'
    assert first['league_adjusted_percentiles'][metric]==0
    assert last['league_adjusted_percentiles'][metric]==100
    assert all(r['player']['market_value_eur'] is None and r['player']['weekly_wage_eur'] is None for r in data['players'])
    assert all(r['cohort_size']==12 for r in data['players'])
    if group=='goalkeepers':assert 'save_pct' in first['league_adjusted_percentiles']


def test_low_minutes_do_not_receive_invented_percentiles(real_fixture):
    p=deepcopy(real_fixture['players'][0]);p['id']='small-sample';p['raw_metrics']['minutes_played']=100
    real_fixture['players'].append(p)
    assert not any(r['player']['id']==p['id'] for r in real_data.comparison('goalkeepers')['players'])
    row=next(r for r in real_data.comparison('goalkeepers',min_minutes=0)['players'] if r['player']['id']==p['id'])
    assert all(v is None for v in row['league_adjusted_percentiles'].values())


def test_primary_cohort_is_not_changed_by_secondary_display_filter(real_fixture):
    p=real_fixture['players'][0];p['secondary_positions']=['CM']
    broad=real_data.comparison('midfielders',True)
    narrow=real_data.comparison('midfielders',False)
    assert len(broad['players'])==13 and len(narrow['players'])==12
    assert broad['players'][0]['cohort_size']==12


def test_real_api_search_and_metadata_are_consistent(real_fixture):
    with TestClient(app) as client:
        assert client.get('/api/health').json()['mode']=='statsbomb'
        assert client.get('/api/dataset').json()['financial_data_available'] is False
        assert client.get('/').status_code==200
        assert '/static/research.js' in client.get('/').text
        assert client.get('/api/players').json()['players'][0]['age'] is None
        result=client.post('/api/scout/search',json={'objective':'Find a CM','min_minutes':900})
        assert result.status_code==200
        data=result.json()
        assert data['candidates'] and data['metadata']['season']=='2015/16'
        assert 'budget_max_eur' not in data['profile'] and 'age_max' not in data['profile']
        assert all(r['scored_metric_count']>0 for r in data['candidates'])
        stream=client.get('/api/scout/stream',params={'objective':'Find a CM'})
        assert stream.status_code==200 and '"event": "complete"' in stream.text
        assert client.post('/api/simulate',params={'candidate_id':'midfielders-0'}).status_code==422
        unknown=client.post('/api/scout/search',json={'objective':'Find a good person'}).json()
        assert unknown['status']=='needs_clarification'


@pytest.mark.parametrize('body',[
    {'objective':'Find a striker under 40M'},
    {'objective':'Find a U24 midfielder'},
    {'objective':'Find a left-footed winger'},
    {'objective':'Find a CM','budget_eur':100},
    {'objective':'Find a CM','wage_cap_pw':100},
    {'objective':'Find a CM','age_max':25},
])
def test_real_search_rejects_unknown_financial_and_demographic_constraints(real_fixture,body):
    with TestClient(app) as client:
        assert client.post('/api/scout/search',json=body).status_code==422


def test_event_aggregation_handles_halves_substitutions_dismissals_and_xa():
    lineups=[{'team_id':1,'team_name':'A','lineup':[{'player_id':1,'player_name':'Starter'},{'player_id':2,'player_name':'Sub'},{'player_id':4,'player_name':'A GK'}]},
             {'team_id':2,'team_name':'B','lineup':[{'player_id':3,'player_name':'B GK'}]}]
    def e(kind,minute=0,period=1,**fields):
        return dict(id=f'{kind}-{minute}',type={'name':kind},period=period,timestamp=f'00:{minute:02d}:00.000',**fields)
    events=[e('Starting XI',team={'id':1},tactics={'lineup':[{'player':{'id':1},'position':{'id':23}},{'player':{'id':4},'position':{'id':1}}]}),
            e('Starting XI',team={'id':2},tactics={'lineup':[{'player':{'id':3},'position':{'id':1}}]}),
            e('Pass',5,player={'id':1},location=[30,40],**{'pass':{'end_location':[45,40],'assisted_shot_id':'shot'}}),
            dict(e('Shot',6,player={'id':1},team={'id':1},shot={'statsbomb_xg':.4,'outcome':{'name':'Saved'}}),id='shot'),
            e('Substitution',0,2,player={'id':1},substitution={'replacement':{'id':2}}),
            e('Bad Behaviour',35,2,player={'id':2},bad_behaviour={'card':{'name':'Red Card'}})]
    rows=aggregate_match(events,lineups)
    assert sum(rows[1]['positions'].values())==45
    assert sum(rows[2]['positions'].values())==35
    assert sum(rows[3]['positions'].values())==90
    assert rows[1]['counts']['progressive_passes']==1
    assert rows[1]['counts']['xa']==.4 and rows[1]['counts']['xg']==.4
    assert rows[3]['counts']['saves']==1 and rows[3]['counts']['shots_on_target_faced']==1
    assert clock(e('Half End',49))==45
    assert clock(e('Half End',49,2))==90


def test_rates_do_not_treat_no_attempts_as_zero_success():
    rates=raw_rates(Counter(),90)
    assert rates['pass_completion_pct'] is None
    assert rates['aerial_duels_won_pct'] is None
    assert rates['save_pct'] is None
    assert rates['xg_per90']==0


def test_progression_excludes_failed_passes_and_set_pieces_but_includes_open_play_recoveries():
    lineup=[{'team_id':1,'team_name':'A','lineup':[{'player_id':1,'player_name':'A Player'}]}]
    events=[dict(type={'name':'Starting XI'},period=1,timestamp='00:00:00',team={'id':1},
                 tactics={'lineup':[{'player':{'id':1},'position':{'id':14}}]})]
    passes=[{}, {'outcome':{'name':'Incomplete'}}, {'type':{'name':'Corner'}}, {'type':{'name':'Recovery'}}]
    for i,detail in enumerate(passes):
        events.append(dict(id=str(i),type={'name':'Pass'},period=1,timestamp='00:01:00',player={'id':1},
                           location=[20,40],**{'pass':dict(end_location=[40,40],**detail)}))
    row=aggregate_match(events,lineup)[1]
    assert row['counts']['passes']==4
    assert row['counts']['completed_passes']==3
    assert row['counts']['progressive_passes']==2


def test_incomplete_import_does_not_replace_existing_snapshot(tmp_path,monkeypatch):
    from backend.app.data import import_statsbomb
    output=tmp_path/'snapshot.json';output.write_text('previous snapshot',encoding='utf-8')
    monkeypatch.setattr(import_statsbomb,'fetch_bytes',lambda _:b'[]')
    with pytest.raises(ValueError,match='Incomplete season'):
        build(output,tmp_path/'cache')
    assert output.read_text(encoding='utf-8')=='previous snapshot'
