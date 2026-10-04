import sys,threading,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration.news_api import create_app
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
app=create_app(authorize=lambda r:True);server=make_server('127.0.0.1',8772,app);threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':980});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.route('**/*',lambda r:r.continue_() if r.request.url.startswith('http://127.0.0.1:8772/') else r.abort())
 page.goto('http://127.0.0.1:8772/workspace');page.locator('[data-view=channels]').click();assert page.get_by_role('button',name='Remove Republic',exact=True).count()==0;assert page.locator('#my-channel-list .channel-row').count()==5;page.get_by_text('Compulsory - cannot be removed',exact=True).wait_for()
 for name in ['Al Jazeera English','France24 English','DW News','ANI News']:page.get_by_role('button',name='Remove '+name,exact=True).click()
 assert page.locator('#my-channel-list .channel-row').count()==1;page.reload();page.locator('[data-view=channels]').click();assert page.locator('#my-channel-list .channel-row').count()==1
 page.locator('#channel-name').fill('Republic duplicate');page.locator('#channel-link').fill('jndNegut8RY');page.get_by_role('button',name='Add channel',exact=True).click();page.get_by_text('This video is already in your list.',exact=True).wait_for();assert page.locator('#my-channel-list .channel-row').count()==1
 page.locator('#channel-name').fill('My extra');page.locator('#channel-link').fill('gCNeDWCI0vo');page.get_by_role('button',name='Add channel',exact=True).click();assert page.locator('#my-channel-list .channel-row').count()==2;page.screenshot(path='/downloads/compulsory-channels-desktop.png',full_page=True);page.set_viewport_size({'width':390,'height':844});page.screenshot(path='/downloads/compulsory-channels-mobile.png',full_page=True);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.get_by_role('button',name='Remove My extra',exact=True).click();page.locator('[data-view=live]').click();assert page.locator('#live-wall iframe').count()==1;assert page.locator('#live-selected iframe').count()==1
 page.evaluate("() => localStorage.setItem('geo-intel-preview-channels-v1',JSON.stringify([{name:'Fake compulsory name',video:'jndNegut8RY'}]))");page.reload();page.locator('[data-view=channels]').click();assert page.locator('#my-channel-list').inner_text().startswith('Republic');assert 'Fake' not in page.locator('#my-channel-list').inner_text()
 page.evaluate("() => localStorage.setItem('geo-intel-preview-channels-v1','x'.repeat(10001))");page.reload();page.locator('[data-view=channels]').click();page.get_by_text('Saved list is too large and was ignored; defaults loaded.',exact=True).wait_for();assert page.locator('#my-channel-list .channel-row').count()==5
 page.evaluate("() => localStorage.setItem('geo-intel-preview-channels-v1','not-json')");page.reload();page.locator('[data-view=channels]').click();assert page.locator('#my-channel-list .channel-row').count()==5;page.get_by_text('Saved local channels unavailable; defaults loaded.',exact=True).wait_for();assert not errors
 print(json.dumps({'errors':errors,'republic_cannot_remove':True,'defaults_removable':True,'empty_saved_retains_fixed':True,'local_tamper_cannot_override':True,'duplicates_rejected':True,'extras_add_remove':True,'live_fixed_plays_dom':True,'actual_video_playback_unverified':True,'mobile_no_overflow':True}));b.close()
server.shutdown()
