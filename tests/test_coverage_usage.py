import json
from pathlib import Path
import tempfile
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
import update_cfb_data as team_module
from update_players import derive_players
from test_players import fixtures
from refresh_dashboard import request_counter, record_status, write_json

class CoverageUsageTests(unittest.TestCase):
    def test_missing_optional_and_reported_zero(self):
        teams, games, boxes, player_boxes, roster = fixtures()
        # One missing team rush TD; zero is explicitly reported in the other game.
        boxes[0]['teams'][0]['stats'].append({'category': 'rushingTDs', 'stat': '0'})
        data = team_module.derive(teams, games, boxes, 2026)
        row = data['offenseWindows']['rush']['season'][0]
        self.assertEqual(row['fieldCoverage']['td'], {'available': 1, 'total': 2})
        self.assertIsNone(row['td'])
        self.assertEqual(row['fieldCoverage']['ypg']['available'], 2)
        self.assertEqual(data['windows']['rush']['season'][1]['fieldCoverage']['td']['available'], 1)

    def test_player_counts_only_recorded_games(self):
        data = fixtures()
        data[3][1]['teams'][0]['categories'][0]['types'].pop(0)
        out = derive_players(*data, 2026)
        row = out['windows']['season'][0]
        self.assertEqual(row['fieldCoverage']['carries'], {'available': 1, 'total': 2})
        self.assertEqual(row['fieldCoverage']['rushTD'], {'available': 2, 'total': 2})
        self.assertEqual(row['fieldCoverage']['targetShare']['available'], 0)
        self.assertIsNone(row['carries'])
        self.assertEqual(out['windows']['last1'][0]['fieldCoverage']['carries']['total'], 1)

    def test_retries_count_actual_attempts_and_no_key_storage(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return b'[]'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            counter = request_counter(root)
            errors = [HTTPError('https://example', 500, 'error', {}, None), Response()]
            with patch.object(team_module, 'API_REQUEST_OBSERVER', counter), patch.object(team_module, 'urlopen', side_effect=errors), patch.object(team_module.time, 'sleep'):
                self.assertEqual(team_module.api('/teams/fbs', 'DO-NOT-STORE-KEY', year=2026), [])
            record_status(2026, 'failed', '', root)
            text = (root / 'data/refresh-status.json').read_text()
            self.assertNotIn('DO-NOT-STORE-KEY', text)
            usage = json.loads(text)['apiUsage']
            self.assertEqual(usage['latestRequests'], 2)
            self.assertEqual(usage['latestByEndpoint'], {'/teams/fbs': 2})

    def test_month_rollover_and_duplicate_record_protection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_json(root / 'data/refresh-status.json', {'apiUsage': {'monthlyRequests': {'2026-09': 7}}})
            counts = {'token': 'test-token', 'startedAt': '2026-09-30T23:59:00Z', 'requests': 2, 'byEndpoint': {}, 'byMonth': {'2026-09': 1, '2026-10': 1}}
            write_json(root / 'data/api-attempt.tmp', counts)
            record_status(2026, 'failed', '', root)
            usage = json.loads((root / 'data/refresh-status.json').read_text())['apiUsage']
            self.assertEqual(usage['monthlyRequests'], {'2026-09': 8, '2026-10': 1})
            write_json(root / 'data/api-attempt.tmp', counts)
            record_status(2026, 'failed', '', root)
            usage = json.loads((root / 'data/refresh-status.json').read_text())['apiUsage']
            self.assertEqual(usage['monthlyRequests'], {'2026-09': 8, '2026-10': 1})

if __name__ == '__main__': unittest.main()
