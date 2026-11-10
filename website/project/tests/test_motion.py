"""Scroll camera, holds, connector and keyboard, driven by real scrolling (scrollTo / mouse wheel fire the page's own scroll listener)
and real key presses in headless Chrome on file://. python -B tests/test_motion.py -> evidence/motion.json"""
import sys
from playwright.sync_api import sync_playwright
from common import Results, new, go, holds, JS_LAYOUT, JS_CONTRAST

R = Results('motion')
ok = R.ok
IDENT = ('none', 'matrix(1, 0, 0, 1, 0, 0)')
# Everything the camera writes, so two visits to one scroll position can be compared exactly.
SNAP = r'''() => [...document.querySelectorAll('.v3-copy,.v3-frame,.v3-label,.v3-foot,.v3-s,.v3-thread')].map(e => (e.className.baseVal ?? e.className) + '|' + [...e.style].map(k => k + ':' + e.style.getPropertyValue(k)).sort().join(';')).join('\n')'''
HOLD = r'''i => { const f = document.querySelectorAll('.v3-step .v3-frame')[i], l = document.querySelectorAll('.v3-step .v3-label')[i], o = document.querySelectorAll('.v3-step .v3-foot')[i], r = f.getBoundingClientRect(), cs = getComputedStyle(f), lr = l.getBoundingClientRect();
 const marks = [...f.querySelectorAll('.k-fill,.mx-bar,.sc-dot,.sp-dot,.sl-l')].map(e => getComputedStyle(e)).filter(c => c.transform !== 'none' || c.strokeDashoffset !== '0px' && c.strokeDasharray !== 'none').length;
 const strip = [...f.querySelectorAll('.v3-s')].filter(c => getComputedStyle(c).translate !== 'none' || c.style.transition).length;
 return {tf: cs.transform, op: +cs.opacity, lop: +getComputedStyle(l).opacity, ltf: getComputedStyle(l).transform, oop: +getComputedStyle(o).opacity, otf: getComputedStyle(o).transform, ltop: lr.top, lbot: lr.bottom, asm: f.classList.contains('is-asm'), chrome: cs.getPropertyValue('--cam-chrome').trim(), marks, strip,
  top: r.top, bottom: r.bottom, w: r.width, ow: f.offsetWidth}; }'''
# Connector i joins step i-1's foot (story and Table button) to step i's heading, ending just above its kicker: rendered top/bottom after every transform.
JOIN = r'''i => { const sec = document.querySelectorAll('.v3-step')[i], th = sec.querySelector('.v3-thread'), t = th.getBoundingClientRect(), f = sec.querySelector('.v3-label').getBoundingClientRect().top - 16;
 const l = document.querySelectorAll('.v3-step .v3-foot')[i - 1].getBoundingClientRect(), cs = getComputedStyle(th), p = getComputedStyle(th.querySelector('.th-p'));
 return {top: t.top, bottom: t.top + parseFloat(cs.height), label: l.bottom, frame: f, shown: cs.display !== 'none' && cs.opacity === '1', d: +cs.getPropertyValue('--d'), n: +cs.getPropertyValue('--n'), pw: parseFloat(p.width)}; }'''


def opening(pg, tag, H, h):
    ws = []
    for s in (0, .25, .5, .75, 1):
        go(pg, round(H[0] * s)); ws.append(pg.evaluate(HOLD, 0))
    w = [x['w'] for x in ws]
    ok(f'{tag}: zoom: Step 1 grows at every stop from a small preview', all(b > a + 1 for a, b in zip(w, w[1:])) and w[0] < .7 * ws[0]['ow'], w)
    ok(f'{tag}: zoom: Step 1 heading rides above the scaled frame, never over it', all(x['lbot'] <= x['top'] + .5 for x in ws), [(x['lbot'], x['top']) for x in ws])
    OPEN = "() => { const f = document.querySelector('#r2 .v3-frame'), l = document.querySelector('#r2 .v3-label'); return [f.classList.contains('is-asm'), +getComputedStyle(l).opacity, getComputedStyle(document.querySelector('#r2 .v3-thread')).opacity, document.querySelectorAll('.v3-spokes,.is-net').length, getComputedStyle(document.querySelector('.v3-copy')).opacity]; }"
    go(pg, 0); a = pg.evaluate(OPEN)
    ok(f'{tag}: opening: hero readable, Step 1 marks gathered (assembling), heading hidden, no stray connector, no ring network', a[0] and a[1] == 0 and a[2] == '0' and a[3] == 0 and a[4] == '1', a)
    go(pg, round(H[0] * .6)); m = pg.evaluate(OPEN)
    ok(f'{tag}: mid-zoom: marks still assembling, heading fading in', m[0] and 0 < m[1] < 1, m)
    go(pg, H[0]); z = pg.evaluate(OPEN)
    ok(f'{tag}: at hold 1 the marks are complete and the heading opaque', not z[0] and z[1] == 1, z)


