"""Build the portfolio and ChargeScope static website with hash-verified aggregates.
Run python website/project/build.py from the repository root (stdlib only).
"""
import hashlib, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC, SITE = HERE / 'src', HERE.parent
DIST = SITE / 'chargescope'
PAYLOAD = HERE.parents[1] / 'data'
ASSETS = SITE / 'assets'
PINNED = {
    'national-story.json': 'cf580cceb8229b6b71ac1281af3f5c8b5b526ca6de8d6da00f5a1d0b560f53f3',
    'national-story.js': 'f087d579a79e5458bcee329c5a3db40efe35ddec260efe13fd2adcc8554c669b',
}
TYPES = {'.html': 'text/html; charset=utf-8', '.js': 'application/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
         '.json': 'application/json; charset=utf-8', '.png': 'image/png', '.webp': 'image/webp', '.md': 'text/plain; charset=utf-8',
         '.txt': 'text/plain; charset=utf-8', '.xml': 'application/xml; charset=utf-8'}
HOME = ['index.html', 'style.css', 'app.js', 'data.js', 'robots.txt', 'sitemap.xml']  # the portfolio at /
PREFIX = '/chargescope'
REDIRECTS = [PREFIX] + [f'{PREFIX}/v{n}{tail}' for n in (1, 2, 3) for tail in ('', '/', '/index.html')]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    for name, h in PINNED.items():
        assert sha(PAYLOAD / name) == h, f'payload changed: {name}'
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / 'data').mkdir(parents=True)
    for name in ('index.html', 'kit.js', 'app.js', 'kit.css', 'style.css', 'SOURCES.md'):
        shutil.copyfile(SRC / name, DIST / name)
    shutil.copyfile(PAYLOAD / 'national-story.js', DIST / 'data' / 'national-story.js')
    shutil.copyfile(PAYLOAD / 'national-story.json', DIST / 'data' / 'national-story.json')
    shutil.copytree(ASSETS, DIST / 'assets')

    files = sorted(p for p in DIST.rglob('*') if p.is_file())
    rules = {'/': TYPES['.html']}
    rules.update({'/' + n: TYPES[Path(n).suffix] for n in HOME})
    rules[PREFIX + '/'] = TYPES['.html']
    for p in files:
        rules[PREFIX + '/' + p.relative_to(DIST).as_posix()] = TYPES[p.suffix]
    (SITE / '_headers').write_text(''.join(f'{u}\n  Content-Type: {c}\n  X-Content-Type-Options: nosniff\n\n' for u, c in rules.items()), encoding='utf-8', newline='\n')
    (SITE / '_redirects').write_text(''.join(f'{u} {PREFIX}/ 301\n' for u in REDIRECTS), encoding='utf-8', newline='\n')
    print(f'built {len(files)} files in {DIST}; {len(rules)} header rules and {len(REDIRECTS)} redirects at the site root')


if __name__ == '__main__':
    main()
