from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from update_schedule import derive_schedule

class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.teams = [{'id': 1, 'school': 'A'}, {'id': 2, 'school': 'B'}]
        self.now = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)
        self.future = {'id': 1, 'homeId': 1, 'awayId': 2, 'week': 5, 'seasonType': 'regular',
                       'startDate': '2026-10-03T18:00:00Z', 'completed': False, 'startTimeTBD': False}
    def output(self, games): return derive_schedule(self.teams, games, 2026, self.now)
    def test_future_and_participants(self):
        result = self.output([self.future])
        self.assertEqual(result['games'][0]['homeTeam'], 'A')
        self.assertEqual(result['games'][0]['awayTeam'], 'B')
    def test_completed_past_and_fcs_excluded(self):
        games = [dict(self.future, id=2, completed=True), dict(self.future, id=3, startDate='2026-09-29T12:00:00Z'),
                 dict(self.future, id=4, awayId=99)]
        self.assertEqual(self.output(games)['games'], [])
    def test_tbd_retained(self):
        self.assertTrue(self.output([dict(self.future, startDate=None, startTimeTBD=True)])['games'][0]['startTimeTBD'])
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError): self.output([self.future, self.future])
    def test_invalid_date_rejected(self):
        with self.assertRaises(ValueError): self.output([dict(self.future, startDate='bad')])
        with self.assertRaises(ValueError): self.output([dict(self.future, startDate='2026-10-01T12:00:00')])
    def test_missing_completion_rejected(self):
        with self.assertRaises(ValueError): self.output([dict(self.future, completed=None)])
    def test_empty_future_allowed(self): self.assertEqual(self.output([])['games'], [])

if __name__ == '__main__': unittest.main()