def all_holds(pg, tag, H, h, scan):
    for i, y in enumerate(H):
        go(pg, y); s = pg.evaluate(HOLD, i)
        ok(f'{tag}: hold {i + 1}: heading, frame and foot untransformed, opaque, marks at data positions', s['tf'] in IDENT and s['op'] == 1 and s['lop'] == 1 and s['ltf'] in IDENT and s['oop'] == 1 and s['otf'] in IDENT and not s['asm'] and s['marks'] == 0 and s['strip'] == 0 and s['chrome'] in ('', '1'), s)
        ok(f'{tag}: hold {i + 1}: heading and frame top on screen below the header, heading above the frame', s['ltop'] >= 50 and s['top'] < h and s['lbot'] <= s['top'], s)
        if i:
            j = pg.evaluate(JOIN, i)
            ok(f'{tag}: hold {i + 1}: connector complete, node shown, joined', j['d'] == 1 and j['n'] == 1 and abs(j['bottom'] - j['frame']) < 1 and abs(j['top'] - j['label'] - 10) < 1, j)
        z = pg.evaluate("() => [...document.querySelectorAll('.v3-thread')].map((t, k) => [k, getComputedStyle(t).opacity, parseFloat(getComputedStyle(t).height)]).filter(x => x[1] !== '0' && x[2] < 1)")
        ok(f'{tag}: hold {i + 1}: no collapsed connector node left showing (Step 1 stem hidden once its step has gone)', not z, z)
        if scan:
            L = pg.evaluate(JS_LAYOUT, True); c = pg.evaluate(JS_CONTRAST, True)
            ok(f'{tag}: hold {i + 1}: on-screen layout clean and AA contrast', not L['over'] and not L['off'] and L['sw'] <= L['W'] and not c['bad'], (L, c['bad']))


def connector(pg, tag, H):
    caps = []
    for k in range(101):
        go(pg, round(H[0] * k / 100))
        caps.append(pg.evaluate("""() => {const c=document.querySelector('#r2 .th-s'),r=c.getBoundingClientRect();let a=1;for(let e=c;e;e=e.parentElement)a*=+getComputedStyle(e).opacity;return [a,r.top,document.querySelector('.k-head').getBoundingClientRect().bottom];}"""))
    ok(f'{tag}: visible intro connector ring never intersects header (101 positions)', all(a == 0 or top >= bottom - .01 for a, top, bottom in caps), [x for x in caps if x[0] > 0 and x[1] < x[2] - .01])
    bad, n = [], 0
    for i in range(1, len(H)):
        for fr in (.1, .25, .4, .55, .7, .85, .95):
            go(pg, round(H[i - 1] + (H[i] - H[i - 1]) * fr)); j = pg.evaluate(JOIN, i); n += 1
            if not (j['shown'] and abs(j['top'] - j['label'] - 10) < 1 and abs(j['bottom'] - j['frame']) < 1 and j['pw'] >= 4):
                bad.append((i, fr, j))
    ok(f'{tag}: connector starts at the previous foot and meets the moving heading at {n} intermediate positions', not bad, bad[:3])
    col = pg.evaluate("() => { const p = getComputedStyle(document.querySelector('#r7 .th-p')).backgroundColor, c = document.createElement('i'); c.style.color = getComputedStyle(document.documentElement).getPropertyValue('--or'); document.body.append(c); const o = getComputedStyle(c).color; c.remove(); return [p, o]; }")
    ok(f'{tag}: connector line is drawn in the Graphite accent (--or)', col[0] == col[1] == 'rgb(255, 148, 64)', col)
    go(pg, round(H[1] - (H[1] - H[0]) * .5)); a = pg.evaluate(JOIN, 1); go(pg, round(H[1] - (H[1] - H[0]) * .2)); b = pg.evaluate(JOIN, 1)
    ok(f'{tag}: connector progress advances with scroll', 0 <= a['d'] < b['d'] <= 1, (a['d'], b['d']))


