import sys,threading,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration.news_api import create_app
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
app=create_app(authorize=lambda r:True);server=make_server('127.0.0.1',8774,app);threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':390,'height':844});errors=[];requests=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url));page.route('**/*',lambda r:r.continue_() if r.request.url.startswith('http://127.0.0.1:8774/') else r.abort());page.goto('http://127.0.0.1:8774/workspace/map');assert not any('/api/map-data' in u for u in requests)
 page.locator('#map-load').click();page.get_by_text('Load again to refresh; nothing updates by itself.',exact=False).wait_for();text=page.locator('#map-host').inner_text();assert '12' in text and 'Chokepoints' in text;assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path='/downloads/map-wired-mobile.png',full_page=True);assert sum('/api/map-data' in u for u in requests)==1;assert not errors
 page.route('**/api/map-data',lambda r:r.fulfill(status=503,json={'error':'Unavailable'}));page.locator('#map-load').click();page.get_by_text('Map data is unavailable right now (503).',exact=True).wait_for();assert page.locator('#map-load').is_enabled();assert not errors;print(json.dumps({'manual_one_fetch':True,'mobile_no_overflow':True,'errors':errors,'503_recovery':True,'chokepoints12':True}));b.close()
server.shutdown()
