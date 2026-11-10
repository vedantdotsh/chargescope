"""Payload math behind every claim the site shows, recomputed from national-story.json (no hard-coded approximations),
plus package integrity. python -B tests/test_data.py -> evidence/data.json"""
import hashlib, json, sys
from collections import Counter
from decimal import Decimal
from fractions import Fraction
from common import HERE, PAYLOAD, DIST, P, G, ST, DI, BB, Results, rank

R = Results('data')
ok = R.ok
dec = lambda x: Decimal(str(x))

# Conservation: states → Germany; districts + unattributed → state.
for k in ('installations', 'points', 'population'):
    ok(f'states sum to Germany: {k}', sum(s[k] for s in ST) == G[k], (sum(s[k] for s in ST), G[k]))
ok('states sum to Germany: nominal kW (exact decimal)', sum(dec(s['nominalKw']) for s in ST) == dec(G['nominalKw']))
for s in ST:
    kids = [d for d in DI if d['state'] == s['code']]
    good = (len(kids) == s['districts'] and sum(d['points'] for d in kids) + s['districtUnattributedPoints'] == s['points']
            and sum(d['installations'] for d in kids) + s['districtUnattributedInstallations'] == s['installations'] and sum(d['population'] for d in kids) == s['population'])
    ok(f'{s["name"]}: districts + unattributed = state', good)
ok('400 districts, 400 unique codes, 16 states', len(DI) == 400 == len({d['code'] for d in DI}) and len(ST) == 16)
ok('point classes sum to points (Germany, every state, every district)', all(sum(r['pointsByPower'].values()) + r['pointsPowerUnknown'] == r['points'] for r in [G, *ST, *DI]))
ipc = G['installationsByPointCount']
ok('installations by point count: Σ count = installations, Σ n×count = points', sum(ipc.values()) == G['installations'] and sum(int(n) * c for n, c in ipc.items()) == G['points'])
ok('connector entries exceed points (shown only as "connectors are not points")', G['connectorTokens'] > G['points'])
ok('payload status stays a diagnostic pilot', P['meta']['status'] == 'DIAGNOSTIC_PILOT' and P['meta']['validatedReleaseEligible'] is False)
ok('dates: register 2026-09-01, population 2025-12-31', P['meta']['charging']['snapshotDate'] == '2026-09-01' and P['meta']['population']['referenceDate'] == '2025-12-31')

# Rates and ranks the site prints, recomputed as ratios of sums and competition ranks.
for r in [G, *ST, *DI]:
    if abs(r['points'] / r['population'] * 10000 - r['pointsPer10kResidents']) > 1e-9:
        ok(f'rate {r.get("name", "Germany")}', False); break
else:
    ok('every rate = points / residents × 10,000', True)
ok('state ranks are competition ranks among 16 by rate', all(s['rank'] == rank(ST, 'pointsPer10kResidents', s) for s in ST))
ok('district ranks are competition ranks among 400', all(d['rankGermany'] == rank(DI, 'pointsPer10kResidents', d) for d in DI))
ok('rank with groups set aside = rank among all 400 after each district loses its own largest group',
   all(d['rankWithoutTopGroup'] == rank(DI, 'pointsPer10kWithoutTopGroup', d) and d['pointsWithoutTopGroup'] == d['points'] - d['topGroup']['points'] for d in DI))
top_pts, top_rate = max(ST, key=lambda s: s['points']), max(ST, key=lambda s: s['pointsPer10kResidents'])
ok('room II: the state with most points is not the highest-rate state', top_pts['code'] != top_rate['code'], (top_pts['name'], top_rate['name']))
hp = sorted(s['highPowerPointShare'] for s in ST)
ok('room IV: >22 kW share = points above 22 kW / points with known power', all(abs((r['points'] - r['pointsByPower']['le22'] - r['pointsPowerUnknown']) / (r['points'] - r['pointsPowerUnknown']) - r['highPowerPointShare']) < 1e-12 for r in [G, *ST]))
sp = G['districtRateSpread']['all']
rates = sorted(d['pointsPer10kResidents'] for d in DI)
q = lambda p: (lambda pos: rates[int(pos)] + (rates[min(int(pos) + 1, 399)] - rates[int(pos)]) * (pos - int(pos)))(399 * p)
ok('room V: spread min/max/q1/median/q3 recomputed (type 7)', all(abs(a - b) < 1e-9 for a, b in ((sp['min'], rates[0]), (sp['max'], rates[-1]), (sp['q1'], q(.25)), (sp['median'], q(.5)), (sp['q3'], q(.75)))))
flagged = [d for d in DI if d['flags']]
fr = P['meta']['flagRules']
recomputed = sum(1 for d in DI if (d['geo']['agreeShare'] is not None and d['geo']['agreeShare'] < .95) or d['topGroup']['pointShare'] >= .2 or d['points'] < 100 or 'labelGap' in d)
ok('room V: flags recomputed from payload thresholds', recomputed == len(flagged), (recomputed, len(flagged)))
ok('flag counts by kind', Counter(f for d in DI for f in d['flags']) == Counter({'smallPointCount': sum(d['points'] < 100 for d in DI), 'lowLabelCoordinateAgreement': sum(d['geo']['agreeShare'] < .95 for d in DI),
   'concentratedCoLocation': sum(d['topGroup']['pointShare'] >= .2 for d in DI), 'labelGap': sum('labelGap' in d for d in DI)}))
