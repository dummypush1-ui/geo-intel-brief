"""Real preserved Finder HTML in real Chrome, fixture news only."""
import sys,threading,json
from pathlib import Path
import os,tempfile
EVIDENCE=Path(os.environ.get('RELATIONSHIP_EVIDENCE_DIR') or tempfile.mkdtemp(prefix='relationship-evidence-'));EVIDENCE.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from flask import request
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
from integration.news_api import create_app
from integration.news_finder_navigation_prep import install_mount
from integration.code_news_public import install as code_install
from integration.code_news_links import Links
from integration.relationship_navigation import install
origin='http://127.0.0.1:8814'
raw={'geo':[dict(url='https://example.com/one',title='HS 100630 reported',summary='Rice')]}
app=create_app(reader=lambda:raw,authorize=lambda _:True,allowed_origin=origin)
@app.after_request
def shell(r):
 if request.path=='/workspace':
  r.direct_passthrough=False;r.set_data(r.get_data(as_text=True).replace('src="/workspace/finder/index.html"','src="/workspace/finder/offline.html"'))
 return r
install_mount(app);code_install(app,origin,lambda:raw);app.extensions['code_news_public'].model=Links([dict(system='HS',edition='2022',code='100630',description='Rice')],[]);install(app,origin)
server=make_server('127.0.0.1',8814,app,threaded=True);threading.Thread(target=server.serve_forever,daemon=True).start()
source=(Path(__file__).resolve().parents[1]/'integration/ui/relationship_navigation.js').read_text()
framehtml='<html><body><div class="detail-head"><span class="sys-tag">HS</span></div><span class="detail-code">100630</span><span class="detail-desc">Rice</span></body></html>'
checks=[]
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
  for mutated in [False,True]:
   app.extensions['code_news_public'].calls=0
   p=b.new_page(viewport={'width':390,'height':950});p.set_default_timeout(5000)
   def route(r):
    u=r.request.url
    if not u.startswith(origin):r.abort();return
    if '/workspace/finder/offline.html' in u:r.fulfill(content_type='text/html',body=framehtml);return
    if '/relationship_navigation.js' in u:
     code=source
     if mutated:code=code.replace('if(mine!==contextGeneration||!button.isConnected)return;','if(false)return;')
     r.fulfill(content_type='application/javascript',body=code);return
    r.continue_()
   p.route('**/*',route);p.goto(origin+'/workspace');p.locator('[data-view=finder]').click();p.evaluate("document.querySelector('#finder').contentWindow.location.hash='code=0:100630'")
   p.get_by_role('button',name='Check supplied-page news').wait_for()
   payload=app.test_client().get('/api/code-news-context?query=100630&system=HS&edition=2022',base_url=origin).json
   p.evaluate("""v=>{const orig=window.fetch;window.fetch=(u,o)=>String(u).startsWith('/api/code-news-context')?new Promise(resolve=>{window.pendingSignal=o.signal;window.finish=()=>resolve(new Response(JSON.stringify(v),{headers:{'Content-Type':'application/json'}}));}):orig(u,o)}""",payload)
   p.get_by_role('button',name='Check supplied-page news').click();p.wait_for_function('!!window.finish')
   p.locator('[data-view=geo]').click();assert p.evaluate('pendingSignal.aborted')
   p.evaluate('finish()');p.wait_for_function("!document.querySelector('#related-status').textContent.startsWith('Checking')" ) if mutated else p.wait_for_timeout(100)
   painted=p.locator('#related a').count();assert painted==(1 if mutated else 0),(mutated,painted)
   checks.append(dict(stale_forward_mutant=mutated,painted=painted,abort_on_view_switch=True));p.close()
  # Code changes abort pending request and clear old controls/results.
  mutated=False
  p=b.new_page();p.set_default_timeout(5000);p.route('**/*',route);p.goto(origin+'/workspace');p.locator('[data-view=finder]').click();p.evaluate("document.querySelector('#finder').contentWindow.location.hash='code=0:100630'");p.get_by_role('button',name='Check supplied-page news').wait_for()
  payload=app.test_client().get('/api/code-news-context?query=100630&system=HS&edition=2022',base_url=origin).json
  p.evaluate("""v=>{const orig=window.fetch;window.fetch=(u,o)=>String(u).startsWith('/api/code-news-context')?new Promise(resolve=>{window.pendingSignal=o.signal;window.finish=()=>resolve(new Response(JSON.stringify(v),{headers:{'Content-Type':'application/json'}}));}):orig(u,o)}""",payload)
  p.get_by_role('button',name='Check supplied-page news').click();p.wait_for_function('!!finish');p.evaluate("const f=document.querySelector('#finder');f.contentDocument.querySelector('.detail-code').textContent='1006';f.contentWindow.location.hash='code=0:1006'")
  p.get_by_text('HS 1006',exact=True).wait_for();assert p.evaluate('pendingSignal.aborted');p.evaluate('finish()');p.wait_for_timeout(100);assert p.locator('#related a').count()==0
  checks.append(dict(contextswitch_aborts=True,stale_paint=False));p.close()
  # Wrong source path cannot retain previous context controls.
  p=b.new_page();p.set_default_timeout(5000);p.route('**/*',route);p.goto(origin+'/workspace');p.locator('[data-view=finder]').click();p.evaluate("document.querySelector('#finder').contentWindow.location.hash='code=0:100630'");p.get_by_role('button',name='Check supplied-page news').wait_for()
  p.evaluate("""async()=>{const {manualFinderContext}=await import('/workspace/assets/relationship_navigation.js');const frame={src:location.origin+'/wrong-path',contentWindow:document.querySelector('#finder').contentWindow};manualFinderContext(frame,document.querySelector('#related'),document.querySelector('#related-status'),document.querySelector('#context'));}""")
  assert p.get_by_role('button',name='Check supplied-page news').count()==0
  checks.append(dict(wrong_path_clears=True));p.close()
  # Geo button excluded from BRICS rows, and no private path is reintroduced.
  p=b.new_page();p.set_default_timeout(5000);p.route('**/*',route);p.goto(origin+'/workspace')
  p.evaluate("""async()=>{const {attachReportedCodes}=await import('/workspace/assets/relationship_navigation.js');const row=document.createElement('div');row.id='brics-fixture';document.body.append(row);attachReportedCodes(row,{article_key:'a'.repeat(64),project:'brics'},document.querySelector('#finder'));}""")
  assert p.locator('#brics-fixture button').count()==0
  checks.append(dict(brics_button_absent=True));p.close()
  # Two physical clicks while response is pending admit only one manual start.
  for mutated in [False,True]:
   p=b.new_page();p.set_default_timeout(5000)
   def click_route(r):
    u=r.request.url
    if not u.startswith(origin):r.abort();return
    if '/workspace/finder/offline.html' in u:r.fulfill(content_type='text/html',body=framehtml);return
    if '/relationship_navigation.js' in u:r.fulfill(content_type='application/javascript',body=source.replace('button.disabled=true;','button.disabled=false;') if mutated else source);return
    r.continue_()
   p.route('**/*',click_route);p.goto(origin+'/workspace');p.locator('[data-view=finder]').click();p.evaluate("document.querySelector('#finder').contentWindow.location.hash='code=0:100630'");btn=p.get_by_role('button',name='Check supplied-page news');btn.wait_for()
   p.evaluate("window.starts=0;const real=fetch;window.fetch=(u,o)=>String(u).startsWith('/api/code-news-context')?(starts++,new Promise(()=>{})):real(u,o)")
   bb=btn.bounding_box();p.mouse.click(bb['x']+10,bb['y']+10);p.wait_for_function('starts===1');p.mouse.click(bb['x']+10,bb['y']+10);p.wait_for_timeout(50)
   assert p.evaluate('starts')==(2 if mutated else 1)
   checks.append(dict(doubleclick_mutant=mutated,starts=p.evaluate('starts')));p.close()
  # Completed cached frame must initialize even when load event was missed.
  from integration.relationship_navigation import transform
  transformed=transform((Path(__file__).resolve().parents[1]/'integration/ui/workspace.js').read_text())
  seam="if(frame.contentDocument?.readyState==='complete')bindFinderContext();"
  assert transformed.count(seam)==1
  for mutated in [False,True]:
   p=b.new_page();p.set_default_timeout(5000)
   def cached_route(r):
    u=r.request.url
    if not u.startswith(origin):r.abort();return
    if '/workspace/assets/workspace.js' in u:
     # Wait for cached fake frame before executing the workspace module.
     p.wait_for_function("document.querySelector('#finder')?.contentDocument?.querySelector('.detail-code')?.textContent==='100630'")
     p.evaluate("document.querySelector('#finder').contentWindow.location.hash='code=0:100630'")
     r.fulfill(content_type='application/javascript',body=transformed.replace(seam,'') if mutated else transformed);return
    if '/workspace/finder/offline.html' in u:r.fulfill(content_type='text/html',body=framehtml);return
    r.continue_()
   p.route('**/*',cached_route);p.goto(origin+'/workspace');p.locator('[data-view=finder]').click();p.wait_for_timeout(150)
   count=p.get_by_role('button',name='Check supplied-page news').count();assert count==(0 if mutated else 1),(mutated,count)
   checks.append(dict(cached_init_mutant=mutated,buttons=count));p.close()
  # Mutation storms trigger no request; old document observer disconnects.
  mutated=False
  p=b.new_page();p.set_default_timeout(5000);p.route('**/*',route);p.goto(origin+'/workspace');p.locator('[data-view=finder]').click();p.evaluate("document.querySelector('#finder').contentWindow.location.hash='code=0:100630'");p.get_by_role('button',name='Check supplied-page news').wait_for()
  p.evaluate("window.apiCalls=0;const real=window.fetch;window.fetch=(u,o)=>{if(String(u).includes('code-context')||String(u).includes('code-news-context'))apiCalls++;return real(u,o)};window.oldDoc=document.querySelector('#finder').contentDocument;for(let i=0;i<500;i++)oldDoc.body.append(document.createElement('span'))")
  p.wait_for_timeout(100);assert p.evaluate('apiCalls')==0
  p.evaluate("document.querySelector('#finder').contentWindow.location.reload()")
  p.frame_locator('#finder').locator('.detail-code').wait_for();p.evaluate("oldDoc.querySelector('.detail-code').textContent='1006';for(let i=0;i<500;i++)oldDoc.body.append(document.createElement('span'))")
  p.wait_for_timeout(100);assert p.evaluate('apiCalls')==0
  checks.append(dict(mutation_storm=1000,no_network=True));p.close()
  # Reverse request: a stale response must not paint while away from news.
  for mutated in [False,True]:
   app.extensions['code_news_public'].calls=0
   p=b.new_page();p.set_default_timeout(5000)
   def reverse_route(r):
    u=r.request.url
    if not u.startswith(origin):r.abort();return
    if '/workspace/finder/offline.html' in u:r.fulfill(content_type='text/html',body=framehtml);return
    if '/relationship_navigation.js' in u:r.fulfill(content_type='application/javascript',body=source.replace('if(mine!==generation||!row.isConnected)return;','if(false)return;') if mutated else source);return
    r.continue_()
   p.route('**/*',reverse_route);p.goto(origin+'/workspace');p.locator('[data-view=geo]').click();p.get_by_role('button',name='Check reported codes').first.wait_for()
   key=app.extensions['code_news_public'].rows()[0]['article_key']
   payload=app.test_client().get('/api/news-code-context?project=geo&article_key='+key,base_url=origin).json
   p.evaluate("""v=>{const orig=window.fetch;window.fetch=(u,o)=>String(u).startsWith('/api/news-code-context')?new Promise(resolve=>{window.pendingSignal=o.signal;window.finish=()=>resolve(new Response(JSON.stringify(v),{headers:{'Content-Type':'application/json'}}));}):orig(u,o)}""",payload)
   p.get_by_role('button',name='Check reported codes').first.click();p.wait_for_function('!!window.finish');p.locator('[data-view=finder]').click();assert p.evaluate('pendingSignal.aborted');p.evaluate('finish()');p.wait_for_timeout(100)
   painted=p.locator('#news-results').get_by_text('Reported code mention, not verified classification: HS 100630',exact=True).count();assert painted==(1 if mutated else 0),(mutated,painted)
   checks.append(dict(stale_reverse_mutant=mutated,painted=painted,abort_on_view_switch=True));p.close()
  # Context identity must clear old controls rather than retain a stale code.
  for hashvalue in ['code=0:%31%30%30%36%33%30','code=1:100630','code=0:../100630']:
   p=b.new_page();p.set_default_timeout(5000);p.route('**/*',route);p.goto(origin+'/workspace');p.locator('[data-view=finder]').click();p.evaluate("document.querySelector('#finder').contentWindow.location.hash='code=0:100630'");p.get_by_role('button',name='Check supplied-page news').wait_for()
   p.evaluate("v=>document.querySelector('#finder').contentWindow.location.hash=v",hashvalue);p.get_by_text('Select a supported HS or India code. Latest-100 only; no private lookup.',exact=True).wait_for();assert p.get_by_role('button',name='Check supplied-page news').count()==0
   checks.append(dict(invalid_hash=hashvalue,rejected=True));p.close()
  b.close()
finally:server.shutdown()
(EVIDENCE/'lifecycle.json').write_text(json.dumps(checks,indent=2));print(checks)
