import sys,threading,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration.news_api import create_app
from integration.brics_streams import FixtureStreams
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
app=create_app(authorize=lambda r:True,brics_stream_fixture=FixtureStreams([]),allowed_origin='http://127.0.0.1:8778');server=make_server('127.0.0.1',8778,app);threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':390,'height':844});errors=[];outside=[];page.on('pageerror',lambda e:errors.append(str(e)));page.route('**/*',lambda r:r.continue_() if r.request.url.startswith('http://127.0.0.1:8778/') else (outside.append(r.request.url),r.abort()))
 page.goto('http://127.0.0.1:8778/workspace/brics-streams');page.locator('#status').filter(has_text='Fixture list').wait_for();page.fill('#name','Fixture stream');page.fill('#country','India');page.fill('#link','https://youtube.com/live/abcdefghijk');page.locator('form button').click();page.get_by_role('heading',name='Fixture stream').wait_for();page.screenshot(path='/downloads/brics-stream-fixture-mobile.png',full_page=True);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.get_by_role('button',name='Remove Fixture stream').click();page.get_by_role('heading',name='Fixture stream').wait_for(state='detached');assert not outside and not errors;print(json.dumps({'add_remove':True,'mobile_no_overflow':True,'external_requests':outside,'errors':errors,'fixture_only':True}));b.close()
server.shutdown()
