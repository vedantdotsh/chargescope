"""Shared helpers for the ChargeScope tests: payload, number formatting as the site does it (Intl en-GB / de-DE), browser contexts."""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
PAYLOAD = HERE.parents[1] / 'data'
DIST = HERE.parent / 'chargescope'  # the subpath build inside the analysis site
URL = (DIST / 'index.html').as_uri()
EVID = HERE / 'evidence' / 'intro'  # intro-polish results; earlier rounds stay in evidence/ and evidence/publication/
EVID.mkdir(parents=True, exist_ok=True)
P = json.loads((PAYLOAD / 'national-story.json').read_text(encoding='utf-8'))
G, ST, DI, BB = P['germany'], P['states'], P['districts'], P['brandenburg']
sys.stdout.reconfigure(encoding='utf-8')


class Results:
    def __init__(self, name):
        self.name, self.rows = name, []

    def ok(self, label, cond, detail=''):
        self.rows.append({'name': label, 'ok': bool(cond), 'detail': str(detail)[:600]})
        print('ok  ' if cond else 'FAIL', label, '' if cond else str(detail)[:600])
        return bool(cond)

    def save(self):
        EVID.mkdir(exist_ok=True)
        bad = [r for r in self.rows if not r['ok']]
        (EVID / f'{self.name}.json').write_text(json.dumps({'passed': len(self.rows) - len(bad), 'total': len(self.rows), 'failed': bad, 'results': self.rows}, indent=1, ensure_ascii=False), encoding='utf-8')
        print(f'\n{self.name}: {len(self.rows) - len(bad)}/{len(self.rows)} passed')
        return 1 if bad else 0


def fmt(v, d=0, lang='en'):
    s = f'{v:,.{d}f}'
    return s.replace(',', '\0').replace('.', ',').replace('\0', '.') if lang == 'de' else s


def pct(v, d=1, lang='en'):
    return fmt(v * 100, d, lang) + (' %' if lang == 'de' else '%')


def rank(rows, key, row):
    return 1 + sum(1 for o in rows if o[key] > row[key])


def new(b, w, h=900, motion='no-preference', lang=None, query='', seed=None):
    """A fresh context. lang is stored as an explicit earlier choice (the site's own persistence) before the first load only; seed adds other
    stored keys the same way (e.g. retired {'theme': 'light', 'palette': 'plum'}); query is appended to the page address (e.g. '?palette=plum')."""
    ctx = b.new_context(viewport={'width': w, 'height': h}, reduced_motion=motion)
    init = "window.__raf=0;const _r=window.requestAnimationFrame.bind(window);window.__rawRAF=_r;window.requestAnimationFrame=f=>{window.__raf++;return _r(f)};"
    init += ''.join(f"try{{if(!sessionStorage.getItem('seed-{k}')){{localStorage.setItem('chargescope-site-{k}','{v}');sessionStorage.setItem('seed-{k}','1')}}}}catch(e){{}}" for k, v in (('lang', lang), *(seed or {}).items()) if v)
    ctx.add_init_script(init)
    pg = ctx.new_page()
    pg._errors = []
    pg.on('pageerror', lambda e: pg._errors.append(str(e)))
    pg.on('console', lambda m: m.type in ('error', 'warning') and pg._errors.append(m.text))
    pg.on('requestfailed', lambda r: pg._errors.append('failed ' + r.url))
    pg.goto(URL + query)
    pg.wait_for_timeout(250)
    return ctx, pg


def go(pg, y):
    """Real scroll: scrollTo fires the page's scroll listener; two frames later its single rAF has drawn this position."""
    pg.evaluate(f"() => new Promise(r => {{ scrollTo(0,{y}); __rawRAF(() => __rawRAF(r)); }})")
    pg.wait_for_timeout(20)


def holds(pg):
    return pg.evaluate("() => window.CSMotion ? CSMotion.holds() : null")


def text(pg, sel):
    return pg.locator(sel).first.inner_text()