def reversal(pg, tag, H):
    for y in (round(H[0] * .4), round((H[1] + H[2]) / 2), round((H[2] + H[3]) / 2)):
        go(pg, y); a = pg.evaluate(SNAP); go(pg, H[-1]); go(pg, 0); go(pg, y); b = pg.evaluate(SNAP)
        ok(f'{tag}: position {y} gives the same state after a round trip', a == b and len(a) > 100)
    go(pg, 0); a = pg.evaluate(SNAP); go(pg, H[-1]); go(pg, 0)
    ok(f'{tag}: returning to the top restores the first-load state', a == pg.evaluate(SNAP))


def idle(pg, tag):
    pg.wait_for_timeout(300); n = pg.evaluate('__raf'); pg.wait_for_timeout(800)
    ok(f'{tag}: idle page requests no animation frames', pg.evaluate('__raf') == n)


def wheel(pg, tag, H):
    go(pg, 0); pg.mouse.move(300, 400); ys = []
    for _ in range(14):
        pg.mouse.wheel(0, 400); pg.wait_for_timeout(70); ys.append(pg.evaluate('scrollY'))
    ok(f'{tag}: wheel scrolls natively and monotonically forward (no trap, no snap)', all(b > a for a, b in zip(ys, ys[1:])) and ys[-1] >= 14 * 400 - 400, ys)
    back = []
    for _ in range(6):
        pg.mouse.wheel(0, -400); pg.wait_for_timeout(70); back.append(pg.evaluate('scrollY'))
    ok(f'{tag}: wheel reverses monotonically', all(b < a for a, b in zip([ys[-1]] + back, back)), back)
    pg.keyboard.press('End'); pg.wait_for_timeout(250)
    s = pg.evaluate("() => [scrollY + innerHeight >= document.documentElement.scrollHeight - 2, getComputedStyle(document.querySelectorAll('.v3-step .v3-frame')[3]).transform, CSMotion.room(), [...document.querySelectorAll('.v3-x .v3-frame')].every(f => !f.getAttribute('style'))]")
    ok(f'{tag}: End reaches the page foot with the last step at rest and still in view; Explore frames never posed', s[0] and s[1] in IDENT and s[2] == 3 and s[3], s)
    pg.keyboard.press('Home'); pg.wait_for_timeout(250)
    ok(f'{tag}: Home returns to the opening', pg.evaluate("() => scrollY") == 0)


def keyboard(pg, tag, h):
    go(pg, 0); pg.evaluate("document.querySelector('.k-skip').focus({preventScroll:true})"); bad, n = [], 0
    for _ in range(110):
        pg.keyboard.press('Tab'); pg.wait_for_timeout(45)
        s = pg.evaluate("""() => { const e = document.activeElement; if (!e || e === document.body) return null; const r = e.getBoundingClientRect(), f = e.closest('.v3-frame'), l = e.closest('.v3-label,.v3-foot'), hd = document.querySelector('.k-head').offsetHeight;
          const rest = x => !x || [x, ...(x.closest('.v3-step') ? [x.closest('.v3-step').querySelector('.v3-label')] : [])].every(y => ['none', 'matrix(1, 0, 0, 1, 0, 0)'].includes(getComputedStyle(y).transform) && getComputedStyle(y).opacity === '1');
          return {k: e.dataset.k || e.tagName, in: e.closest('.k-head,.k-rail,.k-foot') ? 'fixed' : 'page', vis: r.top >= (e.closest('.k-head') ? 0 : hd) - 1 && r.bottom <= innerHeight + 1, rest: rest(f) && rest(l), copy: !e.closest('.v3-copy') || +getComputedStyle(e.closest('.v3-copy')).opacity > .95}; }""")
        if s is None:
            continue
        n += 1
        if s['in'] == 'page' and not (s['vis'] and s['rest'] and s['copy']):
            bad.append(s)
        pg._walk = getattr(pg, '_walk', []) + [s['k']]
        if s['k'] == 'fabout':
            break
    ok(f'{tag}: Tab walk ({n} stops) reveals every control on screen, never on a transformed or fading frame, heading or foot', not bad and n > 15 and 'fabout' in pg._walk, (bad[:4], pg._walk))
    # Shift+Tab back up to the hero link brings the opening copy back.
    go(pg, 2000)
    pg.evaluate("document.querySelector('[data-k=m2points]').focus({preventScroll:true})")
    pg.keyboard.press('Shift+Tab'); pg.wait_for_timeout(60)
    s = pg.evaluate("() => [document.activeElement.dataset.k, scrollY, +getComputedStyle(document.querySelector('.v3-copy')).opacity]")
    ok(f'{tag}: Shift+Tab to the hero link restores the readable opening', s[0] == 'habout' and s[1] == 0 and s[2] == 1, s)


