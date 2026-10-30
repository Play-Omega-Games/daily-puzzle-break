"""Command line.
  python3 -m puzzlebreak day --date 2026-11-02 --state DIR      build today's set into DIR/today.json
  python3 -m puzzlebreak check --state DIR --n 1 --answer "..."  check an answer for puzzle n
  python3 -m puzzlebreak verify --state DIR                      re-verify today's set
  python3 -m puzzlebreak record --state DIR --date D --n 1 --status solved --hints 1 --tries 2 [--bonus]
                                                                 save a result and its points to history
  python3 -m puzzlebreak stats --state DIR --date 2026-11-02     streak and score summary
  python3 -m puzzlebreak rebuild --state DIR --start 2026-11-02 --date 2026-12-01
                                                                 fresh computer: rebuild history fingerprints
                                                                 for past delivery days so nothing repeats
  python3 -m puzzlebreak bonus --state DIR --date D --type anagram --difficulty medium
                                                                 one extra verified puzzle (n 101, 102, ...)
DIR holds profile.json (salt, types, difficulty, count, days) and history.json."""
import argparse
import json
import sys
from pathlib import Path

from . import day as daymod
from . import stats


def load(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def main(argv=None):
    ap = argparse.ArgumentParser(prog='puzzlebreak')
    ap.add_argument('cmd', choices=['day', 'check', 'verify', 'record', 'stats', 'rebuild', 'bonus'])
    ap.add_argument('--state', required=True)
    ap.add_argument('--date')
    ap.add_argument('--n', type=int)
    ap.add_argument('--start')
    ap.add_argument('--type')
    ap.add_argument('--difficulty')
    ap.add_argument('--answer')
    ap.add_argument('--found', default='', help='Letter Pool words already found, comma separated')
    ap.add_argument('--status', choices=['solved', 'revealed', 'skipped', 'missed'])
    ap.add_argument('--hints', type=int, default=0)
    ap.add_argument('--tries', type=int, default=0)
    ap.add_argument('--bonus', action='store_true', help='ladder solved at par')
    a = ap.parse_args(argv)
    state = Path(a.state)
    profile = load(state / 'profile.json', None)
    history = load(state / 'history.json', [])
    if a.cmd == 'day':
        d = daymod.build_day(a.date, profile, history)
        problems = daymod.verify_day(d)
        if problems:
            print(json.dumps({'ok': False, 'problems': problems}))
            return 1
        (state / 'today.json').write_text(json.dumps(d, indent=1))
        known = {(h['date'], h['n']) for h in history}
        history += [r for r in daymod.history_records(d) if (r['date'], r['n']) not in known]
        (state / 'history.json').write_text(json.dumps(history, indent=1))
        public = [{'n': p['n'], 'title': p['title'], 'difficulty': p['difficulty'], 'prompt': p['prompt']}
                  for p in d['puzzles']]
        print(json.dumps({'ok': True, 'date': d['date'], 'puzzles': public}, indent=1))
    elif a.cmd == 'check':
        d = load(state / 'today.json', {'puzzles': []})
        pool = d['puzzles'] + load(state / 'bonus.json', [])
        p = next(x for x in pool if x['n'] == a.n)
        kw = {'found_so_far': [w for w in a.found.split(',') if w]} if p['type'] == 'pool' else {}
        print(json.dumps(daymod.check(p, a.answer, **kw)))
    elif a.cmd == 'verify':
        d = load(state / 'today.json', None)
        problems = daymod.verify_day(d)
        print(json.dumps({'ok': not problems, 'problems': problems}))
        return 1 if problems else 0
    elif a.cmd == 'record':
        rec = next(h for h in history if h['date'] == a.date and h['n'] == a.n)
        base = daymod.POINTS[rec['difficulty']]
        rec.update({'status': a.status, 'hints': a.hints, 'tries': a.tries, 'bonus': a.bonus})
        rec['points'] = stats.score({'status': a.status, 'base': base, 'hints': a.hints, 'bonus': a.bonus})
        (state / 'history.json').write_text(json.dumps(history, indent=1))
        print(json.dumps(rec))
    elif a.cmd == 'rebuild':
        import datetime as dt
        days = {'weekdays': {0, 1, 2, 3, 4}, 'weekends': {5, 6}}.get(profile.get('days'), set(range(7)))
        d, end, rebuilt = dt.date.fromisoformat(a.start), dt.date.fromisoformat(a.date), []
        known = {h['date'] for h in history}
        while d < end:
            if d.weekday() in days and d.isoformat() not in known:
                recs = daymod.history_records(daymod.build_day(d, profile, history + rebuilt))
                for r in recs:
                    r['status'] = 'restored'
                rebuilt += recs
            d += dt.timedelta(days=1)
        history = sorted(history + rebuilt, key=lambda h: (h['date'], h['n']))
        (state / 'history.json').write_text(json.dumps(history, indent=1))
        print(json.dumps({'ok': True, 'restored_days': len({r['date'] for r in rebuilt})}))
    elif a.cmd == 'bonus':
        from .common import rng_for
        import datetime as dt
        bonus = [b for b in load(state / 'bonus.json', []) if b['date'] == a.date]
        avoid = daymod.recent_fingerprints(history, dt.date.fromisoformat(a.date) + dt.timedelta(days=1))
        diff = a.difficulty or daymod.difficulty_for(profile, dt.date.fromisoformat(a.date))
        kind = a.type or profile['types'][len(bonus) % len(profile['types'])]
        for k in range(200):
            p = daymod.MODULES[kind].generate(rng_for(profile['salt'], a.date, 'bonus', len(bonus), k), diff)
            if p['fingerprint'] not in avoid and not daymod.MODULES[kind].verify(p):
                break
        p.update({'n': 101 + len(bonus), 'date': a.date, 'points': daymod.POINTS[diff]})
        bonus.append(p)
        (state / 'bonus.json').write_text(json.dumps(bonus, indent=1))
        rec = daymod.history_records({'date': a.date, 'puzzles': [p]})[0]
        rec['bonus_puzzle'] = True
        history.append(rec)
        (state / 'history.json').write_text(json.dumps(history, indent=1))
        print(json.dumps({'ok': True, 'n': p['n'], 'title': p['title'], 'difficulty': diff, 'prompt': p['prompt']}))
    elif a.cmd == 'stats':
        days = {'weekdays': {0, 1, 2, 3, 4}, 'weekends': {5, 6}}.get(profile.get('days'))
        print(json.dumps(stats.summary(history, a.date, profile.get('paused_days', []), days)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
