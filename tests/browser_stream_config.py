import sys,threading,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration.news_api import create_app
from integration.stream_fixture_app import create_stream_fixture
from datetime import datetime,timezone
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
raw=(Path(__file__).resolve().parents[1]/'intelligence/brics/config/streams.yaml').read_bytes();app=create_stream_fixture(raw,datetime.now(timezone.utc),authorize=lambda r:True,allowed_origin='http://127.0.0.1:8778');server=make_server('127.0.0.1',8778,app);threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':390,'height':844});errors=[];outside=[];page.on('pageerror',lambda e:errors.append(str(e)));page.route('**/*',lambda r:r.continue_() if r.request.url.startswith('http://127.0.0.1:8778/') else (outside.append(r.request.url),r.abort()))
 page.goto('http://127.0.0.1:8778/workspace/brics-streams');page.locator('#status').filter(has_text='Fixture list').wait_for();assert page.locator('#streams article').count()==5;assert page.get_by_role('heading',name='republiclive',exact=True).count()==1;page.fill('#name','Fixture stream');page.fill('#country','India');page.fill('#link','https://youtube.com/live/abcdefghijk');page.locator('form button').click();page.get_by_role('heading',name='Fixture stream').wait_for();page.screenshot(path='/downloads/brics-configured-fixture-mobile.png',full_page=True);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.get_by_role('button',name='Remove Fixture stream').click();page.get_by_role('heading',name='Fixture stream').wait_for(state='detached');assert page.locator('#streams article').count()==5;assert not outside and not errors;print(json.dumps({'add_remove':True,'mobile_no_overflow':True,'external_requests':outside,'errors':errors,'fixture_only':True,'original_configured_rows':5}));b.close()
server.shutdown()
