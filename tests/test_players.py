import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from update_players import derive_players, normalize_player_team

def fixtures():
    teams = [{'id': 1, 'school': 'A', 'conference': 'Test'}, {'id': 2, 'school': 'B', 'conference': 'Test'}]
    games, boxes, player_boxes = [], [], []
    roster = [{'id': str(tid), 'team': name, 'position': 'RB'} for tid, name in ((1, 'A'), (2, 'B'))]
    for gid in (1, 2):
        games.append({'id': gid, 'completed': True, 'homeId': 1, 'awayId': 2, 'startDate': f'2026-09-0{gid}'})
        sides, psides = [], []
        for tid, name in ((1, 'A'), (2, 'B')):
            stats = {'netPassingYards': '200', 'completionAttempts': '10-20', 'rushingYards': '100', 'rushingAttempts': '25'}
            sides.append({'teamId': tid, 'stats': [{'category': k, 'stat': v} for k, v in stats.items()]})
            psides.append({'team': name, 'categories': [{'name': 'rushing', 'types': [
                {'name': label, 'athletes': [{'id': str(tid), 'name': f'RB {tid}', 'stat': value}]}
                for label, value in [('CAR', str(10 * gid)), ('YDS', str(40 * gid)), ('TD', '1')]]},
                {'name': 'receiving', 'types': [{'name': label, 'athletes': [{'id': str(tid), 'name': f'RB {tid}', 'stat': value}]}
                 for label, value in [('REC', '2'), ('YDS', '12'), ('TD', '0')]]}]})
        boxes.append({'id': gid, 'teams': sides})
        player_boxes.append({'id': gid, 'teams': psides})
    return teams, games, boxes, player_boxes, roster

class PlayerTests(unittest.TestCase):
    def test_matching_totals_and_shares(self):
        r = derive_players(*fixtures(), 2026)['windows']['season'][0]
        self.assertEqual(r['carries'], 30)
        self.assertEqual(r['carriesPerGame'], 15)
        self.assertEqual(r['carryShare'], 60)
        self.assertEqual(r['receptionShare'], 20)
        self.assertEqual(r['ypc'], 4)
        self.assertIsNone(r['targets'])
        self.assertIsNone(r['targetShare'])
    def test_last_game_uses_team_window(self):
        data = fixtures()
        data[3][1]['teams'][0]['categories'][0]['types'][0]['athletes'].append({'id': 'backup', 'name': 'Backup', 'stat': '1'})
        output = derive_players(*data, 2026)
        backup = next(x for x in output['windows']['last1'] if x['playerId'] == 'backup')
        self.assertEqual(backup['teamGames'], 1)
        self.assertEqual(backup['statGames'], 1)
        self.assertEqual(backup['position'], 'Other')
    def test_missing_metric_is_not_zero(self):
        data = fixtures()
        data[3][1]['teams'][0]['categories'][0]['types'] = data[3][1]['teams'][0]['categories'][0]['types'][1:]
        r = derive_players(*data, 2026)['windows']['season'][0]
        self.assertIsNone(r['carries'])
        self.assertIsNone(r['carryShare'])
    def test_missing_game_fails(self):
        data = list(fixtures()); data[3] = data[3][:1]
        with self.assertRaises(ValueError): derive_players(*data, 2026)
    def test_duplicate_stat_fails(self):
        data = fixtures()
        side = data[3][0]['teams'][0]
        side['categories'][0]['types'].append(side['categories'][0]['types'][0])
        with self.assertRaises(ValueError): normalize_player_team(side, 1)
    def test_pass_and_target_parsing(self):
        side = {'categories': [{'name': 'passing', 'types': [{'name': 'C/ATT', 'athletes': [{'id': 'x', 'name': 'QB', 'stat': '10/20'}]}]},
                {'name': 'receiving', 'types': [{'name': 'TGT', 'athletes': [{'id': 'y', 'name': 'WR', 'stat': '7'}]}]}]}
        players = normalize_player_team(side, 1)
        self.assertEqual(players[0]['attempts'], 20)
        self.assertEqual(players[1]['targets'], 7)
    def test_invalid_counts_rejected(self):
        data = fixtures()
        data[3][0]['teams'][0]['categories'][0]['types'][0]['athletes'][0]['stat'] = '-1'
        with self.assertRaises(ValueError): derive_players(*data, 2026)

if __name__ == '__main__': unittest.main()
