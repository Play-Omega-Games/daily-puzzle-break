"""Code cracker: an original sentence with every letter swapped for another."""
import json
import string
from functools import lru_cache

from .common import DATA, words, letters_only, tokens, text_problems

BANDS = {'gentle': {'reveal': 4, 'parts': [2, 3]}, 'medium': {'reveal': 2, 'parts': [3]}, 'tricky': {'reveal': 0, 'parts': [3]}}
ABC = string.ascii_lowercase


@lru_cache(maxsize=None)
def phrases():
    return json.loads((DATA / 'cipher_phrases.json').read_text())


def make_sentence(rng, parts):
    p = phrases()
    s = rng.choice(p['subjects']) + ' ' + rng.choice(p['actions'])
    if parts == 3:
        s += ' ' + rng.choice(p['endings'])
    return s + '.'


def encode(text, key):
    out = []
    for ch in text:
        low = ch.lower()
        if low in key:
            out.append(key[low].upper())
        else:
            out.append(ch)
    return ''.join(out)


def generate(rng, difficulty):
    band = BANDS[difficulty]
    sentence = make_sentence(rng, rng.choice(band['parts']))
    while True:
        shuffled = list(ABC)
        rng.shuffle(shuffled)
        key = dict(zip(ABC, shuffled))
        coded = encode(sentence, key)
        if all(a != b for a, b in zip(ABC, shuffled)) and not text_problems(coded):
            break
    used = sorted(set(letters_only(sentence)))
    rng.shuffle(used)
    reveal = sorted(used[:band['reveal']])
    hint_letters = [c for c in used if c not in reveal][:3]
    given = ', '.join(f'{key[c].upper()} = {c.upper()}' for c in reveal)
    return {
        'type': 'cipher',
        'title': 'Code cracker',
        'difficulty': difficulty,
        'prompt': ('Each letter stands for a different letter, the same swap all the way through. Crack the sentence:\n'
                   + coded + (f'\nStarter letters: {given}.' if reveal else '')),
        'data': {'coded': coded, 'revealed': reveal},
        'solution': sentence,
        'key': key,
        'answer_text': sentence,
        'accepts': 'The sentence, or any decoding that keeps the same letter swaps and uses only real words.',
        'hints': [f'{key[hint_letters[0]].upper()} stands for {hint_letters[0].upper()}.',
                  f'{key[hint_letters[1]].upper()} stands for {hint_letters[1].upper()}, '
                  f'and {key[hint_letters[2]].upper()} stands for {hint_letters[2].upper()}.',
                  f'The first two words are {" ".join(sentence.split()[:2]).upper()}.'],
        'explain': f'{coded} reads: {sentence}',
        'fingerprint': 'cipher:' + letters_only(sentence),
    }


def check(puzzle, answer):
    guess, target = letters_only(answer), letters_only(puzzle['solution'])
    if guess == target:
        return {'correct': True, 'feedback': 'Yes! Code cracked.'}
    coded = letters_only(puzzle['data']['coded'])
    if len(guess) == len(coded):
        fwd, back = {}, {}
        ok = all(fwd.setdefault(c, g) == g and back.setdefault(g, c) == c for c, g in zip(coded, guess))
        if ok and all(t in words('accept') or len(t) == 1 and t in 'ai' for t in tokens(answer)):
            return {'correct': True, 'feedback': 'Yes! That decoding works too.'}
    right = sum(1 for a, b in zip(guess, target) if a == b)
    return {'correct': False, 'feedback': f'Not quite: {right} of {len(target)} letters are right.'}


def verify(puzzle):
    problems = []
    key = puzzle['key']
    if any(a == b for a, b in key.items()):
        problems.append('a letter maps to itself')
    if len(set(key.values())) != 26:
        problems.append('key is not one to one')
    if encode(puzzle['solution'], key) != puzzle['data']['coded']:
        problems.append('coded text does not match')
    bad = [t for t in tokens(puzzle['solution']) if t not in words('accept') and t not in ('a',)]
    if bad:
        problems.append('sentence has words outside the list: ' + ', '.join(bad))
    if not check(puzzle, puzzle['solution'])['correct']:
        problems.append('checker rejects its own answer')
    return problems
