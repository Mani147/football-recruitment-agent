"""Source-backed season records and reproducible position-specific percentiles."""
from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path
import re

from backend.app.analytics.comparison import POSITION_COMPARISON_GROUPS

SNAPSHOT = Path(__file__).with_name('statsbomb_pl_2015_16.json')
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

@lru_cache(maxsize=1)
def snapshot():
    if not SNAPSHOT.exists():
        raise RuntimeError('Real-data snapshot missing. Run python -m backend.app.data.import_statsbomb before starting the app.')
    data = json.loads(SNAPSHOT.read_text(encoding='utf-8'))
    if data['metadata']['match_count'] != 380 or not data['metadata']['complete_fixture_list']:
        raise RuntimeError('The bundled season snapshot is incomplete.')
    return data

def metadata():
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
        return r['aerial_duels_won_pct'] if c.get('aerial_won',0)+c.get('aerial_lost',0)>=20 else None
    if key=='possession_retention':
        return r['pass_completion_pct'] if c.get('passes',0)>=200 else None
    if key=='save_pct':
        return r['save_pct'] if c.get('shots_on_target_faced',0)>=20 else None
    if key=='tackles_interceptions':
        return r['tackles_per90']+r['interceptions_per90']
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

@lru_cache(maxsize=6)
def cohort(group):
    members=[p for p in snapshot()['players'] if primary_group(p)==group and p['raw_metrics']['minutes_played']>=COHORT_MINUTES]
    values={key:[v for p in members if (v:=metric_value(p,key)) is not None] for key in GROUPS[group]['metrics']}
    return members,values

def record(player,group):
    members,values=cohort(group)
    minutes=player['raw_metrics']['minutes_played']
    metrics={key:percentile(metric_value(player,key),values[key]) if minutes>=COHORT_MINUTES else None
             for key in GROUPS[group]['metrics']}
    return {'data_mode':'statsbomb','player':player,'league_adjusted_percentiles':metrics,
        'cohort_size':len(members),'metric_cohort_sizes':{k:len(v) for k,v in values.items()},
        'reference_group':group,'sample_minutes':minutes,
        'sample_note':f'{minutes:.1f} regulation minutes; position cohort threshold: {COHORT_MINUTES}. This measures sample exposure, not data accuracy.',
        'source_url':f"https://github.com/hudl/open-data/tree/{snapshot()['metadata']['upstream_revision']}/data"}

def comparison(group,include_secondary=True,min_minutes=900):
    players=snapshot()['players']
    rows=[record(p,group) for p in players if in_group(p,group,include_secondary) and p['raw_metrics']['minutes_played']>=min_minutes]
    rows.sort(key=lambda r:(r['player']['name'].casefold(),r['player']['id']))
    notice='Real match-event aggregates from StatsBomb Open Data, Premier League 2015/16. Historical season; no fee, wage or current-ability estimates.'
    return {'group':group,'include_secondary':include_secondary,'players':rows,'min_minutes':min_minutes,
        'groups':{key:dict(g,count=sum(in_group(p,key,include_secondary) and p['raw_metrics']['minutes_played']>=min_minutes for p in players)) for key,g in GROUPS.items()},
        'dataset_count':len(players),'dataset_notice':notice,'metadata':metadata(),'data_mode':'statsbomb'}

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
        for key in GROUPS[group]['metrics']:
            targets.setdefault(key,75.0)
    return payload

def search(req):
    p,group=interpret(req)
    if not group:
        return {'status':'needs_clarification','profile':profile_payload(p,group),'candidates':[],
            'message':'Please name a position, such as goalkeeper, left back, centreback, midfielder, winger or striker.','metadata':metadata()}
    rows=comparison(group,True,p.min_minutes_played)['players']
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
        'metrics':GROUPS[group]['metrics'],'candidates':rows[:10],'eligible_count':len(rows),
        'message':'Historical role-target alignment on measured percentile axes; not a transfer recommendation. Equal weight per available axis. Missing axes are excluded; compare the scored-axis count.',
        'metadata':metadata()}
