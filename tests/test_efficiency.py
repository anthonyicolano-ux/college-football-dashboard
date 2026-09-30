from collections import defaultdict
from copy import deepcopy
import unittest
from test_metrics import module, fixtures

def rate_history():
    def game(gid, opp, yards, attempts):
        stats = {u: {'yards': yards, 'attempts': attempts} for u in ('pass', 'rush')}
        return {'id': gid, 'opponent': opp, 'allowed': stats, 'offense': deepcopy(stats)}
    history = defaultdict(list)
    history[1] = [game(1, 2, 100, 20), game(2, 3, 300, 100)]
    history[2] = [game(1, 1, 100, 20), game(3, 3, 200, 40)]
    history[3] = [game(2, 1, 300, 100), game(3, 2, 300, 30)]
    windows = {u: {p: [{'teamId': 1, 'games': 1 if p == 'last1' else 2}]
                     for p in ('season', 'last3', 'last1')} for u in ('pass', 'rush')}
    return history, windows

class EfficiencyTests(unittest.TestCase):
    def test_attempt_weighted_efficiency_and_separate_volume(self):
        history, windows = rate_history()
        row = module.add_efficiency(windows, history, 'allowed')['pass']['season'][0]
        self.assertEqual(row['attemptsPerGame'], 60)
        self.assertAlmostEqual(row['adjustedEffRatio'], 100 * 400 / 1100)
        self.assertAlmostEqual(row['effExpected'], 1100 / 120)
        self.assertAlmostEqual(row['effActual'], 400 / 120)
        self.assertAlmostEqual(row['volumeRatio'], 100 * 120 / 70)
        self.assertEqual(row['effBaselineGames'], 2)
        self.assertEqual(row['baselineMinGames'], 1)
        self.assertEqual(row['effRank'], 1)
    def test_current_game_does_not_set_opponent_rate(self):
        history, windows = rate_history()
        history[2][0]['offense']['pass']['yards'] = 9999
        row = module.add_efficiency(windows, history, 'allowed')['pass']['season'][0]
        self.assertAlmostEqual(row['adjustedEffRatio'], 100 * 400 / 1100)
    def test_partial_baseline_has_percentage_but_no_rank(self):
        history, windows = rate_history()
        history[3] = history[3][:1]
        row = module.add_efficiency(windows, history, 'allowed')['rush']['season'][0]
        self.assertEqual(row['effBaselineGames'], 1)
        self.assertEqual(row['adjustedEffRatio'], 100)
        self.assertIsNone(row['effRank'])
    def test_zero_attempts_no_division_or_rank(self):
        history, windows = rate_history()
        history[1][0]['allowed']['pass']['attempts'] = 0
        row = module.add_efficiency(windows, history, 'allowed')['pass']['season'][0]
        self.assertEqual(row['effBaselineGames'], 1)
        self.assertIsNone(row['effRank'])
    def test_last_game_uses_own_window(self):
        history, windows = rate_history()
        row = module.add_efficiency(windows, history, 'offense')['rush']['last1'][0]
        self.assertEqual(row['attemptsPerGame'], 100)
        self.assertEqual(row['adjustedEffRatio'], 30)
        self.assertAlmostEqual(row['volumeRatio'], 100 * 100 / 30)
    def test_rank_direction_and_regression(self):
        output = module.derive(*fixtures(), 2026)
        self.assertEqual(output['offenseWindows']['pass']['season'][2]['effRank'], 1)
        self.assertEqual(output['windows']['pass']['season'][0]['ratio'], 100)
        self.assertEqual(output['windows']['pass']['season'][0]['effRank'], 1)
        self.assertEqual(output['windows']['pass']['season'][0]['attemptsPerGame'], 20)
    def test_no_baseline_stays_missing(self):
        teams, games, boxes = fixtures()
        output = module.derive(teams, games[:1], boxes[:1], 2026)
        row = output['windows']['rush']['season'][0]
        self.assertIsNone(row['adjustedEffRatio'])
        self.assertIsNone(row['volumeRatio'])
        self.assertIsNone(row['baselineMinGames'])

if __name__ == '__main__': unittest.main()