JS_LAYOUT = r'''(onscreen) => {
 const W = innerWidth, H = innerHeight, skip = el => el.closest('.k-scroll,dialog,.k-vh,.k-skip,[hidden],[inert],.v3-spokes,.v3-thread');
 const vis = r => !onscreen || (r.bottom > 0 && r.top < H);
 const off = [], over = [];
 for (const el of document.querySelectorAll('#site *')) {
  if (skip(el)) continue; const r = el.getBoundingClientRect(); if (!r.width && !r.height) continue;
  if (r.right > W + 0.5 || r.left < -0.5) off.push((el.className.baseVal ?? el.className) + ':' + (el.textContent || '').trim().slice(0, 30) + ' ' + Math.round(r.left) + '-' + Math.round(r.right));
 }
 const seen = t => getComputedStyle(t).opacity !== '0' && getComputedStyle(t).display !== 'none' && t.textContent.trim();
 for (const svg of document.querySelectorAll('#site svg')) {
  const ts = [...svg.querySelectorAll('text')].filter(seen).map(t => [t.textContent.trim(), t.getBoundingClientRect()]).filter(x => vis(x[1]));
  for (let i = 0; i < ts.length; i++) for (let j = i + 1; j < ts.length; j++) {
   const a = ts[i][1], b = ts[j][1], x = Math.min(a.right, b.right) - Math.max(a.left, b.left), y = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
   if (x > 1 && y > 1) over.push(ts[i][0] + ' / ' + ts[j][0]);
  }
  const cs = [...svg.querySelectorAll('circle:not(.v3-spokes circle)')].filter(c => getComputedStyle(c).opacity !== '0' && !c.closest('.v3-spokes')).map(c => c.getBoundingClientRect());
  for (const t of svg.querySelectorAll('text')) { if (!seen(t)) continue; const a = t.getBoundingClientRect(); if (!vis(a)) continue;
   for (const b of cs) { const x = Math.min(a.right, b.right) - Math.max(a.left, b.left), y = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top); if (x > 2 && y > 2) { over.push(t.textContent.trim() + ' / dot'); break; } } }
 }
 return {sw: document.documentElement.scrollWidth, W, off: off.slice(0, 8), over: over.slice(0, 8)};
}'''

JS_CONTRAST = r'''(onscreen) => {
 const parse = c => { const m = c.match(/[\d.]+/g); if (!m) return null; let [r, g, b, a] = m.map(Number); if (c.startsWith('color(')) { r *= 255; g *= 255; b *= 255; } return [r, g, b, a ?? 1]; };
 const lum = ([r, g, b]) => { const f = v => (v /= 255) <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; return .2126 * f(r) + .7152 * f(g) + .0722 * f(b); };
 const bgOf = el => { for (let e = el; e; e = e.parentElement) { const c = parse(getComputedStyle(e).backgroundColor); if (c && c[3] > .5) return c; } return parse(getComputedStyle(document.documentElement).backgroundColor); };
 const bad = []; let n = 0;
 for (const el of document.querySelectorAll('#site *')) {
  if (el.closest('dialog,.k-vh,.k-skip,[hidden],[aria-hidden=true]')) continue;
  const own = [...el.childNodes].some(x => x.nodeType === 3 && x.textContent.trim()); if (!own) continue;
  const r = el.getBoundingClientRect(); if (!r.width) continue; if (onscreen && (r.bottom < 0 || r.top > innerHeight)) continue;
  const cs = getComputedStyle(el), svg = el instanceof SVGElement;
  let fg = parse(svg ? cs.fill : cs.color); if (!fg) continue; const bg = bgOf(el);
  let a = fg[3]; for (let e = el; e; e = e.parentElement) a *= Number(getComputedStyle(e).opacity);
  if (a === 0) continue;
  fg = fg.map((v, i) => i < 3 ? v * a + bg[i] * (1 - a) : 1);
  const L1 = lum(fg), L2 = lum(bg), ratio = (Math.max(L1, L2) + .05) / (Math.min(L1, L2) + .05);
  const size = parseFloat(cs.fontSize), large = size >= 24 || size >= 18.66 && Number(cs.fontWeight) >= 700; n++;
  if (ratio < (large ? 3 : 4.5)) bad.push(el.textContent.trim().slice(0, 30) + ' ' + ratio.toFixed(2));
 }
 return {n, bad: bad.slice(0, 10)};
}'''
