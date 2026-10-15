"""Real bundled renderer/worker, local synthetic responses. NEVER calls provider.
OpenFreeMap style is pinned; remote requests are intercepted by Playwright.
Synthetic empty vector tiles verify plumbing, NOT real street data fidelity.
"""
import sys,threading,json,base64,logging
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration.public_preview_builder import build_public_preview
from tests.test_code_news_coverage_binding_prep import SAMPLE
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
out=Path('/tmp/map-m3/evidence');out.mkdir(parents=True,exist_ok=True)
origin='http://127.0.0.1:8793'
from integration.news_api import create_app
from integration import public_map_m2 as m2,public_map_m3 as m3
app=create_app(authorize=lambda _:True);m2.install(app,origin,lambda:{'geo':[]});m3.install(app,origin)
logging.getLogger('werkzeug').setLevel(logging.ERROR)
server=make_server('127.0.0.1',8793,app,threaded=True);threading.Thread(target=server.serve_forever,daemon=True).start()
import struct,zlib
def chunk(t,b):return struct.pack('!I',len(b))+t+b+struct.pack('!I',zlib.crc32(t+b)&0xffffffff)
png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',256,256,8,6,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+bytes([202,221,230,255])*256)*256))+chunk(b'IEND',b'')
requests=[];unexpected=[];mode=['ok'];errors=[];csp=[];console=[];pending=[]
def route(r):
 u=r.request.url
 if u.startswith(origin+'/'):return r.continue_()
 requests.append(u)
 if not u.startswith('https://tiles.openfreemap.org/'):
  unexpected.append(u);return r.abort()
 headers={'Access-Control-Allow-Origin':'*','Cache-Control':'no-store'}
 if mode[0]=='hang':pending.append(r);return
 if mode[0]=='fail':return r.fulfill(status=503,headers=headers,body='fixture unavailable')
 if u.endswith('/planet'):return r.fulfill(status=200,headers=headers,content_type='application/json',body=json.dumps({'tilejson':'3.0.0','tiles':['https://evil.test/steal/{z}/{x}/{y}.pbf'if mode[0]=='evil'else'https://tiles.openfreemap.org/planet/fixture/{z}/{x}/{y}.pbf'],'minzoom':0,'maxzoom':14,'attribution':'<img src=x onerror=alert(1)>'}))
 if u.endswith('.pbf'):return r.fulfill(status=200,headers=headers,content_type='application/x-protobuf',body=b'')
 if '.json'in u:return r.fulfill(status=200,headers=headers,content_type='application/json',body='{}')
 if '.png'in u:return r.fulfill(status=200,headers=headers,content_type='image/png',body=png)
 unexpected.append(u);return r.abort()
