"""Letter Pool: make words from a pool of seven letter tiles, each tile used at most once per word."""
from collections import Counter
from functools import lru_cache

from .common import words, tokens

BANDS = {'gentle': 8, 'medium': 12, 'tricky': 16}


@lru_cache(maxsize=None)
def _candidates():
    return tuple((w, Counter(w)) for w in sorted(words('accept')) if 4 <= len(w) <= 7)


def fits(word, tiles):
    need, have = Counter(word), Counter(tiles)
    return all(have[c] >= n for c, n in need.items())


def all_words(tiles):
    have = Counter(tiles)
    return sorted(w for w, need in _candidates() if all(have[c] >= n for c, n in need.items()))


def generate(rng, difficulty):
    goal = BANDS[difficulty]
    seeds = sorted(w for w in words('accept') if len(w) == 7)
    for _ in range(500):
        tiles = list(rng.choice(seeds))
        rng.shuffle(tiles)
        accepted = all_words(tiles)
        common = [w for w in accepted if w in words('common')]
        if len(common) < goal + 4:
            continue
        tray = '  '.join(f'[{c.upper()}]' for c in tiles)
        return {
            'type': 'pool',
            'title': 'Letter Pool',
            'difficulty': difficulty,
            'prompt': (f'Your letter tiles: {tray}\n'
                       f'Make {goal} words of 4 or more letters from these tiles. '
                       'Each tile can be used once per word.'),
            'data': {'tiles': tiles, 'goal': goal},
            'solution': common,
            'accepted': accepted,
            'answer_text': f'{len(common)} everyday words, for example ' + ', '.join(w.upper() for w in common[:goal]),
            'accepts': 'Any word in the accepted list.',
            'hints': [
                f'There are {len(common)} everyday words here. One starts with {common[0][:2].upper()}.',
                f'Try a word starting with {common[len(common) // 2][:2].upper()}, '
                f'and one ending in {common[-1][-2:].upper()}.',
                'Three to try: ' + ', '.join(w.upper() for w in rng.sample(common, 3)) + '.',
            ],
            'explain': 'Everyday words: ' + ', '.join(w.upper() for w in common) + '.',
            'fingerprint': 'pool:' + ''.join(sorted(tiles)),
        }
    raise RuntimeError('no letter pool found')


def check(puzzle, answer, found_so_far=()):
    acc = set(puzzle['accepted'])
    tiles = puzzle['data']['tiles']
    found = set(found_so_far)
    new, rejected, too_many = [], [], []
    for t in tokens(answer):
        if t in found:
            continue
        if t in acc:
            found.add(t)
            new.append(t)
        elif t in words('accept') and not fits(t, tiles):
            too_many.append(t)
        else:
            rejected.append(t)
    goal = puzzle['data']['goal']
    msg = []
    if new:
        msg.append('Got it: ' + ', '.join(w.upper() for w in new) + '.')
    if too_many:
        msg.append('Needs tiles you do not have: ' + ', '.join(w.upper() for w in too_many) + '.')
    if rejected:
        msg.append('Not in the list: ' + ', '.join(w.upper() for w in rejected) + '.')
    msg.append(f'{len(found)} of {goal} found.')
    return {'correct': len(found) >= goal, 'found': sorted(found), 'feedback': ' '.join(msg)}


def verify(puzzle):
    d = puzzle['data']
    problems = []
    if len(d['tiles']) != 7:
        problems.append('pool does not have seven tiles')
    if all_words(d['tiles']) != sorted(puzzle['accepted']):
        problems.append('accepted list is not complete')
    if any(not fits(w, d['tiles']) for w in puzzle['accepted']):
        problems.append('an accepted word needs missing tiles')
    if len(puzzle['solution']) < d['goal']:
        problems.append('not enough everyday words to reach the goal')
    if not check(puzzle, ' '.join(puzzle['solution'][:d['goal']]))['correct']:
        problems.append('checker rejects its own words')
    return problems
