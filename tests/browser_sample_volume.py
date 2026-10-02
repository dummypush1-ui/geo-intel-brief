import sys,threading,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration.news_api import create_app
from integration.dashboard_snapshots import DashboardSnapshots
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
STAMP='2026-10-02T00:00:00Z'
rows={'geo_events':[{'name':'Trade summit <img src=x>','event_date':'2026-10-03','source_url':'https://example.com/event','description':'<script>alert(1)</script> Captured event description.','category':'CONFERENCE','confidence':'CONFIRMED'}],'brics_sources':[{'name':'Source A <script>x</script>','url':'https://example.com/news','country':'India','last_status':'ok','last_count':4,'last_checked':STAMP}],'brics_streams':[{'name':'Official stream link','country':'Brazil','watch_url':'https://www.youtube.com/channel/UC'+'a'*22+'/live'}]}
readers={k:lambda k=k:{'observed_at':STAMP,'items':rows[k]} for k in rows}
adapter=DashboardSnapshots(readers,True,{k:(['example.com','www.youtube.com'] if k=='brics_streams' else ['example.com']) for k in rows})
news={'geo':[{'url':'https://example.com/a','created_at':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'title':'Z story','country':'India','score':2},{'url':'https://example.com/b','title':'A story','country':'Brazil','score':9}],'brics':[]}
app=create_app(reader=lambda:news,authorize=lambda r:True,dashboard_snapshot_reader=adapter)
server=make_server('127.0.0.1',8770,app);threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.route('**/*',lambda r:r.continue_() if r.request.url.startswith('http://127.0.0.1:8770/') else r.abort())
 page.goto('http://127.0.0.1:8770/workspace');page.locator('[data-view=geo]').click();page.locator('.snapshot-row a').wait_for()
 assert 'Trade summit <img src=x>' in page.locator('#snapshot-panels').inner_text();assert page.locator('#snapshot-panels img,#snapshot-panels script,#snapshot-panels iframe').count()==0
 assert 'Snapshot observed at' in page.locator('#snapshot-panels').inner_text()
 assert 'Category: CONFERENCE' in page.locator('#snapshot-panels').inner_text() and 'Confidence: CONFIRMED' in page.locator('#snapshot-panels').inner_text()
 page.locator('#news-sort').select_option('score');page.wait_for_function("() => document.querySelector('#news-results a')?.textContent==='A story'")
 with page.expect_download() as info:page.locator('#news-export').click()
 download=info.value;download.save_as('/downloads/loaded-sample.csv');assert download.suggested_filename=='loaded-news-sample.csv'
 assert 'not a full database backup' in page.locator('#export-status').inner_text()
 page.wait_for_function("() => document.getElementById('volume-summary').textContent.startsWith('Peak day:')")
 assert not page.locator('#volume-details').get_attribute('open');page.locator('#volume-details summary').click();assert page.locator('.volume-day meter').count()==7
 page.screenshot(path='/downloads/sample-volume-desktop.png',full_page=True)
 page.locator('[data-view=brics]').click();page.get_by_text('Official stream link',exact=True).wait_for();assert 'Captured status: ok' in page.locator('#snapshot-panels').inner_text();assert 'Availability not checked' in page.locator('#snapshot-panels').inner_text();assert page.get_by_text('Official stream link',exact=True).get_attribute('href')=='https://www.youtube.com/channel/UC'+'a'*22+'/live'
 page.screenshot(path='/downloads/dashboard-snapshots-brics.png',full_page=True)
 page.locator('[data-view=geo]').click();page.locator('#news-results a').first.wait_for();page.set_viewport_size({'width':390,'height':844});page.locator('#volume-details summary').click();page.screenshot(path='/downloads/sample-volume-mobile.png',full_page=True);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')

 page.locator('[data-view=brics]').click();page.wait_for_function("() => document.getElementById('volume-summary').textContent.startsWith('No dated stories')");page.locator('#volume-details summary').click();assert page.locator('.volume-day meter').count()==14
 pending=[]
 def delayed_volume(route):
  if 'project=geo' in route.request.url:pending.append(route)
  else:route.continue_()
 page.route('**/api/sample-volume?*',delayed_volume);page.locator('[data-view=geo]').click();page.wait_for_function("() => document.getElementById('volume-summary').textContent.startsWith('Loading')");page.locator('[data-view=brics]').click();page.wait_for_function("() => document.getElementById('volume-summary').textContent.startsWith('No dated stories')");assert pending
 for route in pending:route.fulfill(status=200,json={'scope':'loaded_read_view','not_total_database':True,'daily_volume':[]})
 page.wait_for_timeout(100);assert page.locator('#volume-summary').inner_text().startswith('No dated stories')
 page.route('**/api/sample-volume?*',lambda r:r.fulfill(status=503,json={'error':'unavailable'}));page.locator('[data-view=brics]').click();page.get_by_text('Sample volume unavailable.',exact=True).wait_for();assert page.locator('#volume-details').is_hidden() and page.locator('.volume-day').count()==0
 assert not errors;print('Static sample volume: desktop/mobile, collapsed default, empty BRICS14-day, no page errors')
 browser.close()
server.shutdown()
