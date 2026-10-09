"""Local-only event promotion: pixels, TZ invariance and response order races."""
import sys,json,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from integration.news_api import create_app
from integration.dashboard_snapshots import DashboardSnapshots
from integration.public_preview_builder import build_public_preview
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
STAMP='2026-10-09T04:00:00Z'
rows=[{'name':'<img src=x onerror=alert(1)> '+('N'*200),'event_date':'2024-02-29','source_url':'https://example.com/event','category':'</details>','confidence':'FIXTURE','description':'x'*2000}]
adapter=DashboardSnapshots({'geo_events':lambda:{'observed_at':STAMP,'items':rows}},True,{'geo_events':['example.com']})
app=create_app(authorize=lambda r:True,dashboard_snapshot_reader=adapter)
server=make_server('127.0.0.1',8799,app);threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright()as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
 for tz,width in [('America/Los_Angeles',390),('Asia/Kolkata',1280)]:
  c=b.new_context(viewport={'width':width,'height':900},timezone_id=tz);page=c.new_page();errors=[];external=[];calls=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  def route(r):
   if r.request.url.startswith('http://127.0.0.1:8799/'):
    if '/api/dashboard-snapshots?'in r.request.url:calls.append(r.request.url)
    return r.continue_()
   external.append(r.request.url);r.abort()
  page.route('**/*',route);page.goto('http://127.0.0.1:8799/workspace');page.get_by_text('Events - 1 in snapshot',exact=True).wait_for()
  assert not page.locator('#events-panel').evaluate('(e)=>e.open')
  page.locator('#events-summary').focus();page.keyboard.press('Enter');assert page.locator('#events-panel').evaluate('(e)=>e.open')
  assert 'Event date: 2024-02-29'in page.locator('#events-rows').inner_text();assert '</details>'in page.locator('#events-rows').inner_text()
  assert page.locator('#events-panel img,#events-panel script,#events-panel iframe').count()==0
  page.wait_for_function("document.querySelector('[data-event-stat] .num').textContent==='1'");assert page.locator('[data-event-stat] .lbl').text_content()=='Events in snapshot'
  assert page.locator('.event-row a').get_attribute('rel')=='noopener noreferrer'
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  page.locator('#events-panel').screenshot(path='/downloads/events210-'+str(width)+'.png')
  start=len(calls);page.locator('#news-refresh').click();page.get_by_text('Events - 1 in snapshot',exact=True).wait_for();assert len(calls)==start+1
  # New snapshots win even when stats complete first/last and older snapshot completes last.
  pending=[]
  page.route('**/api/dashboard-snapshots?*',lambda r:pending.append(r))
  page.locator('#news-refresh').click();page.get_by_text('Events - loading',exact=True).wait_for();assert page.locator('[data-event-stat] .num').inner_text()=='Loading'
  page.locator('#news-refresh').click();page.wait_for_timeout(100);assert len(pending)==2
  def data(items):return {'project':'geo','not_live_status':True,'panels':{'geo_events':{'state':'supplied_snapshot','observed_at':STAMP,'items':items}}}
  pending[1].fulfill(json=data([]));page.get_by_text('Events - 0 in snapshot',exact=True).wait_for();pending[0].fulfill(json=data(rows));page.wait_for_timeout(100);assert page.locator('[data-event-stat] .num').inner_text()=='0';assert page.locator('.event-row').count()==0
  # Stats refresh does not erase snapshot count after snapshot wins first.
  statpending=[];page.unroute('**/api/dashboard-snapshots?*');page.route('**/api/news-stats?*',lambda r:statpending.append(r));page.locator('#news-refresh').click();page.get_by_text('Events - 1 in snapshot',exact=True).wait_for()
  for r in statpending:r.fulfill(json={'scope':'loaded_read_view','not_total_database':True,'count':0,'categories':[]})
  page.wait_for_timeout(100);assert page.locator('[data-event-stat] .num').inner_text()=='1';page.unroute('**/api/news-stats?*')
  # Forged client rows: actual shown count, HTTPS-only and field controls inert/dropped.
  hostile=[]
  for field in ('name','category','confidence','description'):
   for text in ('\u202e','\u200b','\u2800','\r','<img src=x onerror=alert(1)>','</details>'):
    hostile.append({**rows[0],field:'field'+text})
  hostile.extend([{**rows[0],'source_url':'http://example.com/event'},{**rows[0],'source_url':'javascript:alert(1)'}])
  page.route('**/api/dashboard-snapshots?*',lambda r:r.fulfill(json=data(hostile)))
  page.locator('#news-refresh').click();page.wait_for_function("document.getElementById('events-summary').textContent!=='Events - loading'")
  shown=page.locator('.event-row').count();assert int(page.locator('[data-event-stat] .num').inner_text())==shown;assert shown<len(hostile)
  assert page.locator('#events-panel img,#events-panel script').count()==0
  page.unroute('**/api/dashboard-snapshots?*');page.route('**/api/dashboard-snapshots?*',lambda r:r.fulfill(json={'project':'geo','not_live_status':True,'state':'snapshot_readers_unwired'}));page.locator('#news-refresh').click();page.get_by_text('Events - not connected',exact=True).wait_for();assert page.locator('[data-event-stat] .num').inner_text()=='Unavailable'
  assert not errors and not external;(print(json.dumps({'tz':tz,'width':width,'same_date':'2024-02-29','one_fetch':True,'stale_guard':True,'inert':True,'no_overflow':True})));c.close()
 b.close()
server.shutdown()
