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
origin='http://127.0.0.1:8813'
raw={'geo':[dict(url='https://example.com/one',title='HS 100630 reported',summary='Rice')]}
app=create_app(reader=lambda:raw,authorize=lambda _:True,allowed_origin=origin)
@app.after_request
def shell(r):
 if request.path=='/workspace':
  r.direct_passthrough=False;r.set_data(r.get_data(as_text=True).replace('src="/workspace/finder/index.html"','src="/workspace/finder/offline.html"'))
 return r
install_mount(app);code_install(app,origin,lambda:raw);app.extensions['code_news_public'].model=Links([dict(system='HS',edition='2022',code='100630',description='Rice')],[]);install(app,origin)
server=make_server('127.0.0.1',8813,app,threaded=True);threading.Thread(target=server.serve_forever,daemon=True).start()
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
    else:r.continue_()
   p.route('**/*',route);p.goto(origin+'/workspace');p.locator('[data-view=finder]').click()
   f=p.frame_locator('#finder');f.locator('#q-main').wait_for()
   p.evaluate("document.querySelector('#finder').contentWindow.location.hash='code=0:100630'")
   f.locator('.detail-code').wait_for();print('IDENTITY',width,f.locator('.detail-code').inner_text(),f.locator('.detail-head .sys-tag').inner_text())
   p.get_by_role('button',name='Check supplied-page news').wait_for();p.get_by_role('button',name='Check supplied-page news').click()
   p.get_by_text('Latest-100 reported mentions. Not full-store or meaning-based search.',exact=True).wait_for()
   assert p.locator('#related a').count()==1
   assert not any('/api/finder-context' in u or '/api/related-news' in u for u in calls)
   assert not errors,errors
   p.screenshot(path=str(EVIDENCE/f'real-finder-{width}.png'),full_page=True)
   results.append(dict(width=width,real_finder=True,manual_forward=True,no_private_paths=True));p.close()
  b.close()
finally:server.shutdown()
print(results)
