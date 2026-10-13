"""Real preserved Finder HTML in real Chrome, fixture news only."""
import sys,threading,json
from pathlib import Path
import os,tempfile
EVIDENCE=Path(os.environ.get('RELATIONSHIP_EVIDENCE_DIR') or tempfile.mkdtemp(prefix='relationship-evidence-'));EVIDENCE.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from flask import request
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
from integration.news_api import create_app
from integration.news_finder_navigation_prep import install_mount
from integration.code_news_public import install as code_install
from integration.code_news_links import Links
from integration.relationship_navigation import install
origin='https://example.test'
from integration.public_live_builder import build_public_live_preview
from tests.test_code_news_coverage_binding_prep import LIVE,Client,Tests
flags=dict(LIVE,PUBLIC_CODE_NEWS_ENABLED='true',PUBLIC_CODE_NEWS_SCOPE_REVIEWED='true',PUBLIC_AI_ANSWERS_ENABLED='true',PUBLIC_WEEKLY_PDF_ENABLED='true',PUBLIC_WEEKLY_FULL_STORE_ENABLED='true',PUBLIC_NEWS_FULL_PAGES_ENABLED='true',PUBLIC_BRICS_STREAMS_ENABLED='true',PUBLIC_WEATHER_UI_ENABLED='true',PUBLIC_WEATHER_ENABLED='true',OPEN_METEO_TERMS_ACK='2026-10-11/noncommercial',PUBLIC_WEATHER_NONCOMMERCIAL='true',PUBLIC_WEATHER_CAPACITY_REVIEWED='true',PUBLIC_WEATHER_SINGLE_WORKER_VERIFIED='true',PUBLIC_MAP_ENABLED='true',PUBLIC_MAP_M2_ENABLED='true',PUBLIC_RELATIONSHIP_NAV_ENABLED='true')
client=Client();app=build_public_live_preview(flags,client_factory=lambda *a,**k:client,coverage_binding_provider=Tests().binding)
raw={'geo':[dict(url='https://example.com/one',title='HS 100630 reported',summary='Rice')]}
app.extensions['code_news_public'].model=Links([dict(system='HS',edition='2022',code='100630',description='Rice')],[])
app.extensions['code_news_public'].reader=lambda:raw
results=[]
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
  for width in [390,1100]:
   app.extensions['code_news_public'].calls=0
   p=b.new_page(viewport={'width':width,'height':950});p.set_default_timeout(20000);errors=[];calls=[]
   p.on('pageerror',lambda e:errors.append(str(e)))
   def route(r):
    calls.append(r.request.url)
    if not r.request.url.startswith(origin):r.abort()
    else:
     from urllib.parse import urlsplit
     response=app.test_client().open(urlsplit(r.request.url).path+('?' + urlsplit(r.request.url).query if urlsplit(r.request.url).query else ''),method=r.request.method,base_url=origin,headers=r.request.headers,data=r.request.post_data)
     r.fulfill(status=response.status_code,headers=dict(response.headers),body=response.data)
   p.route('**/*',route);p.goto(origin+'/workspace');p.locator('[data-view=finder]').click()
   f=p.frame_locator('#finder');f.locator('#q-main').wait_for()
   p.evaluate("document.querySelector('#finder').contentWindow.location.hash='code=0:100630'")
   f.locator('.detail-code').wait_for();print('IDENTITY',width,f.locator('.detail-code').inner_text(),f.locator('.detail-head .sys-tag').inner_text())
   p.get_by_role('button',name='Check supplied-page news').wait_for();p.get_by_role('button',name='Check supplied-page news').click()
   p.get_by_text('Latest-100 reported mentions. Not full-store or meaning-based search.',exact=True).wait_for()
   assert p.locator('#related a').count()==1
   assert not any('/api/finder-context' in u or '/api/related-news' in u for u in calls)
   assert not errors,errors
   p.screenshot(path=str(EVIDENCE/f'combined-finder-{width}.png'),full_page=True)
   for path in ['/workspace/weather','/workspace/weekly','/workspace/countries','/workspace/map','/workspace/brics-streams','/workspace/ai-answers','/workspace/code-news']:
    p.goto(origin+path);p.get_by_role('link',name='Reported code-news',exact=True).wait_for();assert p.locator('body').count()==1
   results.append(dict(width=width,real_finder=True,manual_forward=True,no_private_paths=True));p.close()
  b.close()
finally:app.extensions['coverage_close']()
print(results)
