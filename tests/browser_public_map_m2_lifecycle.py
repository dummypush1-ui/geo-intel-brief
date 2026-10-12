import os
import sys,threading,time,base64,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,os.environ.get('M2_BASE',str(ROOT)));import integration;integration.__path__.insert(0,str(ROOT/'integration'))
from integration.news_api import create_app
from integration import public_map_m2 as m
from flask import Response
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
app=create_app(authorize=lambda _:True);origin='http://127.0.0.1:8789';m.install(app,origin,lambda:{'geo':[]},local_provider=m.LocalProvider());delay=[0];png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg==')
@app.get('/workspace/map-fixture/tiles/<int:z>/<int:x>/<int:y>.png')
def tile(z,x,y):
 time.sleep(delay[0]);return Response(png,mimetype='image/png')
server=make_server('127.0.0.1',8789,app,threaded=True);threading.Thread(target=server.serve_forever,daemon=True).start()
src=(m.ROOT/'map.js').read_text();variants={'baseline':src,'eviction':src.replace('this._removeTile(key);}return L.TileLayer.prototype._update','void 0;}return L.TileLayer.prototype._update'),'remove':src.replace('if(tile&&tile.el._record)gate.cancel(tile.el._record);',''),'abortGIF':re.sub(r'_abortLoading\(\)\{for\(const key.*?\},\n _update', '_abortLoading(){return L.TileLayer.prototype._abortLoading.call(this);},\n _update',src)};out=[]
with sync_playwright()as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
 for name,script in variants.items():
  assert name=='baseline'or script!=src
  page=b.new_page(viewport={'width':1100,'height':844});violations=[];errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.add_init_script("window.__csp=[];document.addEventListener('securitypolicyviolation',e=>__csp.push({blocked:e.blockedURI,directive:e.effectiveDirective}));")
  page.route('**/map-fixture/map.js',lambda route:route.fulfill(body=script,content_type='application/javascript'))
  page.goto(origin+'/workspace/map');page.locator('#load').click();page.wait_for_function('()=>window.__map');page.evaluate('window.__now=0;__gate.clock=()=>__now;__map.setZoom(5);void 0');delay[0]=0;page.locator('#tiles').click()
  def audit():
   v=page.evaluate('__audit()');assert v['dom']==v['tiles']==v['jobs']==v['levels']<=64,v;assert v['active']==v['activeJobs']<=4 and not v['outside']and not v['detached']and not v['srcOutside'],v;assert not page.evaluate('__csp'),page.evaluate('__csp');assert not errors,errors;return v
  def settle():
   for _ in range(80):
    page.evaluate('__now+=1001;__gate.pump()');page.wait_for_timeout(40);v=audit()
    if not v['active']and not v['queue']:return
   assert False,'not settled'
  detected=None
  try:
   settle();assert page.evaluate('__audit().jobs')>0
   # Drive inner lifecycle directly so motion-layer disposal cannot mask obsolete eviction.
   page.evaluate("__layer._removeTile(Object.keys(__layer._tiles)[0]);void 0");audit()
   page.evaluate("__layer._pruneTiles=()=>{};__layer._update(L.latLng(20,-80));void 0");audit()
   keys=page.evaluate('Object.values(__layer._tiles).map(t=>[t.coords.x,t.coords.y])');rng=page.evaluate('(()=>{const r=__layer._pxBoundsToTileRange(__layer._getTiledPixelBounds(L.latLng(20,-80)));return [r.min.x,r.max.x,r.min.y,r.max.y]})()');assert all(rng[0]<=x<=rng[1]and rng[2]<=y<=rng[3]for x,y in keys),(keys,rng)
   page.evaluate('__visibility(false);__map.setZoom(3);__now+=61000;void 0');delay[0]=.4;page.evaluate('__activate();__now+=1001;__gate.pump()');assert page.evaluate('__audit().active')>0
   page.evaluate('__layer._tileZoom=8;__layer._abortLoading();void 0');page.wait_for_timeout(50);audit();assert page.evaluate('__audit().jobs')==0
   delay[0]=0;page.evaluate('__visibility(false);__now+=61000;void 0');page.set_viewport_size({'width':8000,'height':4000});page.evaluate("__map.getContainer().style.width='8000px';__map.getContainer().style.height='4000px';__map.invalidateSize();__activate();void 0");page.wait_for_timeout(550);audit();assert page.evaluate('__oversized===true && __audit().jobs===0')
  except AssertionError as e:
   import traceback;detected=traceback.format_exc()
  if name=='baseline':
   assert detected is None,detected
   # Deliberate, isolated forbidden data image proves event monitoring non-vacuous.
   page.evaluate("let i=document.createElement('img');i.src='data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==';document.body.append(i)");page.wait_for_timeout(50);v=page.evaluate('__csp');assert any(x['directive']=='img-src'and x['blocked']=='data'for x in v),v
   out.append({'variant':name,'pass':True,'nonvacuous_csp':v,'oversized':True})
  else:assert detected is not None,name;out.append({'variant':name,'killed':True,'reason':detected,'csp':page.evaluate('__csp')})
  page.close()
 b.close()
server.shutdown();(Path(os.environ.get('MAP_EVIDENCE_DIR','/tmp/public-map-m2-evidence'))/'lifecycle-mutants.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
