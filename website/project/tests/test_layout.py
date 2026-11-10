"""Layouts at 320/390/728/1440 × EN/DE in the one appearance, Graphite dark (reduced motion: the static, fully drawn page); each step's heading
above its frame and its foot below; the findings and About sections; the story rail versus the in-flow story, the report drawer at every width, accessible names, dialogs returning focus without moving the page.
python -B tests/test_layout.py -> evidence/layout.json"""
import sys
from playwright.sync_api import sync_playwright
from common import Results, new, JS_LAYOUT, JS_CONTRAST

R = Results('layout')
ok = R.ok
NAMES = r'''() => { const bad = [];
 for (const el of document.querySelectorAll('#site button, #site a[href], #site select, #site [role=button]')) {
  if (el.closest('[hidden]') || !el.getClientRects().length) continue;
  const lab = el.getAttribute('aria-label') || (el.labels && el.labels[0] && el.labels[0].textContent) || el.textContent;
  if (!lab || !lab.trim()) bad.push(el.outerHTML.slice(0, 80)); }
 for (const g of document.querySelectorAll('#site [role=group]')) if (!g.getAttribute('aria-label') && !g.closest('[hidden]')) bad.push('group ' + g.className);
 for (const s of document.querySelectorAll('#site svg[role=img]')) if (!s.getAttribute('aria-label')) bad.push('svg ' + s.parentElement.dataset.r);
 return bad; }'''
STEPS = r'''() => [...document.querySelectorAll('.v3-step')].map(s => { const k = [...s.children].filter(c => !c.matches('.v3-thread')), l = s.querySelector('.v3-label'), f = s.querySelector('.v3-frame'), o = s.querySelector('.v3-foot');
 const L = l.getBoundingClientRect(), F = f.getBoundingClientRect(), O = o.getBoundingClientRect();
 return k[0] === l && k[1] === f && k[2] === o && l.children[0].matches('.v3-room-no') && l.children[1].tagName === 'H2' && l.children[2].tagName === 'P' && L.bottom <= F.top && F.bottom <= O.top && !!o.querySelector('[data-act=table]'); })'''
FIT = r'''() => { const bad = []; let n = 0; for (const e of document.querySelectorAll('#findings, #about')) { n++; const r = e.getBoundingClientRect(); if (r.left < 0 || r.right > innerWidth) bad.push(e.id);
  for (const t of e.querySelectorAll('*')) { const q = t.getBoundingClientRect(); if (q.width && (q.left < -.5 || q.right > innerWidth + .5 || t.scrollWidth > t.clientWidth + 1 && getComputedStyle(t).overflow !== 'visible')) bad.push(e.id + ' ' + t.tagName + ' ' + t.textContent.slice(0, 30)); } }
 return {n, bad}; }'''
RAIL = r'''() => { const r = document.querySelector('.k-rail'), b = r.getBoundingClientRect(), btn = document.querySelector('.k-rp-btn');
 const hit = [...document.querySelectorAll('.v3-frame, .v3-label, .v3-foot, .v3-copy, .v3-end, .v3-xs, .v3-chart text')].filter(e => { const q = e.getBoundingClientRect(); return q.width && q.right > b.left && q.left < b.right && q.bottom > b.top && q.top < b.bottom; }).length;
 const inl = [...document.querySelectorAll('.v3-story')].filter(e => getComputedStyle(e).display !== 'none' && e.textContent.trim()).length;
 return {shown: getComputedStyle(r).display !== 'none', btn: getComputedStyle(btn).display !== 'none', inline: inl, hit, fits: b.bottom <= innerHeight + 1, right: b.right, W: innerWidth}; }'''


