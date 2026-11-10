"""What the page shows equals payload math, in EN and DE, driven through real clicks and selects. Headless Chrome on file://.
python -B tests/test_display.py -> evidence/display.json"""
import re, sys
from playwright.sync_api import sync_playwright
from common import P, G, ST, DI, BB, Results, fmt, pct, rank, new, text

R = Results('display')
ok = R.ok
by = lambda c: next(s for s in ST if s['code'] == c)
dis = lambda c: next(d for d in DI if d['code'] == c)
DUP = {d['name'] for d in DI if sum(e['name'] == d['name'] for e in DI) > 1}
KIND = {'en': {'city': 'city', 'county': 'county'}, 'de': {'city': 'Stadt', 'county': 'Landkreis'}}
nm = lambda d, lang: f"{d['name']} ({KIND[lang][d['kind']]})" if d['name'] in DUP else d['name']  # duplicated names carry their kind


def rows(pg, sel):
    return pg.evaluate(f"""() => [...document.querySelectorAll('{sel} .k-row')].sort((a,b)=>a.style.getPropertyValue('--i')-b.style.getPropertyValue('--i')).map(r=>[r.querySelector('.k-name').textContent,r.querySelector('.k-val').textContent])""")


def run(b, lang, w):
    tag = f'{lang} {w}'
    ctx, pg = new(b, w, 900, motion='reduce', lang=lang)
    L = lambda v, d=0: fmt(v, d, lang)
    ok(f'{tag}: html lang and Graphite dark on load', pg.evaluate("() => [document.documentElement.lang, getComputedStyle(document.body).backgroundColor, getComputedStyle(document.documentElement).colorScheme]") == [lang, 'rgb(23, 23, 23)', 'dark'])
    ok(f'{tag}: no retired variant links or switcher', pg.locator('a[href^="../v"],a[href^="/v"],a[href^="v1"],a[href^="v2"],a[href^="v3"],.k-vars').count() == 0)
    h1 = text(pg, 'h1')
    ok(f'{tag}: question heading, no Brandenburg-only headline', h1.endswith('?') and 'Brandenburg' not in h1, h1)
    hero = text(pg, '.v3-hero'); osd = dis('12067')
    motto = {'en': 'Explore public charging infrastructure. Compare regions. Understand the evidence.', 'de': 'Öffentliche Ladeinfrastruktur erkunden. Regionen vergleichen. Die Belege verstehen.'}[lang]
    # The plan retires the motto and moves "pilot" to Method; the hero now carries the national finding (Germany-wide ranks).
    ok(f'{tag}: national finding, total points and both dates in the hero; motto and pilot status gone', motto not in hero and L(G['points']) in hero and '2026' in hero and '2025' in hero and 'pilot' not in hero.lower()
       and f" {osd['rankGermany']} " in hero and f" {osd['rankWithoutTopGroup']}" in hero and ' 400 ' in hero, hero)
    # I · rings
    ok(f'{tag}: I · 16 state arcs, 400 district arcs, one hatched unattributed gap', [pg.locator(s).count() for s in ('.sb-s', '.sb-d', '.sb-gap')] == [16, 400, 1])
    titles = pg.evaluate("() => [...document.querySelectorAll('.sb-d title')].map(t => t.textContent)")
    ok(f'{tag}: I · each district arc is titled with its own points', titles == [f"{nm(d, lang)} ({s['name']}): {L(d['points'])}" for s in ST for d in DI if d['state'] == s['code']], titles[:2])
    ro = text(pg, '[data-r=ro1]')
    ok(f'{tag}: I · Germany readout', all(x in ro for x in (L(G['points']), L(G['installations']), L(G['nominalMw']))), ro)
    pg.select_option('select[data-k=s1]', '06'); he = by('06'); ro = text(pg, '[data-r=ro1]')
    ok(f'{tag}: I · Hessen readout with share and the 249 unmatched points', all(x in ro for x in (L(he['points']), pct(he['points'] / G['points'], 1, lang), L(he['districtUnattributedPoints']))), ro)
    ok(f'{tag}: I · state choice is shared with room III', pg.locator('select[data-k=s3]').input_value() == '06')
    labels = pg.evaluate("() => [...document.querySelectorAll('[data-r=scatter] text.v3-lab')].map(t => t.textContent)")
    mk = next(d for d in DI if 'labelGap' in d)
    ok(f'{tag}: III · Hessen labels are its extremes, never the label-gap district', nm(mk, lang) not in labels and nm(max((d for d in DI if d['state'] == '06'), key=lambda d: d['pointsPer10kResidents']), lang) in labels, labels)
    r3 = text(pg, '[data-r=ro3]'); dr = he['districtRate']
    ok(f'{tag}: III · Hessen readout min/max/median', all(x in r3 for x in (L(dr['min'], 1), L(dr['max'], 1), L(dr['median'], 1), str(dr['n']))), r3)
    pg.select_option('select[data-k=d5]', '11000')
    picked = pg.locator('.sc-dot.is-on')
    ok(f'{tag}: III ? Berlin pick stays fully visible under Hessen highlight', picked.count() == 1 and picked.get_attribute('data-v') == '11000' and picked.evaluate("el => getComputedStyle(el).opacity") == '1')
    pg.select_option('select[data-k=d5]', '')
    pg.select_option('select[data-k=s3]', '')
    # II · counts vs rates
    pts = rows(pg, '[data-r=bars]')
    exp = sorted(ST, key=lambda s: (-s['points'], s['name']))
    ok(f'{tag}: II · points order and values', pts == [[s['name'], L(s['points'])] for s in exp], pts[:3])
    top = exp[0]; r2 = text(pg, '[data-r=st0]')
    ok(f'{tag}: II · points story: top state and its rate rank', top['name'] in r2 and str(rank(ST, 'pointsPer10kResidents', top)) in r2, r2)
    pg.click('[data-act=mode][data-m=m2][data-v=rate]')
    rt = rows(pg, '[data-r=bars]'); exp = sorted(ST, key=lambda s: (-s['pointsPer10kResidents'], s['name']))
    ok(f'{tag}: II · rate order and values after toggle', rt == [[s['name'], L(s['pointsPer10kResidents'], 1)] for s in exp], rt[:3])
    ok(f'{tag}: II · Germany reference line value', L(G['pointsPer10kResidents'], 1) in pg.locator('[data-r=bars] .k-ref').text_content())
    r2 = text(pg, '[data-r=st0]')
    ok(f'{tag}: II · rate story: top state and its points rank', exp[0]['name'] in r2 and str(rank(ST, 'points', exp[0])) in r2, r2)
    ok(f'{tag}: II · toggle aria-pressed', pg.locator('[data-m=m2][aria-pressed=true]').get_attribute('data-v') == 'rate')
    # III · scatter
    ok(f'{tag}: III · 400 dots', pg.locator('.sc-dot').count() == 400)
    r3 = text(pg, '[data-r=ro3]'); sp = G['districtRateSpread']['all']
    ok(f'{tag}: III · default readout median and middle half', all(x in r3 for x in (L(sp['median'], 1), L(sp['q1'], 1), L(sp['q3'], 1))), r3)
    # IV · mix
    hs = sorted(ST, key=lambda s: s['highPowerPointShare'])
    h4 = text(pg, '#r4')
    ok(f'{tag}: IV · lowest and highest state share from payload shown', pct(hs[0]['highPowerPointShare'], 1, lang) in h4 and pct(hs[-1]['highPowerPointShare'], 1, lang) in h4, h4[:200])
    mx = pg.evaluate("() => [...document.querySelectorAll('.mx-row')].map(r => [r.querySelector('.mx-name').textContent, r.querySelector('.mx-val').textContent, [...r.querySelectorAll('.mx-bar i')].map(i => parseFloat(i.style.width))])")
    exp = [G] + sorted(ST, key=lambda s: -s['highPowerPointShare'])
    ok(f'{tag}: IV · rows: Germany first, then states by >22 kW share, values', [m[1] for m in mx] == [pct(r['highPowerPointShare'], 1, lang) for r in exp] and [m[0] for m in mx[1:]] == [s['name'] for s in exp[1:]], mx[:2])
    ok(f'{tag}: IV · segment widths are the four class shares', all(abs(m[2][j] - r['pointsByPower'][k] / (r['points'] - r['pointsPowerUnknown']) * 100) < .006 for m, r in zip(mx, exp) for j, k in enumerate(('le22', 'gt22to149', 'gt149to299', 'gt299'))))
    # V · spread
    fl = [d for d in DI if d['flags']]
    ok(f'{tag}: V · 400 dots, flagged ones drawn as rings', pg.locator('.sp-dot').count() == 400 and pg.locator('.sp-dot.is-flag').count() == len(fl))
    ok(f'{tag}: V · flagged toggle names the count', f'({len(fl)})' in pg.locator('[data-m=m5][data-v=flag]').inner_text())
    pg.click('[data-act=mode][data-m=m5][data-v=flag]')
    ok(f'{tag}: V · flagged view dims every unflagged district', pg.locator('.sp-dot.is-dim').count() == 400 - len(fl) and pg.locator('.sp-dot.is-flag.is-dim').count() == 0)
    r5 = text(pg, '#r5 .v3-label p') + ' ' + text(pg, '[data-r=st1]') + ' ' + pg.evaluate("() => { document.querySelector('[data-m=m5][data-v=all]').click(); return document.querySelector('[data-r=st1]').textContent; }")
    pg.click('[data-act=mode][data-m=m5][data-v=flag]')
    ok(f'{tag}: V · spread (step heading and story)', all(x in r5 for x in (L(sp['min'], 1), L(sp['max'], 1), L(sp['q1'], 1), L(sp['q3'], 1), L(sp['max'] / sp['min']))), r5)
    pg.select_option('select[data-k=d5]', mk['code']); r5 = text(pg, '[data-r=ro5]')
    ok(f'{tag}: V · Main-Kinzig readout states the Hanau gap, rate by label', L(mk['labelGap']['points']) in r5 and L(mk['pointsPer10kResidents'], 1) in r5, r5)
    pg.select_option('select[data-k=d5]', '12067'); r5 = text(pg, '[data-r=ro5]')
    ok(f'{tag}: V · Oder-Spree readout: rate, rank of 400, flag', L(osd['pointsPer10kResidents'], 1) in r5 and str(osd['rankGermany']) in r5 and L(osd['points']) in r5, r5)
    ok(f'{tag}: V · picked district is shared with III and VIII', pg.locator('.sc-dot.is-on').count() == 1 and pg.locator('.sl-l.is-on').count() == 1)
    pg.select_option('select[data-k=d5]', '11000')
    ok(f'{tag}: V selected unflagged district overrides Flagged filter', pg.locator('.sp-dot.is-on').evaluate("el => getComputedStyle(el).opacity") == '1' and pg.locator('.sp-dot.is-dim').count() == 400 - len(fl) - 1)
    pg.select_option('select[data-k=d5]', '')
    # VI · composition
    ipc = G['installationsByPointCount']
    c6 = rows(pg, '[data-r=comp]')
    ok(f'{tag}: VI · installations by point count', [v[1].split(' · ')[0] for v in c6] == [L(ipc[n]) for n in '123456'], c6)
    pg.click('[data-act=mode][data-m=m6][data-v=pts]'); c6 = rows(pg, '[data-r=comp]')
    ok(f'{tag}: VI · points by installation size (n × count)', [v[1].split(' · ')[0] for v in c6] == [L(int(n) * ipc[n]) for n in '123456'], c6)
    r6 = text(pg, '[data-r=ro6]')
    ok(f'{tag}: VI · points per installation, Germany/Brandenburg/Berlin', all(L(r['pointsPerInstallation'], 2) in r6 for r in (G, by('12'), by('11'))), r6)
    ok(f'{tag}: VI · caption share of one- or two-point installations', pct((ipc['1'] + ipc['2']) / G['installations'], 0, lang) in text(pg, '#r6 .v3-x-p'))
    # VII · Brandenburg case
    o = next(d for d in BB['districts'] if d['code'] == '12067'); fg = BB['flaggedGroup']
    s7 = text(pg, '[data-r=osline]')
    ok(f'{tag}: VII · registered: rate, rank of 18, points', L(o['registered']['rate'], 1) in s7 and f" {o['registered']['rank']} " in s7 and L(o['registered']['points']) in s7, s7)
    ok(f'{tag}: VII · caption names the flagged group size', L(fg['installations']) in text(pg, '#r7 .v3-label p'))
    pg.click('[data-act=scen][data-v="1"]'); s7 = text(pg, '[data-r=osline]')
    ok(f'{tag}: VII · hypothetical: 17.8, rank 11, 319 of 832', all(x in s7 for x in (L(o['hypothetical']['rate'], 1), f" {o['hypothetical']['rank']} ", L(o['hypothetical']['points']), L(o['registered']['points']))), s7)
    ok(f'{tag}: VII · Berlin shown separately at its own rate', L(P['berlin']['registered']['rate'], 1) in pg.locator('.v3-berlin').text_content())
    # VII · selection line: empty by default; a picked Brandenburg district shows its rate and rank of 18 in the current scenario; a pick elsewhere is scoped out.
    ro7 = lambda: pg.evaluate("() => { const e = document.querySelector('[data-r=ro7]'); return [e.textContent, getComputedStyle(e).display]; }")
    e0 = ro7(); bd = next(d for d in BB['districts'] if d['code'] != '12067' and d['registered']['rank'] != d['hypothetical']['rank'])
    pg.select_option('select[data-k=d5]', bd['code']); e1 = ro7()[0]; pg.click('[data-act=scen][data-v="0"]'); e2 = ro7()[0]
    pg.select_option('select[data-k=d5]', '11000'); e3 = ro7()[0]; pg.select_option('select[data-k=d5]', ''); e4 = ro7()
    ok(f'{tag}: VII · selection line: none by default; Brandenburg pick follows the scenario; a pick outside Brandenburg is scoped out; clearing empties it',
       e0 == ['', 'none'] and all(x in e1 for x in (bd['name'], L(bd['hypothetical']['rate'], 1), f" {bd['hypothetical']['rank']} ")) and all(x in e2 for x in (bd['name'], L(bd['registered']['rate'], 1), f" {bd['registered']['rank']} "))
       and 'Berlin' in e3 and 'Brandenburg' in e3 and e4 == ['', 'none'], (e0, e1, e2, e3, e4))
    pg.click('[data-act=scen][data-v="1"]')
    pg.click('[data-act=scen][data-v="0"]')
    # VIII · national sensitivity
    for k in (20, 50):
        pg.click(f'[data-act=mode][data-m=m8][data-v="{k}"]')
        mv = [d for d in DI if abs(d['rankGermany'] - d['rankWithoutTopGroup']) >= k]; r8 = text(pg, '[data-r=st3]')
        ok(f'{tag}: VIII · {k}+ movers counted, drawn and read out; Oder-Spree ranks', pg.locator('.sl-l').count() == 400 and pg.locator('.sl-l.is-mv').count() == len(mv) and str(len(mv)) in r8 and f"{osd['rankGermany']} → {osd['rankWithoutTopGroup']}" in r8, (len(mv), r8))
    ends = pg.evaluate("() => [...document.querySelectorAll('.sl-l')].map(l => [l.querySelector('title').textContent, +l.getAttribute('y1'), +l.getAttribute('y2')])")
    name = {f"{nm(d, lang)}: {d['rankGermany']} → {d['rankWithoutTopGroup']}": d for d in DI}
    pairs = [(name[t], y1, y2) for t, y1, y2 in ends]
    a, z = min(pairs, key=lambda x: x[0]['rankGermany']), max(pairs, key=lambda x: x[0]['rankGermany'])
    k = (z[1] - a[1]) / (z[0]['rankGermany'] - a[0]['rankGermany']); y = lambda r: a[1] + (r - a[0]['rankGermany']) * k
    ok(f'{tag}: VIII · all 400 lines start and end at their two ranks on one linear scale', len(pairs) == 400 and all(abs(y1 - y(d['rankGermany'])) < .06 and abs(y2 - y(d['rankWithoutTopGroup'])) < .06 for d, y1, y2 in pairs))
    # Tables and dialog
    def table(v):
        pg.click(f'[data-act=table][data-v={v}] >> nth=0')
        t = pg.evaluate("() => { const d = document.querySelector('#k-dt'); return {open: d.open, body: [...d.querySelectorAll('tbody tr')].map(r => [...r.children].map(c => c.textContent)), foot: d.querySelector('tfoot') ? d.querySelector('tfoot').textContent : ''}; }")
        pg.keyboard.press('Escape'); return t
    t = table('state')
    ok(f'{tag}: state table: 16 rows by rate rank, Germany total', len(t['body']) == 16 and [r[0] for r in t['body']] == [s['name'] for s in sorted(ST, key=lambda s: s['rank'])] and L(G['points']) in t['foot'] and all(L(by(next(s['code'] for s in ST if s['name'] == r[0]))['points']) == r[1] for r in t['body']))
    t = table('flag')
    ok(f'{tag}: flag table lists every flagged district', sorted(r[0] for r in t['body']) == sorted(nm(d, lang) for d in fl))
    t = table('bb')
    ok(f'{tag}: Brandenburg table: 18 ranked rows, Berlin unranked in the foot', len(t['body']) == 18 and 'Berlin' in t['foot'] and t['body'][0][0] == 'Oder-Spree')
    pg.click('[data-act=mode][data-m=m8][data-v="20"]'); t = table('move')
    ok(f'{tag}: movers table equals the 20+ movers', sorted(r[0] for r in t['body']) == sorted(nm(d, lang) for d in DI if abs(d['rankGermany'] - d['rankWithoutTopGroup']) >= 20))
    pg.click('[data-k=habout]')
    ab = pg.locator('#k-dt').inner_text(); h = P['unattributedLabels'][0]
    need = [L(G['installations']), L(G['points']), L(G['nominalKw'], 1), L(G['population']), L(G['connectorTokens']), L(h['points']), L(h['installations']), L(mk['pointsPer10kResidents'], 1),
            str(sum('lowLabelCoordinateAgreement' in d['flags'] for d in DI)), L(P['statisticsContext']['points']), 'CC BY 4.0', 'dl-de/by-2.0', 'WGS84'] + [dis(a['code'])['name'] for a in P['meta']['labelMapping']['spacingAliases']]
    ok(f'{tag}: method & sources: totals, licences, Hanau, aliases, WGS84, statistics kept separate', all(x in ab for x in need), [x for x in need if x not in ab])
    ok(f'{tag}: method & sources links the JSON aggregates and SOURCES.md', pg.locator('#k-dt a[href="data/national-story.json"]').count() == 1 and pg.locator('#k-dt a[href="SOURCES.md"]').count() == 1)
    pg.keyboard.press('Escape')
    body = pg.evaluate("() => document.getElementById('main').innerText + ' ' + document.querySelector('.k-rail').textContent")
    banned = re.findall(r'\b(unmet demand|adequate|adequacy|underserved|oversupplied|ROI|return on investment|investment|optimal location|lowest provision)\b', body, re.I)
    ok(f'{tag}: canvas and story rail make no demand/adequacy/ROI claims', not banned, banned)
    ok(f'{tag}: no console errors', not pg._errors, pg._errors)
    ctx.close()


with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    for lang in ('en', 'de'):
        for w in (1440, 390):
            run(b, lang, w)
    b.close()
sys.exit(R.save())