try:
 with sync_playwright()as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);context=b.new_context(viewport={'width':1100,'height':844});context.route('**/*',route);page=context.new_page();page.on('pageerror',lambda x:errors.append(str(x)));page.on('console',lambda x:console.append(x.text));page.on('console',lambda x:csp.append(x.text)if'violates'in x.text or'Content Security Policy'in x.text else None)
  page.goto(origin+'/workspace/map');page.evaluate("()=>{const old=L.MaplibreGL.prototype._initGL;L.MaplibreGL.prototype._initGL=function(){old.call(this);window.__testGL=this._glMap;window.__glEvents=[];for(const ev of ['load','idle','error','dataloading','data'])this._glMap.on(ev,e=>__glEvents.push({type:ev,error:e.error?.message}));}}");assert page.locator('#m3-start').count()==1
  assert not requests;page.locator('#m3-start').click();assert 'Load reference map first'in page.locator('#m3-status').inner_text();assert not requests
  page.locator('#load').click();page.wait_for_function('()=>window.__map');assert not requests
  page.locator('#m3-start').dispatch_event('click');page.wait_for_timeout(100);assert not requests;assert not page.evaluate('__m3Audit().active')
  page.locator('#m3-start').click();page.wait_for_function("()=>document.getElementById('m3-status').textContent.includes('Online streets shown')",timeout=25000)
  assert page.evaluate('__m3Audit().active');assert page.locator('#m3-credit').is_visible();assert 'OpenMapTiles' in page.locator('#m3-credit').inner_text();assert 'OpenStreetMap contributors' in page.locator('#m3-credit').inner_text();assert page.locator('#m3-credit img').count()==0;assert page.evaluate('__map.getMaxZoom()')==18
  for width in [1100,390,320]:
   page.set_viewport_size({'width':width,'height':844});page.evaluate('__map.invalidateSize();void 0');page.wait_for_timeout(500);assert page.locator('#m3-credit').is_visible();assert page.evaluate("()=>{const c=document.getElementById('m3-credit').getBoundingClientRect(),m=document.getElementById('map').getBoundingClientRect();return c.width>0&&c.height>0&&c.top>=m.top&&c.bottom<=m.bottom&&c.left>=m.left&&c.right<=m.right+1}");assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.locator('#map').screenshot(path=str(out/f'm3-renderer-fixture-{width}.png'));page.locator('#m3-credit').screenshot(path=str(out/f'm3-credit-{width}.png'));page.screenshot(path=str(out/f'm3-page-{width}.png'),full_page=True)
  page.evaluate('__map.setView([13.08,80.27],16,{animate:false});void 0');page.wait_for_timeout(400);assert page.evaluate('__map.getZoom()')==16
  page.locator('#m3-stop').click();assert not page.evaluate('__m3Audit().active');assert page.evaluate('__map.getMaxZoom()')==8;assert page.locator('#map canvas').count()==1 # Leaflet reference canvas only
  before=len(requests);page.wait_for_timeout(700);assert len(requests)==before
  page.evaluate('()=>{window.__savedInit=L.MaplibreGL.prototype._initGL;L.MaplibreGL.prototype._initGL=()=>{throw Error("WebGL fixture unavailable")}}');page.locator('#m3-start').click();assert not page.evaluate('__m3Audit().active');assert page.locator('.leaflet-gl-layer').count()==0;page.evaluate('()=>{L.MaplibreGL.prototype._initGL=window.__savedInit}')
  mode[0]='fail';page.locator('#m3-start').click();page.wait_for_function("()=>document.getElementById('m3-status').textContent.includes('unavailable')",timeout=20000);assert not page.evaluate('__m3Audit().active');before=len(requests);page.wait_for_timeout(700);assert len(requests)==before
  page.locator('#map').screenshot(path=str(out/'m3-failure-fallback.png'));page.screenshot(path=str(out/'m3-failure-page.png'),full_page=True)
  page.locator('#refresh').click();assert page.locator('#status').inner_text().startswith('0 country-tagged');assert page.evaluate('__map.getMaxZoom()')==8
  mode[0]='evil';page.locator('#m3-start').click();page.wait_for_function("()=>document.getElementById('m3-status').textContent.includes('unavailable')",timeout=20000);assert not page.evaluate('__m3Audit().active');assert not unexpected
  mode[0]='hang';page.locator('#m3-start').click();page.wait_for_function("()=>document.getElementById('m3-status').textContent.includes('unavailable')",timeout=20000);assert not page.evaluate('__m3Audit().active');assert page.locator('.leaflet-gl-layer').count()==0;before=len(requests);page.wait_for_timeout(700);assert len(requests)==before
  for r in pending:
   try:r.abort()
   except:pass
  pending.clear()
  mode[0]='ok';page.locator('#m3-start').click();page.wait_for_function("()=>document.getElementById('m3-status').textContent.includes('Online streets shown')",timeout=25000)
  page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});document.dispatchEvent(new Event('visibilitychange'))");assert not page.evaluate('__m3Audit().active');page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,get:()=>false});document.dispatchEvent(new Event('visibilitychange'))");assert not page.evaluate('__m3Audit().active');before=len(requests);page.wait_for_timeout(700);assert len(requests)==before
  assert not unexpected,unexpected;assert not errors,errors;assert not csp,csp
  b.close()
 (out/'browser.json').write_text(json.dumps({'result':'PASS','remote_requests_intercepted':len(requests),'unexpected':unexpected,'errors':errors,'csp':csp,'startup_failure_checked':True,'high_zoom_checked':True,'fixture_only':True,'real_provider_tiles_tested':False,'requests':requests},indent=2));print('PASS M3 browser',len(requests),'intercepted, no provider tile calls')
except Exception:
 try:
  print(page.evaluate("()=>({status:document.getElementById('m3-status').textContent,events:window.__glEvents,gl:window.__testGL?{loaded:__testGL.loaded(),tiles:__testGL.areTilesLoaded()}:null})"));page.screenshot(path=str(out/'m3-debug.png'),full_page=True)
 except:pass
 print(json.dumps({'requests':requests,'unexpected':unexpected,'errors':errors,'csp':csp,'console':console},indent=2));raise
finally:server.shutdown()