def matrix(b):
    for w in (320, 390, 728, 1440):
        for lang in ('en', 'de'):
            tag = f'{w} {lang}'
            ctx, pg = new(b, w, 900, motion='reduce', lang=lang)
            L = pg.evaluate(JS_LAYOUT, False)
            ok(f'{tag}: no horizontal overflow', L['sw'] <= L['W'] and not L['off'], L)
            ok(f'{tag}: no chart label collisions', not L['over'], L['over'])
            c = pg.evaluate(JS_CONTRAST, False)
            ok(f'{tag}: text contrast AA ({c["n"]} texts)', not c['bad'] and c['n'] > 100, c['bad'])
            hole = pg.evaluate("() => { const s = document.querySelector('[data-r=ring] svg'), k = s.getBoundingClientRect().width / s.viewBox.baseVal.width, r = +s.dataset.hole * k; const c = [...s.querySelectorAll('.sb-ctr text')].map(t => t.getBoundingClientRect()); const o = s.querySelector('.sb-big').getBoundingClientRect(), cx = o.left + o.width / 2, cy = o.bottom; return c.every(b => Math.hypot(Math.max(Math.abs(b.left - cx), Math.abs(b.right - cx)), Math.max(Math.abs(b.top - cy), Math.abs(b.bottom - cy)) - 6) <= r) ; }")
            ok(f'{tag}: ring centre text stays inside the hole', hole)
            ok(f'{tag}: controls, groups and charts have accessible names', not pg.evaluate(NAMES), pg.evaluate(NAMES))
            ok(f'{tag}: reduced motion: no camera, connectors or network drawn', pg.evaluate("() => !document.documentElement.classList.contains('v3-motion') && [...document.querySelectorAll('.v3-thread,.v3-spokes')].every(e => getComputedStyle(e).display === 'none') && [...document.querySelectorAll('.v3-frame')].every(f => !f.style.transform)"))
            r = pg.evaluate(RAIL)
            ok(f'{tag}: story rail on wide screens, the same story under all 4 step frames otherwise; Report button at every width', (r['shown'], r['inline'], r['btn']) == ((True, 0, True) if w >= 1180 else (False, 4, True)), r)
            order = pg.evaluate(STEPS)
            ok(f'{tag}: each of the 4 steps reads kicker, takeaway, why, then its frame, then its foot with the Table button', len(order) == 4 and all(order), order)
            fit = pg.evaluate(FIT)
            ok(f'{tag}: findings and About sections fit the width, text unclipped', fit['n'] == 2 and not fit['bad'], fit)
            if w == 320 and lang == 'de':
                seg = pg.evaluate("() => { const f = document.querySelector('#r7 .v3-frame').getBoundingClientRect(); return [...document.querySelectorAll('#r7 .v3-seg button')].map(b => { const r = b.getBoundingClientRect(); return [r.left >= f.left - .5, r.right <= f.right + .5, b.scrollWidth <= b.clientWidth + 1]; }).flat(); }")
                ok(f'{tag}: German scenario buttons wrap inside the frame', all(seg), seg)
                pg.click('#r7 [data-act=scen][data-v="1"]')
                ok(f'{tag}: hypothetical readout fits at 320', pg.evaluate("() => { const e = document.querySelector('[data-r=osline]'); return e.scrollWidth <= e.clientWidth + 1; }"))
                pg.select_option('select[data-k=d5]', '12063')
                ok(f'{tag}: Step 3 legend and selection line wrap inside the frame at 320', pg.evaluate("() => { const f = document.querySelector('#r7 .v3-frame').getBoundingClientRect(); return [...document.querySelectorAll('#r7 :is(.v3-legend,[data-r=ro7])')].every(e => { const r = e.getBoundingClientRect(); return e.textContent && r.left >= f.left - .5 && r.right <= f.right + .5 && e.scrollWidth <= e.clientWidth + 1; }); }"))
                pg.select_option('select[data-k=d5]', '')
            pg.click('.k-menu-btn')
            c = pg.evaluate(JS_CONTRAST.replace("'#site *'", "'#k-pop *'"), False)
            ok(f'{tag}: settings menu (language, Method & sources): text contrast AA', not c['bad'] and c['n'] >= 3, c)
            ok(f'{tag}: no console errors', not pg._errors, pg._errors)
            ctx.close()


