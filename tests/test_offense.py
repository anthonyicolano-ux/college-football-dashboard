import unittest
from test_metrics import fixtures, module

class OffenseTests(unittest.TestCase):
    def test_expected_totals_and_direction(self):
        output = module.derive(*fixtures(), 2026)
        rows = output['offenseWindows']['pass']['season']
        self.assertEqual(rows[0]['expected'], 250)
        self.assertEqual(rows[0]['ratio'], 40)
        self.assertEqual(rows[2]['ratio'], 200)
        self.assertEqual(rows[2]['rawRank'], 1)
        self.assertEqual(rows[2]['adjRank'], 1)
        self.assertEqual(rows[0]['adjRank'], 3)
        self.assertEqual(rows[0]['comp'], 50)
    def test_current_game_excluded_from_expectation(self):
        teams, games, boxes = fixtures()
        boxes[0]['teams'][0]['stats'][0]['stat'] = '900'
        rows = module.derive(teams, games, boxes, 2026)['offenseWindows']['pass']['season']
        self.assertEqual(rows[0]['expected'], 250)
        self.assertEqual(rows[0]['ratio'], 200)
    def test_no_baseline_unranked_not_zero(self):
        teams, games, boxes = fixtures()
        output = module.derive(teams, games[:1], boxes[:1], 2026)
        row = output['offenseWindows']['rush']['season'][0]
        self.assertIsNone(row['ratio'])
        self.assertIsNone(row['adjRank'])
        self.assertIsNone(row['delta'])
        self.assertEqual(row['baselineGames'], 0)
    def test_last_game_and_optional_fields(self):
        output = module.derive(*fixtures(), 2026)
        row = output['offenseWindows']['rush']['last1'][2]
        self.assertEqual(row['games'], 1)
        self.assertEqual(row['ypg'], 150)
        self.assertEqual(row['expected'], 50)
        self.assertEqual(row['ratio'], 300)
        self.assertIsNone(row['td'])
    def test_offense_does_not_change_defense_windows(self):
        output = module.derive(*fixtures(), 2026)
        self.assertEqual(output['windows']['pass']['season'][0]['ypg'], 250)
        self.assertEqual(output['windows']['pass']['season'][0]['ratio'], 100)
    def test_all_windows_finite_and_correct_pool(self):
        import math
        output = module.derive(*fixtures(), 2026)
        for unit in ('pass', 'rush'):
            for period in ('season', 'last3', 'last1'):
                rows = output['offenseWindows'][unit][period]
                self.assertTrue(all(math.isfinite(r['ratio']) for r in rows))
                self.assertTrue(all(r['delta'] == r['comparableRawRank'] - r['adjRank'] for r in rows))

if __name__ == '__main__': unittest.main()
