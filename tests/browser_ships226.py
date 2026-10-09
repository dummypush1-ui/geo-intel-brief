"""Disposable local UI fixtures. Every request mocked; no realaccount/network."""
import sys,threading,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from flask import Flask,send_from_directory
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];app=Flask(__name__)
@app.get('/assets/<path:name>')
def assets(name):return send_from_directory(ROOT/'integration/finder198_ui',name)
@app.get('/')
def home():return '''<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Finder broker fixture</title><link rel="stylesheet" href="/assets/panel.css"><style>body{margin:0;padding:14px;background:#f4f7fb;font:16px/1.5 Arial;color:#182437}header{padding:16px;background:#234c80;color:white;border-radius:10px}nav button{min-height:44px;margin:4px;padding:8px;font:inherit}main{max-width:720px;margin:auto}</style><main><header><h1>Geo news</h1><p>Local source fixture. No real account or live request.</p><nav><button>Geo news</button><button>Finder</button></nav></header><section><h2>Finder</h2><div id="panel"></div></section></main><script type="module">import {mountBrokerPanel} from '/assets/panel.mjs';let mode='ok',n=0;window.fixtureMode=v=>mode=v;const r=(status,data)=>({status,text:async()=>JSON.stringify(data)});window.client=mountBrokerPanel(document.querySelector('#panel'),{enabled:true,nonceFactory:()=>('fixture'+(++n)).padEnd(24,'x'),fetcher:async(path,options)=>{if(path==='/account/preauth')return r(200,{csrf:'pre'});if(path==='/account/login')return r(200,{ok:true,csrf:'session',username:'fixture-alice'});if(path==='/account/logout')return r(200,{ok:true});if(path==='/account/whoami')return r(401,{ok:false});if(mode==='held')return r(503,{ok:false});if(mode==='unknown')throw Error('fixture');if(mode==='replay')return r(409,{state:'replay_status_only'});return r(200,window.shipFixture);}});</script>'''
server=make_server('127.0.0.1',8790,app);threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright()as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':390,'height':844});errors=[];external=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def route(r):
  if r.request.url.startswith('http://127.0.0.1:8790/'):r.continue_()
  else:external.append(r.request.url);r.abort()
 page.route('**/*',route);page.goto('http://127.0.0.1:8790/');page.get_by_role('heading',name='Built-in AI and ships').wait_for();page.screenshot(path='/downloads/finder198d-login390.png',full_page=True)
 page.locator('[data-username]').fill('fixture-alice');page.locator('[data-password]').fill('synthetic-test-password');page.get_by_role('button',name='Sign in',exact=True).click();page.get_by_text('Signed in as fixture-alice').wait_for();assert page.locator('[data-password]').input_value()=='';page.screenshot(path='/downloads/finder198d-signed390.png',full_page=True)
 page.evaluate("""async()=>{const m=await import('/assets/ships226.mjs');window.shipFixture={ok:true,warming:false,stalled:false,updated:'2026-10-10T01:00:00.000Z',count:200,ports:m.PORT_OPTIONS226.map(([code,name])=>({code,name,count:99})),vessels:Array.from({length:150},(_,i)=>({mmsi:String(100000000+i),name:'Long supplied vessel name '.repeat(4),type:'<img src=https://attack.invalid/x onerror=window.attacked=true>',flag:'javascript:alert(1)',sog:10,dest:'Chennai',eta:'2026-10-11 08:00 UTC',lat:13,lon:80,port:'INMAA',seenAgoSec:50}))};}""")
 page.get_by_role('button',name='Read ships once').click();page.get_by_text('Showing 150 supplied rows; source reported 200').wait_for()
 assert page.locator('[data-port] option').count()==43
 assert page.locator('[data-ship-view] tbody tr').count()==150
 assert not page.evaluate('window.attacked||false')
 for key in ('name','type','flag','dest','eta'):
  page.evaluate("key=>shipFixture.vessels[0][key]='<img src=https://attack.invalid/x onerror=window.attacked=true> javascript:x'",key)
 page.get_by_role('button',name='Read ships once').click();page.get_by_text('Showing 150 supplied rows; source reported 200').wait_for()
 assert not page.evaluate('window.attacked||false')
 assert page.locator('[data-ship-view] img,[data-ship-view] a').count()==0
 page.evaluate("shipFixture.vessels[0].port='javascript:x'")
 page.get_by_role('button',name='Read ships once').click();page.get_by_text('Structured ship view unavailable.',exact=False).wait_for()
 page.evaluate("shipFixture.vessels[0].port='INMAA'")
 page.get_by_role('button',name='Read ships once').click();page.get_by_text('Showing 150 supplied rows; source reported 200').wait_for()
 for width in (320,390,1200):
  page.set_viewport_size({'width':width,'height':844});page.locator('[data-port]').focus();assert page.evaluate("document.activeElement.matches('[data-port]')")
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  assert page.locator('[data-ship-view] [role=region]').evaluate('(e)=>e.scrollWidth>e.clientWidth')
  page.locator('[data-ship-view]').scroll_into_view_if_needed();page.screenshot(path=f'/tmp/ships226-review/ships-{width}.png',full_page=False)
 page.evaluate("shipFixture.ports.pop()")
 page.get_by_role('button',name='Read ships once').click();page.get_by_text('Structured ship view unavailable.',exact=False).wait_for();assert page.locator('[data-answer]').is_visible()
 page.evaluate("shipFixture.ports.push({code:'EGSUZ',name:'Suez Canal (both ends)',count:99});shipFixture.count=0;shipFixture.vessels=[];shipFixture.warming=true;shipFixture.stalled=true")
 page.get_by_role('button',name='Read ships once').click();page.get_by_text('Supplied response has no vessels.').wait_for()
 page.screenshot(path='/tmp/ships226-review/empty.png',full_page=False)
 page.evaluate("fixtureMode('unknown')");page.get_by_role('button',name='Read ships once').click();page.get_by_text('Request outcome is unknown.',exact=False).wait_for();assert page.locator('[data-ships]').is_disabled();page.screenshot(path='/downloads/finder198d-unknown390.png',full_page=True)
 page.set_viewport_size({'width':320,'height':844});page.screenshot(path='/downloads/finder198d-unknown320.png',full_page=True);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.reload();page.locator('[data-username]').fill('fixture-alice');page.locator('[data-password]').fill('synthetic-test-password');page.get_by_role('button',name='Sign in',exact=True).click();page.get_by_text('Signed in as fixture-alice').wait_for();page.evaluate("fixtureMode('replay')");page.get_by_role('button',name='Read ships once').click();page.get_by_text('This request was already recorded.',exact=False).wait_for();page.screenshot(path='/downloads/finder198d-replay320.png',full_page=True)
 page.reload();page.get_by_role('button',name='Check session').click();page.get_by_text('Session expired or signed out.',exact=False).wait_for();page.screenshot(path='/downloads/finder198d-expired320.png',full_page=True)
 page.locator('[data-username]').fill('fixture-alice');page.locator('[data-password]').fill('synthetic-test-password');page.get_by_role('button',name='Sign in',exact=True).click();page.get_by_text('Signed in as fixture-alice').wait_for();page.evaluate("fixtureMode('held')");page.get_by_role('button',name='Read ships once').click();page.get_by_text('Request held. Its outcome',exact=False).wait_for();page.screenshot(path='/downloads/finder198d-held320.png',full_page=True)
 assert not errors and not external;print(json.dumps({'fixture_only':True,'no_external_requests':True,'mobile320390_no_overflow':True,'errors':errors}));b.close()
server.shutdown()
