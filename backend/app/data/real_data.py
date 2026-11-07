"""Source-backed season records and reproducible position-specific percentiles."""
from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path
import re

from backend.app.analytics.comparison import POSITION_COMPARISON_GROUPS

SNAPSHOT = Path(__file__).with_name('openplay_2023_2026.json')
COHORT_MINUTES = 900
MIN_COHORT = 10
METRIC_DEFINITIONS = {
    'progressive_passes':'Completed open-play passes advancing at least 12 StatsBomb x-units toward goal per regulation 90 minutes; excludes pass types such as set pieces and throw-ins.',
    'progressive_carries':'Carries advancing at least 12 StatsBomb x-units toward goal per regulation 90 minutes.',
    'tackles_interceptions':'Tackle attempts plus successful interceptions per regulation 90 minutes.',
    'ball_recoveries_pressures':'Pressure events plus successful ball recoveries per regulation 90 minutes; a volume measure, not a success rate.',
    'aerial_dominance':'Aerial wins divided by wins plus Aerial Lost duels; at least 20 recorded contests required.',
    'chance_creation_xa':'Sum of StatsBomb xG of shots linked by assisted_shot_id to a pass, per regulation 90 minutes.',
    'possession_retention':'Completed passes / attempted passes, excluding throw-ins; at least 200 attempts required. This is pass completion, not a general retention score.',
    'goal_threat_xg':'Sum of provider shot xG per regulation 90 minutes, including penalties.',
    'save_pct':'Saves / opponent shots on target while this goalkeeper is active. On-target outcomes are Goal, Saved and Saved to Post; at least 20 faced required. Not post-shot-xG adjusted.',
    'keeper_claims_per90':'Goal Keeper events with type Claim or Collected per regulation 90 minutes; collection volume, not success percentage.',
    'keeper_sweeps_per90':'Goal Keeper events with type Keeper Sweeper per regulation 90 minutes; volume, not success percentage.',
}
GROUPS = deepcopy(POSITION_COMPARISON_GROUPS)
GROUPS['goalkeepers']['metrics'] = ['save_pct','keeper_claims_per90','keeper_sweeps_per90','progressive_passes','possession_retention']
OPENPLAY_GROUPS = deepcopy(GROUPS)
for group in OPENPLAY_GROUPS.values():
    group['metrics'] = [{'progressive_carries':'successful_takeons','ball_recoveries_pressures':'ball_recoveries'}.get(k,k) for k in group['metrics']]
OPENPLAY_GROUPS['goalkeepers']['metrics'] = ['keeper_saves_per90','keeper_claims_per90','keeper_sweeps_per90','progressive_passes','possession_retention']
OPENPLAY_DEFINITIONS = {
    'progressive_passes':'Completed non-set-piece passes starting at x >= 40 and ending at least 25% closer to goal centre, per expanded 90 minutes. OpenPlay definition; not the previous StatsBomb definition.',
    'successful_takeons':'Successful take-ons per expanded 90 minutes. This is not progressive carrying distance.',
    'tackles_interceptions':'Tackle attempts plus interceptions per expanded 90 minutes.',
    'ball_recoveries':'Ball recoveries per expanded 90 minutes. Pressure events are not available.',
    'aerial_dominance':'Aerial duels won / aerial duels attempted, with at least 20 recorded contests.',
    'chance_creation_xa':'Sum of OpenPlay model xG of shots set up by this player, per expanded 90 minutes. Modelled by Noah Bair; not StatsBomb or Opta xG.',
    'possession_retention':'Completed passes / attempted passes, all types including set pieces; at least 200 attempts. Labelled pass completion.',
    'goal_threat_xg':'OpenPlay model shot xG per expanded 90 minutes, including penalties.',
    'keeper_saves_per90':'Goalkeeper saves per expanded 90 minutes. Workload volume, not save percentage or shot-stopping quality.',
    'keeper_claims_per90':'High balls claimed per expanded 90 minutes. Volume, not claim success rate.',
    'keeper_sweeps_per90':'Successful goalkeeper sweeper actions per expanded 90 minutes. Volume, not success rate.',
}

