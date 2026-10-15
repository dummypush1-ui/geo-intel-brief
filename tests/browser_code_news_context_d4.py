"""Local actual ContextBroker/UI fixture. No database/provider/external request."""
import sys,threading,logging,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from flask import Flask
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
from integration import code_news_context_d4 as d
from integration.news_pages import WholeGeoPages
from integration.public_live_builder import sanitize_public_geo_rows
from integration.code_news_links import Links
from integration.code_news_parent_prep import ResolveQuota
from integration.code_news_coverage_route_prep import install as api
from integration.code_news_coverage_ui_prep import install as ui
from tests.test_news_pages185 import Store,rows
nav='--finder' in sys.argv
out=Path('/tmp/code-news-d4/evidence'+('-finder'if nav else''));out.mkdir(parents=True,exist_ok=True);origin='http://127.0.0.1:8798'
r=rows(60)
for i,x in enumerate(r):x.update(title=f'HS 8517; Article {i} <img src=x onerror=alert(1)>',summary='HS 8517; multilingual தமிழ் trade report',source='Fixture source',url=f'https://news.example/article/{i}',secret='PRIVATE')
pages=WholeGeoPages(Store(r),sanitize_public_geo_rows,verified=True,start_cleaner=False);model=Links([{'system':'HS','edition':'2022','code':'8517','description':'Preserved fixture phones heading'}],[]);from unittest.mock import Mock
broker=d.ContextBroker(pages,model,'a'*64,'fixture',resolve_quota=ResolveQuota(),finder_proof=Mock(bound=Mock(return_value=None))if nav else None);app=Flask('d4');api(app,origin,broker,{'PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED':'true','PUBLIC_NEWS_FINDER_LINKS_ENABLED':'true'if nav else'false'},response_validator=d.validate);ui(app,{'PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED':'true','PUBLIC_NEWS_FINDER_LINKS_ENABLED':'true'if nav else'false'},coverage_available=True);app.extensions['code_news_coverage_broker']=broker;d.install_ui(app)
server=make_server('127.0.0.1',8798,app,threaded=True);logging.getLogger('werkzeug').setLevel(logging.ERROR);threading.Thread(target=server.serve_forever,daemon=True).start();errors=[];csp=[];external=[]
try:
 with sync_playwright()as p:
  browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1100,'height':900});page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda e:csp.append(e.text)if'Content Security Policy'in e.text or'violates'in e.text else None)
  def guard(route):
   if route.request.url.startswith(origin+'/'):return route.continue_()
   external.append(route.request.url);return route.abort()
  page.route('**/*',guard);page.goto(origin+'/workspace/code-news-coverage');assert not pages.store.calls
  page.fill('#system','HS');page.fill('#edition','2022');page.fill('#code','8517');page.click('#start');page.wait_for_selector('#coverage-items .article h3 a');assert page.locator('#coverage-items .article').count()==25
  assert page.locator('#coverage-items img').count()==0;assert page.locator('#coverage-items h3 a').first.get_attribute('href').startswith('https://news.example/article/');assert page.locator('#coverage-items h3 a').first.get_attribute('rel')=='noopener noreferrer';assert 'PRIVATE'not in page.locator('body').inner_text();assert len(pages.store.calls)==1
  for width in [1100,390,320]:
   page.set_viewport_size({'width':width,'height':900});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path=str(out/f'd4-results-{width}.png'),full_page=True)
  first=page.locator('#coverage-items h3 a').first.inner_text();page.click('#next');page.wait_for_function('(v)=>document.querySelector("#coverage-items h3 a").textContent!==v',arg=first);assert len(pages.store.calls)==1;assert page.locator('#coverage-items .article').count()==25
  first=page.locator('#coverage-items h3 a').first.inner_text();page.click('#next');page.wait_for_function('(v)=>document.querySelector("#coverage-items h3 a").textContent!==v',arg=first);assert page.locator('#coverage-items .article').count()==10;assert len(pages.store.calls)==1
  # Failing content is rejected before display and cannot create unsafe links.
  page.fill('#code','8517');page.route('**/api/code-news-coverage',lambda route:route.fulfill(status=200,content_type='application/json',body=json.dumps({'state':'complete_mutable_read','items':[{'article_context':{'state':'source_context','url':'javascript:alert(1)'}}]})));page.click('#start');page.wait_for_function('()=>document.getElementById("status").textContent.includes("Invalid response")');assert page.locator('#coverage-items a').count()==0
  assert not errors,errors;assert not csp,csp;assert not external,external;browser.close()
 (out/'browser.json').write_text(json.dumps({'result':'PASS','external':external,'js_errors':errors,'csp':csp,'source_calls':len(pages.store.calls),'synthetic_local_only':True},indent=2));print('PASS D4 actual broker/browser local fixture')
finally:server.shutdown();pages.close()
