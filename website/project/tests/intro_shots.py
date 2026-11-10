"""Intro-polish screenshots (motion on, after the 2 s entrance): 1440 EN and 1280 DE at the top, 25/50/75% of the way to Step 1's hold and at the hold;
390 and 320 at the top in both languages; the short German screens 1280x720 and 1180x700 at the top; Step 1 at its hold in both views (points, per
10,000 residents) at 1440 EN and 390 DE; one sheet each (sheet-intro-*.png, named apart from shots.py's sheets). python -B tests/intro_shots.py -> evidence/intro/shots/*.png"""
from PIL import Image
from playwright.sync_api import sync_playwright
from common import HERE, new, go, holds

ENTRANCE = 2100  # the opening's one-off entrance ends by 2.0 s

OUT = HERE / 'evidence' / 'intro' / 'shots'


def sheet(paths, name):
    ims = [Image.open(p) for p in paths]
    w, h = ims[0].size; k = 2400 / (w * 3); tw, th = int(w * k), int(h * k)
    s = Image.new('RGB', (tw * 3 + 16, th * 2 + 8), (128, 128, 128))
    for i, im in enumerate(ims):
        s.paste(im.convert('RGB').resize((tw, th)), ((i % 3) * (tw + 8), (i // 3) * (th + 8)))
    s.save(OUT.parent / f'sheet-intro-{name}.png')


with sync_playwright() as p:
    OUT.mkdir(parents=True, exist_ok=True)
    b = p.chromium.launch(channel='chrome')
    for w, h, lang in ((1440, 900, 'en'), (1280, 720, 'de')):
        ctx, pg = new(b, w, h, lang=lang); pg.wait_for_timeout(ENTRANCE); H = holds(pg); shots = []
        for name, fr in (('top', 0), ('25', .25), ('50', .5), ('75', .75), ('hold1', 1)):
            go(pg, round(H[0] * fr)); pg.wait_for_timeout(80); f = OUT / f'{w}-{lang}-{name}.png'; pg.screenshot(path=str(f)); shots.append(f)
        sheet(shots, f'{w}-{lang}')
        ctx.close()
    for w, h in ((390, 844), (320, 640)):
        for lang in ('en', 'de'):
            ctx, pg = new(b, w, h, lang=lang); pg.wait_for_timeout(ENTRANCE)
            pg.screenshot(path=str(OUT / f'{w}-{lang}-top.png'))
            ctx.close()
    ims = [Image.open(OUT / f'{w}-{lang}-top.png').convert('RGB') for w in (390, 320) for lang in ('en', 'de')]
    s = Image.new('RGB', (sum(i.size[0] for i in ims) + 24, max(i.size[1] for i in ims)), (128, 128, 128)); x = 0
    for im in ims:
        s.paste(im, (x, 0)); x += im.size[0] + 8
    s.save(OUT.parent / 'sheet-intro-mobile-top.png')

    def row(paths, name):
        ims = [Image.open(f).convert('RGB') for f in paths]; k = 900 / max(i.size[1] for i in ims); ims = [i.resize((round(i.size[0] * k), round(i.size[1] * k))) for i in ims]
        s = Image.new('RGB', (sum(i.size[0] for i in ims) + 8 * (len(ims) - 1), 900), (128, 128, 128)); x = 0
        for im in ims:
            s.paste(im, (x, 0)); x += im.size[0] + 8
        s.save(OUT.parent / f'sheet-intro-{name}.png')
    short = []
    for w, h in ((1280, 720), (1180, 700)):
        ctx, pg = new(b, w, h, lang='de'); pg.wait_for_timeout(ENTRANCE); f = OUT / f'{w}x{h}-de-top.png'; pg.screenshot(path=str(f)); short.append(f); ctx.close()
    row(short, 'short-de-top')
    phone = []
    for lang in ('en', 'de'):
        ctx, pg = new(b, 390, 844, lang=lang); pg.wait_for_timeout(ENTRANCE); H = holds(pg)
        for name, fr in (('exit', .35), ('50', .5)):
            go(pg, round(H[0] * fr)); f = OUT / f'390-{lang}-{name}.png'; pg.screenshot(path=str(f)); phone.append(f)
        ctx.close()
    row(phone, 'mobile-transition')

    step1 = []
    for w, h, lang in ((1440, 900, 'en'), (390, 844, 'de'), (320, 640, 'de')):
        ctx, pg = new(b, w, h, lang=lang); pg.wait_for_timeout(ENTRANCE); H = holds(pg)
        for mode in (('rate',) if w == 320 else ('points', 'rate')):
            if mode == 'rate':
                pg.click('#r2 [data-act=mode][data-v=rate]'); pg.wait_for_timeout(900)
            go(pg, H[0]); pg.wait_for_timeout(80); f = OUT / f'{w}-{lang}-step1-{mode}.png'; step1.append(f)
            (pg.locator('#r2 .v3-frame') if w < 600 else pg).screenshot(path=str(f))  # phones: the whole frame, all 16 rows
        ctx.close()
    row(step1, 'step1')
    b.close()
print('intro shots written to', OUT)
