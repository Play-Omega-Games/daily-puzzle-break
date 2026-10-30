"""Number puzzles: reach the target, number sequence, number pyramid, number grid."""
import ast
import itertools
import json
import operator
import re
from fractions import Fraction

SUBTYPES = ['target', 'sequence', 'pyramid', 'grid']

# ---------- reach the target ----------
OPS = {'+': operator.add, '-': operator.sub, '*': operator.mul, '/': operator.truediv}


def _combine(items):
    """items: list of (value, text). Yields every (value, text) using all items once."""
    if len(items) == 1:
        yield items[0]
        return
    seen = set()
    for i, j in itertools.combinations(range(len(items)), 2):
        rest = [items[x] for x in range(len(items)) if x not in (i, j)]
        (a, ta), (b, tb) = items[i], items[j]
        options = [(a + b, f'({min(ta, tb)} + {max(ta, tb)})'), (a * b, f'({min(ta, tb)} * {max(ta, tb)})'),
                   (a - b, f'({ta} - {tb})'), (b - a, f'({tb} - {ta})')]
        if b != 0:
            options.append((a / b, f'({ta} / {tb})'))
        if a != 0:
            options.append((b / a, f'({tb} / {ta})'))
        for v, t in options:
            key = (v, t)
            if key in seen:
                continue
            seen.add(key)
            yield from _combine(rest + [(v, t)])


def target_solutions(nums, target):
    sols = set()
    for v, t in _combine([(Fraction(n), str(n)) for n in nums]):
        if v == target:
            sols.add(t[1:-1] if t.startswith('(') else t)
    return sorted(sols)


TARGET_BANDS = {
    'gentle': {'nums': (1, 9), 'targets': list(range(10, 21)), 'sols': (6, 10 ** 6)},
    'medium': {'nums': (1, 13), 'targets': [24] + list(range(20, 41)), 'sols': (2, 6)},
    'tricky': {'nums': (1, 13), 'targets': list(range(24, 61)), 'sols': (1, 2)},
}


def _gen_target(rng, difficulty):
    b = TARGET_BANDS[difficulty]
    for _ in range(3000):
        nums = sorted(rng.randint(*b['nums']) for _ in range(4))
        target = rng.choice(b['targets'])
        sols = target_solutions(nums, target)
        if b['sols'][0] <= len(sols) <= b['sols'][1]:
            nice = min(sols, key=len)
            return {
                'subtype': 'target', 'title': 'Reach the target',
                'prompt': (f'Use {", ".join(map(str, nums[:-1]))} and {nums[-1]} once each, with + - x and /, '
                           f'to make {target}. Brackets are fine.'),
                'data': {'numbers': nums, 'target': target, 'solution_count': len(sols)},
                'solution': nice, 'accepted_rule': 'Any expression using each number once that equals the target.',
                'answer_text': nice.replace('*', 'x'),
                'hints': ['Only one arrangement works, so be precise.' if len(sols) == 1 else 'There is more than one way to do it.',
                          f'One way starts by combining {_first_pair(nice)}.',
                          'One answer: ' + _mask(nice) + '.'],
                'explain': f'{nice.replace("*", "x")} = {target}.',
                'fingerprint': f'target:{"-".join(map(str, nums))}:{target}',
            }
    raise RuntimeError('no target puzzle')


def _first_pair(expr):
    m = re.search(r'\((\d+) ([-+*/]) (\d+)\)', '(' + expr + ')') or re.search(r'(\d+) ([-+*/]) (\d+)', expr)
    return f'{m.group(1)} and {m.group(3)}' if m else 'two of the numbers'


def _mask(expr):
    return re.sub(r'[-+*/]', '?', expr)


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return Fraction(node.value), [node.value]
    if isinstance(node, ast.BinOp) and type(node.op) in (ast.Add, ast.Sub, ast.Mult, ast.Div):
        a, la = _eval(node.left)
        b, lb = _eval(node.right)
        f = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}[type(node.op)]
        if isinstance(node.op, ast.Div) and b == 0:
            raise ValueError('divide by zero')
        return f(a, b), la + lb
    raise ValueError('not allowed')


def eval_expression(text):
    t = text.lower().replace('\u00d7', '*').replace('x', '*').replace('\u00f7', '/').replace('\u2212', '-')
    t = t.split('=')[0]
    if not re.fullmatch(r'[\d\s+\-*/()]+', t):
        raise ValueError('use only numbers, + - x / and brackets')
    return _eval(ast.parse(t.strip(), mode='eval'))


