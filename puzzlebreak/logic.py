"""Logic grid: match each person to one value of each attribute using the clues."""
import itertools
import json
import re
from functools import lru_cache

from .common import DATA

BANDS = {'gentle': (3, 2), 'medium': (4, 3), 'tricky': (5, 3)}
NAME = -1


@lru_cache(maxsize=None)
def theme():
    return json.loads((DATA / 'logic_grid.json').read_text())


@lru_cache(maxsize=None)
def perms(n):
    return list(itertools.permutations(range(n)))


def _holds(clue, assign, n):
    """assign: dict attr_index -> perm (perm[person] = value). NAME attr is identity."""
    kind, (ka, va), (kb, vb) = clue
    def person(k, v):
        return v if k == NAME else assign[k].index(v)
    same = person(ka, va) == person(kb, vb)
    return same if kind == 'eq' else not same


def count_solutions(n, k, clues, limit=2):
    by_level = [[] for _ in range(k)]
    for c in clues:
        lvl = max(c[1][0], c[2][0])
        by_level[lvl].append(c)
    count = 0
    found = None
    assign = {}

    def rec(level):
        nonlocal count, found
        if level == k:
            count += 1
            found = dict(assign)
            return count >= limit
        for p in perms(n):
            assign[level] = p
            if all(_holds(c, assign, n) for c in by_level[level]):
                if rec(level + 1):
                    return True
        del assign[level]
        return False

    rec(0)
    return count, found


def _clue_text(clue, names, attrs):
    kind, (ka, va), (kb, vb) = clue
    b = attrs[kb]
    pred = (b['pos'] if kind == 'eq' else b['neg']).format(v=b['values'][vb])
    if ka == NAME:
        return f'{names[va]} {pred}.'
    a = attrs[ka]
    return f'The person {a["rel"].format(v=a["values"][va])} {pred}.'


def generate(rng, difficulty):
    n, k = BANDS[difficulty]
    t = theme()
    for _ in range(50):
        names = sorted(rng.sample(t['names'], n))
        keys = rng.sample(sorted(t['attributes']), k)
        attrs = []
        for key in keys:
            a = dict(t['attributes'][key])
            a['key'] = key
            a['values'] = rng.sample(a['values'], n)
            attrs.append(a)
        sol = [tuple(rng.sample(range(n), n)) for _ in range(k)]
        cands = []
        levels = [NAME] + list(range(k))
        for ia, ka in enumerate(levels):
            for kb in levels[ia + 1:]:
                for va in range(n):
                    for vb in range(n):
                        pa = va if ka == NAME else sol[ka].index(va)
                        pb = sol[kb].index(vb)
                        cands.append(('eq' if pa == pb else 'ne', (ka, va), (kb, vb)))
        pos = [c for c in cands if c[0] == 'eq']
        neg = [c for c in cands if c[0] == 'ne']
        rng.shuffle(pos)
        rng.shuffle(neg)
        share = {'gentle': 0.5, 'medium': 0.35, 'tricky': 0.25}[difficulty]
        order = []
        while pos or neg:
            if pos and (not neg or rng.random() < share):
                order.append(pos.pop())
            else:
                order.append(neg.pop())
        clues = []
        for c in order:
            clues.append(c)
            cnt, _ = count_solutions(n, k, clues)
            if cnt == 1:
                break
        else:
            continue
        for c in list(clues):
            trial = [x for x in clues if x != c]
            if count_solutions(n, k, trial)[0] == 1:
                clues = trial
        rng.shuffle(clues)
        grid = {names[p]: {attrs[i]['key']: attrs[i]['values'][sol[i][p]] for i in range(k)} for p in range(n)}
        texts = [_clue_text(c, names, attrs) for c in clues]
        cats = '; '.join(f'{a["label"]}: ' + ', '.join(sorted(a['values'])) for a in attrs)
        return {
            'type': 'logic',
            'title': 'Logic grid',
            'difficulty': difficulty,
            'prompt': (f'{", ".join(names[:-1])} and {names[-1]} each have a different '
                       f'{_join([a["label"].lower() for a in attrs])}. {cats}. '
                       'Use the clues to match everyone.\n' + '\n'.join(f'{i + 1}. {c}' for i, c in enumerate(texts))),
            'data': {'names': names, 'attributes': [{'key': a['key'], 'label': a['label'], 'values': a['values'],
                                                     'pos': a['pos'], 'neg': a['neg'], 'rel': a['rel']} for a in attrs],
                     'clues': [[c[0], list(c[1]), list(c[2])] for c in clues], 'clue_text': texts},
            'solution': grid,
            'answer_text': '; '.join(f'{p}: ' + ', '.join(grid[p].values()) for p in names),
            'accepts': 'Only the one solution (the clues allow exactly one).',
            'hints': _hints(clues, names, attrs, grid, rng),
            'explain': explain(names, attrs, clues),
            'fingerprint': 'logic:' + json.dumps(grid, sort_keys=True),
        }
    raise RuntimeError('no logic grid found')


