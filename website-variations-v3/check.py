import json
import math
import statistics
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

PROJECT = Path(__file__).resolve().parent.parent
ROOT = PROJECT / 'website-combined'
OUTPUT = PROJECT / '.scratch/v3'
DATA = json.loads((ROOT/'data.js').read_text(encoding='utf-8').removeprefix('window.COMBINED_DATA=').strip().removesuffix(';'))
RESULT = {'designs': [], 'math_cases': 0, 'page_errors': [], 'external_requests': []}

def overflow(page):
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
    assert not page.evaluate('''() => [...document.querySelectorAll('h1,h2,h3,.readout,.preferences,select,.quartiles,.active-view')].filter(element => {const box=element.getBoundingClientRect(); return box.left < -1 || box.right > innerWidth+1 || element.scrollWidth>element.clientWidth+2}).map(element=>element.outerHTML.slice(0,160))''')

def math_checks(page, excluded):
    page.locator('#scenario').set_checked(excluded)
    scenario = 'hypothetical' if excluded else 'registered'
    rates = sorted(item[scenario]['rate'] for item in DATA['districts'])
    q1, median, q3 = statistics.quantiles(rates, n=4, method='inclusive')
    actual = json.loads(page.locator('#boxplot').get_attribute('data-statistics'))
    for key, expected in [('q1',q1),('median',median),('q3',q3)]:
        assert math.isclose(actual[key],expected,abs_tol=1e-10)
    snapshots = page.evaluate('''() => {
      const snapshots=[];
      for(const option of document.getElementById('focus').options){
        const focus=document.getElementById('focus');focus.value=option.value;focus.dispatchEvent(new Event('change'));
        for(const metric of ['rate','points','kw']){
          document.querySelector('[data-metric="'+metric+'"]').click();
          const lane=document.querySelector('[data-lane="0"]');
          snapshots.push({code:option.value,metric,value:Number(lane.querySelector('[data-value]').dataset.value),rank:Number(lane.querySelector('[data-rank]').dataset.rank),selected:document.querySelectorAll('[data-select="'+option.value+'"][aria-pressed="true"]').length,counts:document.querySelectorAll('#counts-rates [data-select]').length,capacity:document.querySelectorAll('#capacity [data-select]').length,dots:document.querySelectorAll('#boxplot [data-select]').length});
        }
      }return snapshots;
    }''')
    for snapshot in snapshots:
        district = next(item for item in DATA['districts'] if item['code']==snapshot['code'])
        expected = district[scenario][snapshot['metric']] / (1000 if snapshot['metric']=='kw' else 1)
        assert math.isclose(snapshot['value'],expected,abs_tol=1e-10)
        assert snapshot['rank'] == 1+sum(item[scenario][snapshot['metric']]>district[scenario][snapshot['metric']] for item in DATA['districts'])
        assert snapshot['selected']==3
        assert snapshot['counts']==snapshot['capacity']==snapshot['dots']==18
        RESULT['math_cases'] += 1
    totals = {key: sum(item[scenario][key] for item in DATA['districts']) for key in ['points','population']}
    regional = page.locator('#regional').inner_text()
    expected_rate = totals['points']/totals['population']*10000
    assert page.evaluate('(rate)=>document.getElementById("regional").textContent.includes(new Intl.NumberFormat(document.documentElement.lang==="de"?"de-DE":"en-GB",{minimumFractionDigits:1,maximumFractionDigits:1}).format(rate))',expected_rate)
    assert 'Berlin' in regional