# ---------- sequence ----------
def _rules():
    for a in range(1, 41):
        for d in range(-9, 16):
            if d:
                yield ('add', a, d, 0)
    for a in range(1, 13):
        for r in (2, 3, 4):
            yield ('times', a, r, 0)
    for a in range(1, 31):
        for d in range(1, 10):
            for c in range(1, 6):
                yield ('growing', a, d, c)
    for a in range(1, 21):
        for p in range(2, 13):
            for q in range(1, 10):
                if p != q:
                    yield ('zigzag', a, p, q)
    for a in range(1, 10):
        for b in range(1, 10):
            yield ('sum2', a, b, 0)
    for k in range(1, 8):
        for c in range(-3, 4):
            yield ('square', k, c, 0)


def _terms(rule, n=6):
    kind, a, b, c = rule
    if kind == 'add':
        return [a + i * b for i in range(n)]
    if kind == 'times':
        return [a * b ** i for i in range(n)]
    if kind == 'growing':
        out, step = [a], b
        for _ in range(n - 1):
            out.append(out[-1] + step)
            step += c
        return out
    if kind == 'zigzag':
        out = [a]
        for i in range(n - 1):
            out.append(out[-1] + (b if i % 2 == 0 else -c))
        return out
    if kind == 'sum2':
        out = [a, b]
        while len(out) < n:
            out.append(out[-1] + out[-2])
        return out
    if kind == 'square':
        return [(a + i) ** 2 + b for i in range(n)]


RULE_WORDS = {
    'add': 'add the same amount each time', 'times': 'multiply by the same number each time',
    'growing': 'the step grows by the same amount each time', 'zigzag': 'add one amount, then take away another, in turn',
    'sum2': 'each number is the sum of the two before it', 'square': 'square numbers, shifted by the same amount',
}
SEQ_BANDS = {'gentle': (['add', 'times'], [5]), 'medium': (['add', 'times', 'growing', 'sum2'], [2, 3, 5]),
             'tricky': (['growing', 'zigzag', 'sum2', 'square'], [1, 2, 3, 4, 5])}


def sequence_fits(shown, blank):
    """Every distinct value for the blank predicted by any rule in the family that fits the shown terms."""
    values = set()
    for rule in _rules():
        t = _terms(rule)
        if all(t[i] == v for i, v in enumerate(shown) if i != blank):
            values.add(t[blank])
    return values


def _gen_sequence(rng, difficulty):
    kinds, blanks = SEQ_BANDS[difficulty]
    rules = [r for r in _rules() if r[0] in kinds]
    for _ in range(3000):
        rule = rng.choice(rules)
        t = _terms(rule)
        if any(v < 0 or v > 999 for v in t):
            continue
        blank = rng.choice(blanks)
        if sequence_fits(t, blank) != {t[blank]}:
            continue
        shown = ['?' if i == blank else str(v) for i, v in enumerate(t)]
        return {
            'subtype': 'sequence', 'title': 'Number sequence',
            'prompt': 'Each number follows one simple rule. What is the missing number? ' + ', '.join(shown),
            'data': {'terms': t, 'blank': blank},
            'solution': t[blank], 'answer_text': str(t[blank]),
            'hints': [f'The rule: {RULE_WORDS[rule[0]]}.',
                      _gap_hint(t, blank),
                      f'The missing number is between {t[blank] - 5} and {t[blank] + 5}.'],
            'explain': f'The rule: {RULE_WORDS[rule[0]]}. So the missing number is {t[blank]}.',
            'fingerprint': 'sequence:' + '-'.join(map(str, t)) + f':{blank}',
        }
    raise RuntimeError('no sequence')


def _gap_hint(t, blank):
    gaps = []
    for i in range(len(t) - 1):
        gaps.append('?' if blank in (i, i + 1) else str(t[i + 1] - t[i]))
    return 'The gaps between neighbors are ' + ', '.join(gaps) + '.'


# ---------- pyramid ----------
def _pyramid(base):
    rows = [list(base)]
    while len(rows[-1]) > 1:
        r = rows[-1]
        rows.append([r[i] + r[i + 1] for i in range(len(r) - 1)])
    return rows


def _coeffs(n):
    """Brick value as a linear combination of base values."""
    rows = [[[1 if j == i else 0 for j in range(n)] for i in range(n)]]
    while len(rows[-1]) > 1:
        r = rows[-1]
        rows.append([[a + b for a, b in zip(r[i], r[i + 1])] for i in range(len(r) - 1)])
    return rows


