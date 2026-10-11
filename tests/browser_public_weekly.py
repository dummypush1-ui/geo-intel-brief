import sys,threading,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration.public_preview_builder import build_public_preview
from tests.test_code_news_coverage_binding_prep import SAMPLE
from integration import public_weekly_pdf as w
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
out=Path('/tmp/public-weekly-result');out.mkdir(exist_ok=True)
app=build_public_preview(dict(SAMPLE,**{w.FLAG:'true'}))
original=app.wsgi_app
def proxy(environ,start_response):environ['HTTP_HOST']='example.test';environ['wsgi.url_scheme']='https';return original(environ,start_response)
app.wsgi_app=proxy
server=make_server('127.0.0.1',8784,app);threading.Thread(target=server.serve_forever,daemon=True).start()
results=[]
with sync_playwright()as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
 for width in (390,1100):
  page=b.new_page(viewport={'width':width,'height':844},accept_downloads=True);errors=[];starts=[];external=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  def route(r):
   if not r.request.url.startswith('http://127.0.0.1:8784/'):external.append(r.request.url);r.abort()
   else:
    if '/api/weekly-report.pdf' in r.request.url:starts.append(r.request.url)
    r.continue_()
  page.route('**/*',route);page.goto('http://127.0.0.1:8784/workspace/weekly');assert not starts
  page.locator('#weekly-start').fill('2026-10-01');page.locator('#weekly-end').fill('2026-10-05')
  with page.expect_download()as d:page.get_by_role('button',name='Download supplied-news PDF').click()
  d.value.save_as(str(out/('sample-'+str(width)+'.pdf')))
  page.get_by_text('PDF download prepared from supplied sample rows only, not complete weekly history. Empty means no supplied items, not no events.',exact=True).wait_for()
  page.screenshot(path=str(out/('page-'+str(width)+'.png')),full_page=True)
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  for code,expect in [(429,'Busy or global start limit reached.'),(400,'Check the dates:'),(503,'Supplied-news PDF unavailable.')]:
   page.route('**/api/weekly-report.pdf?*',lambda r,request,code=code:r.fulfill(status=code,json={'error':'not echoed private'}));page.get_by_role('button',name='Download supplied-news PDF').click();page.locator('#weekly-status').filter(has_text=expect).wait_for();assert page.get_by_role('button').is_enabled();page.unroute('**/api/weekly-report.pdf?*')
  assert not errors and not external;results.append(dict(width=width,download=True,no_auto_request=True,no_overflow=True,errors=errors,external=external));page.close()
 b.close()
server.shutdown();print(json.dumps(results,indent=2))
