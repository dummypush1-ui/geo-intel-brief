"""Local synthetic stored-data browser checks. External traffic aborted."""
import sys,threading,json,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
from integration.news_api import create_app
from integration import public_brics_news as base
from integration import brics_live_b3 as m
origin='http://127.0.0.1:8833';out=Path('/tmp/brics-live-b3/pixels');out.mkdir(exist_ok=True)
app=create_app(reader=lambda:(_ for _ in ()).throw(AssertionError('Geo read')),authorize=lambda r:r.path.startswith('/workspace')or r.path=='/api/brics/news',allowed_origin=origin)
base.install(app,origin);r=m.SQLiteReader('/synthetic/not-opened');binding=m.Binding(r,m.Review(r.identity,'synthetic mapping','synthetic disclosure','synthetic readonly'),('sanctions',));m.install(app,binding);rows=[dict(url='https://fixture.invalid/article',title='BRICS <script>window.__xss=1</script> sanctions summit',summary='<img src=x onerror=window.__xss=2> Synthetic stored data only.',source='Synthetic source',country='IN',category='SANCTIONS',collected_at='2026-10-15T22:00:00Z',published='')];calls=[0]
def read():calls[0]+=1;return rows
r.read=read
server=make_server('127.0.0.1',8833,app,threaded=True);threading.Thread(target=server.serve_forever,daemon=True).start();report=[]
try:
 with sync_playwright()as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
  for width in (320,390,1100):
   service=app.extensions['brics_live_b3'];service.cached=None;service.failed=False;r.closed=False
   page=browser.new_page(viewport={'width':width,'height':950});errors=[];network=[];page.on('pageerror',lambda e:errors.append(str(e)))
   def route(route):
    if not route.request.url.startswith(origin):route.abort();return
    network.append(route.request.url);route.continue_()
   page.route('**/*',route);page.goto(origin+base.PAGE);assert not any(base.API in n for n in network)
   page.locator('#read').click();page.wait_for_function("()=>document.querySelector('#status').textContent.includes('1 BRICS-relevant')");assert page.locator('#results article').count()==1;assert page.locator('#results script,#results img').count()==0;assert page.evaluate('window.__xss||0')==0;assert page.locator('#results a').first.get_attribute('rel')=='noopener noreferrer';assert 'unknown, not cleared'in page.locator('#results').inner_text()
   page.screenshot(path=str(out/f'precheck-{width}.png'),full_page=True);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
   page.screenshot(path=str(out/f'stored-{width}.png'),full_page=True)
   before=calls[0];page.locator('#read').click();page.wait_for_function("()=>!document.querySelector('#read').disabled");assert calls[0]==before
   rows[:]=[dict(url='javascript:bad',title='BRICS sanctions')];service.cached=None;page.locator('#read').click();page.wait_for_function("()=>document.querySelector('#status').textContent.includes('1 unsafe rows skipped')");assert page.locator('#results article').count()==0
   def fail():raise OSError('SECRET')
   r.read=fail;service.cached=None;page.locator('#read').click();page.wait_for_function("()=>document.querySelector('#status').textContent.includes('unavailable')");r.read=read
   page.screenshot(path=str(out/f'unavailable-{width}.png'),full_page=True);assert not errors,errors;assert not any('youtube'in n for n in network);report.append({'width':width,'manualOnly':True,'noXSS':True,'cached':True,'failureClears':True,'noPlayerLoads':True,'errors':errors});rows[:]=[dict(url='https://fixture.invalid/article',title='BRICS <script>window.__xss=1</script> sanctions summit',summary='<img src=x onerror=window.__xss=2> Synthetic stored data only.',source='Synthetic source',country='IN',category='SANCTIONS',collected_at='2026-10-15T22:00:00Z',published='')];page.close()
  browser.close()
finally:app.extensions['brics_live_close']();server.shutdown()
(out/'report.json').write_text(json.dumps(report,indent=2));print(report)