def _rank(vectors):
    m = [[Fraction(x) for x in v] for v in vectors]
    rank, cols = 0, len(m[0]) if m else 0
    for c in range(cols):
        piv = next((r for r in range(rank, len(m)) if m[r][c] != 0), None)
        if piv is None:
            continue
        m[rank], m[piv] = m[piv], m[rank]
        for r in range(len(m)):
            if r != rank and m[r][c] != 0:
                f = m[r][c] / m[rank][c]
                m[r] = [x - f * y for x, y in zip(m[r], m[rank])]
        rank += 1
    return rank


PYR_BANDS = {'gentle': (3, 9), 'medium': (4, 9), 'tricky': (5, 12)}


def _gen_pyramid(rng, difficulty):
    n, hi = PYR_BANDS[difficulty]
    for _ in range(2000):
        base = [rng.randint(1, hi) for _ in range(n)]
        rows = _pyramid(base)
        co = _coeffs(n)
        cells = [(r, i) for r in range(n) for i in range(len(rows[r]))]
        given = rng.sample(cells, n)
        if difficulty != 'gentle' and sum(1 for r, _ in given if r == 0) > n - 2:
            continue
        if (n - 1, 0) in given:
            continue
        if _rank([co[r][i] for r, i in given]) != n:
            continue
        show = [[(str(rows[r][i]) if (r, i) in given else '?') for i in range(len(rows[r]))] for r in range(n)]
        picture = '\n'.join(' ' * (n - 1 - r) + ' '.join(f'[{x:>3}]' for x in show[r]) for r in reversed(range(n)))
        return {
            'subtype': 'pyramid', 'title': 'Number pyramid',
            'prompt': ('Each brick is the sum of the two bricks under it. What number goes in the top brick?\n' + picture),
            'data': {'size': n, 'given': [[r, i, rows[r][i]] for r, i in given]},
            'solution': rows[-1][0], 'full': rows, 'answer_text': str(rows[-1][0]),
            'hints': ['Start where a brick and one neighbor are known: the brick between them is easy.',
                      _pyr_hint(rows, given),
                      'Bottom row: ' + ', '.join(map(str, rows[0])) + '.'],
            'explain': 'Rows from the bottom: ' + ' / '.join(', '.join(map(str, r)) for r in rows) + '.',
            'fingerprint': 'pyramid:' + json.dumps([[r, i, rows[r][i]] for r, i in sorted(given)]),
        }
    raise RuntimeError('no pyramid')


def _pyr_hint(rows, given):
    for r in range(len(rows)):
        for i in range(len(rows[r])):
            if (r, i) not in given:
                where = 'bottom row' if r == 0 else f'row {r + 1} from the bottom'
                return f'In the {where}, brick {i + 1} from the left is {rows[r][i]}.'
    return 'Every brick but the top is given.'


# ---------- number grid ----------
def grid_solutions(puzzle, n, limit=2):
    cells = [list(r) for r in puzzle]
    sols = []

    def options(r, c):
        used = set(cells[r]) | {cells[x][c] for x in range(n)}
        return [v for v in range(1, n + 1) if v not in used]

    def rec():
        best = None
        for r in range(n):
            for c in range(n):
                if cells[r][c] == 0:
                    o = options(r, c)
                    if best is None or len(o) < len(best[2]):
                        best = (r, c, o)
        if best is None:
            sols.append([row[:] for row in cells])
            return len(sols) >= limit
        r, c, o = best
        for v in o:
            cells[r][c] = v
            if rec():
                return True
            cells[r][c] = 0
        return False

    rec()
    return sols


GRID_BANDS = {'gentle': (4, 8), 'medium': (4, 6), 'tricky': (5, 0)}


def _gen_grid(rng, difficulty):
    n, keep_min = GRID_BANDS[difficulty]
    base = [[(r + c) % n + 1 for c in range(n)] for r in range(n)]
    rows, cols, syms = list(range(n)), list(range(n)), list(range(1, n + 1))
    rng.shuffle(rows); rng.shuffle(cols); rng.shuffle(syms)
    sol = [[syms[base[r][c] - 1] for c in cols] for r in rows]
    puz = [row[:] for row in sol]
    cells = [(r, c) for r in range(n) for c in range(n)]
    rng.shuffle(cells)
    for r, c in cells:
        if sum(1 for row in puz for v in row if v) <= keep_min:
            break
        old = puz[r][c]
        puz[r][c] = 0
        if len(grid_solutions(puz, n)) != 1:
            puz[r][c] = old
    picture = '\n'.join(' '.join(str(v) if v else '.' for v in row) for row in puz)
    return {
        'subtype': 'grid', 'title': 'Number grid',
        'prompt': f'Fill the grid so every row and every column has each number from 1 to {n} exactly once.\n' + picture,
        'data': {'size': n, 'puzzle': puz},
        'solution': sol, 'answer_text': '\n'.join(' '.join(map(str, r)) for r in sol),
        'hints': [_grid_hint(puz, sol),
                  'Row 1: ' + ' '.join(map(str, sol[0])) + '.',
                  'Rows 1 and 2: ' + ' / '.join(' '.join(map(str, r)) for r in sol[:2]) + '.'],
        'explain': 'Look for a cell where only one number fits its row and column, fill it, and repeat. Full grid:\n'
                   + '\n'.join(' '.join(map(str, r)) for r in sol),
        'fingerprint': 'grid:' + json.dumps(puz),
    }