def is_openplay():
    return snapshot()['metadata'].get('mode') == 'openplay'

def groups():
    return OPENPLAY_GROUPS if is_openplay() else GROUPS

def selection(competition=None,season=None):
    meta = snapshot()['metadata']
    if not is_openplay():
        return None,None
    competition = competition or meta['default_competition']
    season = season or meta['default_season']
    if not any(r['competition_code']==competition and r['season']==season for r in meta['coverage']):
        raise ValueError('Choose an available league and season from 2023/24, 2024/25 or 2025/26. The snapshot has no live 2026/27 feed.')
    return competition,season

def selected_players(competition=None,season=None):
    competition,season = selection(competition,season)
    return [p for p in snapshot()['players'] if competition is None or (p['competition_code']==competition and p['season']==season)]

@lru_cache(maxsize=1)
def snapshot():
    if not SNAPSHOT.exists():
        raise RuntimeError('OpenPlay snapshot missing. Run python -m backend.app.data.import_openplay before starting the app.')
    data = json.loads(SNAPSHOT.read_text(encoding='utf-8'))
    if data['metadata'].get('mode') != 'openplay' or len(data['metadata'].get('coverage',[])) != 15 or not data['players']:
        raise RuntimeError('The OpenPlay snapshot is invalid; rebuild it using import_openplay.')
    return data

def metadata(competition=None,season=None):
    competition,season = selection(competition,season)
    if is_openplay():
        meta = snapshot()['metadata']
        active = next(r for r in meta['coverage'] if r['competition_code']==competition and r['season']==season)
        return dict(meta,active_selection=active,competition=active['competition'],season=season,
            match_count=active['included_matches'],cohort_min_minutes=COHORT_MINUTES,minimum_cohort_size=MIN_COHORT,
            percentile_method='Within the selected league, season and position group, against primary-position peers with 900+ expanded minutes; at least 10 peers per metric. Average ranks handle ties. No league-strength adjustment; percentiles from different leagues are not directly comparable.',
            metric_definitions=OPENPLAY_DEFINITIONS,
            limitations=['Season snapshots through 2025/26; no live 2026/27 ability, club or availability information.',
                'OpenPlay v0.1.0 is a community preview. Checksums and source-score reconciliation verify ingestion, not independent annotation or model accuracy.',
                'Fixtures with published issues, missing minutes/lineups or score mismatches are excluded; coverage is displayed for each league-season.',
                'Positions use starting-position codes weighted by minutes in those starts; substitute positions and in-match role changes are not inferred. Players with no observed starts remain unclassified.',
                'Secondary positions need 270 starting-appearance minutes and 10% of observed starting-appearance minutes. Output includes all appearances, not only minutes in the displayed position.',
                'Current ages, preferred foot, fees, wages and contracts are not verified. Source age fields are not used.',
                'Take-ons are not progressive carries. Recoveries are not pressures. Goalkeeper axes are volumes, not shot-difficulty-adjusted quality; save percentage and post-shot xG are unavailable.',
                'The maintainer declares CC BY 4.0; this project has not independently verified upstream redistribution permissions. Raw and derived records remain local.'])
    return dict(snapshot()['metadata'], cohort_min_minutes=COHORT_MINUTES, minimum_cohort_size=MIN_COHORT,
        percentile_method='Within the requested position group and season, using primary-position peers with at least 900 regulation minutes. Ties use average rank: 100*(less+(equal-1)/2)/(N-1). No league multiplier. Metrics with fewer than 10 eligible peers are unavailable.',
        metric_definitions=METRIC_DEFINITIONS,
        limitations=['Historical 2015/16 performance, not current ability or availability.',
            'Position-group comparisons use whole-season statistics, including minutes in other positions.',
            'Secondary positions require at least 270 minutes and 10% of season minutes.',
            'Fees, wages, contracts, birth dates and preferred foot are not available in this snapshot.',
            'Goalkeeper save rates are not adjusted for shot difficulty; post-shot xG is unavailable.',
            'StatsBomb event annotations and our aggregation definitions may contain errors; raw source IDs and hashes are retained.'])

