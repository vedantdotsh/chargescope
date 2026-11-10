"""Build, run the portable website suites sequentially, and capture screenshots.
Run python website/project/run_gate.py; generated results go in evidence/logs.
"""
import re, subprocess, sys, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
L = HERE / 'evidence' / 'logs'
STEPS = ['build', 'tests/test_data', 'tests/test_display', 'tests/test_layout', 'tests/test_motion', 'tests/test_graphite',
         'tests/review_regressions', 'tests/shots', 'tests/intro_shots']


def main():
    L.mkdir(parents=True, exist_ok=True)
    rows, total, bad = [], [0, 0], 0
    for step in STEPS:
        name = Path(step).name
        start = datetime.datetime.now().isoformat(timespec='seconds')
        with open(L / f'{name}.log', 'w', encoding='utf-8') as log:
            rc = subprocess.run([sys.executable, '-B', step + '.py'], cwd=HERE, stdout=log, stderr=subprocess.STDOUT).returncode
        tail = re.findall(r'^([a-z-]+): (\d+)/(\d+) passed', (L / f'{name}.log').read_text(encoding='utf-8', errors='replace'), re.M)
        line = f'{start} {name} exit={rc} ' + (f'{tail[-1][0]}: {tail[-1][1]}/{tail[-1][2]} passed' if tail else '')
        if tail:
            total[0] += int(tail[-1][1]); total[1] += int(tail[-1][2])
        bad += rc != 0
        rows.append(line); print(line, flush=True)
    rows.append(f'TOTAL suites: {total[0]}/{total[1]} passed; failed steps: {bad}')
    print(rows[-1])
    (L / 'summary.txt').write_text('\n'.join(rows) + '\n', encoding='utf-8')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
