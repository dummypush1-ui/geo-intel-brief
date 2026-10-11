"""Injected fake provider only. Pixels/bridge/no-token evidence, not live AI."""
import sys,threading,json,time,logging,io,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration.news_api import create_app
from integration import public_ai_answers as a
from integration.public_preview_builder import build_public_preview
from tests.test_code_news_coverage_binding_prep import SAMPLE
from tests.test_public_ai_answers import RAW
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
out=Path('/tmp/public-ai-a1-evidence');out.mkdir(exist_ok=True)
origin='http://127.0.0.1:8786'
s=a.Service(lambda:RAW,lambda *args: {'state':'resolved','items':[{'system':args[1],'edition':args[2],'code':args[0],'description':'SIMULATED preserved wording'}]},a.FakeTransport(),a.FakeCatalog())
app=create_app(authorize=lambda r:True,allowed_origin=origin)
@app.after_request
def public_fixture_shell(response):
 from flask import request
 if request.path=='/workspace':
  response.direct_passthrough=False;response.set_data(response.get_data(as_text=True).replace('src="/workspace/finder/index.html"','src="/workspace/finder/offline.html"'))
 return response
a.install(app,origin,service=s)
capture=io.StringIO();handler=logging.StreamHandler(capture);logging.getLogger('werkzeug').addHandler(handler)
server=make_server('127.0.0.1',8786,app,threaded=True);threading.Thread(target=server.serve_forever,daemon=True).start()
report=[]
with sync_playwright()as p:
 browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
 # Adversarial browser-only fixtures. Does not consume backend job allowance.
 attack=browser.new_page(viewport={'width':390,'height':844})
 attack.set_default_timeout(3000)
 attack.add_init_script("""window.__fetches=[];window.__xss=0;const real=window.fetch;window.fetch=(u,o)=>{window.__fetches.push({url:String(u),credentials:o.credentials,referrerPolicy:o.referrerPolicy});return real(u,o);};""")
 attack.route('**/*',lambda r:r.continue_()if r.request.url.startswith(origin)else r.abort())
 ticket='A'*43
 completion={'state':'complete','fixture_only':True,'answer':'Summary: ordinary text.','sources':[{'id':'S1','title':'<img src=x onerror="window.__xss=1">','url':'https://news.example.com/a','source':'supplied','date':'recorded','scope':'latest100_supplied_unverified'}],'warning':a.WARNING,'scope':a.SCOPE,'source_notice':'Supplied only'}
 attack.route('**/api/public-ai-answers',lambda r:r.fulfill(json={'state':'pending','ticket':ticket}))
 attack.route('**/api/public-ai-answers/status',lambda r:r.fulfill(json=completion))
 attack.goto(origin+'/workspace/ai-answers');attack.locator('#question').fill('India');attack.locator('#ask').click();attack.locator('#result').wait_for(state='visible')
 assert attack.locator('#sources img').count()==0 and attack.evaluate('window.__xss')==0
 assert attack.locator('#sources a').inner_text().endswith('<img src=x onerror="window.__xss=1">')
 assert attack.locator('#held').is_hidden()
 assert all(r['credentials']=='omit' and r['referrerPolicy']=='no-referrer' for r in attack.evaluate('window.__fetches'))
 # Wrong warning from otherwise valid completed result must not be painted.
 attack.unroute('**/api/public-ai-answers/status');attack.route('**/api/public-ai-answers/status',lambda r:r.fulfill(json=dict(completion,warning='Verified answer')))
 attack.locator('#ask').click();attack.locator('#status').filter(has_text='Invalid answer').wait_for();assert attack.locator('#result').is_hidden()
 # JSON remains valid: whitespace prefix defeats postparse-only length tests.
 attack.unroute('**/api/public-ai-answers/status');attack.route('**/api/public-ai-answers/status',lambda r:r.fulfill(content_type='application/json',body=' '*24001+json.dumps(completion)))
 attack.locator('#ask').click();attack.locator('#status').filter(has_text='Oversized response').wait_for();assert attack.locator('#result').is_hidden()
 attack.close()
 # Source+origin checks on parent controller independently exercised. The source
 # frame is controlled here, not the expensive actual Finderbutton test below.
 host=browser.new_page(viewport={'width':390,'height':844})
 host.set_default_timeout(3000)
 host.route('**/workspace/finder/offline.html',lambda r:r.fulfill(content_type='text/html',body='<html><body>Hostile frame fixture</body></html>'))
 host.goto(origin+'/workspace',wait_until='domcontentloaded',timeout=10000);host.evaluate("document.querySelector('#finder').src='about:blank'")
 good={'type':'public-ai-question-v1','mode':'finder','question':'fixture','candidates':[{'system':'HS','edition':'2022','code':'0101'}]}
 def event(source,send_origin,data):
  host.evaluate("([source,sendOrigin,data])=>window.dispatchEvent(new MessageEvent('message',{origin:sendOrigin,source:source==='owned'?document.querySelector('#finder').contentWindow:window,data}))",[source,send_origin,data])
 event('wrong',origin,good);assert host.locator('dialog').count()==0
 event('owned','https://evil.test',good);assert host.locator('dialog').count()==0
 event('owned',origin,dict(good,extra='attack'));assert host.locator('dialog').count()==0
 event('owned',origin,good);host.locator('dialog iframe').wait_for()
 assert host.locator('dialog iframe').get_attribute('sandbox')=='allow-scripts allow-same-origin allow-forms'
 modal=host.frame_locator('dialog iframe');modal.locator('#question').filter if False else None
 modal.locator('#candidate-note').filter(has_text='Preserved candidates').wait_for();assert modal.get_by_role('link',name='Back to news and Finder').is_hidden()
 wrong=dict(good,question='WRONGFRAME')
 host.evaluate("d=>document.querySelector('dialog iframe').contentWindow.dispatchEvent(new MessageEvent('message',{origin:location.origin,source:document.querySelector('dialog iframe').contentWindow,data:d}))",wrong)
 assert modal.locator('#question').input_value()=='fixture'
 host.evaluate("d=>document.querySelector('dialog iframe').contentWindow.dispatchEvent(new MessageEvent('message',{origin:'https://evil.test',source:window,data:d}))",wrong)
 assert modal.locator('#question').input_value()=='fixture'
 host.close()
 report.append({'hostile_title_escaped':True,'wrong_warning_refused':True,'oversize_stream_refused':True,'fetch_credentials_omit':True,'fetch_referrer_no_referrer':True,'postMessage_wrong_source_and_origin_refused':True,'sandbox_exact':True})
 if os.environ.get('AI_BROWSER_ATTACKS_ONLY')=='1':
  browser.close();server.shutdown();print(json.dumps(report));sys.exit(0)
 for width in [390,1100]:
  page=browser.new_page(viewport={'width':width,'height':844});errors=[];outside=[];requests=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  def route(r):
   requests.append({'url':r.request.url,'method':r.request.method,'referer':r.request.headers.get('referer','')})
   if not r.request.url.startswith(origin):outside.append(r.request.url);r.abort()
   else:r.continue_()
  page.route('**/*',route)
  page.goto(origin+'/workspace/ai-answers');assert not s.transport.calls or width==1100
  assert page.get_by_text(a.WARNING,exact=True).count()==1
  assert 'Full-store AI search is NOT done' in page.locator('#scope').inner_text()
  page.locator('#question').fill('India');page.locator('#ask').click();page.locator('#result').wait_for(state='visible')
  assert 'SIMULATED' in page.locator('#answer').inner_text()
  assert page.locator('#sources a').count()==1
  assert page.locator('#sources a').get_attribute('rel')=='noopener noreferrer'
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  page.screenshot(path=str(out/f'ai-{width}.png'),full_page=True)
  assert all('?ticket=' not in r['url'] and 'ticket' not in r['referer'] for r in requests)
  assert not errors and not outside
  # Rejected hostile parent message from same window cannot alter the question.
  page.evaluate("window.postMessage({type:'public-ai-question-v1',mode:'finder',question:'WRONGFRAME',candidates:[]},location.origin)")
  assert page.locator('#question').input_value()=='India'
  report.append({'width':width,'pixels':True,'fixture_only':True,'no_outbound_provider':True,'ticket_body_only':True,'no_referrer':True,'no_errors':True});page.close()
 # New fixture epoch, rather than pretending fresh limits after a live restart.
 with s.lock:s.dispatches.clear();s.requests.clear();s.peers.clear()
 # Real original Finder served-copy bridge and parent modal, all requests local.
 page=browser.new_page(viewport={'width':390,'height':844});page.route('**/*',lambda r:r.continue_()if r.request.url.startswith(origin)else r.abort())
 page.goto(origin+'/workspace');page.locator('[data-view="finder"]').click()
 frame=page.frame_locator('#finder');frame.locator('#q-main').fill('horse');frame.locator('#assist-go').wait_for(timeout=30000);frame.locator('#assist-go').click();page.locator('dialog iframe').wait_for()
 modal=page.frame_locator('dialog iframe');modal.locator('#candidate-note').filter(has_text='Preserved candidates').wait_for();assert modal.locator('#question').input_value()=='horse'
 assert modal.locator('#candidate-note').inner_text().startswith('Preserved candidates')
 page.screenshot(path=str(out/'finder-modal-390.png'),full_page=True)
 modal.locator('#ask').click();modal.locator('#result').wait_for(state='visible');assert modal.locator('#sources a').count()>=1
 modal.locator('#answer').scroll_into_view_if_needed();page.screenshot(path=str(out/'finder-answer-390.png'),full_page=True)
 page.get_by_role('button',name='Close AI answers').click();assert page.locator('dialog').count()==0
 report.append({'finder_original_button_bridge':True,'network_remains_inert':True,'modal_close':True})
 browser.close()
assert s.job['ticket'] not in capture.getvalue()
server.shutdown();s.close();print(json.dumps(report,indent=2))