def primary_group(player):
    return next((key for key,g in GROUPS.items() if player['primary_position'] in g['positions']),None)

def in_group(player,group,secondary=True):
    positions = [player['primary_position']] + (player['secondary_positions'] if secondary else [])
    return bool(set(positions)&set(GROUPS[group]['positions']))

def metric_value(player,key):
    r,c = player['raw_metrics'],player['counts']
    if key=='aerial_dominance':
        attempts=c.get('aerials',c.get('aerial_won',0)+c.get('aerial_lost',0))
        return r['aerial_duels_won_pct'] if attempts>=20 else None
    if key=='possession_retention':
        return r['pass_completion_pct'] if c.get('passes',0)>=200 else None
    if key=='save_pct':
        return r['save_pct'] if c.get('shots_on_target_faced',0)>=20 else None
    if key=='tackles_interceptions':
        return r['tackles_per90']+r['interceptions_per90']
    if key=='successful_takeons':
        return r.get('successful_takeons_per90')
    if key=='ball_recoveries':
        return r.get('ball_recoveries_per90')
    fields={'progressive_passes':'progressive_passes_per90','progressive_carries':'progressive_carries_per90',
        'ball_recoveries_pressures':'pressures_recoveries_per90','chance_creation_xa':'xa_per90','goal_threat_xg':'xg_per90'}
    return r.get(fields.get(key,key))

def percentile(value,peer_values):
    if value is None or len(peer_values)<MIN_COHORT:
        return None
    less=sum(v<value for v in peer_values)
    equal=sum(v==value for v in peer_values)
    # A secondary-position player need not belong to the primary-position reference cohort.
    rank = less+(equal-1)/2 if equal else less-.5
    return round(max(0,min(100,100*rank/(len(peer_values)-1))),1)

@lru_cache(maxsize=90)
def cohort(group,competition=None,season=None):
    members=[p for p in selected_players(competition,season) if primary_group(p)==group and p['raw_metrics']['minutes_played']>=COHORT_MINUTES]
    values={key:[v for p in members if (v:=metric_value(p,key)) is not None] for key in groups()[group]['metrics']}
    return members,values

def record(player,group,competition=None,season=None):
    members,values=cohort(group,competition,season)
    minutes=player['raw_metrics']['minutes_played']
    metrics={key:percentile(metric_value(player,key),values[key]) if minutes>=COHORT_MINUTES else None
             for key in groups()[group]['metrics']}
    unit='expanded' if is_openplay() else 'regulation'
    return {'data_mode':'openplay' if is_openplay() else 'statsbomb','player':player,'league_adjusted_percentiles':metrics,
        'cohort_size':len(members),'metric_cohort_sizes':{k:len(v) for k,v in values.items()},
        'reference_group':group,'sample_minutes':minutes,
        'sample_note':f'{minutes:.1f} {unit} minutes; position cohort threshold: {COHORT_MINUTES}. This measures sample exposure, not data accuracy.',
        'source_url':snapshot()['metadata']['source_url']}

def comparison(group,include_secondary=True,min_minutes=900,competition=None,season=None):
    competition,season=selection(competition,season)
    players=selected_players(competition,season)
    rows=[record(p,group,competition,season) for p in players if in_group(p,group,include_secondary) and p['raw_metrics']['minutes_played']>=min_minutes]
    rows.sort(key=lambda r:(r['player']['name'].casefold(),r['player']['id']))
    notice='Real match-event aggregates from StatsBomb Open Data, Premier League 2015/16. Historical season; no fee, wage or current-ability estimates.'
    meta=metadata(competition,season)
    if is_openplay():
        active=meta['active_selection']
        notice=f"OpenPlay · {active['competition']} {season} · {active['included_matches']}/{active['expected_matches']} fixtures included. Season performance, not current transfer availability."
    return {'group':group,'include_secondary':include_secondary,'players':rows,'min_minutes':min_minutes,
        'groups':{key:dict(g,count=sum(in_group(p,key,include_secondary) and p['raw_metrics']['minutes_played']>=min_minutes for p in players)) for key,g in groups().items()},
        'dataset_count':len(players),'dataset_notice':notice,'metadata':meta,'data_mode':'openplay' if is_openplay() else 'statsbomb'}

