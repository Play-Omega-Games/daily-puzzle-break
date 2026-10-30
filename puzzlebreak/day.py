"""Build one day's puzzle set: seeded by date and the owner's salt, no repeats within 365 days."""
import datetime as dt

from . import anagram, cipher, ladder, logic, numbers, pool
from .common import rng_for, text_problems

MODULES = {'ladder': ladder, 'anagram': anagram, 'pool': pool, 'logic': logic, 'numbers': numbers, 'cipher': cipher}
RAMP = {0: 'gentle', 1: 'gentle', 2: 'medium', 3: 'medium', 4: 'tricky', 5: 'tricky', 6: 'tricky'}
RAMP_WEEKDAYS = {0: 'gentle', 1: 'gentle', 2: 'medium', 3: 'medium', 4: 'tricky'}
POINTS = {'gentle': 10, 'medium': 20, 'tricky': 30}
REPEAT_WINDOW = 365


def difficulty_for(profile, date):
    d = profile.get('difficulty', 'medium')
    if d != 'ramp':
        return d
    wd = date.weekday()
    if profile.get('days') == 'weekdays':
        return RAMP_WEEKDAYS.get(wd, 'tricky')
    return RAMP[wd]


def recent_fingerprints(history, date):
    start = date - dt.timedelta(days=REPEAT_WINDOW)
    return {h['fingerprint'] for h in history
            if start <= dt.date.fromisoformat(h['date']) < date}


def build_day(date, profile, history=()):
    """date: datetime.date. profile: dict with salt, types, difficulty, count. history: list of past puzzle records."""
    if isinstance(date, str):
        date = dt.date.fromisoformat(date)
    types = profile.get('types') or list(MODULES)
    count = int(profile.get('count', 3))
    difficulty = difficulty_for(profile, date)
    avoid = recent_fingerprints(history, date)
    ordinal = date.toordinal()
    puzzles = []
    for slot in range(count):
        kind = types[(ordinal * count + slot) % len(types)]
        for attempt in range(200):
            rng = rng_for(profile['salt'], date.isoformat(), slot, attempt)
            p = MODULES[kind].generate(rng, difficulty)
            shown = p['prompt'] + ' ' + ' '.join(p['hints']) + ' ' + p['title']
            if p['fingerprint'] in avoid or text_problems(shown):
                continue
            avoid.add(p['fingerprint'])
            break
        else:
            raise RuntimeError(f'could not build a fresh {kind} puzzle for {date}')
        p['n'] = slot + 1
        p['date'] = date.isoformat()
        p['points'] = POINTS[difficulty]
        puzzles.append(p)
    return {'date': date.isoformat(), 'difficulty': difficulty, 'puzzles': puzzles}


def history_records(day):
    return [{'date': day['date'], 'n': p['n'], 'type': p['type'], 'difficulty': p['difficulty'],
             'fingerprint': p['fingerprint'], 'status': 'open', 'tries': 0, 'hints': 0, 'points': 0}
            for p in day['puzzles']]


def verify_day(day):
    problems = []
    for p in day['puzzles']:
        for prob in MODULES[p['type']].verify(p):
            problems.append(f'#{p["n"]} {p["type"]}: {prob}')
        shown = p['prompt'] + ' ' + ' '.join(p['hints']) + ' ' + p['title'] + ' ' + str(p['answer_text'])
        for prob in text_problems(shown):
            problems.append(f'#{p["n"]} {p["type"]}: {prob}')
    fps = [p['fingerprint'] for p in day['puzzles']]
    if len(set(fps)) != len(fps):
        problems.append('repeat inside the day')
    return problems


def check(puzzle, answer, **kw):
    return MODULES[puzzle['type']].check(puzzle, answer, **kw)
