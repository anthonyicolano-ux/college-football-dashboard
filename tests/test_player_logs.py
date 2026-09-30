import json
import unittest
from test_players import fixtures
from update_players import derive_players

class PlayerLogTests(unittest.TestCase):
    def test_game_usage_and_window_reconcile(self):
        out = derive_players(*fixtures(), 2026)
        p = out['playerLogs'][0]
        self.assertEqual([g['gameId'] for g in p['games']], [2, 1])
        self.assertEqual(p['games'][0]['carryShare'], 80)
        self.assertEqual(p['games'][1]['carryShare'], 40)
        self.assertEqual(p['games'][0]['receptionShare'], 20)
        self.assertEqual(p['games'][0]['ypc'], 4)
        self.assertEqual(sum(g['carries'] for g in p['games']), out['windows']['season'][0]['carries'])
        self.assertIsNone(p['games'][0]['targets'])
        self.assertEqual(p['games'][0]['opponent'], 'B')
        self.assertEqual(p['games'][0]['location'], 'Home')
        json.dumps(out, allow_nan=False)

    def test_no_record_is_not_zero_or_last_appearance(self):
        data = fixtures()
        for category in data[3][1]['teams'][0]['categories']:
            for stat in category['types']:
                for athlete in stat['athletes']:
                    athlete['id'] = 'backup'
                    athlete['name'] = 'Backup'
        out = derive_players(*data, 2026)
        p = next(p for p in out['playerLogs'] if p['teamId'] == 1 and p['playerId'] == '1')
        self.assertEqual(len(p['games']), 2)
        self.assertFalse(p['games'][0]['recorded'])
        self.assertIsNone(p['games'][0]['carries'])
        self.assertIsNone(p['games'][0]['carryShare'])
        self.assertFalse(any(p['playerId'] == '1' and p['teamId'] == 1 for p in out['windows']['last1']))
        self.assertTrue(p['games'][1]['recorded'])

    def test_missing_optional_field_preserved(self):
        data = fixtures()
        data[3][1]['teams'][0]['categories'][0]['types'].pop(0)
        out = derive_players(*data, 2026)
        p = out['playerLogs'][0]
        self.assertTrue(p['games'][0]['recorded'])
        self.assertIsNone(p['games'][0]['carries'])
        self.assertIsNone(p['games'][0]['ypc'])
        self.assertIsNone(out['windows']['season'][0]['carries'])

    def test_team_identity_and_neutral_location(self):
        data = fixtures()
        data[1][0]['neutralSite'] = True
        # Same athlete ID on different teams must remain distinct.
        data[4][1]['id'] = '1'
        for game in data[3]:
            for category in game['teams'][1]['categories']:
                for stat in category['types']:
                    stat['athletes'][0]['id'] = '1'
        out = derive_players(*data, 2026)
        self.assertEqual(len(out['playerLogs']), 2)
        self.assertEqual({p['teamId'] for p in out['playerLogs']}, {1, 2})
        self.assertTrue(all(p['games'][1]['location'] == 'Neutral' for p in out['playerLogs']))

if __name__ == '__main__': unittest.main()
