import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

PROJECT=Path(__file__).resolve().parent.parent
OUTPUT=PROJECT/'.scratch/v3'
results={'touch_swipes':[],'drawer_focus_states':0,'blocked_storage':[],'inline_mobile':[]}
with sync_playwright() as playwright:
    browser=playwright.chromium.launch()
    for design in ['current','workbench','profile','guided']:
        path=PROJECT/('website-combined/index.html' if design=='current' else 'website-variations-v3/'+design+'/index.html')
        for width in [1440,390]:
            for lang in ['en','de']:
                for theme in ['light','dark']:
                    page=browser.new_page(viewport={'width':width,'height':900},reduced_motion='reduce')
                    page.goto(path.as_uri());page.locator('#lang-'+lang).click();page.locator('#theme-'+theme).click()
                    page.select_option('#comparison','12064')
                    for resized in [width-20,width]:
                        page.set_viewport_size({'width':resized,'height':900})
                        page.wait_for_function('document.querySelector("#boxplot svg").viewBox.baseVal.width===Math.max(280,document.getElementById("boxplot").clientWidth-28)')
                        expect(page.locator('.is-comparison[data-select="12064"]')).to_have_count(3)
                    page.locator('#findings-open').click()
                    for key in ['Tab','Shift+Tab']:
                        page.keyboard.press(key)
                        assert page.locator('#findings-close').evaluate('(element)=>element===document.activeElement')
                    page.locator('#findings-title').click()
                    expect(page.locator('#findings')).to_be_visible()
                    page.locator('#findings').evaluate('(element)=>element.scrollTop=element.scrollHeight')
                    close=page.locator('#findings-close').bounding_box()
                    assert close['y']>=-1 and close['y']+close['height']<=900
                    page.locator('#findings-close').click()
                    page.locator('#findings-open').click()
                    assert page.locator('#findings').evaluate('(element)=>element.scrollTop')==0
                    page.screenshot(path=str(OUTPUT/f'{design}-{lang}-{theme}-{width}-drawer.png'))
                    page.keyboard.press('Escape')
                    assert page.locator('#findings-open').evaluate('(element)=>element===document.activeElement')
                    page.locator('#gallery').scroll_into_view_if_needed()
                    page.locator('#gallery img').evaluate_all('(images)=>images.forEach(image=>image.loading="eager")')
                    page.wait_for_function('[...document.querySelectorAll("#gallery img")].every(image=>image.complete && image.naturalWidth>0)')
                    page.evaluate('scrollTo(0,0)')
                    page.screenshot(path=str(OUTPUT/f'{design}-{lang}-{theme}-{width}.png'),full_page=True)
                    page.screenshot(path=str(OUTPUT/f'{design}-{lang}-{theme}-{width}-opening.png'))
                    results['drawer_focus_states']+=1
                    page.close()
        context=browser.new_context(viewport={'width':390,'height':844},has_touch=True,is_mobile=True,reduced_motion='reduce')
        page=context.new_page();page.goto(path.as_uri())
        page.locator('#findings-open').tap();expect(page.locator('#findings')).to_be_visible()
        page.locator('#findings-close').tap();expect(page.locator('#findings')).not_to_be_visible()
        page.locator('#gallery').scroll_into_view_if_needed()
        session=context.new_cdp_session(page)
        bounds=page.locator('#gallery').bounding_box();start={'x':bounds['x']+bounds['width']*.85,'y':bounds['y']+bounds['height']*.5}
        session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[start]})
        for step in range(1,9):session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':start['x']-step*32,'y':start['y']}]})
        session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
        page.wait_for_function('document.getElementById("gallery").scrollLeft>100')
        results['touch_swipes'].append(design);context.close()
        context=browser.new_context()
        context.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new DOMException('Denied','SecurityError')}})")
        page=context.new_page();page.goto(path.as_uri());page.locator('#lang-de').click();page.locator('#theme-dark').click()
        assert page.locator('html').get_attribute('lang')=='de'
        assert page.locator('html').get_attribute('data-theme')=='dark'
        page.locator('#findings-open').click();expect(page.locator('#findings')).to_be_visible()
        results['blocked_storage'].append(design);context.close()
    page=browser.new_page(viewport={'width':390,'height':844})
    page.goto((PROJECT/'website-variations-v3/review.html').as_uri())
    for design in ['current','workbench','profile','guided']:
        page.locator('nav [data-design="'+design+'"]').click()
        frame=page.frame_locator('#candidate')
        frame.locator('#lang-de').click();frame.locator('#theme-dark').click()
        frame.locator('#scenario').check();frame.locator('[data-metric="kw"]').click()
        frame.locator('#findings-open').click();expect(frame.locator('#findings')).to_be_visible()
        frame.locator('#findings-close').click()
        assert frame.locator('html').evaluate('()=>document.documentElement.scrollWidth<=innerWidth+1')
        results['inline_mobile'].append(design)
    browser.close()
results['result']='PASS'
(OUTPUT/'qa-extra.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print('PASS: 32 drawer focus/scroll/close states; four actual touch swipes and touch drawer controls; four blocked-storage states; four inline mobile options')
