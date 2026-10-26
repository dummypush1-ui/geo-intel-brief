"""Offline iframe intercepts: layout/construction only, not provider playback."""
import sys,json,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration.public_preview_builder import build_public_preview
from tests.test_code_news_coverage_binding_prep import SAMPLE
from integration import public_brics_streams as module
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
out=Path('/tmp/public-brics-result');out.mkdir(exist_ok=True)
app=build_public_preview(dict(SAMPLE,**{module.FLAG:'true'}));old=app.wsgi_app
def proxy(environ,start):environ['HTTP_HOST']='example.test';environ['wsgi.url_scheme']='https';return old(environ,start)
app.wsgi_app=proxy;server=make_server('127.0.0.1',8785,app);threading.Thread(target=server.serve_forever,daemon=True).start()
reports=[]
with sync_playwright()as p:
 browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
 for width in [390,1100]:
  page=browser.new_page(viewport={'width':width,'height':844});errors=[];writes=[];outside=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  def intercept(route):
   url=route.request.url
   if route.request.method in ['POST','DELETE']:writes.append(url)
   if url.startswith('https://www.youtube-nocookie.com/embed/'):
    route.fulfill(content_type='text/html',body='<html><body style="margin:0;background:#182c40;color:white;font:18px sans-serif;display:grid;place-items:center;height:100vh">OFFLINE EMBED FIXTURE<br>Layout only, playback unverified</body></html>')
   elif url.startswith('http://127.0.0.1:8785/'):route.continue_()
   else:outside.append(url);route.abort()
  page.route('**/*',intercept)
  page.add_init_script('''window.localStorage.setItem('geo-intel-preview-channels-v1',JSON.stringify([{name:'Republic',video:'abcdefghijk'}]));window.__reads=[];const get=Storage.prototype.getItem;Storage.prototype.getItem=function(k){window.__reads.push(k);return get.call(this,k);};''')
  page.goto('http://127.0.0.1:8785/workspace/brics-streams');page.locator('#wall article').nth(4).wait_for();assert page.locator('iframe').count()==6
  assert 'geo-intel-preview-channels-v1'not in page.evaluate('window.__reads')
  attrs=page.locator('iframe').evaluate_all('(fs)=>fs.map(f=>({url:f.src,sandbox:f.getAttribute("sandbox"),referrer:f.getAttribute("referrerpolicy")}))')
  for f in attrs:
   assert f['url'].startswith('https://www.youtube-nocookie.com/embed/')and'autoplay=1&mute=1' in f['url']
   assert f['sandbox']=='allow-scripts allow-same-origin allow-presentation'and f['referrer']=='strict-origin-when-cross-origin'
  assert page.locator('a[target="_blank"]').evaluate_all('(as)=>as.every(a=>a.rel==="noopener noreferrer")')

  rect=page.locator('#stop').bounding_box();assert rect['y']+rect['height']<844
  page.screenshot(path=str(out/('wall-'+str(width)+'.png')),full_page=True);page.screenshot(path=str(out/('viewport-'+str(width)+'.png')))
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  before=page.locator('#wall iframe').evaluate_all('(fs)=>{fs.forEach((f,i)=>f.dataset.proof="keep"+i);return fs.map(f=>f.dataset.proof)}')
  page.get_by_role('button',name='Select DW News',exact=True).evaluate('(e)=>e.click()');assert page.locator('#wall iframe').evaluate_all('(fs)=>fs.map(f=>f.dataset.proof)')==before
  for i in range(4):
   page.locator('#name').fill(('தமிழ் '+str(i)+' ')+'x'*55);page.locator('#link').fill('abcdefghij'+str(i));page.get_by_role('button',name='Add extra channel',exact=True).evaluate('(e)=>e.click()');page.wait_for_function('(n)=>document.querySelectorAll("#wall article").length===n',arg=6+i)
  assert page.locator('#wall article').count()==9 and page.locator('iframe').count()==6
  page.locator('#name').fill('Ninth');page.locator('#link').fill('abcdefghij9');page.get_by_role('button',name='Add extra channel',exact=True).evaluate('(e)=>e.click()');page.locator('#status').filter(has_text='up to 8').wait_for();assert page.locator('#wall article').count()==9
  page.screenshot(path=str(out/('max9-'+str(width)+'.png')),full_page=True);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  page.locator('#wall article').nth(8).get_by_role('button',name='Load mini').evaluate('(e)=>e.click()');page.wait_for_function('document.querySelectorAll("iframe").length===7')
  assert page.get_by_role('button',name='Remove Republic',exact=True).count()==0
  page.get_by_role('button',name='Stop players',exact=True).evaluate('(e)=>e.click()');assert page.locator('iframe').count()==0
  page.get_by_role('button',name='Start default players',exact=True).evaluate('(e)=>e.click()');assert page.locator('iframe').count()==6
  # Saved custom extras survive reload, but they do not autoplay.
  page.reload();page.locator('#wall article').nth(8).wait_for();assert page.locator('iframe').count()==6
  # Removed default does not autoplay, and private storage never influences fixed.
  page.get_by_role('button',name='Remove DW News',exact=True).evaluate('(e)=>e.click()');page.wait_for_function('document.querySelectorAll("#wall article").length===8');page.reload();page.locator('#wall article').nth(7).wait_for();assert page.locator('iframe').count()==5
  page.evaluate("localStorage.setItem('geo-intel-public-brics-extras-v1','{\"__proto__\":{\"name\":\"Republic\"}}')");page.reload();page.locator('#status').filter(has_text='four defaults restored').wait_for();assert page.locator('#wall article').count()==5

  page.evaluate("localStorage.setItem('geo-intel-public-brics-extras-v1','x'.repeat(10001))");page.reload();page.locator('#status').filter(has_text='four defaults restored').wait_for();assert page.locator('#wall article').count()==5
  # Pause init fetch in the real browser, invoke Start before ready resolves.
  page.add_init_script("const realFetch=window.fetch;window.fetch=(...a)=>a[0]==='/api/brics/streams'?new Promise(()=>{}):realFetch(...a)")
  page.reload();page.locator('#status').filter(has_text='Loading supplied').wait_for();page.locator('#start').evaluate('(e)=>e.click()');assert page.locator('iframe').count()==0
  # A fresh page removes the intentionally paused fetch setup.
  page.close();page=browser.new_page(viewport={'width':width,'height':844});page.route('**/*',intercept)
  # Real UI blocked before ready, even if Start/reset/form handlers are invoked.
  page.route('**/api/brics/streams',lambda r:r.fulfill(json={'streams':[]}))
  page.goto('http://127.0.0.1:8785/workspace/brics-streams');page.locator('#status').filter(has_text='configuration unavailable').wait_for();page.locator('#start').evaluate('(e)=>e.click()');assert page.locator('iframe').count()==0
  assert page.locator('#add button').is_disabled()
  # A forged 4-row payload cannot start any frames (5-row check exercised).
  page.unroute('**/api/brics/streams')
  page.route('**/api/brics/streams',lambda r:r.fulfill(json={'streams':[{'name':'Republic','video':'jndNegut8RY'}]*4}))
  page.reload();page.locator('#status').filter(has_text='configuration unavailable').wait_for();assert page.locator('iframe').count()==0
  page.unroute('**/api/brics/streams')
  page.route('**/api/brics/streams',lambda r:r.fulfill(json={'streams':[{'name':'Republic','video':'jndNegut8RY'}]*6}))
  page.reload();page.locator('#status').filter(has_text='configuration unavailable').wait_for();assert page.locator('iframe').count()==0
  page.unroute('**/api/brics/streams')
  assert not errors and not writes and not outside
  reports.append(dict(width=width,layout_only=True,real_playback_verified=False,no_errors=True,private_key_not_read=True,max8extras=True,extra_click_load=True,local_saved=True,corrupt_restored=True,removed_default_no_autoplay=True,stop_visible=True));page.close()
 browser.close()
server.shutdown();print(json.dumps(reports,indent=2))
