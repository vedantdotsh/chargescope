"""Graphite dark is the only appearance, and the report section after room VIII.
- Retired preferences never override it: stored theme/palette values and ?palette= / ?theme= in the address are ignored; language still persists.
- No appearance UI is left (settings: language and Method & sources only), and no dead theme/palette code ships.
- The colours Graphite dark actually renders (computed fills, opacities, alpha blends) keep the contrast, grayscale and colour-vision gates
  the palette suite applied to it; the five removed palettes and every light variant are gone, so nothing is claimed for them.
- The power classes: neighbouring classes further apart in lightness than before, inside the Graphite palette.
- The findings and About sections after Step 4: not steps; AA text; About names the Brandenburg Power BI case study and opens the existing
  drawer, slides and lightbox; keyboard open/close returns focus there without moving the page; End passes it to Explore, Home returns to the opening.
python -B tests/test_graphite.py -> evidence/graphite.json"""
import re, sys
from playwright.sync_api import sync_playwright
from common import Results, new, go, holds, DIST, JS_LAYOUT, JS_CONTRAST

R = Results('graphite')
ok = R.ok
DL = 'https://github.com/vedantdotsh/chargescope/releases/download/v1.0.0/ChargeScope-PowerBI-source.zip'
TOKENS = {'--bg': '#171717', '--frame': '#252525', '--base': '#8f8a84', '--or': '#ff9440', '--or-text': '#ff9d55', '--on-acc': '#171717'}
LOOK = r'''() => { const h = document.documentElement, v = k => getComputedStyle(h).getPropertyValue(k).trim();
 return {theme: h.getAttribute('data-theme'), palette: h.getAttribute('data-palette'), scheme: getComputedStyle(h).colorScheme, body: getComputedStyle(document.body).backgroundColor,
  tokens: Object.fromEntries(['--bg','--frame','--base','--or','--or-text','--on-acc'].map(k => [k, v(k)])), lang: h.lang,
  conn: getComputedStyle(document.querySelector('#r7 .th-p')).backgroundColor, menu: [...document.querySelectorAll('#k-pop button')].map(b => b.dataset.k),
  dead: document.querySelectorAll('[data-act=theme],[data-act=palette],[data-palette],.k-sw,.k-pal').length,
  store: Object.keys(localStorage).filter(k => k.startsWith('chargescope-site-')).sort()}; }'''


def stale(b):
    cases = [({}, '', 'en', 'nothing stored, plain address'), ({'theme': 'light'}, '', 'en', 'stored Light theme'), ({'palette': 'plum'}, '', 'en', 'stored Plum palette'),
             ({'theme': 'light', 'palette': 'ivory'}, '?palette=forest', 'en', 'stored Light + Ivory and ?palette=forest'), ({}, '?palette=stone&theme=light', 'en', '?palette=stone&theme=light only'),
             ({'lang': 'de', 'theme': 'light', 'palette': 'charcoal'}, '?palette=charcoal', 'de', 'stored DE + Light + Charcoal and ?palette=charcoal: German kept, Graphite dark')]
    for seed, q, lang, label in cases:
        lg = seed.pop('lang', None)
        ctx, pg = new(b, 1280, 800, lang=lg, seed=seed, query=q)
        s = pg.evaluate(LOOK)
        ok(f'{label}: Graphite dark rendered (tokens, page, connector, colour scheme), no theme/palette attribute', s['tokens'] == TOKENS and s['body'] == 'rgb(23, 23, 23)' and s['conn'] == 'rgb(255, 148, 64)'
           and s['scheme'] == 'dark' and s['theme'] is None and s['palette'] is None, s)
        ok(f'{label}: language {lang}; settings offer only EN/DE and Method & sources', s['lang'] == lang and s['menu'] == ['len', 'lde', 'mabout'] and s['dead'] == 0, s)
        # Switching language keeps Graphite dark and stores only the language (retired keys are left as they were, never rewritten).
        pg.click('.k-menu-btn'); pg.click('[data-k=l' + ('en' if lang == 'de' else 'de') + ']'); pg.wait_for_timeout(60); s2 = pg.evaluate(LOOK)
        want = sorted({'chargescope-site-lang'} | {'chargescope-site-' + k for k in seed})
        ok(f'{label}: a language switch keeps Graphite dark and writes only the language', s2['tokens'] == TOKENS and s2['store'] == want and s2['dead'] == 0, s2)
        ok(f'{label}: no console errors', not pg._errors, pg._errors)
        ctx.close()
    # Nothing that could restore a retired appearance ships.
    code = {n: (DIST / n).read_text(encoding='utf-8') for n in ('index.html', 'kit.js', 'app.js', 'kit.css', 'style.css')}
    hits = {n: re.findall(r'data-theme|data-palette|\[data-act=(?:theme|palette)\]|data-act="(?:theme|palette)"|read\(.(?:theme|palette)|searchParams|replaceState|prefers-color-scheme|\.k-sw|\.k-pal\b|--or-track:[^;]*light', s) for n, s in code.items()}
    ok('no theme/palette selectors, reads, URL writes or light tokens ship', not any(hits.values()), hits)
    ok('style.css defines the accent once (no alternative palettes)', len(re.findall(r'--or:#', code['style.css'])) == 1, re.findall(r'--or:#\w+', code['style.css']))


