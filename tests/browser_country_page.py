import sys,threading,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration.news_api import create_app
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
news={'geo':[{'url':'https://example.com/a','title':'Steel trade update <img src=x>','country':'India','summary':'<script>alert(1)</script> Fixture article, not a live news claim.','created_at':'2026-10-04T12:00:00Z','category':'TRADE'}], 'brics':[{'url':'https://example.com/b','title':'Trade meeting fixture','country':'India'}]}
app=create_app(reader=lambda:news,authorize=lambda r:True)
server=make_server('127.0.0.1',8771,app);threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':980});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.route('**/*',lambda r:r.continue_() if r.request.url.startswith('http://127.0.0.1:8771/') else r.abort())
 page.goto('http://127.0.0.1:8771/workspace/countries');page.get_by_text('Choose a stored label. No country selected.',exact=True).wait_for();page.locator('#country-label').fill('India');page.get_by_role('button',name='Load country',exact=True).click();page.get_by_text('India: 2 supplied rows.',exact=True).wait_for();assert page.locator('#country-stories img,#country-stories script,#country-stories iframe').count()==0
 page.get_by_role('button',name='Add to watchlist').click();page.get_by_text('Saved in this browser.',exact=True).wait_for();page.reload();page.get_by_role('button',name='India',exact=True).click();page.get_by_text('India: 2 supplied rows.',exact=True).wait_for()
 page.get_by_role('button',name='Find matching trade codes').first.click();page.get_by_text('Verified Finder index is not connected.',exact=True).wait_for();page.screenshot(path='/downloads/country-page-desktop.png',full_page=True)
 page.set_viewport_size({'width':390,'height':844});page.screenshot(path='/downloads/country-page-mobile.png',full_page=True);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.locator('#country-project').select_option('brics');page.get_by_role('button',name='Load country',exact=True).click();page.get_by_text('India: 1 supplied rows.',exact=True).wait_for();assert page.locator('#country-stories article').count()==1
 page.locator('#country-label').fill('Unknown');page.get_by_role('button',name='Load country',exact=True).click();page.get_by_text('No supplied rows use this exact label. Country coverage is unknown.',exact=True).wait_for();page.get_by_role('button',name='Add to watchlist').click();page.get_by_text('Load a country label before adding it.',exact=True).wait_for()
 page.get_by_role('button',name='India',exact=True).click();page.get_by_text('India: 1 supplied rows.',exact=True).wait_for();page.evaluate("() => {Storage.prototype.setItem=function(){throw new Error('fixture storage failure')};}");page.get_by_role('button',name='Remove India').click();page.get_by_text('Browser storage unavailable. Changes were not saved.',exact=True).wait_for();assert page.get_by_role('button',name='India',exact=True).count()==1
 page.route('**/api/country-page?*',lambda r:r.fulfill(status=503,json={'error':'unavailable'}));page.get_by_role('button',name='Load country',exact=True).click();page.get_by_text('Country news unavailable. Coverage cannot be checked.',exact=True).wait_for();assert not errors
 print(json.dumps({'errors':errors,'safe_text':True,'browser_watchlist_reload':True,'storage_failure_visible':True,'project_isolated':True,'unknown_coverage_distinct':True,'mobile_no_overflow':True,'no_external_requests_allowed':True}));b.close()
server.shutdown()
