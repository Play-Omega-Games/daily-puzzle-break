"""Generate and verify 30 sample days. Writes samples/30-days.json and samples/30-days.md.
Run from the repo root: python3 scripts/make_samples.py"""
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from puzzlebreak import day  # noqa: E402

PROFILE = {'salt': 'sample', 'types': ['ladder', 'anagram', 'pool', 'logic', 'numbers', 'cipher'],
           'difficulty': 'ramp', 'count': 5}
START = dt.date(2026, 11, 2)


def main():
    history, days, failures = [], [], []
    for i in range(30):
        d = day.build_day(START + dt.timedelta(days=i), PROFILE, history)
        problems = day.verify_day(d)
        for p in d['puzzles']:
            ans = p['solution'] if p['type'] in ('logic', 'pool', 'anagram') else p['answer_text']
            if p['type'] == 'pool':
                ans = ' '.join(p['solution'][:p['data']['goal']])
            if p['type'] == 'numbers' and p['subtype'] == 'target':
                ans = p['solution']
            if not day.check(p, ans)['correct']:
                problems.append(f'#{p["n"]} checker rejects the answer')
        failures += [f'{d["date"]} {x}' for x in problems]
        history += day.history_records(d)
        days.append({'date': d['date'], 'difficulty': d['difficulty'], 'verified': not problems,
                     'puzzles': [{'n': p['n'], 'type': p['type'], 'title': p['title'], 'prompt': p['prompt'],
                                  'answer': p['answer_text'], 'accepts': p['accepts'], 'hints': p['hints']}
                                 for p in d['puzzles']]})
    out = Path(__file__).resolve().parent.parent / 'samples'
    out.mkdir(exist_ok=True)
    (out / '30-days.json').write_text(json.dumps(days, indent=1) + '\n')
    lines = ['# 30 sample days', '', 'Settings: all puzzle types, ramp up through the week, 5 puzzles a day.', '']
    for d in days:
        lines += [f'## {d["date"]} ({d["difficulty"]})', '']
        for p in d['puzzles']:
            lines += [f'**{p["n"]}. {p["title"]}**', '', p['prompt'].replace('\n', '  \n'), '',
                      f'Answer: {str(p["answer"]).replace(chr(10), " / ")}', '']
    (out / '30-days.md').write_text('\n'.join(lines))
    total = sum(len(d['puzzles']) for d in days)
    print(json.dumps({'days': len(days), 'puzzles': total, 'failures': failures,
                      'types': sorted({p['type'] for d in days for p in d['puzzles']})}))
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
