"""Isolated invented fixtures for the OpenPlay schema and league-season boundary."""
from copy import deepcopy
import hashlib

import pytest
from fastapi.testclient import TestClient

from backend.app.data import import_openplay as importer, real_data
from backend.app.main import app


def source_row(**overrides):
    row=dict(match_id=1,player_id=1,player='Fixture Player',comp='eng',season='2526',
        team='Fixture Club',is_starter=True,in_lineup=True,position='MC',minutes_played=95,
        **{key:0 for key in importer.COUNT_FIELDS})
    row.update(overrides)
    return row


def test_season_aggregation_preserves_transfer_totals_and_separates_leagues_and_seasons():
    first=source_row()
    first.update(passes=30,passes_completed=24,progressive_passes=4,dribbles_completed=2,xa=.4,xg=.2)
    second=dict(first,match_id=2,team='New Club',is_starter=False,position='Sub')
    older=dict(first,match_id=3,season='2425')
    other=dict(first,match_id=4,comp='esp')
    rows=importer.aggregate_players([first,second,older,other])
    assert len(rows)==3
    row=next(r for r in rows if r['id']=='op-eng-2526-1')
    assert row['club']=='Fixture Club / New Club'
    assert row['raw_metrics']['minutes_played']==190
    assert row['raw_metrics']['successful_takeons_per90']==round(4*90/190,4)
    assert row['raw_metrics']['pass_completion_pct']==80
    assert row['primary_position']=='CM' and row['starting_position_minutes']=={'CM':95}
    assert row['source_match_ids']==[1,2] and row['age'] is None
    assert 'progressive_carries_per90' not in row['raw_metrics']


def test_substitute_only_players_are_not_given_a_guessed_position():
    row=importer.aggregate_players([source_row(is_starter=False,position='Sub')])[0]
    assert row['primary_position']=='UNKNOWN' and not row['secondary_positions']


def test_secondary_positions_require_meaningful_starting_exposure():
    rows=[source_row(match_id=i,minutes_played=90,position='DC') for i in range(9)]
    rows += [source_row(match_id=20+i,minutes_played=90,position='DMC') for i in range(3)]
    rows += [source_row(match_id=30,minutes_played=90,position='DR')]
    player=importer.aggregate_players(rows)[0]
    assert player['primary_position']=='CB' and player['secondary_positions']==['DM']


@pytest.mark.parametrize('override',[{'minutes_played':0},{'in_lineup':False},{'xg':float('nan')},{'passes_completed':1}])
def test_invalid_source_records_fail_instead_of_creating_measured_profiles(override):
    row=source_row();row.update(override)
    with pytest.raises(ValueError): importer.aggregate_players([row])


def test_duplicate_player_match_and_zero_denominators():
    with pytest.raises(ValueError,match='Duplicate'): importer.aggregate_players([source_row(),source_row()])
    raw=importer.raw_rates({},90)
    assert raw['pass_completion_pct'] is None and raw['aerial_duels_won_pct'] is None
    assert raw['xg_per90']==0 and 'save_pct' not in raw


def test_checksum_failure_does_not_replace_a_previous_file(tmp_path,monkeypatch):
    from io import BytesIO
    target=tmp_path/'fixture.parquet';target.write_bytes(b'previous')
    monkeypatch.setattr(importer,'urlopen',lambda *a,**k:BytesIO(b'corrupt transfer'))
    monkeypatch.setattr(importer.time,'sleep',lambda _:None)
    with pytest.raises(ValueError,match='Checksum'): importer.checked_download(tmp_path,target.name,hashlib.sha256(b'expected').hexdigest())
    assert target.read_bytes()==b'previous'
    assert not target.with_suffix('.parquet.part').exists()


def test_incomplete_build_preserves_existing_snapshot(tmp_path,monkeypatch):
    import duckdb
    connection=duckdb.connect()
    for name in ['matches.parquet','player_match_stats.parquet']:
        connection.sql("SELECT 'eng' AS comp, '2526' AS season, 1 AS match_id").write_parquet(str(tmp_path/name))
    connection.close()
    (tmp_path/'checksums.json').write_text('{"matches.parquet":{"sha256":"fixture"},"player_match_stats.parquet":{"sha256":"fixture"},"coverage.csv":{"sha256":"fixture"},"data_issues.csv":{"sha256":"fixture"}}')
    (tmp_path/'coverage.csv').write_text('comp,season,matches_with_events\neng,2526,1\n')
    (tmp_path/'data_issues.csv').write_text('comp,season,match_id,issue\n')
    monkeypatch.setattr(importer,'checked_download',lambda cache,name,digest:cache/name)
    output=tmp_path/'snapshot.json';output.write_text('previous snapshot')
    with pytest.raises(ValueError,match='Missing or duplicate fixtures'): importer.build(output,tmp_path)
    assert output.read_text()=='previous snapshot'


