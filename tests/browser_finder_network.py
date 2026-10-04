import sys,threading,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration.news_api import create_app
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
app=create_app(authorize=lambda r:True,finder_network_preview_enabled=True);server=make_server('127.0.0.1',8775,app);threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':390,'height':844});errors=[];calls=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def route(r):
  u=r.request.url
  if u.startswith('http://127.0.0.1:8775/'):return r.continue_()
  calls.append(u);data={}
  if '/ships?' in u:data={'ports':[],'vessels':[],'count':0,'updated':'2026-10-05T00:00:00Z'}
  elif 'api.frankfurter.dev' in u:data={'rates':{'2025-09-01':{'INR':80,'USD':.012,'EUR':.010},'2026-09-01':{'INR':85,'USD':.011,'EUR':.009},'2026-10-01':{'INR':90,'USD':.010,'EUR':.008}}}
  elif 'marine-api' in u:data={'current':{'wave_height':1.5,'wave_direction':90,'wave_period':6,'swell_wave_height':1}}
  elif 'open-meteo' in u:data={'current':{'temperature_2m':30,'wind_speed_10m':12,'wind_direction_10m':90,'time':'2026-10-05T03:00'}}
  elif 'hsn-ai-proxy' in u:data={'choices':[{'message':{'content':'FIXTURE plain words only. This is simulated, not a live AI answer.'}}],'candidates':[{'content':{'parts':[{'text':'FIXTURE plain words only. This is simulated, not a live AI answer.'}]}}]}
  else:return r.abort()
  r.fulfill(status=200,json=data,headers={'Access-Control-Allow-Origin':'*'})
 page.route('**/*',route);page.goto('http://127.0.0.1:8775/workspace/finder/index.html');page.get_by_role('tab',name='Live ships',exact=True).click();page.locator('#ships-toggle').click();page.get_by_text('manual refresh only in private preview',exact=False).wait_for();assert sum('/ships?' in u for u in calls)==1;page.locator('#ships-toggle').click();page.get_by_role('tab',name='Trade tools',exact=True).click();page.locator('#portwx-toggle').click();page.get_by_role('cell',name='30.0 °C',exact=True).wait_for();page.screenshot(path='/downloads/finder-weather-fixture.png',full_page=True);page.locator('#portwx-pick').locator('..').screenshot(path='/downloads/finder-weather-card-fixture.png')
 page.goto('http://127.0.0.1:8775/workspace/finder/index.html#code=0:090121');page.get_by_text('Plain words - what this code covers',exact=True).click();page.locator('#plain-go').click();page.get_by_text('FIXTURE plain words only.',exact=False).wait_for();page.get_by_text('Plain arithmetic on ECB reference rates',exact=False).wait_for();page.screenshot(path='/downloads/finder-ai-fx-fixture.png',full_page=True);page.locator('#plain-card').screenshot(path='/downloads/finder-ai-card-fixture.png');page.get_by_text('Currency impact - rupee vs dollar',exact=True).click();page.locator('#ccy-impact').screenshot(path='/downloads/finder-fx-card-fixture.png');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors
 assert any('hsn-ai-proxy' in u and '/ships?' not in u for u in calls);assert any('api.frankfurter.dev' in u for u in calls);assert any('marine-api' in u for u in calls);assert any('api.open-meteo' in u for u in calls)
 print(json.dumps({'fixture_only':True,'AI_FX_AIS_weather_requests_intercepted':True,'mobile_no_overflow':True,'errors':errors,'request_count':len(calls),'no_real_external_requests':True}));b.close()
server.shutdown()
