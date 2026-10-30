import datetime as dt
import os
import unittest

from puzzlebreak import day, stats

ALL = ['ladder', 'anagram', 'pool', 'logic', 'numbers', 'cipher']


def run_year(profile, start='2026-11-02', days=365):
    history, d0 = [], dt.date.fromisoformat(start)
    for i in range(days):
        d = day.build_day(d0 + dt.timedelta(days=i), profile, history)
        history += day.history_records(d)
    return history


def assert_no_repeats(tc, history):
    last = {}
    for h in history:
        d = dt.date.fromisoformat(h['date'])
        if h['fingerprint'] in last:
            tc.assertGreater((d - last[h['fingerprint']]).days, 365, h['fingerprint'])
        last[h['fingerprint']] = d


class Days(unittest.TestCase):
    def test_deterministic(self):
        p = {'salt': 'abc', 'types': ALL, 'difficulty': 'medium', 'count': 3}
        self.assertEqual(day.build_day('2026-11-05', p), day.build_day('2026-11-05', p))

    def test_rebuild_same_day_is_identical(self):
        p = {'salt': 'abc', 'types': ALL, 'difficulty': 'tricky', 'count': 3}
        first = day.build_day('2026-11-05', p, [])
        again = day.build_day('2026-11-05', p, day.history_records(first))
        self.assertEqual(first, again)

    def test_ramp(self):
        p = {'salt': 'abc', 'types': ['anagram'], 'difficulty': 'ramp', 'count': 1}
        self.assertEqual(day.build_day('2026-11-02', p)['difficulty'], 'gentle')
        self.assertEqual(day.build_day('2026-11-04', p)['difficulty'], 'medium')
        self.assertEqual(day.build_day('2026-11-08', p)['difficulty'], 'tricky')

    def test_year_all_types_no_repeats(self):
        h = run_year({'salt': 'year', 'types': ALL, 'difficulty': 'ramp', 'count': 3})
        self.assertEqual(len(h), 365 * 3)
        self.assertEqual({x['type'] for x in h}, set(ALL))
        assert_no_repeats(self, h)

    @unittest.skipUnless(os.environ.get('PUZZLE_LONG'), 'set PUZZLE_LONG=1 for the five-a-day stress test')
    def test_year_single_type_five_a_day(self):
        for t in ['anagram', 'cipher', 'ladder', 'pool', 'numbers']:
            for band in ['gentle', 'tricky']:
                h = run_year({'salt': 'stress', 'types': [t], 'difficulty': band, 'count': 5})
                assert_no_repeats(self, h)


class Stats(unittest.TestCase):
    def test_score(self):
        self.assertEqual(stats.score({'status': 'solved', 'base': 20, 'hints': 1}), 17)
        self.assertEqual(stats.score({'status': 'solved', 'base': 10, 'hints': 5}), 0)
        self.assertEqual(stats.score({'status': 'revealed', 'base': 30}), 0)
        self.assertEqual(stats.score({'status': 'solved', 'base': 30, 'bonus': True}), 35)

    def test_streaks(self):
        def rec(d, status, bonus=False):
            return {'date': d, 'type': 'anagram', 'status': status, 'bonus_puzzle': bonus}
        h = [rec('2026-11-01', 'solved'), rec('2026-11-02', 'solved'), rec('2026-11-03', 'revealed'),
             rec('2026-11-04', 'solved'), rec('2026-11-05', 'solved'), rec('2026-11-06', 'solved'),
             rec('2026-11-09', 'solved'), rec('2026-11-10', 'open'), rec('2026-11-10', 'solved', bonus=True)]
        s = stats.streaks(h, '2026-11-10', paused_days=['2026-11-07', '2026-11-08'])
        self.assertEqual(s, {'current': 4, 'best': 4})
        s = stats.streaks(h, '2026-11-11', paused_days=['2026-11-07', '2026-11-08'])
        self.assertEqual(s['current'], 0)
        missed = h + [rec('2026-11-07', 'missed')]
        self.assertEqual(stats.streaks(missed, '2026-11-10')['current'], 1)

    def test_weekday_schedule(self):
        h = [{'date': '2026-11-06', 'type': 'x', 'status': 'solved'},
             {'date': '2026-11-09', 'type': 'x', 'status': 'solved'}]
        self.assertEqual(stats.streaks(h, '2026-11-09', delivery_days={0, 1, 2, 3, 4})['current'], 2)


if __name__ == '__main__':
    unittest.main()