def rail_and_dialogs(b):
    # Wide: the story rail sits beside the gallery, never over a frame, label or chart text, at every hold, and fits the screen.
    for w, h in ((1440, 900), (1280, 720), (1180, 720)):
        ctx, pg = new(b, w, h)
        H = pg.evaluate('CSMotion.holds()'); hits = []
        for y in [0] + H:
            pg.evaluate(f'scrollTo(0,{y})'); pg.wait_for_timeout(60); r = pg.evaluate(RAIL); hits.append((y, r['hit'], r['fits']))
        ok(f'{w}x{h}: story rail never overlaps rooms or chart labels and fits the viewport', all(x[1] == 0 and x[2] for x in hits), hits)
        ok(f'{w}: the rail holds the story, not the Brandenburg slides', pg.locator('.k-rail .k-slide, .k-rail .k-dl').count() == 0 and pg.locator('.k-rail h2#k-rail-h').count() == 1)
        ctx.close()
    # The report is the same labelled drawer at every width, with the slides and lightbox inside; focus goes in and comes back, the page never moves.
    for w, h in ((1440, 900), (1280, 720), (1180, 720), (390, 844), (728, 1024), (320, 640)):
        ctx, pg = new(b, w, h)
        H = pg.evaluate('CSMotion.holds()'); y = H[2]; pg.evaluate(f'scrollTo(0,{y})'); pg.wait_for_timeout(80)
        pg.click('.k-rp-btn')
        d = pg.evaluate("() => { const d = document.querySelector('#k-rp'), r = d.getBoundingClientRect(); return {open: d.open, focus: document.activeElement.dataset.k, fits: r.left >= 0 && r.right <= innerWidth && r.bottom <= innerHeight + 1, label: document.getElementById(d.getAttribute('aria-labelledby')).textContent, slides: d.querySelector('.k-gnav').textContent.includes('/ 4'), dl: !!d.querySelector('a.k-dl')}; }")
        ok(f'{w}: Report opens a labelled drawer, focus on Close, fits, slides and download inside', d['open'] and d['focus'] == 'dclose' and d['fits'] and d['label'] and d['slides'] and d['dl'], d)
        pg.click('#k-rp [data-act=gstep][data-v="1"]')
        ok(f'{w}: drawer slide step keeps focus', pg.evaluate("() => document.activeElement.dataset.k") == 'dn' and '2 / 4' in pg.locator('#k-rp .k-gnav').inner_text())
        pg.click('#k-rp .k-slide'); pg.wait_for_timeout(50)
        st = pg.evaluate("() => ({open: document.querySelector('#k-lb').open && document.querySelector('#k-rp').open, img: document.querySelector('#k-lb img').getAttribute('src'), focus: document.activeElement.dataset.act})")
        ok(f'{w}: lightbox opens over the drawer at full size with focus on Close', st == {'open': True, 'img': 'assets/power-bi-2.png', 'focus': 'close'}, st)
        pg.keyboard.press('ArrowRight')
        ok(f'{w}: lightbox arrow keys step slides', pg.locator('#k-lb img').get_attribute('src') == 'assets/power-bi-3.png')
        ok(f'{w}: Report button names the Brandenburg case study (not a national report) and the drawer has download and source links',
           'Brandenburg' in pg.locator('.k-rp-btn').get_attribute('aria-label') and pg.locator('#k-rp a.k-dl[href$="ChargeScope-PowerBI-source.zip"]').count() == 1 and pg.locator('#k-rp a.k-gh').count() == 1)
        pg.keyboard.press('Escape'); pg.wait_for_timeout(50)
        ok(f'{w}: lightbox closes back to the drawer slide', pg.evaluate("() => document.activeElement.dataset.k") == 'ds')
        pg.keyboard.press('Escape'); pg.wait_for_timeout(80)
        ok(f'{w}: drawer closes back to the Report button, page unmoved', pg.evaluate("() => [document.activeElement.dataset.k, scrollY]") == ['rpbtn', y])
        # A table dialog opened from a room label: focus returns to that button and the page stays.
        pg.evaluate(f'scrollTo(0,{H[1]})'); pg.wait_for_timeout(80)
        pg.locator('#r2 [data-act=table]').scroll_into_view_if_needed(); y2 = pg.evaluate('scrollY'); pg.wait_for_timeout(80)
        pg.click('#r2 [data-act=table]'); pg.keyboard.press('Escape'); pg.wait_for_timeout(80)
        ok(f'{w}: table dialog returns focus to its button without scrolling', pg.evaluate("() => [document.activeElement.dataset.k, scrollY]") == ['tstate', y2])
        pg.click('.k-menu-btn'); pg.click('[data-k=mabout]')
        ok(f'{w}: Method & sources reachable from the settings menu', pg.evaluate("() => document.querySelector('#k-dt').open && document.querySelector('#k-dt-h').textContent.length > 0"))
        pg.keyboard.press('Escape'); pg.wait_for_timeout(80)
        ok(f'{w}: …and returns focus to the menu without scrolling', pg.evaluate("() => scrollY === " + str(y2) + " && document.activeElement.matches('.k-menu-btn')"))
        pg.keyboard.press('Tab'); pg.wait_for_timeout(80)
        ok(f'{w}: next Tab continues without restarting at top', pg.evaluate("() => scrollY > 0 && !document.activeElement.matches('.k-skip')"))
        ok(f'{w}: no console errors', not pg._errors, pg._errors)
        ctx.close()
    # Graphite dark is the only appearance, also when the system prefers light.
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, color_scheme='light'); pg = ctx.new_page(); from common import URL; pg.goto(URL); pg.wait_for_timeout(150)
    ok('a light system preference still renders Graphite dark', pg.evaluate("() => [getComputedStyle(document.body).backgroundColor, getComputedStyle(document.documentElement).colorScheme]") == ['rgb(23, 23, 23)', 'dark'])
    ctx.close()


with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    matrix(b)
    rail_and_dialogs(b)
    b.close()
sys.exit(R.save())
