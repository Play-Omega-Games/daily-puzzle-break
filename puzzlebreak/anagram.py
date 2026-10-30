"""Anagram: unscramble the letters into one word."""
from functools import lru_cache

from .common import words, letters_only, text_problems

BANDS = {
    'gentle': {'lengths': [4, 5], 'max_answers': 1},
    'medium': {'lengths': [6], 'max_answers': 2},
    'tricky': {'lengths': [7, 8], 'max_answers': 3},
}


@lru_cache(maxsize=None)
def index():
    idx = {}
    for w in words('accept'):
        idx.setdefault(''.join(sorted(w)), []).append(w)
    return {k: sorted(v) for k, v in idx.items()}


def answers_for(letters):
    return index().get(''.join(sorted(letters)), [])


def generate(rng, difficulty):
    band = BANDS[difficulty]
    for _ in range(1000):
        length = rng.choice(band['lengths'])
        pool = sorted(w for w in words('common') if len(w) == length and not w.endswith('s'))
        target = rng.choice(pool)
        accepted = answers_for(target)
        if len(accepted) > band['max_answers']:
            continue
        letters = list(target)
        for _ in range(50):
            rng.shuffle(letters)
            scramble = ''.join(letters)
            same = sum(a == b for a, b in zip(scramble, target))
            if scramble not in accepted and same <= 1 and not text_problems(scramble):
                break
        else:
            continue
        others = [w for w in accepted if w != target]
        if text_problems(target[:3]):
            continue
        return {
            'type': 'anagram',
            'title': 'Anagram',
            'difficulty': difficulty,
            'prompt': f'Unscramble {scramble.upper()} into one word.',
            'data': {'scramble': scramble},
            'solution': target,
            'accepted': accepted,
            'answer_text': target.upper() + (' (also accepted: ' + ', '.join(w.upper() for w in others) + ')' if others else ''),
            'accepts': 'Any word in the accepted list.',
            'hints': [
                f'It starts with {target[0].upper()}.',
                f'It starts with {target[0].upper()} and ends with {target[-1].upper()}.',
                f'The first three letters are {target[:3].upper()}.',
            ],
            'explain': f'{scramble.upper()} rearranges to {target.upper()}.',
            'fingerprint': 'anagram:' + ''.join(sorted(target)),
        }
    raise RuntimeError('no anagram found')


def check(puzzle, answer):
    guess = letters_only(answer)
    if guess in puzzle['accepted']:
        return {'correct': True, 'feedback': f'Yes! {guess.upper()} it is.'}
    if sorted(guess) == sorted(puzzle['data']['scramble']):
        return {'correct': False, 'feedback': 'Right letters, but that one is not in my word list. Try again?'}
    return {'correct': False, 'feedback': 'Not quite. Use every letter exactly once.'}


def verify(puzzle):
    problems = []
    s, t = puzzle['data']['scramble'], puzzle['solution']
    if sorted(s) != sorted(t):
        problems.append('scramble letters differ from the answer')
    if sorted(answers_for(s)) != sorted(puzzle['accepted']):
        problems.append('accepted list is not complete')
    if s in puzzle['accepted']:
        problems.append('scramble is already a word')
    if len(puzzle['accepted']) > BANDS[puzzle['difficulty']]['max_answers']:
        problems.append('too many answers for this band')
    if t not in words('common'):
        problems.append('answer not in the common list')
    return problems