@pytest.fixture
def openplay_fixture(monkeypatch):
    players=[]
    for comp in ['eng','esp']:
        for season in ['2425','2526']:
            for position in ['GK','DL','DC','MC','AML','FW']:
                for i in range(12):
                    row=source_row(comp=comp,season=season,player_id=len(players)+1,position=position,minutes_played=1000)
                    row.update({k:i+(100 if comp=='esp' else 0) for k in importer.COUNT_FIELDS})
                    row.update(passes=400,passes_completed=300+i,aerials=40,aerials_won=i+10)
                    players += importer.aggregate_players([row])
    coverage=[dict(competition_code=c,competition=importer.COMPETITIONS[c],season=importer.SEASONS[s],
        expected_matches=380,source_matches=380,included_matches=379,excluded_matches=[dict(match_id=99,reason='Fixture exclusion')],
        missing_source_matches=0,unclassified_players=0,player_count=72) for c in ['eng','esp'] for s in ['2425','2526']]
    data=dict(players=players,metadata=dict(mode='openplay',source='Invented test fixture',source_url=importer.SOURCE_URL,
        default_competition='eng',default_season='2025/26',coverage=coverage,seasons=['2025/26','2024/25'],
        upstream_revision='fixture',financial_data_available=False,minutes_definition='Expanded fixture minutes'))
    monkeypatch.setattr(real_data,'snapshot',lambda:data)
    import backend.app.main as main
    monkeypatch.setattr(main,'DATASET_MODE','openplay')
    real_data.cohort.cache_clear()
    yield data
    real_data.cohort.cache_clear()


@pytest.mark.parametrize('group',list(real_data.OPENPLAY_GROUPS))
def test_openplay_comparison_uses_position_league_season_cohort(openplay_fixture,group):
    result=real_data.comparison(group,competition='eng',season='2025/26')
    assert len(result['players'])==12
    assert all(r['cohort_size']==12 and r['player']['competition_code']=='eng' and r['player']['season']=='2025/26' for r in result['players'])
    assert result['data_mode']=='openplay'
    before=deepcopy(result['players'][0]['league_adjusted_percentiles'])
    real_data.comparison(group,competition='esp',season='2024/25')
    assert real_data.comparison(group,competition='eng',season='2025/26')['players'][0]['league_adjusted_percentiles']==before
    assert 'progressive_carries' not in result['groups'][group]['metrics']
    if group=='goalkeepers': assert 'save_pct' not in result['groups'][group]['metrics']


def test_openplay_api_selection_search_and_validation(openplay_fixture):
    with TestClient(app) as client:
        assert client.get('/api/health').json()['mode']=='openplay'
        meta=client.get('/api/dataset',params=dict(competition='esp',season='2024/25')).json()
        assert meta['season']=='2024/25' and meta['active_selection']['included_matches']==379
        request=dict(objective='Find a centreback with progressive passing',competition='esp',season='2024/25')
        response=client.post('/api/scout/search',json=request)
        assert response.status_code==200
        result=response.json()
        assert result['candidates'] and all(r['player']['competition_code']=='esp' and r['player']['season']=='2024/25' for r in result['candidates'])
        assert set(result['profile']['target_percentiles'])==set(result['metrics'])
        assert client.post('/api/scout/profile',json=request).json()['metadata']['season']=='2024/25'
        stream=client.get('/api/scout/stream',params=request)
        assert stream.status_code==200 and '2024/25' in stream.text
        for endpoint in ['/api/dataset','/api/players','/api/compare/players']:
            assert client.get(endpoint,params=dict(season='2026/27')).status_code==422
        assert client.post('/api/scout/search',json=dict(request,season='2026/27')).status_code==422
        assert client.post('/api/scout/search',json=dict(request,budget_eur=100)).status_code==422