# Rendered-colour gates, as the palette suite applied them, now for the one appearance.
def rgb(c):
    v = [float(x) for x in re.findall(r'[\d.]+', c)]
    if c.startswith('color('):
        v = [x * 255 for x in v[:3]] + v[3:]
    return v[:3]


lin = lambda v: (v / 255) / 12.92 if v / 255 <= .04045 else (((v / 255) + .055) / 1.055) ** 2.4
lum = lambda c: .2126 * lin(c[0]) + .7152 * lin(c[1]) + .0722 * lin(c[2])
cr = lambda a, b: (max(lum(a), lum(b)) + .05) / (min(lum(a), lum(b)) + .05)
over = lambda fg, a, bg: [fg[i] * a + bg[i] * (1 - a) for i in range(3)]
CVD = {'protan': ((0.152286, 1.052583, -0.204868), (0.114503, 0.786281, 0.099216), (-0.003882, -0.048116, 1.051998)),
       'deutan': ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413), (-0.011820, 0.042940, 0.968881)),
       'tritan': ((1.255528, -0.076749, -0.178779), (-0.078411, 0.930809, 0.147602), (0.004733, 0.691367, 0.303900))}


def lab(c):
    r, g, b = (lin(x) for x in c)
    X, Y, Z = (.4124 * r + .3576 * g + .1805 * b) / .95047, .2126 * r + .7152 * g + .0722 * b, (.0193 * r + .1192 * g + .9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > .008856 else 7.787 * t + 16 / 116
    return 116 * f(Y) - 16, 500 * (f(X) - f(Y)), 200 * (f(Y) - f(Z))


def sim(c, m):
    l = [lin(x) for x in c]; o = [max(0, min(1, sum(m[i][j] * l[j] for j in range(3)))) for i in range(3)]
    return [255 * (12.92 * v if v <= .0031308 else 1.055 * v ** (1 / 2.4) - .055) for v in o]


de = lambda a, b: sum((x - y) ** 2 for x, y in zip(lab(a), lab(b))) ** .5
READ = r'''() => { const q = s => document.querySelector(s), cs = s => getComputedStyle(q(s));
 return {page: getComputedStyle(document.body).backgroundColor, frame: cs('#r3 .v3-frame').backgroundColor,
  dim: [cs('.sc-dot.is-dim').fill, +cs('.sc-dot.is-dim').fillOpacity * +cs('.sc-dot.is-dim').opacity], acc: [cs('.sc-dot.is-in').fill, +cs('.sc-dot.is-in').fillOpacity],
  on: [cs('.sc-dot.is-on').stroke, parseFloat(cs('.sc-dot.is-on').strokeWidth), +q('.sc-dot.is-on').getAttribute('r'), +q('.sc-dot.is-in:not(.is-on)').getAttribute('r')],
  sp: [cs('.sp-dot:not(.is-flag):not(.is-on):not(.is-mute)').fill, +cs('.sp-dot:not(.is-flag):not(.is-on):not(.is-mute)').fillOpacity],
  ring: [cs('.sp-dot.is-flag').fill, cs('.sp-dot.is-flag').stroke, parseFloat(cs('.sp-dot.is-flag').strokeWidth)],
  bbBar: cs('#r2 .is-hi .k-fill').backgroundColor, beBar: cs('#r2 .is-be .k-fill').backgroundColor, bbName: +cs('#r2 .is-hi .k-name').fontWeight, otherName: +cs('#r2 .k-row:not(.is-hi):not(.is-be) .k-name').fontWeight,
  mover: [cs('.sl-l.is-mv').stroke, +cs('.sl-l.is-mv').strokeOpacity], still: [cs('.sl-l:not(.is-mv):not(.is-os):not(.is-on)').stroke, +cs('.sl-l:not(.is-mv):not(.is-os):not(.is-on)').strokeOpacity],
  conn: cs('#r8 .v3-thread .th-p').backgroundColor, connW: parseFloat(cs('#r8 .v3-thread .th-p').width), node: cs('#r8 .v3-thread .th-t').backgroundColor,
  segOn: [cs('[data-m=m2][aria-pressed=true]').backgroundColor, cs('[data-m=m2][aria-pressed=true]').color], kick: cs('#r5 .v3-room-no').color, rail: cs('.k-rail .k-rail-kick').color,
  endBtn: [cs('.v3-end-open').backgroundColor, cs('.v3-end-open').color], endKick: cs('#about-k').color,
  pw: [...document.querySelectorAll('.mx-key i')].map(i => getComputedStyle(i).backgroundColor), legend: cs('#r5 .v3-legend').color}; }'''


def colours(b):
    ctx, pg = new(b, 1440, 900); H = holds(pg)
    arcs = pg.evaluate("() => ['.sb-d:not(.is-on):not(.alt)', '.sb-d.alt:not(.is-on)'].map(s => getComputedStyle(document.querySelector(s)).fill)")
    ctxdot = pg.evaluate("() => { const c = getComputedStyle(document.querySelector('.sc-dot')); return [c.fill, +c.fillOpacity * +c.opacity]; }")
    pg.select_option('select[data-k=s3]', '06'); pg.select_option('select[data-k=d5]', '06412')
    arcs.append(pg.evaluate("getComputedStyle(document.querySelector('.sb-d.is-on')).fill"))
    go(pg, round(H[2] + (H[3] - H[2]) * .5)); c = pg.evaluate(READ)
    go(pg, 0); pg.evaluate("document.querySelector('.k-skip').focus({preventScroll:true})"); pg.keyboard.press('Tab'); pg.wait_for_timeout(30)
    fr = pg.evaluate("() => { const c = getComputedStyle(document.activeElement); return [c.outlineColor, c.outlineStyle, parseFloat(c.outlineWidth)]; }")
    ctx.close()
    page, frame = rgb(c['page']), rgb(c['frame'])
    for i, col in enumerate(arcs):
        ok(f'outer district arc {i} / frame ≥ 3:1 (rendered {cr(rgb(col), frame):.2f})', cr(rgb(col), frame) >= 3)
    acc = over(rgb(c['acc'][0]), c['acc'][1], frame); cx = over(rgb(ctxdot[0]), ctxdot[1], frame); sp = over(rgb(c['sp'][0]), c['sp'][1], frame)
    dim = over(rgb(c['dim'][0]), c['dim'][1], frame); conn = rgb(c['conn'])
    still = over(rgb(c['still'][0]), c['still'][1], frame); mover = over(rgb(c['mover'][0]), c['mover'][1], frame)
    m = {'accent mark / frame': (cr(acc, frame), 3), 'context dot / frame': (cr(cx, frame), 3), 'spread dot / frame': (cr(sp, frame), 3), 'flag ring / frame': (cr(rgb(c['ring'][1]), frame), 3),
         'selection outline / frame': (cr(rgb(c['on'][0]), frame), 3), 'Brandenburg bar / frame': (cr(rgb(c['bbBar']), frame), 3), 'Berlin bar / frame': (cr(rgb(c['beBar']), frame), 3),
         'mover line / frame': (cr(mover, frame), 3), 'connector line / page': (cr(conn, page), 3), 'focus ring / page': (cr(rgb(fr[0]), page), 3),
         'pressed toggle text': (cr(rgb(c['segOn'][1]), rgb(c['segOn'][0])), 4.5), 'step kicker text / page': (cr(rgb(c['kick']), page), 4.5), 'legend text / frame': (cr(rgb(c['legend']), frame), 4.5), 'rail kicker / page': (cr(rgb(c['rail']), page), 4.5),
         'end button text': (cr(rgb(c['endBtn'][1]), rgb(c['endBtn'][0])), 4.5), 'end button / page': (cr(rgb(c['endBtn'][0]), page), 3), 'end kicker / page': (cr(rgb(c['endKick']), page), 4.5),
         'dimmed context / frame': (cr(dim, frame), 1.2), 'gray: accent / dimmed context': (cr(acc, dim), 2), 'gray: mover / unmoved line': (cr(mover, still), 2)}
    for k, (v, need) in m.items():
        ok(f'{k} ≥ {need}:1 (rendered {v:.2f})', v >= need, v)
    # Power classes (Explore): rendered swatches, each neighbour pair further apart than the earlier 1.08 / 1.71 / 1.62.
    pw = [rgb(x) for x in c['pw']]; adj = [cr(pw[i], pw[i + 1]) for i in range(3)]
    ok(f'power classes: neighbours further apart than before ({", ".join(f"{a:.2f}" for a in adj)}; was 1.08, 1.71, 1.62)', len(pw) == 4 and adj[0] > 1.2 and adj[1] > 1.8 and adj[2] > 1.8, adj)
    ok('power classes: lightness rises with power across the three orange classes; the top class is the accent', lum(pw[1]) < lum(pw[2]) < lum(pw[3]) and [round(x) for x in pw[3]] == [255, 148, 64], c['pw'])
    cvd = {k: de(sim(acc, M), sim(cx, M)) for k, M in CVD.items()}
    ok('accent and context stay apart under simulated protan/deutan/tritan vision (ΔE ≥ 20)', min(cvd.values()) >= 20, cvd)
    ok('connector is the Graphite accent, a 4 px line; focus ring a solid 3 px outline', c['conn'] == 'rgb(255, 148, 64)' and c['connW'] == 4 and fr[1:] == ['solid', 3], (c['conn'], c['connW'], fr))
    ok('selection never rests on colour alone: outlined, larger, hollow flag rings, bold rows, opaque movers',
       c['on'][1] >= 2 and c['on'][2] > c['on'][3] and [round(x) for x in rgb(c['ring'][0])] == [round(x) for x in frame] and c['ring'][2] >= 1.5 and c['bbName'] >= 600 > c['otherName'] and c['mover'][1] >= .8 > .3 > c['still'][1], c)


END = r'''() => { const e = document.querySelector('#about'), m = document.querySelector('main'), r = e.getBoundingClientRect(), hd = document.querySelector('.k-head').offsetHeight, b = e.querySelector('.v3-end-open').getBoundingClientRect();
 const order = [...m.children].map(x => x.id);
 return {last: order.join() === 'top,r2,r5,r7,r8,findings,about,explore', afterVIII: !!(document.querySelector('#r8').compareDocumentPosition(e) & Node.DOCUMENT_POSITION_FOLLOWING), room: ['#findings', '#about'].some(q => document.querySelector(q).matches('.v3-room,.v3-step') || !!document.querySelector(q).querySelector('.v3-frame,.v3-label,.v3-thread')),
  rooms: [document.querySelectorAll('.v3-step').length, document.querySelectorAll('.v3-step .v3-frame').length, document.querySelectorAll('.v3-label').length, document.querySelectorAll('.v3-thread').length, document.querySelectorAll('.v3-x .v3-frame').length],
  name: document.getElementById(e.getAttribute('aria-labelledby')).textContent, kick: e.querySelector('#about-k').textContent, text: e.textContent, order,
  btn: [e.querySelector('.v3-end-open').textContent, e.querySelector('.v3-end-open').getAttribute('aria-haspopup'), document.getElementById(e.querySelector('.v3-end-open').getAttribute('aria-describedby')).textContent, Math.round(b.height)],
  dl: e.querySelector('a.k-dl').getAttribute('href'), seen: r.top >= hd - 1 && r.bottom <= innerHeight + 1 && r.left >= 0 && r.right <= innerWidth}; }'''


def end(b, w, h, lang, motion='no-preference'):
    tag = f'end section {w}x{h} {lang} {motion}'
    ctx, pg = new(b, w, h, motion=motion, lang=lang)
    s = pg.evaluate(END)
    ok(f'{tag}: page order hero, 4 steps, findings, About, Explore; findings and About are not steps; 4 steps, frames, headings and connectors; 4 Explore frames', s['last'] and s['afterVIII'] and not s['room'] and s['rooms'] == [4, 4, 4, 4, 4], s)
    view = {'en': 'View the Power BI slides', 'de': 'Power-BI-Folien ansehen'}[lang]
    ok(f'{tag}: About names the Brandenburg Power BI case study, not a national report; one dialog button described by the section kicker',
       re.search(r'Power[ -]BI', s['text']) and re.search(r'Brandenburg', s['text']) and not re.search(r'national|bundesweit', s['text'], re.I) and s['btn'][:3] == [view, 'dialog', s['kick']] and s['btn'][3] >= 36, s)
    ok(f'{tag}: download is the existing Power BI project link, the same as in the drawer; GitHub link unchanged', s['dl'] == DL and pg.locator(f'#about a.k-dl[href="{DL}"]').count() == 1 and pg.locator('#about a.k-gh[href="https://github.com/vedantdotsh/chargescope"]').count() == 1, s['dl'])
    # End: the page foot (Explore) with Step 4 at rest and still the step in view; the rail (wide) keeps Step 4.
    pg.keyboard.press('End'); pg.wait_for_timeout(300)
    st = pg.evaluate("() => [scrollY + innerHeight >= document.documentElement.scrollHeight - 2, getComputedStyle(document.querySelectorAll('.v3-step .v3-frame')[3]).transform, CSMotion.room(), getComputedStyle(document.querySelector('.k-rail')).display === 'none' ? -1 : +document.querySelector('.k-rail').dataset.room]")
    ok(f'{tag}: End reaches Explore at the foot; Step 4 at rest stays the step in view', st[0] and st[1] in ('none', 'matrix(1, 0, 0, 1, 0, 0)') and st[2] == 3 and st[3] in (-1, 3), st)
    # The findings and About sections, each brought on screen: width and AA text.
    for q in ('#findings', '#about', '#explore'):
        pg.evaluate(f"document.querySelector('{q}').scrollIntoView({{block: 'start', behavior: 'instant'}})"); pg.wait_for_timeout(120)
        L = pg.evaluate(JS_LAYOUT, True); c = pg.evaluate(JS_CONTRAST.replace("'#site *'", f"'{q} *'"), True)
        ok(f'{tag}: {q} fits the width, AA text ({c["n"]} texts)', L['sw'] <= L['W'] and not L['off'] and not c['bad'] and c['n'] >= 5, (L, c))
    # Keyboard: Tab from Step 4's Table button passes the findings' Method link and reaches About's button; Enter opens the existing drawer, its slides and lightbox.
    pg.evaluate("document.querySelector('[data-k=tmove]').focus({preventScroll:true})"); pg.keyboard.press('Tab'); pg.wait_for_timeout(80)
    ok(f'{tag}: Tab from Step 4 reaches the findings’ Method & sources link', pg.evaluate("() => document.activeElement.dataset.k") == 'cabout')
    pg.keyboard.press('Tab'); pg.wait_for_timeout(80)
    y = pg.evaluate('scrollY'); s = pg.evaluate(END)
    ok(f'{tag}: …then the About section’s View-slides button, on screen', pg.evaluate("() => { const e = document.activeElement, r = e.getBoundingClientRect(); return e.dataset.k === 'erp' && r.top >= document.querySelector('.k-head').offsetHeight && r.bottom <= innerHeight; }"))
    ok(f'{tag}: focus is on the View-slides button', pg.evaluate("() => document.activeElement.dataset.k") == 'erp')
    pg.keyboard.press('Enter'); pg.wait_for_timeout(120)
    d = pg.evaluate("() => { const d = document.querySelector('#k-rp'), i = d.querySelector('.k-slide img'), r = d.getBoundingClientRect(); return {open: d.open, focus: document.activeElement.dataset.k, label: document.getElementById(d.getAttribute('aria-labelledby')).textContent, kick: d.querySelector('.k-rail-kick').textContent, n: d.querySelector('.k-gnav').textContent, thumb: i.getAttribute('src'), fits: r.left >= 0 && r.right <= innerWidth && r.bottom <= innerHeight + 1, dl: d.querySelector('a.k-dl').getAttribute('href')}; }")
    ok(f'{tag}: Enter opens the existing report drawer: focus on Close, Brandenburg case study, slide 1 / 4, same download', d['open'] and d['focus'] == 'dclose' and 'Brandenburg' in d['kick'] and '1 / 4' in d['n']
       and d['thumb'] == 'assets/power-bi-1-thumb.webp' and d['fits'] and d['dl'] == DL, d)
    pg.wait_for_function("() => document.querySelector('#k-rp .k-slide img').naturalWidth > 0", timeout=5000)
    pg.keyboard.press('Tab'); pg.keyboard.press('Enter'); pg.wait_for_timeout(80)
    pg.wait_for_function("() => document.querySelector('#k-lb').open && document.querySelector('#k-lb img').complete && document.querySelector('#k-lb img').naturalWidth > 0", timeout=8000)
    lb = pg.evaluate("() => [document.querySelector('#k-lb img').getAttribute('src'), document.querySelector('#k-lb img').naturalWidth, document.activeElement.dataset.act, document.querySelector('#k-lb').getAttribute('aria-label')]")
    ok(f'{tag}: the slide opens the full-size screenshot in the lightbox (image loaded, focus on Close)', lb[0] == 'assets/power-bi-1.png' and lb[1] == 2466 and lb[2] == 'close' and 'Brandenburg' in lb[3], lb)
    pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(40)
    ok(f'{tag}: lightbox arrow keys step through the four screenshots', pg.locator('#k-lb img').get_attribute('src') == 'assets/power-bi-2.png')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(60)
    ok(f'{tag}: Escape closes the lightbox back to the drawer slide', pg.evaluate("() => [document.querySelector('#k-lb').open, document.querySelector('#k-rp').open, document.activeElement.dataset.k]") == [False, True, 'ds'])
    pg.keyboard.press('Escape'); pg.wait_for_timeout(80)
    ok(f'{tag}: Escape closes the drawer; focus returns to View the slides and the page has not moved', pg.evaluate("() => [document.querySelector('#k-rp').open, document.activeElement.dataset.k, scrollY]") == [False, 'erp', y])
    # Mouse: the button opens the drawer too, and its Close button returns focus the same way.
    pg.click('#about .v3-end-open'); pg.wait_for_timeout(80); pg.click('#k-rp [data-k=dclose]'); pg.wait_for_timeout(80)
    ok(f'{tag}: click open, Close button: focus back on View the slides, page unmoved', pg.evaluate("() => [document.activeElement.dataset.k, scrollY]") == ['erp', y])
    pg.keyboard.press('Home'); pg.wait_for_timeout(300)
    ok(f'{tag}: Home returns to the opening, room I in view', pg.evaluate("() => [scrollY, CSMotion.room()]") == [0, 0])
    pg.click('.k-rp-btn'); pg.wait_for_timeout(60)
    ok(f'{tag}: header Report button (Brandenburg case study) still opens the same drawer', pg.evaluate("() => document.querySelector('#k-rp').open && document.activeElement.dataset.k === 'dclose' && document.querySelector('.k-rp-btn').getAttribute('aria-label').includes('Brandenburg')"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(60)
    ok(f'{tag}: …and returns focus to it', pg.evaluate("() => document.activeElement.dataset.k") == 'rpbtn')
    # Profile links: Tab reaches them after the project source link in About; the footer carrying them and Method's linked sources keep AA text.
    pg.evaluate("document.querySelector('#about a.k-gh').focus({preventScroll:true})"); seq = []
    for _ in range(2):
        pg.keyboard.press('Tab'); pg.wait_for_timeout(60); seq.append(pg.evaluate("() => document.activeElement.closest('#about') ? document.activeElement.getAttribute('href') : null"))
    ok(f'{tag}: Tab from the project source reaches LinkedIn, then the GitHub profile', seq == ['https://linkedin.com/in/patilvedant', 'https://github.com/vedantdotsh'], seq)
    pg.keyboard.press('End'); pg.wait_for_timeout(250)
    c = pg.evaluate(JS_CONTRAST.replace("'#site *'", "'.k-foot *'"), True)
    ok(f'{tag}: footer with the profile links: AA text ({c["n"]} texts)', not c['bad'] and c['n'] >= 4, c)
    pg.click('.k-foot [data-k=fabout]'); pg.wait_for_timeout(80)
    c = pg.evaluate(JS_CONTRAST.replace("'#site *'", "'#k-dt .k-dlg-body *'").replace("el.closest('dialog,", "el.closest('"), False)
    ok(f'{tag}: Method & sources, with the Oder-Spree group’s linked sources: AA text ({c["n"]} texts)', not c['bad'] and c['n'] >= 30 and pg.locator('#k-dt a[href*="gigafactories"]').count() == 1, c)
    pg.keyboard.press('Escape')
    ok(f'{tag}: no console errors', not pg._errors, pg._errors)
    ctx.close()


with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    stale(b)
    colours(b)
    for w, h, lang, motion in ((1440, 900, 'en', 'no-preference'), (1280, 720, 'de', 'no-preference'), (1180, 760, 'en', 'reduce'), (728, 1024, 'de', 'no-preference'),
                               (390, 844, 'de', 'no-preference'), (320, 640, 'en', 'no-preference'), (320, 640, 'de', 'reduce')):
        end(b, w, h, lang, motion)
    b.close()
sys.exit(R.save())
