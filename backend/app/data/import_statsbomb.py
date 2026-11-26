"""Rebuild the pinned, derived PL 2015/16 snapshot. Raw downloads stay in work/."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import time
import urllib.request

REVISION = '4b73468fc5b0f1950f9f66fada70ad3a4f9327cb'
BASE = f'https://raw.githubusercontent.com/hudl/open-data/{REVISION}/'
GROUPS = {'GK':'goalkeepers','RB':'fullbacks','LB':'fullbacks','RWB':'fullbacks','LWB':'fullbacks',
          'CB':'centrebacks','DM':'midfielders','CM':'midfielders','AM':'midfielders',
          'RW':'wingers','LW':'wingers','ST':'strikers'}
POSITIONS = {1:'GK',2:'RB',3:'CB',4:'CB',5:'CB',6:'LB',7:'RWB',8:'LWB',9:'DM',10:'DM',11:'DM',
             12:'RW',13:'CM',14:'CM',15:'CM',16:'LW',17:'RW',18:'AM',19:'AM',20:'AM',21:'LW',22:'ST',23:'ST',24:'ST',25:'ST'}

def clock(event):
    """Regulation minutes only: clip first-half stoppage to 45 and second-half to 90."""
    period = event.get('period',1)
    if period not in (1,2):
        return 90.0
    h,m,s = event.get('timestamp','00:00:00').split(':')
    return (period-1)*45 + min(45, int(h)*60+int(m)+float(s)/60)

def aggregate_match(events, lineups):
    records = {}
    for team in lineups:
        for item in team['lineup']:
            records[item['player_id']] = {'name':item['player_name'],'country':item.get('country',{}).get('name'),
                'team':team['team_name'],'team_id':team['team_id'],'counts':Counter(),'positions':Counter()}
    active, last = {}, {}
    def stop(pid, minute):
        if pid in active:
            position, team = active[pid]
            records[pid]['positions'][position] += max(0,minute-last[pid])
            last[pid] = minute
    def start(pid, position, team, minute):
        if pid not in records:
            raise ValueError(f'Event player {pid} is absent from lineup metadata')
        stop(pid,minute)
        active[pid] = (POSITIONS[position],team)
        last[pid] = minute
    shots = {e['id']:e for e in events if e['type']['name']=='Shot'}
    for event in events:
        kind = event['type']['name']
        minute = clock(event)
        if kind in ('Starting XI','Tactical Shift'):
            for item in event['tactics']['lineup']:
                pid = item['player']['id']
                if kind=='Starting XI' or pid in active:
                    start(pid,item['position']['id'],event['team']['id'],minute)
        pid = event.get('player',{}).get('id')
        if pid not in records:
            continue
        c = records[pid]['counts']
        if kind == 'Substitution':
            if pid in active:
                position,team = active[pid]
                stop(pid,minute)
                del active[pid]
                replacement = event['substitution']['replacement']['id']
                active[replacement] = (position,team)
                last[replacement] = minute
        for card_field in ('bad_behaviour','foul_committed'):
            card = event.get(card_field,{}).get('card',{}).get('name')
            if card in ('Red Card','Second Yellow') and pid in active:
                stop(pid,minute)
                del active[pid]
        detail = event.get('pass',{})
        if kind=='Pass' and detail.get('type',{}).get('name')!='Throw-in':
            c['passes'] += 1
            complete = 'outcome' not in detail
            c['completed_passes'] += int(complete)
            set_piece=detail.get('type',{}).get('name') in ('Corner','Free Kick','Goal Kick','Kick Off','Throw-in')
            if complete and not set_piece and event.get('location') and detail.get('end_location'):
                c['progressive_passes'] += int(detail['end_location'][0]-event['location'][0]>=12)
            assisted = shots.get(detail.get('assisted_shot_id'))
            if assisted:
                c['xa'] += assisted['shot'].get('statsbomb_xg',0)
                c['key_passes'] += 1
            c['assists'] += int(detail.get('goal_assist',False))
        if kind=='Carry' and event.get('location'):
            c['progressive_carries'] += int(event['carry']['end_location'][0]-event['location'][0]>=12)
        if kind=='Duel' and event.get('duel',{}).get('type',{}).get('name')=='Tackle':
            c['tackles'] += 1
        if kind=='Interception' and event.get('interception',{}).get('outcome',{}).get('name') in ('Won','Success','Success In Play','Success Out'):
            c['interceptions'] += 1
        if kind=='Pressure':
            c['pressures'] += 1
        if kind=='Ball Recovery' and not event.get('ball_recovery',{}).get('recovery_failure'):
            c['recoveries'] += 1
        if kind in ('Miscontrol','Dispossessed'):
            c['turnovers'] += 1
        if kind=='Duel' and event.get('duel',{}).get('type',{}).get('name')=='Aerial Lost':
            c['aerial_lost'] += 1
        if any(isinstance(event.get(field),dict) and event[field].get('aerial_won') for field in ('pass','shot','clearance','miscontrol','duel')):
            c['aerial_won'] += 1
        if kind=='Shot':
            shot = event['shot']
            c['xg'] += shot.get('statsbomb_xg',0)
            outcome = shot.get('outcome',{}).get('name')
            c['goals'] += int(outcome=='Goal')
            if outcome in ('Goal','Saved','Saved to Post'):
                keepers = [p for p,(pos,team) in active.items() if pos=='GK' and team!=event['team']['id']]
                if len(keepers)==1:
                    gc = records[keepers[0]]['counts']
                    gc['shots_on_target_faced'] += 1
                    gc['saves'] += int(outcome!='Goal')
        if kind=='Goal Keeper':
            action = event.get('goalkeeper',{}).get('type',{}).get('name')
            c['keeper_claims'] += int(action in ('Claim','Collected'))
            c['keeper_sweeps'] += int(action=='Keeper Sweeper')
    for pid in active:
        stop(pid,90)
    return {pid:r for pid,r in records.items() if sum(r['positions'].values())>0}

def raw_rates(counts, minutes):
    if minutes<=0:
        raise ValueError('Per-90 rates require positive playing time')
    def rate(key): return round(counts.get(key,0)*90/minutes,4) if minutes else None
    aerial = counts.get('aerial_won',0)+counts.get('aerial_lost',0)
    passes = counts.get('passes',0)
    faced = counts.get('shots_on_target_faced',0)
    return dict(goals_per90=rate('goals'),assists_per90=rate('assists'),xg_per90=rate('xg'),xa_per90=rate('xa'),
        progressive_passes_per90=rate('progressive_passes'),progressive_carries_per90=rate('progressive_carries'),
        tackles_per90=rate('tackles'),interceptions_per90=rate('interceptions'),
        pressures_recoveries_per90=round((counts.get('pressures',0)+counts.get('recoveries',0))*90/minutes,4),
        aerial_duels_won_pct=round(100*counts.get('aerial_won',0)/aerial,4) if aerial else None,
        pass_completion_pct=round(100*counts.get('completed_passes',0)/passes,4) if passes else None,
        key_passes_per90=rate('key_passes'),turnovers_per90=rate('turnovers'),
        save_pct=round(100*counts.get('saves',0)/faced,4) if faced else None,
        keeper_claims_per90=rate('keeper_claims'),keeper_sweeps_per90=rate('keeper_sweeps'))

def fetch_bytes(path):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(BASE+path,timeout=60) as response:
                return response.read()
        except Exception:
            if attempt==3: raise
            time.sleep(attempt+1)

def build(output, cache, workers=6):
    cache.mkdir(parents=True,exist_ok=True)
    manifest_raw = fetch_bytes('data/matches/2/27.json')
    matches = json.loads(manifest_raw)
    fixtures = Counter(t[side+'_team_id'] for m in matches for side in ('home','away') for t in [m[side+'_team']])
    directed_pairs={(m['home_team']['home_team_id'],m['away_team']['away_team_id']) for m in matches}
    if len(matches)!=380 or len({m['match_id'] for m in matches})!=380 or len(directed_pairs)!=380 or len(fixtures)!=20 or set(fixtures.values())!={38}:
        raise ValueError('Incomplete season: require 380 matches, 20 teams, 38 fixtures per team')
    def read_match(match):
        mid=match['match_id']; content={}; hashes={}
        for kind in ('events','lineups'):
            target=cache/f'{kind}-{mid}.json.gz'
            if target.exists(): raw=gzip.decompress(target.read_bytes())
            else:
                raw=fetch_bytes(f'data/{kind}/{mid}.json')
                target.write_bytes(gzip.compress(raw))
            content[kind]=json.loads(raw)
            hashes[kind]=hashlib.sha256(raw).hexdigest()
        if not {1,2} <= {e['period'] for e in content['events'] if e['type']['name']=='Half End'}:
            raise ValueError(f'Missing half-end data: {mid}')
        goals=Counter(e['team']['id'] for e in content['events'] if e['type']['name']=='Own Goal For'
                      or (e['type']['name']=='Shot' and e['shot']['outcome']['name']=='Goal'))
        for side in ('home','away'):
            if goals[match[side+'_team'][side+'_team_id']] != match[side+'_score']:
                raise ValueError(f'Event goals do not reconcile with match score: {mid}')
        return mid,aggregate_match(content['events'],content['lineups']),hashes,len(content['events'])
    totals={}; provenance=[]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for index,(mid,rows,hashes,event_count) in enumerate(pool.map(read_match,sorted(matches,key=lambda m:m['match_id'])),1):
            provenance.append({'match_id':mid,'sha256':hashes,'event_count':event_count})
            for pid,row in rows.items():
                if pid not in totals:
                    totals[pid]={'name':row['name'],'country':row['country'],'counts':Counter(),'positions':Counter(),'clubs':set(),'matches':[]}
                r=totals[pid]
                r['counts'].update(row['counts']); r['positions'].update(row['positions']);r['clubs'].add(row['team']);r['matches'].append(mid)
            if index%20==0: print(f'Aggregated {index}/380 matches',flush=True)
    players=[]
    for pid,r in sorted(totals.items()):
        minutes=sum(r['positions'].values())
        positions=sorted(r['positions'],key=lambda p:(-r['positions'][p],p))
        secondary=[p for p in positions[1:] if r['positions'][p]>=270 and r['positions'][p]/minutes>=.1]
        counts=dict(r['counts'])
        players.append({'id':f'sb-{pid}','name':r['name'],'age':None,'preferred_foot':None,
            'primary_position':positions[0],'secondary_positions':secondary,'club':' / '.join(sorted(r['clubs'])),
            'clubs':sorted(r['clubs']),'league':'Premier League','season':'2015/16','nationality':r['country'],
            'market_value_eur':None,'weekly_wage_eur':None,'contract_expiry_year':None,
            'raw_metrics':dict(minutes_played=round(minutes,2),matches_played=len(r['matches']),**raw_rates(counts,minutes)),
            'counts':counts,'position_minutes':{p:round(v,2) for p,v in r['positions'].items()},
            'match_ids':sorted(r['matches'])})
    dataset={'metadata':{'source':'StatsBomb Open Data','competition':'Premier League','season':'2015/16',
        'upstream_revision':REVISION,'source_url':f'https://github.com/hudl/open-data/tree/{REVISION}',
        'match_count':380,'team_count':20,'player_count':len(players),'complete_fixture_list':True,'match_scores_reconciled':380,
        'retrieved_at':datetime.now(timezone.utc).isoformat(),'manifest_sha256':hashlib.sha256(manifest_raw).hexdigest(),
        'minutes_definition':'Regulation on-field minutes derived in event order from Starting XI, substitutions, tactical shifts and dismissals. Each half clipped to 45 minutes; stoppage time and temporary Player Off/On interruptions excluded from the clock adjustment.',
        'financial_data_available':False,'age_and_foot_available':False},'players':players,'matches':provenance}
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary=output.with_suffix('.tmp')
    temporary.write_text(json.dumps(dataset,ensure_ascii=False,sort_keys=True,separators=(',',':')),encoding='utf-8')
    temporary.replace(output)
    print(f'Wrote {len(players)} players to {output}',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=Path(__file__).with_name('statsbomb_pl_2015_16.json'))
    parser.add_argument('--cache',type=Path,default=Path('work/statsbomb-cache'))
    parser.add_argument('--workers',type=int,default=6)
    args=parser.parse_args()
    build(args.output,args.cache,args.workers)
