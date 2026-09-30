"""Stage a complete refresh; share private responses only within this run."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DATA_FILES = ('teams.json', 'players.json', 'schedule.json')

def now():
    return datetime.now(timezone.utc).isoformat()

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, allow_nan=False, separators=(',', ':')), encoding='utf-8')
    temp.replace(path)

def memoized_api(fetch):
    cache = {}
    def shared(path, key, **params):
        identity = (path, key, tuple(sorted(params.items())))
        if identity not in cache:
            cache[identity] = fetch(path, key, **params)
        return deepcopy(cache[identity])
    return shared

def run_refresh(year, root=ROOT, modules=None):
    if modules is None:
        import update_cfb_data
        import update_players
        import update_schedule
        modules = (update_cfb_data, update_players, update_schedule)
    shared = memoized_api(modules[0].api)
    original_argv = sys.argv[:]
    originals = [(m, m.ROOT, m.api) for m in modules]
    try:
        with tempfile.TemporaryDirectory(prefix='cfb-refresh-') as directory:
            stage = Path(directory)
            (stage / 'data').mkdir()
            for name in DATA_FILES:
                previous = root / 'data' / name
                if previous.exists():
                    shutil.copy2(previous, stage / 'data' / name)
            for module in modules:
                module.ROOT = stage
                module.api = shared
                sys.argv = [module.__file__, '--year', str(year)]
                module.main()
            outputs = {}
            for name in DATA_FILES:
                path = stage / 'data' / name
                content = path.read_bytes()
                data = json.loads(content)
                if data.get('schemaVersion') != 1 or data.get('season') != year:
                    raise ValueError('Staged datasets have incompatible seasons or schemas')
                outputs[name] = content
            # GitHub publishes these together in one commit only after validation.
            (root / 'data').mkdir(parents=True, exist_ok=True)
            for name, content in outputs.items():
                temp = root / 'data' / (name + '.tmp')
                temp.write_bytes(content)
            for name in outputs:
                (root / 'data' / (name + '.tmp')).replace(root / 'data' / name)
    finally:
        sys.argv = original_argv
        for module, old_root, old_api in originals:
            module.ROOT, module.api = old_root, old_api

def record_status(year, outcome, run_url, root=ROOT):
    path = root / 'data' / 'refresh-status.json'
    previous = json.loads(path.read_text()) if path.exists() else {}
    marker = root / 'data' / 'refresh-attempt.tmp'
    started = json.loads(marker.read_text()).get('startedAt') if marker.exists() else None
    finished = now()
    dates, seasons = {}, set()
    for name in DATA_FILES:
        dataset = root / 'data' / name
        if dataset.exists():
            data = json.loads(dataset.read_text())
            dates[name.removesuffix('.json')] = data.get('generatedAt')
            seasons.add(data.get('season'))
    fallback = min(dates.values()) if len(dates) == 3 and all(dates.values()) and len(seasons) == 1 else None
    last_success = finished if outcome == 'success' else previous.get('lastSuccessAt') or fallback
    write_json(path, {'schemaVersion': 1, 'attemptedSeason': year, 'startedAt': started,
                      'finishedAt': finished, 'outcome': outcome, 'lastSuccessAt': last_success,
                      'datasetGeneratedAt': dates, 'runUrl': run_url,
                      'message': 'All datasets validated.' if outcome == 'success' else 'Refresh failed; last validated datasets preserved.'})
    marker.unlink(missing_ok=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--year', type=int, required=True)
    parser.add_argument('--begin', action='store_true')
    parser.add_argument('--record', choices=('success', 'failed'))
    parser.add_argument('--run-url', default='')
    args = parser.parse_args()
    if args.begin:
        write_json(ROOT / 'data' / 'refresh-attempt.tmp', {'startedAt': now(), 'season': args.year})
    elif args.record:
        record_status(args.year, args.record, args.run_url)
    else:
        run_refresh(args.year)

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # Never publish exception text or raw API responses in status JSON.
        print('Dashboard refresh failed. See the workflow step for details.', file=sys.stderr)
        raise
