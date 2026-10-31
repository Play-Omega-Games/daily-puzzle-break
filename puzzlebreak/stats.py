"""Streak and score from the owner's own play history. No estimates."""
import datetime as dt

HINT_COST = 3
BONUS = 5


def score(record):
    """record: status solved|revealed|skipped|open|missed, base points, hints used, bonus flag."""
    if record.get('status') != 'solved':
        return 0
    return max(0, record['base'] - HINT_COST * record.get('hints', 0)) + (BONUS if record.get('bonus') else 0)


def streaks(history, today, paused_days=(), delivery_days=None, carry=None):
    """A delivery day counts when at least one of its puzzles was solved (bonus puzzles excluded).
    Paused days and non-delivery days are skipped without breaking the streak.
    Today, if not yet solved, does not break it either."""
    if isinstance(today, str):
        today = dt.date.fromisoformat(today)
    paused = {dt.date.fromisoformat(d) if isinstance(d, str) else d for d in paused_days}
    by_day = {}
    for h in history:
        if h.get('bonus_puzzle'):
            continue
        d = dt.date.fromisoformat(h['date'])
        if h.get('status') == 'restored':
            paused.add(d)  # rebuilt on a fresh computer: play unknown, never breaks the streak
            continue
        by_day.setdefault(d, False)
        if h.get('status') == 'solved':
            by_day[d] = True
    carry = carry or {}
    if not by_day:
        return {'current': carry.get('streak', 0), 'best': carry.get('best_streak', 0)}
    first = min(by_day)
    run = carry.get('streak', 0)  # streak saved in memory before a fresh-computer restore
    best = max(run, carry.get('best_streak', 0))
    current = 0
    d = first
    while d <= today:
        is_delivery = d in by_day if delivery_days is None else d.weekday() in delivery_days
        if d in paused or not is_delivery:
            pass
        elif by_day.get(d):
            run += 1
        elif d == today:
            pass
        else:
            run = 0
        best = max(best, run)
        d += dt.timedelta(days=1)
    current = run
    return {'current': current, 'best': best}


def summary(history, today, paused_days=(), delivery_days=None, carry=None):
    s = streaks(history, today, paused_days, delivery_days, carry)
    total = sum(h.get('points', 0) for h in history) + (carry or {}).get('score', 0)
    by_type = {}
    for h in history:
        t = by_type.setdefault(h['type'], {'played': 0, 'solved': 0, 'hints': 0})
        t['played'] += 1
        t['solved'] += h.get('status') == 'solved'
        t['hints'] += h.get('hints', 0)
    return {'streak': s['current'], 'best_streak': s['best'], 'score': total, 'by_type': by_type}
