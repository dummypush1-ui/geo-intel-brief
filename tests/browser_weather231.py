"""231 SIMULATED local weather geometry probe, no real service request."""
import sys,threading,json,os,hashlib
from pathlib import Path
from urllib.parse import urlsplit
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration.news_api import create_app
from werkzeug.serving import make_server,WSGIRequestHandler
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=Path(os.environ.get('WEATHER231_OUT','/tmp/weather231-review'));OUT.mkdir(parents=True,exist_ok=True)
BEFORE=os.environ.get('WEATHER231_BEFORE')=='1'
class Quiet(WSGIRequestHandler):
 def log_request(self,*a,**k):pass
server=make_server('127.0.0.1',0,create_app(authorize=lambda r:True,finder_network_preview_enabled=True),request_handler=Quiet);origin='http://127.0.0.1:'+str(server.server_port);threading.Thread(target=server.serve_forever,daemon=True).start()
result={'phase':'BEFORE231'if BEFORE else'AFTER231','started_at':datetime.now(timezone.utc).isoformat(),'cases':{},'outbound_successes':0,'simulated':True};geometry_failures=[]
try:
 with sync_playwright()as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox']);result['chromium']=b.version
  result['fixture_caption']='SIMULATED local fixture numbers, not official weather'
  for mode in ['success','stress0','stress359','marine503','forecast503']:
   c=b.new_context(viewport={'width':1100,'height':900},timezone_id='Asia/Kolkata');c.add_init_script("{const D=Date;window.Date=class extends D{constructor(...a){super(...(a.length?a:[1791576000000]));}static now(){return 1791576000000;}};Math.random=()=>0.25;}")
   calls=[];unexpected=[];errors=[];violations=[]
   def route(r):
    u=urlsplit(r.request.url)
    if u.scheme+'://'+u.netloc==origin:return r.continue_()
    call={'method':r.request.method,'host':u.hostname,'path':u.path};ep=tuple(call.values())
    if ep==('GET','api.frankfurter.dev','/v1/2025-09-04..2026-10-09'):calls.append({**call,'fixture':'expected FX abort'});return r.abort()
    stress=mode.startswith('stress');direction=359 if mode=='stress359'else 0
    if ep==('GET','api.open-meteo.com','/v1/forecast'):
     calls.append({**call,'fixture':'SIMULATED forecast'});return r.fulfill(status=503 if mode=='forecast503'else 200,json={'current':{'temperature_2m':123456789.123 if stress else 30,'wind_speed_10m':123456789 if stress else 12,'wind_direction_10m':direction if stress else 90,'time':'2026-10-10T05:30'}},headers={'Access-Control-Allow-Origin':'*'})
    if ep==('GET','marine-api.open-meteo.com','/v1/marine'):
     calls.append({**call,'fixture':'SIMULATED marine'});return r.fulfill(status=503 if mode=='marine503'else 200,json={}if mode=='marine503'else{'current':{'wave_height':123456789.123 if stress else 1.5,'wave_direction':direction if stress else 90,'wave_period':123456789 if stress else 6,'swell_wave_height':123456789.123 if stress else 1}},headers={'Access-Control-Allow-Origin':'*'})
    unexpected.append(call);r.abort()
   c.route('**/*',route);page=c.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:violations.append('CSP violation')if'Content Security Policy'in m.text else None)
   page.goto(origin+'/workspace/finder/index.html');page.get_by_role('tab',name='Trade tools',exact=True).click();page.locator('#portwx-toggle').click();page.wait_for_function('()=>!V.portWxBusy')
   panel=page.locator('#portwx-pick').locator('..');selector='#portwx-pick + .report-table-wrap .report-table'
   if mode=='forecast503':assert page.evaluate('V.portWxErr && V.portWxData===null');page.get_by_text('Live weather unavailable right now',exact=False).wait_for()
   elif mode=='marine503':assert page.evaluate('!V.portWxErr && V.portWxData.wave===null')
   else:assert panel.locator(selector).count()==1
   text=panel.inner_text();case={'text':text,'geometry':{}}
   for width in [320,390,1100]:
    for theme in ['light','dark']:
     page.set_viewport_size({'width':width,'height':1000});page.evaluate("theme=>document.documentElement.classList.toggle('dark-mode',theme==='dark')",theme)
     panel.scroll_into_view_if_needed();panel.screenshot(path=str(OUT/f'{mode}-{width}-{theme}.png'))
     if mode!='forecast503':
      dims=panel.locator('.report-table-wrap').evaluate('e=>({client:e.clientWidth,scroll:e.scrollWidth})');cell=panel.locator('td').evaluate_all("es=>es.map(e=>{const r=e.getBoundingClientRect(),t=e.closest('table').getBoundingClientRect();return{inside:r.left>=t.left-.5&&r.right<=t.right+.5,overflow:e.scrollWidth>e.clientWidth,text:e.innerText};})")
      label_lines=panel.locator('td:first-child').evaluate_all("es=>es.map(e=>{let n=e.firstChild;return [...e.innerText.matchAll(/\\S+/g)].map(m=>{let r=document.createRange();r.setStart(n,m.index);r.setEnd(n,m.index+m[0].length);return r.getClientRects().length;});})")
      assert all(x==1 for row in label_lines for x in row)
      ok=dims['scroll']<=dims['client'] and all(x['inside'] and not x['overflow']for x in cell)
      if not ok:geometry_failures.append(f'{mode}-{width}-{theme}')
      case['geometry'][f'{width}-{theme}']={'wrapper':dims,'cells':cell,'fit':ok}
   if mode=='success':
    assert panel.locator('td').count()==8;assert all(x in text for x in ['Temperature','30.0 °C','Wind','12 km/h from E','Wave height','1.5 m, E, period 6 s','Swell','1.0 m','2026-10-10 05:30 IST','NOT a government source'])
    page.locator('#portwx-pick').focus();assert page.evaluate("document.activeElement.id==='portwx-pick'");page.locator('#portwx-pick').press('ArrowDown');page.locator('#portwx-pick').press('Enter');page.wait_for_function("()=>!V.portWxBusy")
    # Select through native control after a keyboard focus/Tab check, not a mouse-only UI.
    page.locator('#portwx-pick').press('Escape');page.locator('#portwx-pick').focus();page.locator('#portwx-pick').press('Tab');page.wait_for_function("()=>document.activeElement.id!=='portwx-pick'");page.locator('#portwx-pick').select_option('Chennai');page.wait_for_function("()=>!V.portWxBusy && V.portWx==='Chennai'")
    page.get_by_text('Port trade statistics - 13 major ports, traffic + commodity (official)',exact=True).click();other=page.locator('#portwx-pick').locator('..').locator('xpath=preceding-sibling::*')
    # All non-weather tables retain their original computed 680px minimum.
    unrelated=page.locator('table.report-table').evaluate_all("es=>es.filter(e=>!e.matches('#portwx-pick + .report-table-wrap .report-table')).map(e=>getComputedStyle(e).minWidth)");assert unrelated and all(x=='680px'for x in unrelated)
    case['unrelated_table_min_width']=unrelated;case['keyboard_port_control']=True
    page.set_viewport_size({'width':320,'height':1000})
    assert page.locator('table.report-table').evaluate_all("es=>es.filter(e=>!e.matches('#portwx-pick + .report-table-wrap .report-table')).some(e=>e.closest('.report-table-wrap').scrollWidth>e.closest('.report-table-wrap').clientWidth)")
    if not BEFORE:
     # Widening the selector must break an unrelated-table check. Test-only mutation, restored before any final capture.
     css=page.locator('style').all_text_contents();style=page.evaluate("[...document.querySelectorAll('style')].find(e=>e.textContent.includes('231: only')).textContent")
     page.evaluate("()=>{let e=[...document.querySelectorAll('style')].find(e=>e.textContent.includes('231: only'));e.textContent=e.textContent.replaceAll('#portwx-pick + .report-table-wrap .report-table','.report-table');}")
     assert page.locator('table.report-table').evaluate_all("es=>es.filter(e=>!e.matches('#portwx-pick + .report-table-wrap .report-table')).some(e=>getComputedStyle(e).minWidth!=='680px')")
     page.evaluate("s=>[...document.querySelectorAll('style')].find(e=>e.textContent.includes('231: only')).textContent=s",style)
     select=page.locator('#portwx-pick');select.evaluate("e=>e.insertAdjacentHTML('afterend','<span id=fixture-break></span>')")
     assert panel.locator(selector).count()==0;assert panel.locator('table').evaluate("e=>getComputedStyle(e).minWidth==='680px'")
     page.locator('#fixture-break').evaluate('e=>e.remove()')
     case['scope_mutations_detected']=True
   assert not unexpected and not errors and not violations,(unexpected,errors,violations);case['calls']=sorted(calls,key=lambda x:(x['host'],x['path']));result['cases'][mode]=case;c.close()
  b.close()
finally:server.shutdown()
result['geometry_failures']=geometry_failures;result['finished_at']=datetime.now(timezone.utc).isoformat();(OUT/'result.json').write_text(json.dumps(result,indent=2));assert not geometry_failures, 'Weather geometry FAIL: '+','.join(geometry_failures)
