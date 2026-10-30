import json
import unittest
from pathlib import Path

from puzzlebreak.common import ROOT, text_problems


class Text(unittest.TestCase):
    def test_player_facing_text_is_clean(self):
        files = ['README.md', 'samples/30-days.md', 'samples/30-days.json',
                 'data/logic_grid.json', 'data/cipher_phrases.json']
        for f in files:
            path = ROOT / f
            if path.exists():
                self.assertEqual(text_problems(path.read_text()), [], f)

    def test_no_dashes_in_code_strings(self):
        for path in (ROOT / 'puzzlebreak').glob('*.py'):
            text = path.read_text()
            self.assertNotIn('\u2014', text, path)
            self.assertNotIn('\u2013', text, path)


if __name__ == '__main__':
    unittest.main()
