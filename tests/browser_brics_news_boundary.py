"""Real Chrome fixture gates. No production source or Geo read."""
import sys,threading,json,os,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
from integration.news_api import create_app
from integration.public_brics_news import install
from integration.brics_news_boundary import BricsFixtureReader
origin='http://127.0.0.1:8822';out=Path(os.environ.get('BRICS_NEWS_EVIDENCE_DIR') or tempfile.mkdtemp(prefix='brics-news-evidence-'));out.mkdir(parents=True,exist_ok=True)
app=create_app(reader=lambda:(_ for _ in ()).throw(AssertionError('Geo read')),authorize=lambda r:r.path.startswith('/workspace')or r.path=='/api/brics/news',allowed_origin=origin)
install(app,origin);server=make_server('127.0.0.1',8822,app,threaded=True);threading.Thread(target=server.serve_forever,daemon=True).start();report=[]
try:
 with sync_playwright()as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
  for width in (390,1100):
   page=browser.new_page(viewport={'width':width,'height':950});page.set_default_timeout(4000);calls=[];errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   def route(r):
    if not r.request.url.startswith(origin):r.abort();return
    calls.append(r.request.url);r.continue_()
   page.route('**/*',route);app.extensions['public_brics_news'].reader=None;page.goto(origin+'/workspace/brics-news');assert not any('/api/brics/news' in u for u in calls);page.locator('#read').click();page.wait_for_function("()=>document.querySelector('#status').textContent.includes('No BRICS news data supplied')");assert page.locator('#results article').count()==0
   page.screenshot(path=str(out/f'unconnected-{width}.png'))
   app.extensions['public_brics_news'].reader=BricsFixtureReader(lambda:[dict(url='https://fixture.invalid/one',title='BRICS <script>window.__xss=1</script> sanctions summit',summary='<img src=x onerror=window.__xss=2> Offline fixture.',collected_at='2026-10-13T11:00:00')],object(),('sanctions',))
   page.locator('#read').click();page.wait_for_function("()=>document.querySelector('#status').textContent.startsWith('supplied offline fixtures')");assert page.locator('#results article').count()==1;assert page.locator('#results script,#results img').count()==0;assert page.evaluate('window.__xss||0')==0;assert 'unknown, not cleared'in page.locator('#results').inner_text();assert 'not a full-store total'in page.locator('#status').inner_text()
   page.screenshot(path=str(out/f'fixture-{width}.png'))
   app.extensions['public_brics_news'].reader=BricsFixtureReader(lambda:(_ for _ in ()).throw(ValueError('SECRET')),object(),('sanctions',));page.locator('#read').click();page.wait_for_function("()=>document.querySelector('#status').textContent.includes('unavailable')");n=len(calls);page.wait_for_timeout(200);assert len(calls)==n;assert page.locator('#results article').count()==0;assert not errors,errors;assert not any('youtube' in u for u in calls);report.append(dict(width=width,noAutoFetch=True,unconnected=True,literalHTML=True,unknownCorroboration=True,noRetry=True,errors=errors));page.close()
  browser.close()
finally:server.shutdown()
(out/'report.json').write_text(json.dumps(report,indent=2));print(report)