two = ipc['1'] + ipc['2']
ok('room VI: one- or two-point installations share', two / G['installations'] > .95, two / G['installations'])
ok('room VI: points per installation (Germany, Brandenburg, Berlin) are ratios of sums', all(abs(r['points'] / r['installations'] - r['pointsPerInstallation']) < 1e-12 for r in [G, *ST]))

# Room VII: Brandenburg case, ranks among 18 only, Berlin outside.
bb = BB['districts']
for sc in ('registered', 'hypothetical'):
    ok(f'Brandenburg {sc}: ranks among 18 recomputed', all(d[sc]['rank'] == 1 + sum(o[sc]['rate'] > d[sc]['rate'] for o in bb) for d in bb))
os_ = next(d for d in bb if d['code'] == '12067')
fg = BB['flaggedGroup']
ok('Oder-Spree registered − flagged group = hypothetical (points, kW, installations)', os_['registered']['points'] - fg['points'] == os_['hypothetical']['points'] and dec(os_['registered']['kw']) - dec(fg['nominalKw']) == dec(os_['hypothetical']['kw']) and os_['registered']['installations'] - fg['installations'] == os_['hypothetical']['installations'])
ok('only Oder-Spree changes between scenarios', all(d['registered'] == {**d['hypothetical'], 'rank': d['registered']['rank']} or d['code'] == '12067' for d in bb if d['code'] != '12067')
   and all(d['registered']['points'] == d['hypothetical']['points'] for d in bb if d['code'] != '12067'))
ok('flagged group: single-point installations of equal kW', fg['points'] == fg['installations'] and dec(fg['nominalKw']) / fg['installations'] == dec(fg['nominalKw'] / fg['installations']))
bbs = next(s for s in ST if s['code'] == '12')
ok('Brandenburg case totals equal the national Brandenburg state row', BB['totals']['registered']['points'] == bbs['points'] and BB['totals']['registered']['population'] == bbs['population'])
ok('Berlin context equals national Berlin row and is not among the 18', P['berlin']['registered']['points'] == next(s for s in ST if s['code'] == '11')['points'] and all(d['code'] != '11000' for d in bb))
osn = next(d for d in DI if d['code'] == '12067')
ok('Oder-Spree national top group is the same 513-point flagged group', osn['topGroup']['points'] == fg['points'] and osn['pointsWithoutTopGroup'] == os_['hypothetical']['points'])

# Hanau and Main-Kinzig: unattributed, not reassigned, never an extreme call-out.
h = P['unattributedLabels'][0]
mk = next(d for d in DI if 'labelGap' in d)
he = [d for d in DI if d['state'] == h['state']]
ok('Hanau points are in Hessen only, in no district', next(s for s in ST if s['code'] == h['state'])['districtUnattributedPoints'] == h['points'] == P['meta']['unattributedPoints'])
ok('Main-Kinzig carries the label gap; its own rate excludes the Hanau points', mk['labelGap']['points'] == h['points'] and mk['pointsPer10kResidents'] == mk['points'] / mk['population'] * 10000 and list(h['coordinateCandidateDistricts']) == [mk['code']])
ok('Main-Kinzig is neither Hessen extreme nor a national extreme (site never labels it)', mk['code'] not in (min(he, key=lambda d: d['pointsPer10kResidents'])['code'], max(he, key=lambda d: d['pointsPer10kResidents'])['code'], min(DI, key=lambda d: d['pointsPer10kResidents'])['code']))
ok('8 spacing aliases all map to Bavarian district codes', len(P['meta']['labelMapping']['spacingAliases']) == 8 and all(a['code'].startswith('09') for a in P['meta']['labelMapping']['spacingAliases']))

# Package: payload shipped byte-identical; JS wrapper holds the same JSON; nothing record-level shipped.
src = PAYLOAD
ok('dist JSON byte-identical to the payload', (DIST / 'data/national-story.json').read_bytes() == (src / 'national-story.json').read_bytes())
js = (DIST / 'data/national-story.js').read_text(encoding='utf-8')
ok('dist JS payload = window.NATIONAL_STORY + identical JSON', js.startswith('window.NATIONAL_STORY=') and json.loads(js[len('window.NATIONAL_STORY='):].rstrip().rstrip(';')) == P)
ok('payload SHA-256 matches the published aggregate hash', hashlib.sha256((DIST / 'data/national-story.json').read_bytes()).hexdigest() == 'cf580cceb8229b6b71ac1281af3f5c8b5b526ca6de8d6da00f5a1d0b560f53f3')
shipped = {p.relative_to(DIST).as_posix() for p in DIST.rglob('*') if p.is_file()}
ok('no retired variants, shared kit or record-level files in dist', not any(x.startswith(('v1/', 'v2/', 'v3/', 'shared/')) or x in ('spectrum-data.js', 'core.js', 'scroll.js', 'data.js') for x in shipped), sorted(shipped))
sys.exit(R.save())
