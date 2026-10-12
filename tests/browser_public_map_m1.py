import sys,threading,json,base64,time
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]
BASE=Path(os.environ.get('MAP_BASE_ROOT',ROOT))
if (ROOT/'source').is_dir():sys.path[:0]=[str(ROOT/'source'),str(BASE)]
else:sys.path.insert(0,str(ROOT))
from integration.news_api import create_app
from integration import public_map_prep as m
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
out=Path(os.environ.get('MAP_EVIDENCE',ROOT/'map-m1-evidence'));out.mkdir(exist_ok=True);origin='http://127.0.0.1:8788'
raw={'geo':[{'title':'SIMULATED India source <img src=x onerror=alert(1)>','country':'India','source':'Local fixture','url':'https://news.example.com/a','created_at':'2026-10-12T00:00:00Z'},{'title':'SIMULATED Congo unmapped','country':'Congo','source':'Local fixture','url':'https://news.example.com/b'}]}
app=create_app(authorize=lambda r:True);fixture=m.FakeMap(lambda:raw);m.install(app,origin,fixture)
server=make_server('127.0.0.1',8788,app,threaded=True);threading.Thread(target=server.serve_forever,daemon=True).start()
report=[]
with sync_playwright()as p:
 browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
 for width in [390,1100]:
  page=browser.new_page(viewport={'width':width,'height':844});errs=[];requests=[];csp=[]
  page.on('console',lambda msg:csp.append(msg.text)if 'Content Security Policy' in msg.text or 'violates' in msg.text else None)
  page.on('request',lambda r:requests.append(r.url))
  def route(r):
   if '/tiles/'in r.request.url:r.fulfill(status=503,body='simulated unavailable')
   elif r.request.url.startswith(origin):r.continue_()
   else:errs.append(r.request.url);r.abort()
  page.route('**/*',route);page.goto(origin+'/workspace/map');assert not any('/tiles/'in x for x in requests)
  page.locator('#load').click();page.locator('#articles article').first.wait_for();assert page.locator('#articles img').count()==0
  assert page.locator('#articles article').count()==2;assert 'latest-100' in page.locator('#status').inner_text()
  page.screenshot(path=str(out/f'map-{width}.png'),full_page=True)
  page.locator('#tiles').click();page.wait_for_function('()=>window.__mapGate.paused===true')
  n=sum('/tiles/'in x for x in requests);time.sleep(.2);assert n==sum('/tiles/'in x for x in requests)
  assert page.evaluate('__mapGate.maxActive')<=4;assert '3 errors' in page.locator('#tile-status').inner_text()
  page.locator('#tiles').click();assert '60 seconds' in page.locator('#tile-status').inner_text();assert n==sum('/tiles/'in x for x in requests)
  fixture.reader=lambda:(_ for _ in()).throw(ValueError('not available'));page.locator('#refresh').click();page.wait_for_function("()=>document.querySelector('#status').textContent.includes('news cleared')");assert page.locator('#articles article').count()==0
  fixture.reader=lambda:raw
  page.evaluate('if(window.__mapLayer&&window.__map)window.__map.removeLayer(window.__mapLayer)');page.wait_for_timeout(400)
  assert not errs;assert not csp,csp;assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  report.append({'width':width,'tile_requests':n,'csp':csp,'external_requests':errs,'max_active':page.evaluate('__mapGate.maxActive')});page.close()
 # Valid PNG lifecycle, delayed callbacks; ordinary pan/zoom and hidden->visible.
 page=browser.new_page(viewport={'width':1100,'height':844});external=[];latecsp=[]
 page.on('console',lambda msg:latecsp.append(msg.text)if 'Content Security Policy'in msg.text or 'violates'in msg.text else None)
 png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg==')
 def valid_route(r):
  if '/tiles/'in r.request.url:r.fulfill(status=200,content_type='image/png',body=png,headers={'Cache-Control':'public,max-age=604800'})
  elif r.request.url.startswith(origin):r.continue_()
  else:external.append(r.request.url);r.abort()
 page.route('**/*',valid_route);page.goto(origin+'/workspace/map');page.locator('#load').click();page.locator('#articles article').first.wait_for();page.locator('#tiles').click()
 page.wait_for_function('()=>__mapGate.active===0&&__mapGate.queue.length===0')
 snapshots=[]
 for action in ['__map.zoomIn()','__map.zoomIn()','__map.zoomIn()','__map.panBy([500,0])','__map.panBy([-500,0])']:
  page.evaluate(action);page.wait_for_timeout(350);page.wait_for_function('()=>__mapGate.active===0&&__mapGate.queue.length===0')
  v=page.evaluate('()=>({loaded:document.querySelectorAll(".leaflet-tile-loaded").length,images:document.querySelectorAll(".leaflet-tile").length,active:__mapGate.active,queued:__mapGate.queue.length,jobs:__mapGate.jobs.size})');assert v['loaded']>0 and v['active']==0 and v['queued']==0;snapshots.append(v)
 # Interrupt genuinely in-flight tiles; unload must free slots even without load/error.
 page.evaluate('__map.zoomIn();__map.panBy([600,0]);__mapVisibility(false)');assert page.evaluate('__mapGate.active')==0 and page.evaluate('__mapGate.jobs.size')==0
 page.evaluate('__mapVisibility(true)');page.wait_for_function('()=>__mapGate.active===0&&__mapGate.queue.length===0');assert page.locator('.leaflet-tile-loaded').count()>0
 page.evaluate('__map.removeLayer(__mapLayer)');page.wait_for_timeout(400);assert not latecsp,latecsp
 assert not external;report.append({'valid_png_pan_zoom_revisit':snapshots,'hidden_visible_reloaded':True,'csp_after_final_removal_settle':latecsp,'max_active':page.evaluate('__mapGate.maxActive')});page.close()
 browser.close()
server.shutdown();print(json.dumps(report,indent=2));(out/'browser.json').write_text(json.dumps(report,indent=2))
