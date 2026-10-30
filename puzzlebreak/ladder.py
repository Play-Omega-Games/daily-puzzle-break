"""Word ladder: change one letter at a time, every step a real word."""
from collections import deque
from functools import lru_cache

from .common import words, tokens

BANDS = {
    'gentle': {'lengths': [3, 4], 'moves': (3, 3)},
    'medium': {'lengths': [4], 'moves': (4, 5)},
    'tricky': {'lengths': [5], 'moves': (5, 7)},
}


@lru_cache(maxsize=None)
def graph(kind, length):
    ws = [w for w in words(kind) if len(w) == length]
    buckets = {}
    for w in ws:
        for i in range(length):
            buckets.setdefault(w[:i] + '_' + w[i + 1:], []).append(w)
    adj = {w: set() for w in ws}
    for group in buckets.values():
        for a in group:
            for b in group:
                if a != b:
                    adj[a].add(b)
    return adj


def bfs(adj, start):
    dist, parent = {start: 0}, {start: None}
    q = deque([start])
    while q:
        x = q.popleft()
        for y in sorted(adj[x]):
            if y not in dist:
                dist[y] = dist[x] + 1
                parent[y] = x
                q.append(y)
    return dist, parent


def shortest(kind, a, b):
    if len(a) != len(b):
        return None
    adj = graph(kind, len(a))
    if a not in adj or b not in adj:
        return None
    dist, parent = bfs(adj, a)
    if b not in dist:
        return None
    path, x = [], b
    while x is not None:
        path.append(x)
        x = parent[x]
    return path[::-1]


def one_letter_apart(a, b):
    return len(a) == len(b) and sum(x != y for x, y in zip(a, b)) == 1


def generate(rng, difficulty):
    band = BANDS[difficulty]
    for _ in range(500):
        length = rng.choice(band['lengths'])
        adj = graph('common', length)
        pool = sorted(w for w in adj if adj[w] and not w.endswith('s'))
        start = rng.choice(pool)
        dist, _ = bfs(adj, start)
        moves = rng.randint(*band['moves'])
        ends = sorted(w for w, d in dist.items() if d == moves and not w.endswith('s'))
        if not ends:
            continue
        end = rng.choice(ends)
        path = shortest('common', start, end)
        par_path = shortest('accept', start, end)
        if len(par_path) != len(path):
            continue  # a shortcut through a rarer word would make par unfair
        mid = path[len(path) // 2]
        return {
            'type': 'ladder',
            'title': 'Word ladder',
            'difficulty': difficulty,
            'prompt': (f'Turn {start.upper()} into {end.upper()}, changing one letter at a time. '
                       f'Every step must be a real word. Par is {moves} moves.'),
            'data': {'start': start, 'end': end, 'par': moves},
            'solution': path,
            'answer_text': ' > '.join(w.upper() for w in path),
            'accepts': 'Any ladder from start to end where each step is a real word one letter away.',
            'hints': [
                f'A good first step is {path[1].upper()}.',
                f'Halfway there, the ladder passes a word starting with {mid[0].upper()}.',
                f'The middle word is {mid.upper()}.',
            ],
            'explain': 'Each step changes one letter: ' + ' > '.join(w.upper() for w in path) + '.',
            'fingerprint': 'ladder:' + '-'.join(sorted([start, end])),
        }
    raise RuntimeError('no ladder found')


def check(puzzle, answer):
    d = puzzle['data']
    steps = [t for t in tokens(answer) if len(t) == len(d['start'])]
    if not steps:
        return {'correct': False, 'feedback': 'Send your ladder as words, like COLD CORD WORD.'}
    if steps[0] != d['start']:
        steps = [d['start']] + steps
    if steps[-1] != d['end']:
        steps = steps + [d['end']]
    acc = words('accept')
    for a, b in zip(steps, steps[1:]):
        if b not in acc:
            return {'correct': False, 'feedback': f'Not quite: {b.upper()} is not in my word list.'}
        if not one_letter_apart(a, b):
            return {'correct': False, 'feedback': f'Not quite: {a.upper()} to {b.upper()} changes more than one letter.'}
    moves = len(steps) - 1
    at_par = moves <= d['par']
    note = 'Right on par!' if at_par else f'Solved in {moves} moves (par is {d["par"]}).'
    return {'correct': True, 'at_par': at_par, 'moves': moves, 'feedback': f'Yes! {note}'}


def verify(puzzle):
    d, path = puzzle['data'], puzzle['solution']
    problems = []
    if path[0] != d['start'] or path[-1] != d['end']:
        problems.append('solution does not join start and end')
    if any(w not in words('common') for w in path):
        problems.append('solution uses a word outside the common list')
    if any(not one_letter_apart(a, b) for a, b in zip(path, path[1:])):
        problems.append('solution step changes more than one letter')
    best = shortest('accept', d['start'], d['end'])
    if best is None or len(best) - 1 != d['par'] or len(path) - 1 != d['par']:
        problems.append('par is not the true shortest ladder')
    if not check(puzzle, ' '.join(path))['correct']:
        problems.append('checker rejects its own solution')
    return problems
