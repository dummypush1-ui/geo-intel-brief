"""Local fixture + real Chrome. No live DB or provider."""
import sys,json,threading,os,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from flask import request
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
from integration.news_api import create_app
from integration.news_pages import WholeGeoPages
from integration.public_live_builder import sanitize_public_geo_rows
from integration.news_search_progress import install
from tests.test_news_pages185 import Store,rows
origin='http://127.0.0.1:8821';out=Path(os.environ.get('NEWS_SEARCH_EVIDENCE_DIR') or tempfile.mkdtemp(prefix='news-search-evidence-'));out.mkdir(parents=True,exist_ok=True)
store=Store(rows(1100));pages=WholeGeoPages(store,sanitize_public_geo_rows,verified=True,start_cleaner=False)
app=create_app(reader=lambda:{'geo':[]},authorize=lambda _:True,allowed_origin=origin,full_news_pages=pages);app.extensions['whole_news_pages']=pages
install(app)
@app.after_request
def finder(r):
 if request.path=='/workspace':r.direct_passthrough=False;r.set_data(r.get_data(as_text=True).replace('src="/workspace/finder/index.html"','src="/workspace/finder/offline.html"'))
 return r
server=make_server('127.0.0.1',8821,app,threaded=True);threading.Thread(target=server.serve_forever,daemon=True).start()
report=[]
try:
 with sync_playwright()as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
  for width in (390,1100):
   page=b.new_page(viewport={'width':width,'height':950});page.set_default_timeout(6000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   mode={'value':'history','count':0};requests=[]
   def reply(items,cursor,offset,scan):return dict(items=items,next_cursor=cursor,offset=offset,scanned_this_page=scan,exhausted=cursor is None,limit=25,total_count=None,scope='whole_geo_store_cursor',consistency='mutable_read_not_snapshot',sort_semantics='raw_mongo_source_fields_with_id_tiebreak')
   def route(r):
    u=r.request.url
    if not u.startswith(origin):r.abort();return
    if '/workspace/finder/'in u:r.fulfill(content_type='text/html',body='<html><body>Fixture Finder</body></html>');return
    if '/api/news-page'not in u:r.continue_();return
    requests.append(u);mode['count']+=1
    if mode['value']=='history':
     n=mode['count'];items=[] if n<3 else [dict(project='geo',title='Old fixture match',url='https://fixture.invalid/old',summary='Fixture only',source='Fixture')]
     r.fulfill(json=reply(items,chr(96+n)*43 if n<3 else None,0,1000 if n<3 else 25));return
    if mode['value']=='quota':r.fulfill(status=429,json={'state':'busy'});return
    if mode['value']=='large':r.fulfill(content_type='application/json',body=' '*1250001+'{}');return
    if mode['value']=='bad':r.fulfill(json={**reply([],None,0,0),'exhausted':False});return
    r.continue_()
   page.route('**/*',route)
   # Disable automatic intersection only in manual-continuation test.
   page.add_init_script('window.IntersectionObserver=class{observe(){}}')
   page.goto(origin+'/workspace');page.wait_for_function("()=>document.querySelector('#news-scroll-status').textContent.includes('Scanned 1')")
   assert 'keep searching' in page.locator('#news-scroll-status').inner_text();page.locator('#news-load-more').click();page.wait_for_function("()=>document.querySelector('#news-scroll-status').textContent.includes('Scanned 2')");page.locator('#news-load-more').click();page.wait_for_function("()=>document.querySelector('#news-scroll-status').textContent.includes('exhausted without error')");assert page.locator('#news-results .story').count()==1
   assert '120-second idle' in page.locator('#news-scroll-sentinel').inner_text()
   page.locator('#news-scroll-sentinel').scroll_into_view_if_needed();page.screenshot(path=str(out/f'search-{width}.png'),full_page=False)
   for value,copy in [('quota','busy'),('large','too large'),('bad','Invalid search page')]:
    mode.update(value=value,count=0);page.locator('#news-query').fill(value);page.locator('#news-search button').click();page.wait_for_function('(copy)=>document.querySelector("#news-scroll-status").textContent.includes(copy)',arg=copy);assert page.locator('#news-load-more').is_disabled();count=len(requests);page.wait_for_timeout(150);assert len(requests)==count
   mode.update(value='real',count=0);page.locator('#news-query').fill('');page.locator('#news-search button').click()
   for n in range(44):
    page.wait_for_function('()=>!document.querySelector("#news-results").matches("[aria-busy=true]")')
    if page.locator('#news-load-more').is_disabled():break
    page.locator('#news-load-more').click()
   page.wait_for_function("()=>document.querySelector('#news-scroll-status').textContent.includes('exhausted without error')")
   assert page.locator('#news-results .story').count()<=200;assert '1100 matching' in page.locator('#news-scroll-status').inner_text();assert not errors,errors
   report.append(dict(width=width,dom=page.locator('#news-results .story').count(),status=page.locator('#news-scroll-status').inner_text(),errors=errors));page.close()
  b.close()
finally:server.shutdown();pages.close()
(out/'report.json').write_text(json.dumps(report,indent=2));print(report)
