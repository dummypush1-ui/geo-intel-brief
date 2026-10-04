"""Offline visual fixture for original digest with gated event snapshot."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datetime import datetime,timezone
from integration.news_api import create_app
from integration.dashboard_snapshots import DashboardSnapshots
from playwright.sync_api import sync_playwright
now=datetime.now(timezone.utc)
event={'name':'FIXTURE summit <img src=x>','event_date':now.date().isoformat(),'source_url':'https://example.com/event','category':'TRADE','confidence':'fixture only','description':'Public fixture. No event seeded, fetched or mail sent.'}
adapter=DashboardSnapshots({'geo_events':lambda:{'observed_at':now.isoformat(),'items':[event]}},True,{'geo_events':['example.com']})
app=create_app(authorize=lambda r:True,dashboard_snapshot_reader=adapter);data=app.test_client().get('/digest-data').json
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':780,'height':950});outside=[];page.route('**/*',lambda r:(outside.append(r.request.url),r.abort()));page.set_content(data['html']);assert 'FIXTURE summit <img src=x>' in page.inner_text('body');assert page.locator('img,script,iframe').count()==0;assert page.get_by_text('Source →',exact=True).get_attribute('href')=='https://example.com/event';page.screenshot(path='/downloads/event-digest-fixture-desktop.png',full_page=True)
 page.set_viewport_size({'width':390,'height':844});page.screenshot(path='/downloads/event-digest-fixture-mobile.png',full_page=True);assert not outside;print(json.dumps({'events':data['event_snapshot'],'literal_hostile_name':True,'outbound':outside,'delivery':data['delivery'],'mobile_overflow':page.evaluate('document.documentElement.scrollWidth>innerWidth')}));b.close()
