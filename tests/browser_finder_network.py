# 231: CSS-only weather wrapping, derived snapshot pins.
"""230 local SIMULATED network fixture, never a real service accuracy check."""
import sys,threading,json,os,hashlib
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration.news_api import create_app
from integration.finder_network import FINDER_CONNECT_ORIGINS
from werkzeug.serving import make_server,WSGIRequestHandler
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
PINS={'src/app.js': 'bcd406d75b27b053fc5716d141ca278932115f14e39eca74d19a2284fc59d313', 'index.html': '8e1ce9c7fa5da880085afb2b8a20e6fbc3195d8b24f4ffdde4bee09c787d0967', 'integration/news_api.py': '1b58e128aed786137908675be01f8629462ccaf24bf969cea4d6ecd86a52edb3', 'feature_finder_prep/shell.py': 'dc2e4d2b34e859cef7180ae880f2f52c303c97502bc836944ff87da6722ed618', 'integration/finder_network.py': '07fc045266659eadbefef1b52829c4e185ccdc70a3362fbd076a9d79719b3232'}
OUT=Path(os.environ.get('FINDER230_OUT','/tmp/finder230-review'));OUT.mkdir(parents=True,exist_ok=True)
PLACEHOLDER='SYNTHETIC-PLACEHOLDER-NOT-A-KEY'
NARRATIVE='SIMULATED TEST plain words. Not a verified AI answer. <b>literal marker</b> & test.'
RATES={'2025-10-09':{'INR':80},'2026-09-09':{'INR':85},'2026-10-09':{'INR':90}}
for path,sha in PINS.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha
class Quiet(WSGIRequestHandler):
 def log_request(self,*a,**kw):pass
