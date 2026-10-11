"""Local fake weather, no provider/DB. Browser pixel and behavior verification."""
import sys,threading,json
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from werkzeug.serving import make_server
from flask import Flask
from integration.weather_ui import install
from integration.weather_public_prep import typed,display,UNITS
from playwright.sync_api import sync_playwright,expect
OUT=Path('/tmp/weather-w3-pixels');OUT.mkdir(exist_ok=True)
raw=dict(timezone='GMT',utc_offset_seconds=0,current_units=UNITS,current=dict(time='2026-10-11T00:00',interval=900,temperature_2m=25,relative_humidity_2m=None,weather_code=0,wind_speed_10m=10,wind_direction_10m=0))
obj=display(typed('INBOM',raw,fetched_at=datetime.now(timezone.utc)),now=datetime.now(timezone.utc));receipt=[]
with sync_playwright()as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
 for available in (False,True):
  app=Flask(__name__);install(app,available);server=make_server('127.0.0.1',0,app);threading.Thread(target=server.serve_forever,daemon=True).start();origin='http://127.0.0.1:'+str(server.server_port)
  for width in (390,1100):
   ctx=b.new_context(viewport={'width':width,'height':900});page=ctx.new_page();calls=[];errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   def route(r):
    if r.request.url.startswith(origin+'/api/public-weather'):calls.append(r.request.url);return r.fulfill(json=obj)
    if r.request.url.startswith(origin):return r.continue_()
    raise AssertionError('Unexpected external request')
   page.route('**/*',route);page.goto(origin+'/workspace/weather');page.wait_for_selector('#weather-fetch');assert calls==[]
   assert page.locator('#weather-fetch').is_disabled()==(not available)
   if available:
    page.locator('#weather-fetch').click();page.get_by_text('Forecast loaded. Request again only when needed.').wait_for();assert len(calls)==1;assert page.locator('#weather-result').is_visible();assert 'Unavailable'in page.locator('#weather-result').inner_text();assert 'Open-Meteo'in page.locator('#weather-result').inner_text()
   if available:
    for mode in ('stale','403','429','503','missing_source','html_text'):
     page.unroute('**/*')
     def scenario(r):
      if r.request.url.startswith(origin+'/api/public-weather'):
       calls.append(r.request.url)
       if mode in ('403','429','503'):return r.fulfill(status=int(mode),json={'error':'PRIVATE_SERVER_TRACE'})
       import copy
       fixture=copy.deepcopy(obj)
       if mode=='stale':fixture.update(freshness='stale_forecast',age_seconds=1800)
       if mode=='missing_source':fixture.pop('source')
       if mode=='html_text':fixture['label']='<script>window.PWNED=1</script>'
       return r.fulfill(json=fixture)
      if r.request.url.startswith(origin):return r.continue_()
      raise AssertionError('Unexpected external request')
     page.route('**/*',scenario);page.locator('#weather-fetch').click()
     expect(page.locator('#weather-fetch')).to_be_enabled()
     assert page.evaluate('window.PWNED')is None
     if mode=='stale':assert 'Stale forecast'in page.locator('#weather-result').inner_text()
     else:assert page.locator('#weather-result').is_hidden()
     assert 'PRIVATE_SERVER_TRACE'not in page.inner_text('body')
    page.unroute('**/*');page.route('**/*',route);page.locator('#weather-fetch').click();page.get_by_text('Forecast loaded. Request again only when needed.').wait_for()
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert errors==[]
   path=OUT/f'{"on"if available else"off"}-{width}.png';page.screenshot(path=str(path),full_page=True);receipt.append({'available':available,'width':width,'calls':len(calls),'pixel_path':str(path),'errors':errors});ctx.close()
  server.shutdown()
 b.close()
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