def interpret(req):
    from backend.app.agents.tactical_agent import tactical_agent
    text=req.objective.lower()
    unsupported = re.search(r'[€$£]|\b\d+(?:\.\d+)?\s*(?:m|million|k)\b|\b(?:budget|wage|salary|contract|u\d{2}|under\s+\d+|age\s*[<\d]|left.foot|right.foot)',text)
    explicit_finances = bool(req.model_fields_set & {'budget_eur','wage_cap_pw'})
    if unsupported or explicit_finances or req.age_max is not None or req.preferred_foot not in (None,'Either'):
        raise ValueError('This historical dataset has no verified age, preferred-foot, fee or wage records. Remove those constraints; search by position, style and minimum minutes instead.')
    p=tactical_agent.generate_profile(req.objective,req.club,req.budget_eur,req.wage_cap_pw)
    group=next((g for g,info in GROUPS.items() if p.position in info['positions']),None)
    if p.position in ('FB','WINGER'):
        group='fullbacks' if p.position=='FB' else 'wingers'
    p.min_minutes_played=max(900,req.min_minutes)
    return p,group

def profile_payload(profile,group):
    payload=profile.model_dump()
    for unavailable in ('age_min','age_max','budget_max_eur','wage_cap_eur_pw','preferred_foot','priority_weights','target_club'):
        payload.pop(unavailable,None)
    if group:
        targets=payload['target_percentiles']
        if is_openplay():
            # New dimensions have their own targets; never relabel an old carry/pressure target.
            targets={key:targets.get(key,75.0) for key in groups()[group]['metrics']}
            payload['target_percentiles']=targets
        for key in groups()[group]['metrics']:
            targets.setdefault(key,75.0)
    return payload

def search(req):
    competition,season=selection(getattr(req,'competition',None),getattr(req,'season',None))
    p,group=interpret(req)
    if not group:
        return {'status':'needs_clarification','profile':profile_payload(p,group),'candidates':[],
            'message':'Please name a position, such as goalkeeper, left back, centreback, midfielder, winger or striker.','metadata':metadata(competition,season)}
    rows=comparison(group,True,p.min_minutes_played,competition,season)['players']
    if p.position not in ('FB','WINGER'):
        from backend.app.schemas.recruitment import POSITION_GROUPS
        positions=set(POSITION_GROUPS.get(p.position,[p.position]))
        rows=[r for r in rows if positions & {r['player']['primary_position'],*r['player']['secondary_positions']}]
    payload=profile_payload(p,group)
    target=payload['target_percentiles']
    for r in rows:
        available=[(key,value) for key,value in r['league_adjusted_percentiles'].items() if value is not None]
        # Mean shortfall relative to the requested archetype, over measured axes only.
        r['profile_score']=round(sum(max(0,100-max(0,target.get(key,75)-value)) for key,value in available)/len(available),1) if available else None
        r['scored_metric_count']=len(available)
    rows=[r for r in rows if r['profile_score'] is not None]
    rows.sort(key=lambda r:(-r['profile_score'],-r['sample_minutes'],r['player']['id']))
    return {'status':'complete' if rows else 'no_matches','profile':payload,'group':group,
        'metrics':groups()[group]['metrics'],'candidates':rows[:10],'eligible_count':len(rows),
        'message':'Historical role-target alignment on measured percentile axes; not a transfer recommendation. Equal weight per available axis. Missing axes are excluded; compare the scored-axis count.',
        'metadata':metadata(competition,season)}
