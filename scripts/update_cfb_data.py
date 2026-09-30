"""Fetch CFBD box scores privately; publish only dashboard aggregates."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]

def api(path, key, **params):
    request = Request('https://api.collegefootballdata.com' + path + '?' + urlencode(params),
                      headers={'Authorization': 'Bearer ' + key, 'Accept': 'application/json'})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=60) as response:
                result = json.load(response)
            if not isinstance(result, list):
                raise ValueError('Unexpected API response shape for ' + path)
            return result
        except HTTPError as e:
            if e.code in (401, 403):
                raise ValueError('CFBD authentication/access failed. Check CFBD_API_KEY and endpoint access.') from None
            if e.code == 429:
                raise ValueError('CFBD quota or rate limit reached; existing data preserved.') from None
            if e.code < 500 or attempt == 2:
                raise ValueError(f'CFBD request failed for {path}: HTTP {e.code}') from None
        except (URLError, TimeoutError):
            if attempt == 2:
                raise ValueError('CFBD network request failed; existing data preserved.') from None
        time.sleep(2 ** attempt)

def number(value):
    if value in (None, ''):
        return None
    result = float(str(value).replace(',', ''))
    if not math.isfinite(result):
        raise ValueError('Non-finite statistic')
    return result

def offense(team):
    stats = {s['category']: s['stat'] for s in team.get('stats', [])}
    def get(name):
        return number(stats.get(name))
    completions = attempts = None
    if stats.get('completionAttempts'):
        parts = str(stats['completionAttempts']).split('-')
        if len(parts) != 2:
            raise ValueError('Invalid completionAttempts')
        completions, attempts = map(number, parts)
    return {
        'pass': {'yards': get('netPassingYards'), 'attempts': attempts,
                 'completions': completions, 'td': get('passingTDs'),
                 'ints': get('interceptions')},
        'rush': {'yards': get('rushingYards'), 'attempts': get('rushingAttempts'),
                 'td': get('rushingTDs')},
    }

def rank(rows, key, output):
    valid = sorted((r for r in rows if r[key] is not None), key=lambda r: r[key])
    previous = None
    for i, row in enumerate(valid):
        if i == 0 or row[key] != previous:
            place = i + 1
        row[output] = place
        previous = row[key]
    for row in rows:
        row.setdefault(output, None)

def derive(teams, games, boxes, year):
    team_map = {int(t['id']): t for t in teams}
    if not team_map or len(team_map) != len(teams):
        raise ValueError('Empty or duplicate FBS team list')
    eligible = [g for g in games if g.get('completed') is True
                and g.get('homeId') in team_map and g.get('awayId') in team_map]
    if not eligible:
        raise ValueError('No completed FBS-versus-FBS games available')
    if len({g['id'] for g in eligible}) != len(eligible):
        raise ValueError('Duplicate schedule game IDs')
    box_map = {}
    for b in boxes:
        if b['id'] in box_map:
            raise ValueError('Duplicate box score IDs')
        box_map[b['id']] = b
    history = defaultdict(list)
    for g in sorted(eligible, key=lambda g: (g['startDate'], g['id'])):
        b = box_map.get(g['id'])
        if not b or len(b.get('teams', [])) != 2:
            raise ValueError(f"Missing/incomplete box score for game {g['id']}")
        sides = {int(t['teamId']): t for t in b['teams']}
        if set(sides) != {g['homeId'], g['awayId']}:
            raise ValueError('Schedule/box-score participants disagree')
        for own, opponent in ((g['homeId'], g['awayId']), (g['awayId'], g['homeId'])):
            off, allowed = offense(sides[own]), offense(sides[opponent])
            for unit in ('pass', 'rush'):
                for record in (off[unit], allowed[unit]):
                    if record['yards'] is None or record['attempts'] is None or record['attempts'] < 0:
                        raise ValueError('Required yards/attempts missing or invalid')
                    if unit == 'pass' and (record['completions'] is None or not 0 <= record['completions'] <= record['attempts']):
                        raise ValueError('Invalid pass completions')
            history[own].append({'id': g['id'], 'opponent': opponent,
                                 'offense': off, 'allowed': allowed,
                                 'points': number(sides[opponent].get('points'))})
    windows = {}
    for unit in ('pass', 'rush'):
        windows[unit] = {}
        for period, limit in (('season', None), ('last3', 3), ('last1', 1)):
            rows = []
            for tid, t in team_map.items():
                records = history[tid] if limit is None else history[tid][-limit:]
                n = len(records)
                row = {'team': t['school'], 'teamId': tid, 'conference': t.get('conference') or 'Independent',
                       'games': n, 'baselineGames': 0, 'ypg': None, 'eff': None, 'td': None,
                       'comp': None, 'ints': None, 'expected': None, 'ratio': None,
                       'adjustedActual': None, 'points': None}
                if n:
                    def total(field):
                        values = [r['allowed'][unit].get(field) for r in records]
                        return None if any(v is None for v in values) else sum(values)
                    yards, attempts = total('yards'), total('attempts')
                    row['ypg'] = yards / n
                    row['eff'] = yards / attempts if attempts else None
                    row['td'] = total('td') / n if total('td') is not None else None
                    if unit == 'pass':
                        row['comp'] = 100 * total('completions') / attempts if attempts else None
                        row['ints'] = total('ints')
                    points = [r['points'] for r in records]
                    row['points'] = sum(points) / n if all(p is not None for p in points) else None
                    expected, actual = [], []
                    for r in records:
                        others = [x for x in history[r['opponent']] if x['id'] != r['id']]
                        if others:
                            baseline = sum(x['offense'][unit]['yards'] for x in others) / len(others)
                            if baseline > 0:
                                expected.append(baseline)
                                actual.append(r['allowed'][unit]['yards'])
                    row['baselineGames'] = len(expected)
                    if expected:
                        row['expected'] = sum(expected) / len(expected)
                        row['adjustedActual'] = sum(actual) / len(actual)
                        row['ratio'] = 100 * sum(actual) / sum(expected)
                rows.append(row)
            rank(rows, 'ypg', 'rawRank')
            # Prevent misleading raw-versus-adjusted rank movement from unequal pools.
            # Adjusted rankings require an expectation for every selected game.
            for r in rows:
                r['adjustedEligible'] = r['games'] > 0 and r['baselineGames'] == r['games']
                r['rankRatio'] = r['ratio'] if r['adjustedEligible'] else None
            rank(rows, 'rankRatio', 'adjRank')
            comparable = [dict(r) for r in rows if r['adjRank'] is not None]
            rank(comparable, 'ypg', 'comparableRawRank')
            comparison = {r['teamId']: r['comparableRawRank'] for r in comparable}
            for r in rows:
                r['comparableRawRank'] = comparison.get(r['teamId'])
                r['delta'] = r['comparableRawRank'] - r['adjRank'] if r['adjRank'] is not None else None
                del r['rankRatio']
            windows[unit][period] = rows
    return {'schemaVersion': 1, 'season': year, 'generatedAt': datetime.now(timezone.utc).isoformat(),
            'source': 'CollegeFootballData', 'simulated': False, 'scope': 'FBS opponents only',
            'completedGames': len(eligible), 'teamCount': len(teams), 'windows': windows}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--year', type=int, default=datetime.now(timezone.utc).year)
    args = parser.parse_args()
    key = os.environ.get('CFBD_API_KEY', '').strip()
    if not key:
        raise ValueError('Add the repository Actions secret CFBD_API_KEY before running this workflow.')
    teams = api('/teams/fbs', key, year=args.year)
    games = api('/games', key, year=args.year, seasonType='both', classification='fbs')
    team_ids = {t['id'] for t in teams}
    completed = [g for g in games if g.get('completed') is True and g.get('homeId') in team_ids and g.get('awayId') in team_ids]
    boxes = []
    for season_type, week in sorted({(g['seasonType'], g['week']) for g in completed}):
        boxes.extend(api('/games/teams', key, year=args.year, seasonType=season_type, week=week, classification='fbs'))
    output = derive(teams, games, boxes, args.year)
    path = ROOT / 'data' / 'teams.json'
    if path.exists():
        previous = json.loads(path.read_text())
        if previous.get('season') == args.year and output['completedGames'] < previous.get('completedGames', 0):
            raise ValueError('Completed-game coverage regressed; previous dataset preserved')
    payload = json.dumps(output, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
    path.parent.mkdir(exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(payload, encoding='utf-8')
    temporary.replace(path)
    print(f"Validated {output['teamCount']} FBS teams and {output['completedGames']} FBS-versus-FBS games.")

if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError) as e:
        print('Refresh failed: ' + str(e), file=sys.stderr)
        sys.exit(1)
