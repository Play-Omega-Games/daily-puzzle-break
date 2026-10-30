import unittest

from puzzlebreak import anagram, cipher, ladder, logic, numbers, pool
from puzzlebreak.common import rng_for, text_problems

BANDS = ['gentle', 'medium', 'tricky']


class EveryTypeVerifies(unittest.TestCase):
    def run_many(self, mod, n, **kw):
        for band in BANDS:
            for i in range(n):
                p = mod.generate(rng_for('test', mod.__name__, band, i), band, **kw)
                self.assertEqual(mod.verify(p), [], (band, i, p['prompt']))
                self.assertEqual(len(p['hints']), 3)
                self.assertEqual(text_problems(p['prompt'] + ' '.join(p['hints'])), [])

    def test_ladder(self):
        self.run_many(ladder, 25)

    def test_anagram(self):
        self.run_many(anagram, 40)

    def test_pool(self):
        self.run_many(pool, 15)

    def test_logic(self):
        self.run_many(logic, 8)

    def test_numbers_each_subtype(self):
        for sub in numbers.SUBTYPES:
            self.run_many(numbers, 10, subtype=sub)

    def test_cipher(self):
        self.run_many(cipher, 40)

    def test_seeded(self):
        a = ladder.generate(rng_for('s', '2026-11-02', 0, 0), 'medium')
        b = ladder.generate(rng_for('s', '2026-11-02', 0, 0), 'medium')
        c = ladder.generate(rng_for('t', '2026-11-02', 0, 0), 'medium')
        self.assertEqual(a, b)
        self.assertNotEqual(a['fingerprint'], c['fingerprint'])


class Checkers(unittest.TestCase):
    def test_ladder_alternatives_and_errors(self):
        p = ladder.generate(rng_for('chk', 1), 'medium')
        path = p['solution']
        self.assertTrue(ladder.check(p, ' - '.join(path))['correct'])
        self.assertTrue(ladder.check(p, ' '.join(path[1:-1]))['correct'])
        self.assertTrue(ladder.check(p, ' '.join(path))['at_par'])
        self.assertFalse(ladder.check(p, path[0] + ' ' + path[-1])['correct'])
        self.assertFalse(ladder.check(p, 'hello')['correct'])

    def test_anagram_all_accepted(self):
        for i in range(30):
            p = anagram.generate(rng_for('an', i), 'tricky')
            for w in p['accepted']:
                self.assertTrue(anagram.check(p, w.upper())['correct'])
            self.assertFalse(anagram.check(p, p['data']['scramble'])['correct'])

    def test_pool_progress(self):
        p = pool.generate(rng_for('pl', 1), 'gentle')
        first = p['solution'][:3]
        r = pool.check(p, ' '.join(first) + ' zzzz')
        self.assertEqual(sorted(r['found']), sorted(first))
        self.assertFalse(r['correct'])
        r = pool.check(p, ' '.join(p['solution'][3:p['data']['goal']]), found_so_far=r['found'])
        self.assertTrue(r['correct'])

    def test_pool_tiles_used_once(self):
        p = pool.generate(rng_for('pl', 2), 'medium')
        tiles = p['data']['tiles']
        greedy = (tiles[0] * 2 + ''.join(tiles))[:8]
        self.assertFalse(pool.fits(greedy, tiles))
        self.assertTrue(all(pool.fits(w, tiles) for w in p['accepted']))
        self.assertNotIn('center', p['prompt'].lower())

    def test_logic_text_answer(self):
        p = logic.generate(rng_for('lg', 1), 'medium')
        self.assertTrue(logic.check(p, p['answer_text'])['correct'])
        self.assertTrue(logic.check(p, p['solution'])['correct'])
        wrong = {k: dict(v) for k, v in p['solution'].items()}
        a, b = list(wrong)[:2]
        key = list(wrong[a])[0]
        wrong[a][key], wrong[b][key] = wrong[b][key], wrong[a][key]
        self.assertFalse(logic.check(p, wrong)['correct'])

    def test_target_any_expression(self):
        p = numbers.generate(rng_for('tg', 1), 'gentle', subtype='target')
        for s in numbers.target_solutions(p['data']['numbers'], p['data']['target'])[:10]:
            self.assertTrue(numbers.check(p, s.replace('*', 'x'))['correct'], s)
        self.assertFalse(numbers.check(p, '1 + 1')['correct'])
        self.assertFalse(numbers.check(p, '__import__("os")')['correct'])

    def test_grid_and_sequence(self):
        g = numbers.generate(rng_for('gr', 1), 'tricky', subtype='grid')
        self.assertTrue(numbers.check(g, g['answer_text'])['correct'])
        self.assertFalse(numbers.check(g, '1 2 3')['correct'])
        s = numbers.generate(rng_for('sq', 1), 'medium', subtype='sequence')
        self.assertTrue(numbers.check(s, f'It is {s["solution"]}')['correct'])
        self.assertFalse(numbers.check(s, str(s['solution'] + 1))['correct'])

    def test_cipher(self):
        p = cipher.generate(rng_for('cp', 1), 'medium')
        self.assertTrue(cipher.check(p, p['solution'].upper())['correct'])
        self.assertFalse(cipher.check(p, 'the end')['correct'])


if __name__ == '__main__':
    unittest.main()