def controls_mid(pg, tag, H, lang):
    # Scenario toggled during the strip's assembly: no easing composes with the assembly offset; at rest the transition returns.
    y = round(H[2] - (H[2] - H[1]) * .35); go(pg, y)
    res = []
    for v in ('1', '0', '1'):
        res.append(pg.evaluate("""v => { document.querySelector('[data-act=scen][data-v="' + v + '"]').click(); const c = document.querySelector('[data-r=strip] .is-os'), m = new DOMMatrix(getComputedStyle(c).transform), t = new DOMMatrix(c.style.transform);
          return {dx: Math.abs(m.e - t.e), dy: Math.abs(m.f - t.f), tr: getComputedStyle(c).transitionDuration}; }""", v))
    ok(f'{tag}: scenario clicks mid-assembly land immediately (transition suspended)', all(r['dx'] < .02 and r['dy'] < .02 and r['tr'] == '0s' for r in res), res)
    targets = pg.evaluate("""() => [...document.querySelectorAll('[data-r=strip] :is(.v3-med,.v3-oslab,.v3-ghost,.v3-ghostlab)')].map(c => {const cs=getComputedStyle(c),m=new DOMMatrix(cs.transform),t=new DOMMatrix(c.style.transform);return {dx:Math.abs(m.e-t.e),dy:Math.abs(m.f-t.f),tr:cs.transitionDuration,opacity:cs.opacity,ghost:c.matches('.v3-ghost,.v3-ghostlab')};})""")
    ok(f'{tag}: assembly labels median and ghosts reach targets immediately', all(r['dx'] < .02 and r['dy'] < .02 and r['tr'] == '0s' and (not r['ghost'] or r['opacity'] == '1') for r in targets), targets)
    ok(f'{tag}: control clicks never move the page', pg.evaluate('scrollY') == y)
    go(pg, H[2])
    ok(f'{tag}: at rest the strip keeps its ordinary scenario transition', pg.evaluate("() => { const c = document.querySelector('[data-r=strip] .is-os'); return c.style.transition === '' && c.style.translate === '' && getComputedStyle(c).transitionDuration === '0.9s'; }"))
    pg.click('[data-act=scen][data-v="0"]')
    # Language switched mid-scene: no jump, and the camera state is the same after switching back.
    y = round((H[1] + H[2]) / 2); go(pg, y); a = pg.evaluate(SNAP)
    other = {'en': 'de', 'de': 'en'}[lang]
    for k in ('l' + other, 'l' + lang):
        pg.evaluate("document.querySelector('.k-menu-btn').click()"); pg.evaluate(f"document.querySelector('[data-k={k}]').click()"); pg.wait_for_timeout(60)
    pg.keyboard.press('Escape')
    ok(f'{tag}: language switches mid-scene keep scroll and camera state', pg.evaluate('scrollY') == y and pg.evaluate(SNAP) == a)


def reduced_live(pg, tag, H):
    y = round((H[0] + H[1]) / 2); go(pg, y); a = pg.evaluate(SNAP)
    pg.emulate_media(reduced_motion='reduce'); pg.wait_for_timeout(80)
    s = pg.evaluate("() => [document.documentElement.classList.contains('v3-motion'), [...document.querySelectorAll('.v3-copy,.v3-frame,.v3-label,.v3-foot,.v3-thread')].some(e => e.style.transform || e.style.opacity || e.style.top), [...document.querySelectorAll('.v3-frame')].some(f => f.classList.contains('is-asm'))]")
    ok(f'{tag}: switching to reduced motion clears every written style', s == [False, False, False], s)
    pg.emulate_media(reduced_motion='no-preference'); pg.wait_for_timeout(80)
    ok(f'{tag}: switching back rebuilds exactly the state for this scroll position', pg.evaluate(SNAP) == a)


