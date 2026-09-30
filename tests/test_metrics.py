import importlib.util
from pathlib import Path
import unittest
spec = importlib.util.spec_from_file_location('updater', Path(__file__).resolve().parents[1] / 'scripts/update_cfb_data.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def fixtures():
    teams = [{'id': i, 'school': f'Team {i}', 'conference': 'Test'} for i in (1, 2, 3)]
    games, boxes = [], []
    for gid, (home, away) in enumerate(((1, 2), (1, 3), (2, 3)), 1):
        games.append({'id': gid, 'completed': True, 'homeId': home, 'awayId': away,
                      'startDate': f'2026-09-0{gid}T12:00:00Z'})
        sides = []
        for tid in (home, away):
            stats = {'netPassingYards': str(100 * tid), 'completionAttempts': '10-20',
                     'rushingYards': str(50 * tid), 'rushingAttempts': '25'}
            sides.append({'teamId': tid, 'points': 21, 'stats': [{'category': k, 'stat': v} for k, v in stats.items()]})
        boxes.append({'id': gid, 'teams': sides})
    return teams, games, boxes

class MetricsTests(unittest.TestCase):
    def test_adjustment_excludes_current_game_and_preserves_missing_fields(self):
        output = module.derive(*fixtures(), 2026)
        row = output['windows']['pass']['season'][0]
        self.assertEqual(row['ypg'], 250)
        self.assertEqual(row['expected'], 250)
        self.assertEqual(row['ratio'], 100)
        self.assertEqual(row['comp'], 50)
        self.assertEqual(row['baselineGames'], 2)
        self.assertIsNone(row['td'])
        self.assertIsNone(row['ints'])
        self.assertEqual(row['adjRank'], 1)
        self.assertEqual(row['delta'], 2)
    def test_missing_box_score_rejected(self):
        teams, games, boxes = fixtures()
        with self.assertRaises(ValueError): module.derive(teams, games, boxes[:-1], 2026)
    def test_fcs_games_excluded(self):
        teams, games, boxes = fixtures()
        games.append({'id': 9, 'completed': True, 'homeId': 1, 'awayId': 99})
        self.assertEqual(module.derive(teams, games, boxes, 2026)['completedGames'], 3)
    def test_missing_baseline_not_zero(self):
        teams, games, boxes = fixtures()
        output = module.derive(teams, games[:1], boxes[:1], 2026)
        row = output['windows']['rush']['season'][0]
        self.assertIsNone(row['ratio'])
        self.assertIsNone(row['adjRank'])
        self.assertEqual(row['baselineGames'], 0)
    def test_totals_not_average_of_ratios(self):
        teams, games, boxes = fixtures()
        # Team 2 produces 600 yards against 1, 200 against 3.
        boxes[0]['teams'][1]['stats'][0]['stat'] = '600'
        row = module.derive(teams, games, boxes, 2026)['windows']['pass']['season'][0]
        self.assertEqual(row['ratio'], 180)
    def test_duplicate_or_missing_required_stats_fail(self):
        teams, games, boxes = fixtures()
        with self.assertRaises(ValueError): module.derive(teams, games, boxes + boxes[:1], 2026)
        boxes[0]['teams'][0]['stats'] = []
        with self.assertRaises(ValueError): module.derive(teams, games, boxes, 2026)

if __name__ == '__main__': unittest.main()
