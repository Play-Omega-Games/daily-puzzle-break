import re
import unittest

import re as _re

from puzzlebreak.common import DATA, words, is_blocked, is_brand, text_problems


class WordLists(unittest.TestCase):
    def test_shape(self):
        for kind in ('common', 'accept'):
            ws = words(kind)
            self.assertGreater(len(ws), 15000)
            self.assertTrue(all(re.fullmatch(r'[a-z]{2,}', w) for w in ws))

    def test_common_inside_accept(self):
        self.assertTrue(words('common') <= words('accept'))

    def test_family_filter_applied(self):
        self.assertFalse([w for w in words('accept') if is_blocked(w)])

    def test_brand_filter_is_hashed_and_applied(self):
        lines = [l for l in (DATA / 'blocklist_brands.sha256').read_text().splitlines() if not l.startswith('#')]
        self.assertGreater(len(lines), 5)
        self.assertTrue(all(_re.fullmatch(r'[0-9a-f]{64}', l) for l in lines))
        self.assertFalse([w for w in words('accept') if is_brand(w)])
        self.assertFalse(is_brand('word ladder'))

    def test_text_problems(self):
        self.assertEqual(text_problems('A calm word ladder for today.'), [])
        self.assertTrue(text_problems('one \u2014 two'))


if __name__ == '__main__':
    unittest.main()
