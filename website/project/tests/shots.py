"""Viewport screenshots (motion on, Graphite dark) at load, mid-zoom, every step hold and between holds, the findings and About sections,
Explore (End) and the drawer, plus reduced-motion full pages; one contact sheet per configuration. Then the About section, the drawer opened
from it and its lightbox at 1440 EN, 390 DE and 320 DE, as sheet-end-*.png (one per width: the sheet scales every tile to the first).
python -B tests/shots.py -> evidence/shots/*.png, evidence/sheet-*.png"""
from PIL import Image
from playwright.sync_api import sync_playwright
from common import EVID, new, go, holds

OUT = EVID / 'shots'
CONFIGS = [(1440, 900, 'en', True), (1280, 720, 'de', False), (728, 1024, 'de', False), (390, 844, 'de', True), (390, 844, 'en', False), (320, 640, 'de', False), (320, 640, 'en', False)]


def sheet(paths, name, cols):
    ims = [Image.open(p) for p in paths]
    w, h = ims[0].size; k = min(1, 2400 / (w * cols)); tw, th = int(w * k), int(h * k)
    rows = (len(ims) + cols - 1) // cols
    s = Image.new('RGB', (tw * cols + 8 * (cols - 1), th * rows + 8 * (rows - 1)), (128, 128, 128))
    for i, im in enumerate(ims):
        s.paste(im.convert('RGB').resize((tw, th)), ((i % cols) * (tw + 8), (i // cols) * (th + 8)))
    s.save(EVID / f'sheet-{name}.png')


with sync_playwright() as p:
    OUT.mkdir(parents=True, exist_ok=True)
    b = p.chromium.launch(channel='chrome')
    for w, h, lang, full in CONFIGS:
        tag = f'{w}-{lang}'
        ctx, pg = new(b, w, h, lang=lang); pg.wait_for_timeout(2100)  # the hero's one-off entrance (under 2 s) has finished
        H = holds(pg); shots = []
        phases = [('p0', 0), ('z40', round(H[0] * .4))]
        for i, y in enumerate(H):
            if full and i:
                phases.append((f'm{i}{i + 1}', round(H[i - 1] + (H[i] - H[i - 1]) * .55)))
            phases.append((f'h{i + 1}', y))
        for q in ('findings', 'about', 'explore'):
            phases.append((q, pg.evaluate(f"() => {{ let y = 0; for (let e = document.querySelector('#{q}'); e; e = e.offsetParent) y += e.offsetTop; return y - document.querySelector('.k-head').offsetHeight; }}")))
        for name, y in phases:
            go(pg, y); pg.wait_for_timeout(60); f = OUT / f'{tag}-{name}.png'; pg.screenshot(path=str(f)); shots.append(f)
        pg.keyboard.press('End'); pg.wait_for_timeout(250); f = OUT / f'{tag}-end.png'; pg.screenshot(path=str(f)); shots.append(f)
        go(pg, H[2]); pg.click('.k-rp-btn'); pg.wait_for_timeout(120); f = OUT / f'{tag}-drawer.png'; pg.screenshot(path=str(f)); shots.append(f); pg.keyboard.press('Escape')
        sheet(shots, tag, 6 if w < 800 else 4)
        ctx.close()
    for w, lang in ((1440, 'en'), (390, 'de')):
        ctx, pg = new(b, w, 900, motion='reduce', lang=lang)
        pg.screenshot(path=str(OUT / f'reduced-{w}-{lang}-full.png'), full_page=True)
        ctx.close()
    for w, h, lang in ((1440, 900, 'en'), (390, 844, 'de'), (320, 640, 'de')):
        ctx, pg = new(b, w, h, lang=lang); shots = []
        pg.keyboard.press('End'); pg.wait_for_timeout(250)
        pg.evaluate("document.querySelector('[data-k=tmove]').focus({preventScroll:true})"); pg.keyboard.press('Tab'); pg.keyboard.press('Tab'); pg.wait_for_timeout(120)
        f = OUT / f'end-{w}-{lang}-focus.png'; pg.screenshot(path=str(f)); shots.append(f)
        pg.keyboard.press('Enter'); pg.wait_for_function("() => document.querySelector('#k-rp .k-slide img').naturalWidth > 0"); pg.wait_for_timeout(120)
        f = OUT / f'end-{w}-{lang}-drawer.png'; pg.screenshot(path=str(f)); shots.append(f)
        pg.keyboard.press('Tab'); pg.keyboard.press('Enter'); pg.wait_for_function("() => document.querySelector('#k-lb img').naturalWidth > 0"); pg.wait_for_timeout(120)
        f = OUT / f'end-{w}-{lang}-lightbox.png'; pg.screenshot(path=str(f)); shots.append(f)
        pg.keyboard.press('Escape'); pg.keyboard.press('Escape'); pg.wait_for_timeout(120)
        f = OUT / f'end-{w}-{lang}-returned.png'; pg.screenshot(path=str(f)); shots.append(f)
        ctx.close()
        sheet(shots, f'end-{w}-{lang}', 4)
    b.close()
print('shots written to', OUT)