def _grid_hint(puz, sol):
    for r, row in enumerate(puz):
        for c, v in enumerate(row):
            if not v:
                return f'Row {r + 1}, column {c + 1} is {sol[r][c]}.'
    return 'Every row is already started for you.'


# ---------- dispatch ----------
GENERATORS = {'target': _gen_target, 'sequence': _gen_sequence, 'pyramid': _gen_pyramid, 'grid': _gen_grid}


def generate(rng, difficulty, subtype=None):
    sub = subtype or rng.choice(SUBTYPES)
    p = GENERATORS[sub](rng, difficulty)
    p.update({'type': 'numbers', 'difficulty': difficulty})
    p['accepts'] = {'target': 'Any expression using each number once that equals the target.'}.get(
        sub, 'Only the one answer (checked to be unique).')
    return p


def check(puzzle, answer):
    sub = puzzle['subtype']
    if sub == 'target':
        try:
            value, used = eval_expression(answer)
        except (ValueError, SyntaxError):
            return {'correct': False, 'feedback': 'Send it as a sum, like (8 - 2) x 4.'}
        if sorted(used) != sorted(puzzle['data']['numbers']):
            return {'correct': False, 'feedback': 'Use each of the four numbers exactly once.'}
        if value != puzzle['data']['target']:
            return {'correct': False, 'feedback': f'That makes {value}, not {puzzle["data"]["target"]}. Close!'}
        return {'correct': True, 'feedback': 'Yes! That hits the target.'}
    if sub == 'grid':
        n = puzzle['data']['size']
        digits = [int(x) for x in re.findall(r'\d', answer)]
        if len(digits) != n * n:
            return {'correct': False, 'feedback': f'Send all {n * n} numbers, row by row.'}
        rows = [digits[i * n:(i + 1) * n] for i in range(n)]
        wrong = sum(1 for r in range(n) for c in range(n) if rows[r][c] != puzzle['solution'][r][c])
        if wrong == 0:
            return {'correct': True, 'feedback': 'Yes! Every row and column checks out.'}
        return {'correct': False, 'feedback': f'Not quite: {wrong} cell{"s" if wrong > 1 else ""} to fix.'}
    nums = re.findall(r'-?\d+', answer)
    if not nums:
        return {'correct': False, 'feedback': 'Send just the number.'}
    if int(nums[-1]) == puzzle['solution']:
        return {'correct': True, 'feedback': 'Yes! Spot on.'}
    return {'correct': False, 'feedback': 'Not quite. Want a hint?'}


def verify(puzzle):
    sub, d, problems = puzzle['subtype'], puzzle['data'], []
    if sub == 'target':
        sols = target_solutions(d['numbers'], d['target'])
        if not sols or len(sols) != d['solution_count']:
            problems.append('solution count changed')
        if not check(puzzle, puzzle['solution'])['correct']:
            problems.append('checker rejects its own solution')
    elif sub == 'sequence':
        if sequence_fits(d['terms'], d['blank']) != {puzzle['solution']}:
            problems.append('more than one rule fits')
    elif sub == 'pyramid':
        co = _coeffs(d['size'])
        if _rank([co[r][i] for r, i, _ in d['given']]) != d['size']:
            problems.append('givens do not fix the pyramid')
        rows = _pyramid(puzzle['full'][0])
        if any(rows[r][i] != v for r, i, v in d['given']) or rows[-1][0] != puzzle['solution']:
            problems.append('stored pyramid is inconsistent')
    elif sub == 'grid':
        sols = grid_solutions(d['puzzle'], d['size'])
        if len(sols) != 1 or sols[0] != puzzle['solution']:
            problems.append('grid does not have exactly one solution')
    if not check(puzzle, puzzle['answer_text'])['correct']:
        problems.append('checker rejects its own answer text')
    return problems
