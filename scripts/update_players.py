"""Aggregate player game box scores without publishing raw responses."""
from collections import defaultdict
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import sys
from update_cfb_data import api, number, offense

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ('completions', 'attempts', 'passYards', 'passTD', 'ints',
          'carries', 'rushYards', 'rushTD', 'receptions', 'recYards', 'recTD', 'targets')
MAP = {'passing': {'YDS': 'passYards', 'TD': 'passTD', 'INT': 'ints'},
       'rushing': {'CAR': 'carries', 'ATT': 'carries', 'YDS': 'rushYards', 'TD': 'rushTD'},
       'receiving': {'REC': 'receptions', 'YDS': 'recYards', 'TD': 'recTD', 'TGT': 'targets', 'TARGETS': 'targets'}}

def normalize_player_team(side, gid):
    players = {}
    seen = set()
    def assign(pid, field, value):
        marker = (pid, field)
        if marker in seen:
            raise ValueError('Duplicate player/game statistic')
        seen.add(marker)
        players[pid][field] = value
    for category in side.get('categories', []):
        kind = str(category['name']).lower()
        if kind not in MAP:
            continue
        for stat_type in category.get('types', []):
            label = str(stat_type['name']).upper()
            if label not in MAP[kind] and not (kind == 'passing' and label in ('C/ATT', 'COMP/ATT')):
                continue
            for athlete in stat_type.get('athletes', []):
                pid = str(athlete['id'])
                if not pid or not athlete.get('name'):
                    raise ValueError('Missing player identity')
                players.setdefault(pid, {'playerId': pid, 'name': athlete['name'], 'gameId': gid,
                                        **dict.fromkeys(FIELDS)})
                if kind == 'passing' and label in ('C/ATT', 'COMP/ATT'):
                    text = str(athlete['stat']).replace('-', '/')
                    parts = text.split('/')
                    if len(parts) != 2:
                        raise ValueError('Invalid player completions/attempts')
                    completed, attempted = map(number, parts)
                    if completed is None or attempted is None or not 0 <= completed <= attempted:
                        raise ValueError('Invalid player completions/attempts')
                    assign(pid, 'completions', completed)
                    assign(pid, 'attempts', attempted)
                else:
                    value = number(athlete.get('stat'))
                    field = MAP[kind][label]
                    if value is not None and field not in ('passYards', 'rushYards', 'recYards') and (value < 0 or value != int(value)):
                        raise ValueError('Invalid player count')
                    assign(pid, field, value)
    return list(players.values())