app=create_app(authorize=lambda r:True,finder_network_preview_enabled=True)
server=make_server('127.0.0.1',0,app,request_handler=Quiet);origin='http://127.0.0.1:'+str(server.server_port)
threading.Thread(target=server.serve_forever,daemon=True).start()
result={'phase':'AFTER230','started_at':datetime.now(timezone.utc).isoformat(),'simulated':True,'outbound_successes':0,'source_pins':PINS,'cases':{}}
try:
 with sync_playwright()as p:
  browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox']);result['chromium']=browser.version
  for mode in ['success','no-key','429','weather-failure','fx-failure','marine-failure']:
   context=browser.new_context(viewport={'width':1100,'height':900},timezone_id='Asia/Kolkata')
   context.add_init_script("{const D=Date;class F extends D{constructor(...a){super(...(a.length?a:[1791576000000]));}static now(){return 1791576000000;}}window.Date=F;Math.random=()=>0.25;}window.fixtureCSP=[];window.addEventListener('securitypolicyviolation',e=>{fixtureCSP.push(e.violatedDirective);console.error('FIXTURE_CSP '+e.violatedDirective);});")
   if mode in ['success','429']:context.add_init_script("localStorage.setItem('hsn-gemini-api-key','SYNTHETIC-PLACEHOLDER-NOT-A-KEY');localStorage.setItem('hsn-ai-provider','mistral');")
   calls=[];unexpected=[];errors=[];csp_events=[]
   def route(r):
    u=urlsplit(r.request.url)
    if u.scheme+'://'+u.netloc==origin:return r.continue_()
    call={'method':r.request.method,'host':u.hostname,'path':u.path};endpoint=(r.request.method,u.hostname,u.path)
    headers={'Access-Control-Allow-Origin':'*'}
    if endpoint==('GET','api.frankfurter.dev','/v1/2025-09-04..2026-10-09'):
     calls.append({**call,'disposition':'SIMULATED FX HTTP failure'if mode=='fx-failure'else'SIMULATED FX rates'})
     return r.fulfill(status=503 if mode=='fx-failure'else 200,json={'rates':RATES},headers=headers)
    if endpoint==('GET','api.open-meteo.com','/v1/forecast'):
     calls.append({**call,'disposition':'SIMULATED forecast failure'if mode=='weather-failure'else'SIMULATED forecast'})
     return r.fulfill(status=503 if mode=='weather-failure'else 200,json={'current':{'temperature_2m':30,'wind_speed_10m':12,'wind_direction_10m':90,'time':'2026-10-10T05:30'}},headers=headers)
    if endpoint==('GET','marine-api.open-meteo.com','/v1/marine'):
     calls.append({**call,'disposition':'SIMULATED marine failure'if mode=='marine-failure'else'SIMULATED marine'})
     return r.fulfill(status=503 if mode=='marine-failure'else 200,json={}if mode=='marine-failure'else{'current':{'wave_height':1.5,'wave_direction':90,'wave_period':6,'swell_wave_height':1}},headers=headers)
    if endpoint==('POST','api.mistral.ai','/v1/chat/completions') and mode in ['success','429']:
     assert r.request.headers.get('authorization')=='Bearer '+PLACEHOLDER
     calls.append({**call,'disposition':'SIMULATED429'if mode=='429'else'SIMULATED AI success'})
     return r.fulfill(status=429 if mode=='429'else 200,json={'error':{'message':'SIMULATED quota'}}if mode=='429'else{'choices':[{'message':{'content':NARRATIVE}}]},headers=headers)
    unexpected.append(call);r.abort()
   context.route('**/*',route);page=context.new_page();page.on('pageerror',lambda e:errors.append(type(e).__name__));page.on('console',lambda m:csp_events.append(m.text)if m.text.startswith('FIXTURE_CSP ')else None)
   response=page.goto(origin+'/workspace/finder/index.html#code=0:090121');page.locator('#plain-go').wait_for(state='attached')
   csp=response.headers['content-security-policy'];assert all(x in csp for x in FINDER_CONNECT_ORIGINS);assert '*'not in csp
   case={'served_csp':csp,'fixture_numbers_not_official':True}
   def capture(name,selector):
    # Clearly label fixture screenshots without changing product code/state.
    for width in [1100,390]:
     page.set_viewport_size({'width':width,'height':900})
     page.locator(selector).scroll_into_view_if_needed()
     page.evaluate("if(!document.getElementById('fixture-label'))document.body.insertAdjacentHTML('beforeend','<div id=fixture-label style=\"position:fixed;bottom:0;left:0;right:0;z-index:999999;background:#fff3cd;padding:5px\">SIMULATED LOCAL TEST - not official weather/FX or verified AI</div>')")
     assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
     page.screenshot(path=str(OUT/f'{name}-{width}.png'),full_page=False)
     # 231 supersedes the historical230clipping check; current geometry stays live.
     if width==390 and name=='success-weather':
      table=page.locator('#portwx-pick').locator('..').locator('.report-table-wrap')
      dims=table.evaluate('(e)=>({client:e.clientWidth,scroll:e.scrollWidth})');assert dims['scroll']<=dims['client']
      assert table.locator('td').evaluate_all('es=>es.every(e=>e.scrollWidth<=e.clientWidth)')
      case['weather_mobile_table']='231: full weather cells fit without horizontal scroll'
    page.set_viewport_size({'width':1100,'height':900})
   if mode in ['success','no-key','429']:
    page.get_by_text('Plain words - what this code covers',exact=True).click();page.locator('#plain-go').click();page.wait_for_function('()=>!V.plainBusy')
    if mode=='success':
     page.get_by_text(NARRATIVE,exact=True).wait_for();assert page.locator('#plain-slot b').count()==0
     assert page.evaluate("localStorage.getItem('hsn-plain-0:090121')") ==NARRATIVE
    else:
     assert page.evaluate('!V.plain && !!V.plainErr');assert 'SIMULATED TEST plain words'not in page.locator('#plain-slot').inner_text()
     if mode=='no-key':assert page.evaluate('V.plainErr===BUILTIN_PROXY_UNAVAILABLE && !V.settingsOpen')
     else:assert 'limit reached' in page.locator('#plain-slot').inner_text()
    assert not page.locator('#plain-go').is_disabled();case['plain_state']='SIMULATED success'if mode=='success'else'unavailable error'if mode=='no-key'else'429 graceful error'
    capture(mode+'-plain','#plain-card')
   if mode in ['success','fx-failure']:
    if mode=='fx-failure':page.wait_for_function("()=>V.ccyImpact==='err'");assert page.locator('#ccy-impact').count()==0;case['fx_state']='HTTP failure hidden, no invented rate'
    if mode=='fx-failure':capture(mode+'-fx-error','#d-back')
    else:
     page.get_by_text('Currency impact - rupee vs dollar',exact=True).click();page.get_by_text('Plain arithmetic on ECB reference rates',exact=False).wait_for()
     text=page.locator('#ccy-impact').inner_text();year=(90/80-1)*100;month=(90/85-1)*100
     assert f'+{year:.1f}%'in text and f'+{month:.1f}%'in text and '2026-10-09'in text
     case['fx_arithmetic']={'rates':[80,85,90],'year_percent':round(year,1),'month_percent':round(month,1)}
     capture(mode+'-fx','#ccy-impact')
   if mode=='success':
    page.goto(origin+'/workspace/finder/index.html')
    page.get_by_role('tab',name='Live ships',exact=True).click();page.locator('#ships-toggle').click();page.wait_for_function("()=>V.shipsErr==='proxy-unavailable'")
    assert page.evaluate('!AIS_PROXY_URL && !V.shipsBusy && V.shipsData===null && shipsTimer===null');assert page.locator('#ships-slot').inner_text().endswith(page.evaluate('BUILTIN_PROXY_UNAVAILABLE'))
    for _ in range(2):page.locator('#ships-toggle').click()
    assert page.evaluate("V.shipsErr==='proxy-unavailable' && shipsTimer===null");case['ships']='proxy-unavailable, no fetch'
    capture(mode+'-ships','#ships-slot')
   if mode in ['success','weather-failure','marine-failure']:
    page.goto(origin+'/workspace/finder/index.html');page.get_by_role('tab',name='Trade tools',exact=True).click();page.locator('#portwx-toggle').click();page.wait_for_function('()=>!V.portWxBusy')
    if mode=='weather-failure':
     page.get_by_text('Live weather unavailable right now',exact=False).wait_for();assert page.evaluate('V.portWxErr && V.portWxData===null');case['weather']='forecast failure, no result, busy reset'
    else:
     page.get_by_role('cell',name='30.0 °C',exact=True).wait_for()
     if mode=='success':page.get_by_role('cell',name='1.5 m, E, period 6 s',exact=True).wait_for();page.locator('#portwx-pick').select_option('Chennai');page.wait_for_function("()=>!V.portWxBusy && V.portWx==='Chennai'")
     else:assert page.evaluate('V.portWxData.wave===null && !V.portWxErr')
     case['weather']='SIMULATED forecast, marine unavailable'if mode=='marine-failure'else'SIMULATED forecast+marine, port selection'
    capture(mode+'-weather','#portwx-pick')
   violations=csp_events+page.evaluate('fixtureCSP');assert not violations and not errors and not unexpected
   assert not any(c['path']=='/ships'for c in calls);case.update({'sanitized_calls':sorted(calls,key=lambda c:(c['method'],c['host'],c['path'],c['disposition'])),'unexpected_csp':violations,'page_errors':errors,'mobile_no_overflow':True})
   result['cases'][mode]=case;context.close()
  browser.close()
finally:server.shutdown()
result['finished_at']=datetime.now(timezone.utc).isoformat();result['artifacts']=[{'name':x.name,'sha256':hashlib.sha256(x.read_bytes()).hexdigest()}for x in sorted(OUT.glob('*.png'))]
(OUT/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:result[k]for k in ['phase','simulated','outbound_successes']}))
