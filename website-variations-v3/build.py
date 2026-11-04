import base64
import copy
import json
from pathlib import Path
from urllib.parse import quote

PROJECT = Path(__file__).resolve().parent.parent
ROOT = PROJECT / 'website-combined'
VARIATIONS = PROJECT / 'website-variations-v3'

def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8', newline='\n')

index = (ROOT/'index.html').read_text(encoding='utf-8')
for name in ['workbench', 'profile', 'guided']:
    standalone = index.replace('<body>', '<body data-design="' + name + '">')
    for asset in ['style.css', 'experience.css', 'data.js', 'logic.js', 'experience.js', 'app.js', 'SOURCES.md']:
        standalone = standalone.replace('"' + asset + '"', '"../../website-combined/' + asset + '"')
    standalone = standalone.replace('<script src="../../website-combined/experience.js"', '<script src="../assets-paths.js" defer></script><script src="../../website-combined/experience.js"')
    write(VARIATIONS/name/'index.html', standalone)
write(VARIATIONS/'assets-paths.js', "window.COMBINED_DATA.gallery.forEach(item => { for (const key of ['src', 'thumbnail']) item[key] = '../../website-combined/' + item[key]; });\n")
payload = json.loads((ROOT/'data.js').read_text(encoding='utf-8').removeprefix('window.COMBINED_DATA=').strip().removesuffix(';'))
preview = copy.deepcopy(payload)
for item in preview['gallery']:
    item['src'] = 'data:image/webp;base64,' + base64.b64encode((ROOT/item['thumbnail']).read_bytes()).decode()
    item['thumbnail'] = item['src']
inline = index
for name in ['style.css', 'experience.css']:
    inline = inline.replace('<link rel="stylesheet" href="' + name + '">', '<style>' + (ROOT/name).read_text(encoding='utf-8') + '</style>')
inline = inline.replace('<script src="data.js" defer></script>', '')
for name in ['logic.js','experience.js','app.js']:
    inline = inline.replace('<script src="' + name + '" defer></script>', '')
scripts = '<script>window.COMBINED_DATA=' + json.dumps(preview, ensure_ascii=False, separators=(',',':')) + ';</script>'
scripts += ''.join('<script>' + (ROOT/name).read_text(encoding='utf-8') + '</script>' for name in ['logic.js','experience.js','app.js'])
inline = inline.replace('</body>', scripts + '</body>')
inline = inline.replace('href="SOURCES.md"', 'href="data:text/plain;charset=utf-8,' + quote((ROOT/'SOURCES.md').read_text(encoding='utf-8')) + '"')
write(ROOT/'review.html', inline)
escaped = json.dumps(inline,ensure_ascii=False).replace('</','<\\/')
review = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ChargeScope · Four directions</title><style>:root{font-family:system-ui,sans-serif;color-scheme:light dark}body{margin:0}nav{display:flex;flex-wrap:wrap;gap:8px;padding:12px;background:Canvas;border-bottom:1px solid #8886}button{font:inherit;font-size:13px;padding:10px 14px;color:CanvasText;background:Canvas;border:1px solid #8888;border-radius:5px;cursor:pointer}button[aria-pressed=true]{background:#234b78;color:white}button:focus-visible{outline:3px solid #518dcc;outline-offset:2px}iframe{border:0;width:100%;height:1100px;display:block}#note{padding:0 14px;font-size:12px;color:CanvasText;line-height:1.7}@media(max-width:600px){iframe{height:540px}nav{display:grid;grid-template-columns:1fr 1fr}}</style></head><body><nav aria-label="Choose a design"><button data-design="current" aria-pressed="true">Keep current</button><button data-design="workbench" aria-pressed="false">Comparison workbench</button><button data-design="profile" aria-pressed="false">District profile</button><button data-design="guided" aria-pressed="false">Findings first</button></nav><p id="note">Four working options. Preview images are compressed. Open a standalone option for full-quality slides. No website is hosted.</p><iframe id="candidate" title="ChargeScope design"></iframe><script>const source=SOURCE;const frame=document.getElementById('candidate');function select(design){document.querySelectorAll('[data-design]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.design===design)));frame.srcdoc=source.replace('<body>','<body data-design="'+design+'">')}document.querySelector('nav').addEventListener('click',event=>{if(event.target.dataset.design)select(event.target.dataset.design)});select('current');</script></body></html>'''.replace('SOURCE',escaped)
assert len(review) < 512000 and len(review.encode()) < 512000
write(VARIATIONS/'review.html',review)
write(VARIATIONS/'README.md', '''# ChargeScope design options

Open `review.html` to compare the preserved current design with three alternatives:

- **Comparison workbench** (`workbench/index.html`): compact controls; distribution and full-cohort charts side by side on wide screens.
- **District profile** (`profile/index.html`): selected district facts first, with the comparison beside them and the whole cohort below.
- **Findings first** (`guided/index.html`): three question-led starting points set the actual district, metric and scenario controls.

All four reuse the same data, numerical logic, language/theme preferences, gallery and findings drawer. Selections highlight the chosen and comparison districts without removing cohort members. Only language and appearance persist. No framework, account storage or backend is used.

The review embeds compressed images once. Standalone options load the original PNGs from `../website-combined/assets`. These are unscaled crops of genuine 2560px Power BI exports. The public download is the existing v1.0.0 PBIP source package, not a preloaded PBIX. Its pinned-data setup remains required.

Copy follows loose plain-language principles: short sentences, common verbs and consistent terms. No ASD-STE100 compliance or percentage score is claimed. Sources: https://www.asd-ste100.org/about.html ; visual guidance: https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md . Existing data attribution is unchanged. No live website has been deployed.

## Rebuild and check

From the repository root, run `python website-variations-v3/build.py` to regenerate the three standalone options and compact review from the shared website files. The build uses only the Python standard library. Run `node website-combined/logic.test.js` for numerical checks. With Python Playwright and its Chromium browser installed, run `python website-variations-v3/check.py` and `python website-variations-v3/check-extra.py` for the offline browser checks. They write local evidence under `.scratch/v3`, not into report or data folders.
''')
print(json.dumps({'review_characters':len(review),'review_bytes':len(review.encode()),'variants':3}))
