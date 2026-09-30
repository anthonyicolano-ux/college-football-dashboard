"""Publish only the upcoming FBS schedule fields used in Matchups."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from update_cfb_data import api

ROOT = Path(__file__).resolve().parents[1]

def derive_schedule(teams, games, year, now=None):
    now = now or datetime.now(timezone.utc)
    lookup = {int(t['id']): t for t in teams}
    if not lookup or len(lookup) != len(teams):
        raise ValueError('Empty or duplicate FBS team list')
    records, seen = [], set()
    for g in games:
        if g.get('homeId') not in lookup or g.get('awayId') not in lookup:
            continue
        gid = g['id']
        if gid in seen:
            raise ValueError('Duplicate FBS schedule game')
        seen.add(gid)
        if g.get('completed') is True:
            continue
        if g.get('completed') is not False:
            raise ValueError('Unknown game completion status')
        if g['homeId'] == g['awayId']:
            raise ValueError('Invalid schedule participants')
        date = g.get('startDate')
        if date:
            kickoff = datetime.fromisoformat(date.replace('Z', '+00:00'))
            if kickoff.tzinfo is None:
                raise ValueError('Schedule date lacks timezone')
            if kickoff < now and not g.get('startTimeTBD'):
                continue  # Avoid presenting past-started games as upcoming.
            if g.get('startTimeTBD') and kickoff.date() < now.date():
                continue
        elif not g.get('startTimeTBD'):
            raise ValueError('Missing kickoff date without TBD flag')
        records.append({'id': gid, 'week': g['week'], 'seasonType': g['seasonType'],
                        'startDate': date, 'startTimeTBD': bool(g.get('startTimeTBD')),
                        'neutralSite': bool(g.get('neutralSite')),
                        'homeId': g['homeId'], 'awayId': g['awayId'],
                        'homeTeam': lookup[g['homeId']]['school'], 'awayTeam': lookup[g['awayId']]['school']})
    # Empty upcoming schedule is legitimate after the season.
    return {'schemaVersion': 1, 'season': year, 'generatedAt': now.isoformat(),
            'source': 'CollegeFootballData', 'scope': 'FBS opponents only',
            'games': sorted(records, key=lambda g: (g['startDate'] is None, g['startDate'] or '', g['id']))}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--year', type=int, default=datetime.now(timezone.utc).year)
    args = parser.parse_args()
    key = os.environ.get('CFBD_API_KEY', '').strip()
    if not key:
        raise ValueError('Missing repository secret CFBD_API_KEY')
    teams = api('/teams/fbs', key, year=args.year)
    games = api('/games', key, year=args.year, seasonType='both', classification='fbs')
    if not games:
        raise ValueError('Empty season schedule response; published data preserved')
    output = derive_schedule(teams, games, args.year)
    path = ROOT / 'data' / 'schedule.json'
    path.parent.mkdir(exist_ok=True)
    payload = json.dumps(output, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
    temp = path.with_suffix('.tmp')
    temp.write_text(payload, encoding='utf-8')
    temp.replace(path)
    print(f"Validated {len(output['games'])} upcoming FBS-versus-FBS games.")

if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError) as e:
        print('Schedule refresh failed: ' + str(e), file=sys.stderr)
        sys.exit(1)