def rail_live(pg, tag):
    """Wide screens: the rail stays gated (past the right edge, inert, aria-hidden) above Step 1's hold whichever motion setting is live; a live switch never reveals it early or gates it at the hold."""
    hid = lambda: pg.evaluate("() => { const r = document.querySelector('.k-rail'); return r.inert && r.getAttribute('aria-hidden') === 'true' && document.querySelector('.k-layout').classList.contains('is-pre'); }")
    res = []
    go(pg, 0); res.append(hid())
    pg.emulate_media(reduced_motion='reduce'); pg.wait_for_timeout(80); res.append(hid())
    pg.emulate_media(reduced_motion='no-preference'); pg.wait_for_timeout(80); res.append(hid())
    go(pg, holds(pg)[0]); res.append(hid())
    pg.emulate_media(reduced_motion='reduce'); pg.wait_for_timeout(80); res.append(hid())
    go(pg, 0); res.append(hid())
    pg.emulate_media(reduced_motion='no-preference'); pg.wait_for_timeout(80); go(pg, round(holds(pg)[0] * .6)); res.append(hid())
    ok(f'{tag}: rail gated above Step 1’s hold and live at it, across live reduced-motion switches', res == [True, True, True, False, False, True, True], res)


def main():
    with sync_playwright() as p:
        b = p.chromium.launch(channel='chrome')
        for w, h, lang, deep in ((1440, 900, 'en', True), (390, 844, 'de', True), (320, 640, 'de', True),
                                 (1280, 720, 'en', False), (728, 1024, 'de', False), (1180, 760, 'en', False), (320, 640, 'en', False)):
            tag = f'{w}x{h} {lang}'
            ctx, pg = new(b, w, h, lang=lang)
            H = holds(pg)
            ok(f'{tag}: four step holds in page order', H and len(H) == 4 and all(b2 > a2 for a2, b2 in zip(H, H[1:])), H)
            opening(pg, tag, H, h)
            all_holds(pg, tag, H, h, scan=True)
            connector(pg, tag, H)
            if w >= 1180:
                rail_live(pg, tag)
            if deep:
                reversal(pg, tag, H); idle(pg, tag); wheel(pg, tag, H); controls_mid(pg, tag, holds(pg), lang); reduced_live(pg, tag, holds(pg)); keyboard(pg, tag, h)
            ok(f'{tag}: no console errors', not pg._errors, pg._errors)
            ctx.close()
        # Resize mid-scene and bfcache: holds are recomputed and still exact.
        ctx, pg = new(b, 1440, 900); go(pg, 3000); pg.set_viewport_size({'width': 728, 'height': 900}); pg.wait_for_timeout(200)
        H = holds(pg); go(pg, H[3]); s = pg.evaluate(HOLD, 3)
        ok('resize 1440 → 728 mid-scene: new holds exact', s['tf'] in IDENT and s['op'] == 1 and not s['asm'], s)
        ctx.close()
        # Reduced motion from the first load: the camera writes no style anywhere, at any scroll position (chart geometry styles are not the camera's).
        CAM = "() => [...document.querySelectorAll('.v3-copy,.v3-frame,.v3-label,.v3-foot,.v3-thread,.v3-s')].filter(e => e.style.transform && !e.matches('.v3-s') || e.style.opacity || e.style.translate || e.style.top || [...e.style].some(k => k.startsWith('--')) || e.matches('.is-asm')).map(e => e.className.baseVal ?? e.className)"
        for w, lang in ((1440, 'en'), (390, 'de')):
            ctx, pg = new(b, w, 900, motion='reduce', lang=lang); top = pg.evaluate('document.documentElement.scrollHeight - innerHeight'); seen = []
            for y in range(0, top + 1, max(1, top // 12)):
                go(pg, y); seen.append(pg.evaluate(CAM))
            ok(f'reduced motion {w} {lang}: no camera style written at any of {len(seen)} scroll positions', not any(seen) and not pg.evaluate("document.documentElement.classList.contains('v3-motion')"), [x for x in seen if x][:2])
            ctx.close()
        b.close()
    sys.exit(R.save())


if __name__ == '__main__':
    main()
