"""Shared helpers: seeded randomness, word lists, family and brand filters."""
import hashlib
import random
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_BRAND_WORDS = 4
DATA = ROOT / 'data'


def rng_for(*parts):
    """A random generator seeded only by the given parts (date, salt, slot, attempt)."""
    digest = hashlib.sha256('|'.join(str(p) for p in parts).encode()).hexdigest()
    return random.Random(int(digest, 16))


@lru_cache(maxsize=None)
def words(kind):
    """'common' = words we ask for. 'accept' = every word we accept as an answer."""
    text = (DATA / f'words_{kind}.txt').read_text()
    return frozenset(text.split())


@lru_cache(maxsize=None)
def _blocked_hashes():
    lines = (DATA / 'blocklist_family.sha256').read_text().splitlines()
    return frozenset(l.strip() for l in lines if l.strip() and not l.startswith('#'))


@lru_cache(maxsize=None)
def _brand_hashes():
    lines = (DATA / 'blocklist_brands.sha256').read_text().splitlines()
    return frozenset(l.strip() for l in lines if l.strip() and not l.startswith('#'))


def _h(text):
    return hashlib.sha256(text.encode()).hexdigest()


def is_brand(term):
    """True if a word or short phrase (lowercase, single spaces) is a branded name."""
    return _h(' '.join(term.lower().split())) in _brand_hashes()


def is_blocked(word):
    w = word.lower()
    return _h(w) in _blocked_hashes() or is_brand(w)


def text_problems(text):
    """Family and brand problems in text shown to a player. Empty list means clean."""
    problems = []
    low = text.lower()
    for token in set(re.findall(r'[a-z]+', low)):
        if hashlib.sha256(token.encode()).hexdigest() in _blocked_hashes():
            problems.append(f'family filter word: {token[:2]}...')
    toks = re.findall(r'[a-z0-9]+', low)
    for size in range(1, MAX_BRAND_WORDS + 1):
        for i in range(len(toks) - size + 1):
            if is_brand(' '.join(toks[i:i + size])):
                problems.append(f'branded term at word {i + 1}')
    if '\u2014' in text or '\u2013' in text:
        problems.append('em or en dash')
    return problems


def letters_only(text):
    return re.sub(r'[^a-z]', '', text.lower())


def tokens(text):
    return re.findall(r'[a-z]+', text.lower())
