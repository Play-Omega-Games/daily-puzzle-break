# Daily Puzzle Break

Original daily puzzles for a Grok Bot template by Omega Games: word ladders, anagrams, Letter Pools, logic grids, number puzzles and code crackers. Every puzzle is generated fresh from a seed (the date plus a private per-owner salt) and checked by code before it is shown: it has exactly one answer, or every accepted answer is listed in advance.

## Quick start

```
python3 -m puzzlebreak day --state STATE_DIR --date 2026-11-02
python3 -m puzzlebreak check --state STATE_DIR --n 1 --answer "cold cord word ward warm"
python3 -m puzzlebreak verify --state STATE_DIR
python3 -m puzzlebreak record --state STATE_DIR --date 2026-11-02 --n 1 --status solved --hints 0 --tries 1
python3 -m puzzlebreak stats --state STATE_DIR --date 2026-11-02
```

`STATE_DIR/profile.json` holds the owner's settings:

```
{"salt": "any private text", "types": ["ladder", "anagram", "pool", "logic", "numbers", "cipher"],
 "difficulty": "gentle | medium | tricky | ramp", "count": 1, "days": "every | weekdays | weekends"}
```

`day` writes `today.json` (puzzles with answers, kept private until reveal) and appends to `history.json`. The same date and salt always give the same set, and no puzzle repeats within 365 days.

## Puzzle types

| Type | Checked how |
|---|---|
| Word ladder | Par is the true shortest ladder. Any valid ladder is accepted. |
| Anagram | Every word that uses the same letters is listed and accepted. |
| Letter Pool | Every valid word that fits the seven tiles (each tile once per word) is listed in advance. |
| Logic grid | A solver confirms exactly one solution. |
| Number puzzles (target, sequence, pyramid, grid) | Target: any valid expression is accepted. Sequence, pyramid and grid: exactly one answer, confirmed by code. |
| Code cracker | The original sentence, or any decoding with the same letter swaps using real words. |

## Files

- `puzzlebreak/`: generators, checkers, day builder, streak and score.
- `data/words_common.txt`: everyday words we ask for. `data/words_accept.txt`: every word we accept.
- `data/blocklist_family.sha256`: family filter, stored as SHA-256 hashes. `data/blocklist_brands.sha256`: brand filter, also stored as SHA-256 hashes.
- `data/logic_grid.json`, `data/cipher_phrases.json`: Omega Games' own names, items and phrase parts.
- `samples/`: 30 sample days, all verified. `tests/`: run `python3 -m unittest discover -s tests -t .`
- `MANIFEST.txt`: every file with its size and SHA-256, for loading by raw URL.

## License

Data and text are CC0 1.0. Code is MIT. See `LICENSE`. Word lists are public domain.

Questions or ideas? Contact Omega Games at john@playomega.games.
