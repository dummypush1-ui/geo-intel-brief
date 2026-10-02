import sys,threading,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration.news_api import create_app
from integration.dashboard_snapshots import DashboardSnapshots
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
STAMP='2026-10-02T00:00:00Z'
rows={'geo_events':[{'name':'Trade summit <img src=x>','event_date':'2026-10-03','source_url':'https://example.com/event','description':'<script>alert(1)</script> Captured event description.'}],'brics_sources':[{'name':'Source A <script>x</script>','url':'https://example.com/news','country':'India','last_status':'ok','last_count':4,'last_checked':STAMP}],'brics_streams':[{'name':'Official stream link','country':'Brazil','watch_url':'https://example.com/live'}]}
readers={k:lambda k=k:{'observed_at':STAMP,'items':rows[k]} for k in rows}
adapter=DashboardSnapshots(readers,True,{k:['example.com'] for k in rows})
app=create_app(authorize=lambda r:True,dashboard_snapshot_reader=adapter)
server=make_server('127.0.0.1',8770,app);threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.route('**/*',lambda r:r.continue_() if r.request.url.startswith('http://127.0.0.1:8770/') else r.abort())
 page.goto('http://127.0.0.1:8770/workspace');page.locator('[data-view=geo]').click();page.locator('.snapshot-row a').wait_for()
 assert 'Trade summit <img src=x>' in page.locator('#snapshot-panels').inner_text();assert page.locator('#snapshot-panels img,#snapshot-panels script,#snapshot-panels iframe').count()==0
 assert 'Snapshot observed at' in page.locator('#snapshot-panels').inner_text()
 page.screenshot(path='/downloads/dashboard-snapshots-geo.png',full_page=True)
 page.locator('[data-view=brics]').click();page.get_by_text('Official stream link',exact=True).wait_for();assert 'Captured status: ok' in page.locator('#snapshot-panels').inner_text();assert 'Availability not checked' in page.locator('#snapshot-panels').inner_text()
 page.screenshot(path='/downloads/dashboard-snapshots-brics.png',full_page=True)
 page.set_viewport_size({'width':390,'height':844});page.screenshot(path='/downloads/dashboard-snapshots-mobile.png',full_page=True);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 rows['brics_sources']=[];page.locator('[data-view=brics]').click();page.get_by_text('No entries in this supplied snapshot.',exact=True).wait_for()
 adapter.readers.clear();page.locator('[data-view=geo]').click();page.get_by_text('Geo events: verified snapshot unavailable.',exact=True).wait_for()
 # Slow Geo response cannot overwrite a later BRICS view.
 pending=[]
 def delayed(route):
  if 'project=geo' in route.request.url:pending.append(route)
  else:route.continue_()
 page.route('**/api/dashboard-snapshots?*',delayed);page.locator('[data-view=geo]').click();page.wait_for_function("document.getElementById('snapshot-status').textContent.startsWith('Loading')");page.locator('[data-view=brics]').click();page.get_by_text('BRICS source observations: verified snapshot unavailable.',exact=True).wait_for()
 assert pending
 for route in pending:route.fulfill(json={'project':'geo','not_live_status':True,'panels':{}},status=200)
 page.wait_for_function("document.getElementById('snapshot-panels').textContent.includes('BRICS source')")
 assert 'Geo events' not in page.locator('#snapshot-panels').inner_text()
 # Raw confusion/encoded paths and invisible labels must not become links.
 page.route('**/api/dashboard-snapshots?*',lambda r:r.fulfill(json={'project':'brics','not_live_status':True,'panels':{'brics_streams':{'state':'supplied_snapshot','observed_at':STAMP,'items':[{'name':'bad','watch_url':'https://evil.com\\.example.com/'},{'name':'bad','watch_url':'https://example.com/%E2%80%AEname'},{'name':'  ','watch_url':'https://example.com/good'},{'name':'\u200b','watch_url':'https://example.com/zero'},{'name':'\u202eName','watch_url':'https://example.com/bidi'},{'name':'Format path','watch_url':'https://example.com/\u2060name'},*({'name':n,'watch_url':'https://example.com/x'} for n in ['\u2800','\u3164','\u115f','\u1160','\uffa0','\x00ok\x7f','a\ud800','a\ue000','a\u0378','\u034f','\ufe0f','\u180b','\u17b4','\U000e0100','\ufffc','\u0301']),{'name':'Control path','watch_url':'https://example.com/x\x7f'}]}}}))
 page.locator('[data-view=brics]').click();page.get_by_text('No displayable links in this supplied snapshot.',exact=True).wait_for();assert page.locator('#snapshot-panels a').count()==0
 page.route('**/api/dashboard-snapshots?*',lambda r:r.fulfill(json={'project':'brics','not_live_status':True,'state':'snapshot_readers_unwired'}))
 page.locator('[data-view=brics]').click();page.get_by_text('BRICS source observations: snapshot reader is not connected.',exact=True).wait_for()
 assert not errors;print(json.dumps({'errors':errors,'hostile_text_literal':True,'captured_not_live':True,'empty_missing_distinct':True,'no_embed':True,'mobile_no_overflow':True,'tab_switch_guard':True}))
 browser.close()
server.shutdown()
