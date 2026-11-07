"""Build a checked, local OpenPlay snapshot. No API key or runtime network required."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time
from urllib.request import urlopen

RELEASE = 'data-v0.1.0'
BASE_URL = f'https://github.com/nlbair/openplay/releases/download/{RELEASE}/'
MANIFEST_SHA256 = '5d185a3687dc6661a79b0ee9bb4363ed113ecf758142577812ebb9b88c8d0a27'
SOURCE_URL = 'https://github.com/nlbair/openplay'
OUTPUT = Path(__file__).with_name('openplay_2023_2026.json')
COMPETITIONS = {'eng':'Premier League','esp':'La Liga','ger':'Bundesliga','ita':'Serie A','fra':'Ligue 1'}
SEASONS = {'2324':'2023/24','2425':'2024/25','2526':'2025/26'}
POSITIONS = {'GK':'GK','DC':'CB','DL':'LB','DR':'RB','DML':'LWB','DMR':'RWB',
             'DMC':'DM','MC':'CM','AMC':'AM','ML':'LW','MR':'RW','AML':'LW','AMR':'RW',
             'FWL':'LW','FWR':'RW','FW':'ST'}
COUNT_FIELDS = ['passes','passes_completed','progressive_passes','tackles','interceptions',
                'ball_recoveries','aerials','aerials_won','xa','xg','npxg','goals','own_goals',
                'assists','dribbles','dribbles_completed','saves','claims','keeper_sweeper',
                'crosses','crosses_completed','key_passes']


def checked_download(cache, name, digest):
    """Only verified files enter the cache; partial transfers never replace good files."""
    target = cache / name
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == digest:
        return target
    temporary = target.with_suffix(target.suffix + '.part')
    for attempt in range(3):
        try:
            with urlopen(BASE_URL + name, timeout=60) as response, temporary.open('wb') as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
            if hashlib.sha256(temporary.read_bytes()).hexdigest() != digest:
                raise ValueError(f'Checksum mismatch: {name}')
            temporary.replace(target)
            return target
        except Exception:
            temporary.unlink(missing_ok=True)
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def raw_rates(counts, minutes):
    def rate(key):
        return round(90 * counts.get(key, 0) / minutes, 4) if minutes else None
    def pct(num, den):
        return round(100 * counts.get(num, 0) / counts[den], 4) if counts.get(den, 0) else None
    fields = {'progressive_passes':'progressive_passes_per90','tackles':'tackles_per90',
              'interceptions':'interceptions_per90','ball_recoveries':'ball_recoveries_per90',
              'dribbles_completed':'successful_takeons_per90','xa':'xa_per90','xg':'xg_per90',
              'npxg':'npxg_per90','goals':'goals_per90','assists':'assists_per90',
              'saves':'keeper_saves_per90','claims':'keeper_claims_per90',
              'keeper_sweeper':'keeper_sweeps_per90','crosses_completed':'completed_crosses_per90',
              'key_passes':'key_passes_per90'}
    return {**{dest:rate(src) for src,dest in fields.items()},
            'pass_completion_pct':pct('passes_completed','passes'),
            'aerial_duels_won_pct':pct('aerials_won','aerials')}


def aggregate_players(rows):
    """Keep league-seasons separate, combine intra-league transfers, never infer sub positions."""
    buckets = {}
    seen = set()
    for row in rows:
        identity = (row['match_id'],row['player_id'])
        if identity in seen:
            raise ValueError(f'Duplicate player/match: {identity}')
        seen.add(identity)
        minutes = row['minutes_played']
        if not row['in_lineup'] or minutes is None or minutes <= 0:
            raise ValueError(f'Unknown playing time: {identity}')
        for key in COUNT_FIELDS:
            value = row[key]
            if value is None or not math.isfinite(value) or value < 0:
                raise ValueError(f'Invalid {key}: {identity}')
        if row['passes_completed'] > row['passes'] or row['aerials_won'] > row['aerials']:
            raise ValueError(f'Invalid attempt denominator: {identity}')
        key = (row['comp'],row['season'],row['player_id'])
        bucket = buckets.setdefault(key,dict(name=row['player'],minutes=0,counts=Counter(),positions=Counter(),clubs=set(),matches=[]))
        bucket['minutes'] += minutes
        bucket['counts'].update({k:row[k] for k in COUNT_FIELDS})
        position = POSITIONS.get(row['position'])
        if row['is_starter'] and position:
            bucket['positions'][position] += minutes
        bucket['clubs'].add(row['team'])
        bucket['matches'].append(row['match_id'])
    players = []
    for (comp,season,source_id), b in sorted(buckets.items()):
        positions = sorted(b['positions'],key=lambda p:(-b['positions'][p],p))
        primary = positions[0] if positions else 'UNKNOWN'
        observed = sum(b['positions'].values())
        secondary = [p for p in positions[1:] if b['positions'][p] >= 270 and b['positions'][p] >= .1 * observed]
        players.append(dict(id=f'op-{comp}-{season}-{source_id}',source_player_id=source_id,
            name=b['name'],competition_code=comp,league=COMPETITIONS[comp],season=SEASONS[season],
            club=' / '.join(sorted(b['clubs'])),primary_position=primary,secondary_positions=secondary,
            position_basis='Starting-position codes weighted by minutes in those starts; substitute positions are unknown. Whole-season output includes substitute minutes.',
            starting_position_minutes=dict(b['positions']),age=None,preferred_foot=None,
            market_value_eur=None,weekly_wage_eur=None,counts=dict(b['counts']),source_match_ids=sorted(b['matches']),
            raw_metrics=dict(minutes_played=b['minutes'],matches_played=len(b['matches']),**raw_rates(b['counts'],b['minutes']))))
    return players


def build(output=OUTPUT, cache=Path('work/openplay-cache')):
    import duckdb
    cache.mkdir(parents=True,exist_ok=True)
    manifest_file = checked_download(cache,'checksums.json',MANIFEST_SHA256)
    manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
    files = ['coverage.csv','data_issues.csv','matches.parquet','player_match_stats.parquet']
    paths = {name:checked_download(cache,name,manifest[name]['sha256']) for name in files}
    with paths['data_issues.csv'].open(encoding='utf-8',newline='') as stream:
        issues = list(csv.DictReader(stream))
    with paths['coverage.csv'].open(encoding='utf-8',newline='') as stream:
        coverage = {(r['comp'],r['season']):r for r in csv.DictReader(stream)}
    connection = duckdb.connect()
    try:
        connection.read_parquet(str(paths['matches.parquet'])).create_view('matches')
        connection.read_parquet(str(paths['player_match_stats.parquet'])).create_view('stats')
        def records(query, parameters):
            result = connection.execute(query,parameters)
            columns = [c[0] for c in result.description]
            return [dict(zip(columns,row)) for row in result.fetchall()]
        all_players, reports = [], []
        for comp in COMPETITIONS:
            for season in SEASONS:
                source_matches = records('SELECT * FROM matches WHERE comp=? AND season=?',[comp,season])
                ids = [m['match_id'] for m in source_matches]
                id_set = set(ids)
                if len(ids) != len(set(ids)) or not ids:
                    raise ValueError(f'Missing or duplicate fixtures: {comp} {season}')
                cov = coverage[(comp,season)]
                if len(ids) != int(cov['matches_with_events']):
                    raise ValueError(f'Coverage manifest disagrees: {comp} {season}')
                excluded = {int(r['match_id']):r['issue'] for r in issues if r['comp']==comp and r['season']==season and int(r['match_id']) in id_set}
                rows = records('SELECT * FROM stats WHERE comp=? AND season=?',[comp,season])
                by_match = defaultdict(list)
                for row in rows:
                    if row['match_id'] not in id_set:
                        raise ValueError('Player stats reference an unknown fixture')
                    by_match[row['match_id']].append(row)
                for match in source_matches:
                    mid = match['match_id']
                    match_rows = by_match[mid]
                    if not match['score_matches_events']:
                        excluded[mid] = 'event score mismatch'
                    if not match_rows or any(not r['in_lineup'] or r['minutes_played'] is None or r['minutes_played'] <= 0 for r in match_rows):
                        excluded[mid] = 'missing player minutes or lineup'
                    for side,opponent in [('home','away'),('away','home')]:
                        total = sum(r['goals'] for r in match_rows if r['side']==side) + sum(r['own_goals'] for r in match_rows if r['side']==opponent)
                        if total != match[f'{side}_score']:
                            excluded[mid] = 'player totals disagree with source score'
                    starters = Counter(r['side'] for r in match_rows if r['is_starter'])
                    if starters != Counter(home=11,away=11):
                        excluded[mid] = 'incomplete starting lineups'
                kept = [r for r in rows if r['match_id'] not in excluded]
                players = aggregate_players(kept)
                if not players:
                    raise ValueError(f'No usable players: {comp} {season}')
                all_players.extend(players)
                reports.append(dict(competition_code=comp,competition=COMPETITIONS[comp],season=SEASONS[season],
                    expected_matches=int(cov['matches_played']),source_matches=len(ids),included_matches=len(ids)-len(excluded),
                    excluded_matches=[dict(match_id=mid,reason=reason) for mid,reason in sorted(excluded.items())],
                    missing_source_matches=int(cov['matches_played'])-len(ids),player_count=len(players),
                    unclassified_players=sum(p['primary_position']=='UNKNOWN' for p in players),
                    all_included_scores_reconciled=True))
    finally:
        connection.close()
    meta = dict(mode='openplay',source='openplay (Noah Bair)',source_url=SOURCE_URL,
        upstream_revision=RELEASE,retrieved_at=datetime.now(timezone.utc).isoformat(),
        license='CC BY 4.0 (as declared by the dataset maintainer)',license_url=SOURCE_URL+'/blob/main/LICENSE',
        original_match_source='WhoScored match pages (as linked in OpenPlay records)',
        competitions=[dict(code=k,label=v) for k,v in COMPETITIONS.items()],seasons=list(reversed(list(SEASONS.values()))),
        default_competition='eng',default_season='2025/26',coverage=reports,player_count=len(all_players),
        financial_data_available=False,minutes_definition='Expanded minutes include stoppage time. Per-90 rates use this denominator, matching the OpenPlay release.',
        file_hashes={name:manifest[name]['sha256'] for name in files},checksum_manifest_sha256=MANIFEST_SHA256)
    data = dict(metadata=meta,players=all_players)
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary = output.with_suffix('.tmp')
    temporary.write_text(json.dumps(data,ensure_ascii=False,allow_nan=False,separators=(',',':')),encoding='utf-8')
    temporary.replace(output)
    print(json.dumps(dict(player_seasons=len(all_players),coverage=reports),indent=2))
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=OUTPUT)
    parser.add_argument('--cache',type=Path,default=Path('work/openplay-cache'))
    args = parser.parse_args()
    build(args.output,args.cache)
