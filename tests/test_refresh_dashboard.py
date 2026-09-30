from pathlib import Path
import json
import sys
import tempfile
from types import SimpleNamespace
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from refresh_dashboard import memoized_api, record_status, run_refresh, write_json

class RefreshTests(unittest.TestCase):
    def test_cache_is_isolated_and_reset(self):
        calls = []
        def fetch(*args, **params):
            calls.append(params)
            return [{'id': 1}]
        cache = memoized_api(fetch)
        cache('/teams', 'key', year=2026)[0]['id'] = 9
        self.assertEqual(cache('/teams', 'key', year=2026)[0]['id'], 1)
        cache('/teams', 'key', year=2025)
        self.assertEqual(len(calls), 2)
        memoized_api(fetch)('/teams', 'key', year=2026)
        self.assertEqual(len(calls), 3)

    def modules(self, root, fail=False, wrong=False):
        result = []
        for i, name in enumerate(('teams.json', 'players.json', 'schedule.json')):
            m = SimpleNamespace(ROOT=root, api=lambda *a, **k: [], __file__=name)
            def main(m=m, name=name, i=i):
                if fail and i == 1: raise ValueError('Invalid player data')
                write_json(m.ROOT / 'data' / name, {'schemaVersion': 1, 'season': 2025 if wrong and i == 2 else 2026, 'new': True})
            m.main = main
            result.append(m)
        return result

    def test_failed_refresh_preserves_all_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('teams.json', 'players.json', 'schedule.json'):
                write_json(root / 'data' / name, {'old': name})
            before = {p.name: p.read_bytes() for p in (root / 'data').iterdir()}
            modules = self.modules(root, fail=True)
            with self.assertRaises(ValueError): run_refresh(2026, root, modules)
            self.assertEqual(before, {p.name: p.read_bytes() for p in (root / 'data').iterdir()})
            self.assertTrue(all(m.ROOT == root for m in modules))

    def test_success_publishes_all_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            modules = self.modules(root)
            run_refresh(2026, root, modules)
            self.assertTrue(all(json.loads((root / 'data' / name).read_text())['new'] for name in ('teams.json', 'players.json', 'schedule.json')))
            self.assertTrue(all(m.ROOT == root for m in modules))

    def test_incompatible_stage_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError): run_refresh(2026, root, self.modules(root, wrong=True))
            self.assertFalse((root / 'data').exists())

    def test_status_preserves_success_on_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_json(root / 'data' / 'refresh-status.json', {'lastSuccessAt': '2026-09-29T12:00:00Z'})
            write_json(root / 'data' / 'refresh-attempt.tmp', {'startedAt': '2026-09-30T12:00:00Z'})
            record_status(2026, 'failed', '', root)
            status = json.loads((root / 'data' / 'refresh-status.json').read_text())
            self.assertEqual(status['lastSuccessAt'], '2026-09-29T12:00:00Z')
            self.assertEqual(status['outcome'], 'failed')
            self.assertEqual(status['startedAt'], '2026-09-30T12:00:00Z')
            self.assertFalse((root / 'data' / 'refresh-attempt.tmp').exists())
            self.assertNotIn('error', status)

if __name__ == '__main__': unittest.main()