def derive_players(teams, games, team_boxes, player_boxes, roster, year):
    teams_by_id = {int(t['id']): t for t in teams}
    names = {t['school']: int(t['id']) for t in teams}
    eligible = sorted([g for g in games if g.get('completed') is True
                       and g.get('homeId') in teams_by_id and g.get('awayId') in teams_by_id],
                      key=lambda g: (g['startDate'], g['id']))
    boxes, pboxes = {}, {}
    for records, mapping in ((team_boxes, boxes), (player_boxes, pboxes)):
        for record in records:
            if record['id'] in mapping:
                raise ValueError('Duplicate game box score')
            mapping[record['id']] = record
    positions = {}
    for person in roster:
        if person.get('team') in names:
            positions[(names[person['team']], str(person['id']))] = (person.get('position') or 'Other').upper()
    history, totals, team_games = defaultdict(dict), {}, defaultdict(list)
    for g in eligible:
        gid = g['id']
        if gid not in boxes or gid not in pboxes:
            raise ValueError(f'Missing team/player box score for game {gid}')
        psides = {names.get(s.get('team')): s for s in pboxes[gid].get('teams', [])}
        tsides = {int(s['teamId']): s for s in boxes[gid].get('teams', [])}
        participants = {g['homeId'], g['awayId']}
        if set(psides) != participants or set(tsides) != participants:
            raise ValueError('Player/team box score participants disagree')
        for tid in participants:
            parsed = normalize_player_team(psides[tid], gid)
            if not parsed:
                raise ValueError(f'No recognized offensive player stats for game {gid}, team {tid}')
            off = offense(tsides[tid])
            totals[(tid, gid)] = {'carries': off['rush']['attempts'], 'receptions': off['pass']['completions']}
            # Explicit targets only; don't infer targets from catches.
            totals[(tid, gid)]['targets'] = None  # No verified complete team-target denominator.
            team_games[tid].append(gid)
            for p in parsed:
                history[(tid, p['playerId'])][gid] = p
    if not history:
        raise ValueError('Empty player statistics')
    windows = {}
    for period, limit in (('season', None), ('last3', 3), ('last1', 1)):
        rows = []
        for (tid, pid), records in history.items():
            selected = team_games[tid] if limit is None else team_games[tid][-limit:]
            recorded = [records[gid] for gid in selected if gid in records]
            if not recorded:
                continue
            def total(field):
                values = [p[field] for p in recorded]
                return sum(values) if all(x is not None for x in values) else None
            row = {'playerId': pid, 'teamId': tid, 'name': recorded[-1]['name'],
                   'team': teams_by_id[tid]['school'], 'conference': teams_by_id[tid].get('conference') or 'Independent',
                   'position': positions.get((tid, pid), 'Other'), 'statGames': len(recorded),
                   'teamGames': len(selected), **{f: total(f) for f in FIELDS}}
            if row['position'] not in ('QB', 'RB', 'WR', 'TE'):
                row['position'] = 'Other'
            def ratio(numerator, denominator, scale=1):
                a, b = row[numerator], row[denominator]
                return scale * a / b if a is not None and b is not None and b > 0 else None
            row['compPct'] = ratio('completions', 'attempts', 100)
            row['ypa'] = ratio('passYards', 'attempts')
            row['ypc'] = ratio('rushYards', 'carries')
            row['ypr'] = ratio('recYards', 'receptions')
            for f in ('attempts', 'passYards', 'carries', 'rushYards', 'receptions', 'recYards', 'targets'):
                row[f + 'PerGame'] = row[f] / len(recorded) if row[f] is not None else None
            for f, share in (('carries', 'carryShare'), ('receptions', 'receptionShare'), ('targets', 'targetShare')):
                denom = [totals[(tid, p['gameId'])][f] for p in recorded]
                denominator = sum(denom) if all(x is not None for x in denom) else None
                if row[f] is not None and denominator is not None and row[f] > denominator:
                    raise ValueError('Player usage exceeds matching team totals')
                row[share] = 100 * row[f] / denominator if row[f] is not None and denominator and denominator > 0 else None
            rows.append(row)
        windows[period] = rows
    # Derived dashboard logs, including team games with no recorded player stats.
    game_meta = {g['id']: g for g in eligible}
    player_logs = []
    for identity in windows['season']:
        tid, pid = identity['teamId'], identity['playerId']
        records = history[(tid, pid)]
        logs = []
        for gid in reversed(team_games[tid]):
            g = game_meta[gid]
            p = records.get(gid)
            oid = g['awayId'] if g['homeId'] == tid else g['homeId']
            row = {'gameId': gid, 'date': g['startDate'], 'week': g.get('week'),
                   'seasonType': g.get('seasonType'), 'opponentId': oid,
                   'opponent': teams_by_id[oid]['school'],
                   'location': 'Neutral' if g.get('neutralSite') else ('Home' if g['homeId'] == tid else 'Away'),
                   'recorded': p is not None, **{f: p[f] if p else None for f in FIELDS}}
            for numerator, denominator, field, scale in (
                    ('completions', 'attempts', 'compPct', 100),
                    ('passYards', 'attempts', 'ypa', 1),
                    ('rushYards', 'carries', 'ypc', 1),
                    ('recYards', 'receptions', 'ypr', 1)):
                a, b = row[numerator], row[denominator]
                row[field] = scale * a / b if a is not None and b is not None and b > 0 else None
            for field, share in (('carries', 'carryShare'), ('receptions', 'receptionShare')):
                denominator = totals[(tid, gid)][field]
                if row[field] is not None and denominator is not None and row[field] > denominator:
                    raise ValueError('Player game usage exceeds team total')
                row[share] = 100 * row[field] / denominator if row[field] is not None and denominator and denominator > 0 else None
            logs.append(row)
        player_logs.append({k: identity[k] for k in ('playerId', 'teamId', 'name', 'team', 'conference', 'position')} | {'games': logs})
    classified = sum(p['position'] != 'Other' for p in windows['season'])
    if not classified:
        raise ValueError('No roster positions matched player statistics')
    return {'schemaVersion': 1, 'season': year, 'generatedAt': datetime.now(timezone.utc).isoformat(),
            'source': 'CollegeFootballData', 'simulated': False, 'scope': 'FBS opponents only',
            'completedGames': len(eligible), 'playerCount': len(history), 'classifiedPlayers': classified,
            'windows': windows, 'playerLogs': player_logs, 'playerLogVersion': 1}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--year', type=int, default=datetime.now(timezone.utc).year)
    args = parser.parse_args()
    key = os.environ.get('CFBD_API_KEY', '').strip()
    if not key:
        raise ValueError('Missing repository secret CFBD_API_KEY')
    teams = api('/teams/fbs', key, year=args.year)
    games = api('/games', key, year=args.year, seasonType='both', classification='fbs')
    roster = api('/roster', key, year=args.year, classification='fbs')
    if not roster:
        raise ValueError('Empty roster response')
    tids = {t['id'] for t in teams}
    completed = [g for g in games if g.get('completed') is True and g.get('homeId') in tids and g.get('awayId') in tids]
    boxes, players = [], []
    for season_type, week in sorted({(g['seasonType'], g['week']) for g in completed}):
        params = {'year': args.year, 'seasonType': season_type, 'week': week, 'classification': 'fbs'}
        boxes.extend(api('/games/teams', key, **params))
        players.extend(api('/games/players', key, **params))
    output = derive_players(teams, games, boxes, players, roster, args.year)
    path = ROOT / 'data' / 'players.json'
    if path.exists():
        previous = json.loads(path.read_text())
        if previous.get('season') == args.year and (output['completedGames'] < previous.get('completedGames', 0)
                or output['playerCount'] < previous.get('playerCount', 0)
                or output['classifiedPlayers'] < previous.get('classifiedPlayers', 0)):
            raise ValueError('Player data coverage regressed; previous dataset preserved')
    payload = json.dumps(output, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
    path.parent.mkdir(exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(payload, encoding='utf-8')
    temp.replace(path)
    print(f"Validated {output['playerCount']} players across {output['completedGames']} eligible games.")

if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError) as e:
        print('Player refresh failed: ' + str(e), file=sys.stderr)
        sys.exit(1)

