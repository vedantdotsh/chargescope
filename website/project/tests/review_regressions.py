import sys
from playwright.sync_api import sync_playwright
from common import Results,new,go,holds,EVID
# Fresh-reader frictions from the last review are kept as regressions: the rail no longer competes with the opening, the language menu closes after a choice.
R=Results('review-regressions')
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome')
 for w,h,room in [(1440,900,1),(1280,720,0)]:
  for motion in ['no-preference','reduce']:
   ctx,pg=new(b,w,h,motion=motion);H=holds(pg);go(pg,round((H[room]+H[room+1])/2))
   got=pg.evaluate('''() => ({room:CSMotion.room(),tops:[...document.querySelectorAll('.v3-frame')].map(f=>f.getBoundingClientRect().top)})''')
   R.ok(f'{w} {motion}: old midpoint retains previous story until incoming chart is visible',got['room']==room,got)
   pg.screenshot(path=str(EVID/f'fixed-rail-{w}-{motion}.png'))
   ctx.close()
 ctx,pg=new(b,1440,900)
 pg.select_option('select[data-k=s3]','06');pg.select_option('select[data-k=d5]','03255');pg.click('[data-m=m5][data-v=flag]')
 text=pg.locator('[data-r=st1]').inner_text()
 R.ok('Hessen plus Holzminden retains concentration flag', '20%' in text or '20 %' in text,text)
 for mode,phrase in [('points','by points'),('rate','by rate')]:
  pg.click(f'[data-m=m2][data-v={mode}]')
  R.ok(f'state ranks identify {mode}',phrase in pg.locator('[data-r=st0]').inner_text())
 ctx.close()
 ctx,pg=new(b,1440,900)
 R.ok('opening: the rail shows no step story beside the hero (waiting past the right edge, inert, hidden from assistive technology)',pg.evaluate("() => { const r = document.querySelector('.k-rail'); return r.inert && r.getAttribute('aria-hidden') === 'true' && r.getBoundingClientRect().left >= document.documentElement.clientWidth && scrollY === 0; }"))
 pg.click('.k-menu-btn');pg.click('[data-k=lde]');pg.wait_for_timeout(60)
 R.ok('language choice closes the menu and keeps focus on its button',pg.evaluate("() => document.documentElement.lang === 'de' && document.querySelector('#k-pop').hidden && document.activeElement.matches('.k-menu-btn')"))
 ctx.close();b.close()
sys.exit(R.save())