def interactions(page, design, lang, theme, width):
    page.locator('#reset').click()
    page.select_option('#comparison','12064')
    page.locator('#scenario').focus(); page.keyboard.press('Space')
    page.locator('#boxplot [data-select="12065"]').focus(); page.keyboard.press('Enter')
    expect(page.locator('#focus')).to_have_value('12065')
    assert page.locator('.is-comparison[data-select="12064"]').count()==3
    page.locator('#counts-rates [data-select="12067"]').focus()
    expect(page.locator('#tooltip')).to_be_visible()
    assert '319' in page.locator('#tooltip').inner_text()
    page.locator('#capacity [data-select="12073"]').click()
    expect(page.locator('#focus')).to_have_value('12073')
    assert 'undefined' not in page.locator('#active-view').inner_text()
    before = page.locator('#boxplot').get_attribute('data-statistics')
    page.locator('#findings-open').click()
    expect(page.locator('#findings')).to_be_visible()
    assert page.locator('#findings-close').evaluate('(element)=>element===document.activeElement')
    assert page.locator('#findings-open').get_attribute('aria-expanded')=='true'
    body = page.locator('#findings').inner_text()
    assert all(value in body for value in ['513','319','35','42'])
    if lang=='en': assert 150<=len(body.split())<=220
    else: assert 'Next check' not in body and 'Read the findings' not in body
    page.screenshot(path=str(OUTPUT/f'{design}-{lang}-{theme}-{width}-drawer.png'))
    page.keyboard.press('Escape')
    expect(page.locator('#findings')).not_to_be_visible()
    assert page.locator('#findings-open').evaluate('(element)=>element===document.activeElement')
    assert before==page.locator('#boxplot').get_attribute('data-statistics')
    expect(page.locator('#focus')).to_have_value('12073')
    page.locator('#findings-open').click(); page.locator('#findings-close').click()
    if width==1440:
        page.locator('#findings-open').click(); page.mouse.click(10,10)
        expect(page.locator('#findings')).not_to_be_visible()
    page.locator('#reset').click()
    expect(page.locator('#focus')).to_have_value('12067')
    expect(page.locator('#comparison')).to_have_value('12068')
    expect(page.locator('#scenario')).not_to_be_checked()
    if design=='guided':
        for index, code in [(0,'12069'),(1,'12067'),(2,'12061')]:
            page.locator('[data-question="'+str(index)+'"]').click()
            expect(page.locator('#focus')).to_have_value(code)
            assert page.locator('#scenario').is_checked()==(index==1)
    page.locator('#reset').click()
    page.locator('#gallery-next').click()
    expect(page.locator('#gallery-counter')).to_have_text('2 / 4')
    page.locator('#gallery').focus(); page.keyboard.press('End')
    expect(page.locator('#gallery-counter')).to_have_text('4 / 4')
    page.keyboard.press('Home')
    page.locator('.slide').first.click()
    page.wait_for_function('document.getElementById("modal-image").complete && document.getElementById("modal-image").naturalWidth===2466')
    page.keyboard.press('ArrowRight')
    page.wait_for_function('document.getElementById("modal-image").complete && document.getElementById("modal-image").naturalWidth===2466')
    assert page.locator('#modal-image').get_attribute('src').endswith('power-bi-2.png')
    page.keyboard.press('Escape')
    assert page.locator('.slide').first.evaluate('(element)=>element===document.activeElement')
    assert '/releases/download/v1.0.0/' in page.locator('.download-link').get_attribute('href')
    assert not any(word in page.locator('body').inner_text().lower() for word in ['coming soon','repository is private','repository ist privat','carefully bounded'])
    page.locator('#lang-'+('de' if lang=='en' else 'en')).click()
    page.locator('#theme-'+('dark' if theme=='light' else 'light')).click()
    expect(page.locator('#focus')).to_have_value('12067')
    page.locator('#lang-'+lang).click();page.locator('#theme-'+theme).click()
    page.reload();page.wait_for_selector('#active-view')
    assert page.locator('html').get_attribute('lang')==lang
    assert page.locator('html').get_attribute('data-theme')==theme
    overflow(page)

def main():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    for item in DATA['gallery']:
        assert (ROOT/item['src']).is_file()
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch()
        for design in ['current','workbench','profile','guided']:
            path=ROOT/'index.html' if design=='current' else PROJECT/'website-variations-v3'/design/'index.html'
            for width in [1440,390]:
                for lang in ['en','de']:
                    for theme in ['light','dark']:
                        context=browser.new_context(viewport={'width':width,'height':1000 if width==1440 else 844},reduced_motion='reduce',has_touch=width==390)
                        page=context.new_page()
                        page.on('pageerror',lambda error: RESULT['page_errors'].append(str(error)))
                        page.on('request',lambda request: RESULT['external_requests'].append(request.url) if request.url.startswith(('https:','http:')) else None)
                        page.goto(path.as_uri());page.wait_for_selector('#active-view')
                        page.locator('#lang-'+lang).click();page.locator('#theme-'+theme).click()
                        for excluded in [False,True]: math_checks(page,excluded)
                        interactions(page,design,lang,theme,width)
                        page.screenshot(path=str(OUTPUT/f'{design}-{lang}-{theme}-{width}.png'),full_page=True)
                        RESULT['designs'].append({'design':design,'width':width,'language':lang,'theme':theme})
                        print('PASS',design,width,lang,theme,flush=True)
                        context.close()
            for width in [320,768,1000]:
                page=browser.new_page(viewport={'width':width,'height':900})
                page.goto(path.as_uri());page.locator('#lang-de').click();page.locator('#theme-dark').click()
                page.locator('#scenario').check();page.locator('[data-metric="kw"]').click();overflow(page);page.close()
        page=browser.new_page(viewport={'width':1440,'height':900})
        page.goto((PROJECT/'website-variations-v3/review.html').as_uri())
        for design in ['current','workbench','profile','guided']:
            page.locator('nav [data-design="'+design+'"]').click()
            frame=page.frame_locator('#candidate')
            expect(frame.locator('#active-view')).to_be_visible()
            frame.locator('#lang-de').click();frame.locator('#theme-dark').click()
            frame.locator('#findings-open').click();expect(frame.locator('#findings')).to_be_visible()
            frame.locator('#findings-close').click()
            frame.locator('.slide').first.click();expect(frame.locator('#lightbox')).to_be_visible()
            assert frame.locator('#modal-image').get_attribute('src').startswith('data:image/webp;base64,')
        browser.close()
    assert RESULT['math_cases']==3456
    assert not RESULT['page_errors'],RESULT['page_errors']
    assert not RESULT['external_requests'],RESULT['external_requests']
    RESULT['result']='PASS'
    (OUTPUT/'qa-results.json').write_text(json.dumps(RESULT,indent=2),encoding='utf-8')
    print('PASS: 3456 math cases; 32 design/viewport/language/theme combinations; 12 extra responsive states; four inline options; no page errors or network requests')

if __name__=='__main__': main()