def _join(items):
    return items[0] if len(items) == 1 else ', '.join(items[:-1]) + ' and ' + items[-1]


def _hints(clues, names, attrs, grid, rng):
    p = rng.choice(names)
    first = attrs[0]
    return [
        f'Clue {1 + next((i for i, c in enumerate(clues) if c[0] == "eq"), 0)} pins one pair down, so start there.',
        f'{p} {first["pos"].format(v=grid[p][first["key"]])}.',
        'Two more: ' + '; '.join(f'{q} {attrs[-1]["pos"].format(v=grid[q][attrs[-1]["key"]])}'
                                 for q in [x for x in names if x != p][:2]) + '.',
    ]


def explain(names, attrs, clues):
    """Plain-words deduction replay using simple elimination. Falls back to a closing line if needed."""
    n, k = len(names), len(attrs)
    poss = {(p, a): set(range(n)) for p in range(n) for a in range(k)}
    steps, fixed = [], set()

    def has(p, ka, va):
        return (va == p) if ka == NAME else (va in poss[(p, ka)])

    def only(p, ka, va):
        return (va == p) if ka == NAME else (poss[(p, ka)] == {va})

    changed = True
    while changed:
        changed = False
        for idx, (kind, (ka, va), (kb, vb)) in enumerate(clues):
            for p in range(n):
                for (x, xv, y, yv) in ((ka, va, kb, vb), (kb, vb, ka, va)):
                    if y == NAME:
                        continue
                    if kind == 'eq' and not has(p, x, xv) and yv in poss[(p, y)]:
                        poss[(p, y)].discard(yv); changed = True
                    if kind == 'eq' and only(p, x, xv) and poss[(p, y)] != {yv}:
                        poss[(p, y)] = {yv}; changed = True
                    if kind == 'ne' and only(p, x, xv) and yv in poss[(p, y)]:
                        poss[(p, y)].discard(yv); changed = True
        for a in range(k):
            for p in range(n):
                if len(poss[(p, a)]) == 1:
                    v = next(iter(poss[(p, a)]))
                    for q in range(n):
                        if q != p and v in poss[(q, a)]:
                            poss[(q, a)].discard(v); changed = True
            for v in range(n):
                holders = [p for p in range(n) if v in poss[(p, a)]]
                if len(holders) == 1 and len(poss[(holders[0], a)]) > 1:
                    poss[(holders[0], a)] = {v}; changed = True
        for p in range(n):
            for a in range(k):
                if len(poss[(p, a)]) == 1 and (p, a) not in fixed:
                    fixed.add((p, a))
                    v = next(iter(poss[(p, a)]))
                    steps.append(f'{names[p]} {attrs[a]["pos"].format(v=attrs[a]["values"][v])}.')
    if len(fixed) < n * k:
        steps.append('The rest follows by trying each remaining option: only one fits every clue.')
    return 'Step by step: ' + ' '.join(steps)


def _parse(puzzle, answer):
    d = puzzle['data']
    out = {}
    names = d['names']
    low = answer.lower()
    spans = []
    for nm in names:
        m = re.search(r'\b' + nm.lower() + r'\b', low)
        if m:
            spans.append((m.start(), nm))
    spans.sort()
    for i, (start, nm) in enumerate(spans):
        end = spans[i + 1][0] if i + 1 < len(spans) else len(low)
        seg = low[start:end]
        out[nm] = {}
        for a in d['attributes']:
            for v in a['values']:
                if re.search(r'\b' + re.escape(v) + r'\b', seg):
                    out[nm][a['key']] = v
    return out


def check(puzzle, answer):
    guess = answer if isinstance(answer, dict) else _parse(puzzle, answer)
    sol = puzzle['solution']
    total = sum(len(v) for v in sol.values())
    right = sum(1 for p in sol for key, v in sol[p].items() if guess.get(p, {}).get(key) == v)
    if right == total:
        return {'correct': True, 'feedback': 'Yes! Every match is right.'}
    return {'correct': False, 'right': right, 'total': total,
            'feedback': f'Not quite: {right} of {total} matches are right. Want a hint?'}


def verify(puzzle):
    d = puzzle['data']
    n, k = len(d['names']), len(d['attributes'])
    clues = [(c[0], tuple(c[1]), tuple(c[2])) for c in d['clues']]
    cnt, found = count_solutions(n, k, clues, limit=2)
    problems = []
    if cnt != 1:
        problems.append(f'clues allow {cnt} solutions')
    else:
        grid = {d['names'][p]: {d['attributes'][i]['key']: d['attributes'][i]['values'][found[i][p]] for i in range(k)}
                for p in range(n)}
        if grid != puzzle['solution']:
            problems.append('stored solution differs from the solver')
    if not check(puzzle, puzzle['answer_text'])['correct']:
        problems.append('checker rejects its own answer text')
    return problems
