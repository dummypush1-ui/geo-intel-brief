"""Loopback real Chrome, existing authenticated broker with simulated response.
No actual proxy/provider request, credentials or production activation.
Usage OUTPUT ARCHIVE SHA ROOT. Fixtures are deliberately not live evidence.
"""
import sys,json,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from unittest.mock import patch
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
from integration import finder_binding_f8 as f8,finder_composition_f9 as f9,finder_proxy_f12 as m
from integration.finder_proxy_f12.evidence import Evidence
from integration.public_preview_builder import build_public_preview
from integration.finder198_connector import ModelEntry
from integration.finder198_transport import FixedProxyTransport
from integration.finder198_receipts import ProxyReceiptBudget
from integration.accounts.service import AccountService
from integration.accounts.store import MemoryStore
from tests.test_finder198ba import Collection,R
from tests.test_finder198a import evidence,PW
from tests.test_code_news_coverage_binding_prep import SAMPLE,ORIGIN
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
b=f8.prepare({f8.FLAG:'true'},archive=sys.argv[2],expected_sha256=sys.argv[3],root=sys.argv[4]);env=dict(SAMPLE,**{f9.FLAG:'true','PUBLIC_FINDER_DATA_REPORT_ENABLED':'true',m.FLAG:'true'})
app=build_public_preview(env,finder_candidate_binding=b);col=Collection();col.doc.update(schema=2,receipts=[]);budget=ProxyReceiptBudget(col,review=R);transport=FixedProxyTransport({'FINDER_PROXY_BASE_URL':'https://hsn-ai-proxy.onrender.com','FINDER_PROXY_SECRET':'x'*48},enabled=True)
store=MemoryStore();service=AccountService(store,b'x'*48,lambda:101,signup_mode='closed',allowed_origins=[ORIGIN]);store.create_account('alice',{'uid':'alice','password':service.hasher.hash(PW),'created':100,'pwv':0},None,50)
h=m.FeatureBroker(Evidence(f9.selected(app)),budget,transport,lambda:101,provider='groq',model='fixture-reviewed',permission=m.FeaturePermission('fixture-disclosure','fixture-spend','fixture-retention','fixture-no-paid-fallback',100,200));m.activate(app,handler=h,service=service,origin=ORIGIN,client_identity=lambda r:'trusted',worker_evidence=evidence,clock=lambda:101)
old=app.wsgi_app
def proxy(env,start):
 env['HTTP_HOST']='example.test';env['wsgi.url_scheme']='https'
 if env.get('HTTP_ORIGIN','').startswith('http://127.0.0.1:'):env['HTTP_ORIGIN']=ORIGIN
 return old(env,start)
app.wsgi_app=proxy;server=make_server('127.0.0.1',0,app,threaded=True);threading.Thread(target=server.serve_forever,daemon=True).start();origin='http://127.0.0.1:'+str(server.server_port);results=[];calls=[]
def simulated(plan,body):
 calls.append(json.loads(body));return {'status':200,'body':json.dumps({'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':json.dumps({'answer':'SIMULATED TEST TEXT from supplied snapshot only.','citations':['S1']})}}]}).encode()}
try:
 with patch('integration.finder198_connector.MODEL_CATALOG',(ModelEntry('groq','fixture-reviewed','fixture-owner','fixture-vendor','fixture-entitlement',100,200),)),patch.object(FixedProxyTransport,'execute',side_effect=simulated)as mock_transport,sync_playwright()as p:
  browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
  for width in (390,1100):
   ctx=browser.new_context(viewport={'width':width,'height':1000});page=ctx.new_page();errors=[];outside=[];requests=[];ctx.on('page',lambda pg:pg.on('pageerror',lambda e:errors.append(str(e))));page.on('pageerror',lambda e:errors.append(str(e)))
   def route(r):
    requests.append(r.request.url)
    if r.request.url.startswith(origin+'/'):r.continue_()
    else:outside.append(r.request.url);r.abort()
   ctx.route('**/*',route);page.goto(origin+'/workspace');page.wait_for_selector('#finder-proxy-f12-account [data-signin]',state='attached');assert len(calls)==(0 if width==390 else 6);assert 'your typed query (up to 1,000 characters)' in page.locator('#finder-proxy-f12-account').inner_text()
   # Workspace switching is original behavior; direct visibility is harness-only.
   page.locator('#finder-view').evaluate('(e)=>e.hidden=false');page.locator('#finder-proxy-f12-account').screenshot(path=str(out/f'disclosure-{width}.png'));frame=page.frame_locator('#finder');frame.locator('#q-main').wait_for();frame.locator('#q-main').fill('coffee');frame.locator('[data-sysf="0"]').click();frame.locator('#q-main').press('Enter');frame.locator('#f12-status').wait_for();assert not any('/api/finder-broker/features'in x for x in requests)
   page.locator('[data-username]').fill('alice');page.locator('[data-password]').fill(PW);page.locator('[data-signin]').click();page.wait_for_function("()=>document.querySelector('[data-identity]').textContent.includes('alice')")
   frame.locator('#q-main').press('Enter');
   try:frame.locator('#f12-status').filter(has_text='SIMULATED TEST TEXT').wait_for(timeout=5000)
   except Exception:
    print('DEBUG',page.locator('[data-status]').inner_text(),frame.locator('#f12-status').inner_text(),errors,flush=True);raise
   inner=page.locator('#finder').element_handle().content_frame();inner.goto(origin+'/workspace/finder/offline.html#code=1:090121');frame.locator('#d-back').wait_for()
   for selector,slot in (('#plain-go','#plain-slot'),('#brief-go','#brief-slot'),('#doc-go','#doc-slot')):
    frame.locator(selector).evaluate('(e)=>{let p=e.parentElement;while(p){if(p.tagName==="DETAILS")p.open=true;p=p.parentElement}}');frame.locator(selector).click();frame.locator(slot).filter(has_text='SIMULATED TEST TEXT').wait_for(state='attached')
   with page.expect_popup()as popup:frame.locator('#f12-report').click()
   report=popup.value;report.wait_for_selector('text=Optional AI snapshot context');report.wait_for_function('()=>document.__templateReport228?.complete===true');assert report.locator('.tpl-sec').count()==22;report.pdf(path=str(out/f'ai-context-{width}.pdf'),format='A4',print_background=True);report.close()
   # Original data-only report still never dispatches.
   before=len(calls)
   with page.expect_popup()as popup:frame.locator('#d-tpl').click()
   report=popup.value;report.wait_for_selector('#tpl-print');assert report.locator('.tpl-sec').count()==21;report.close();assert len(calls)==before
   frame.locator('#d-compare').click();frame.locator('#cmp-q').fill('tea');frame.locator('#cmp-res [data-pick]').first.click();frame.locator('#cmpv-go').click();frame.locator('#cmpv-slot').filter(has_text='SIMULATED TEST TEXT').wait_for(state='attached')
   assert len(calls)==(6 if width==390 else 12)
   if width==1100:
    frame.locator('#cmp-close').click();inner.goto(origin+'/workspace/finder/offline.html#code=1:090121');frame.locator('#f12-report').wait_for()
    mock_transport.side_effect=ValueError('SIMULATED unknown transport')
    with page.expect_popup()as popup:frame.locator('#f12-report').click()
    fallback=popup.value;fallback.wait_for_selector('#tpl-print');assert fallback.locator('.tpl-sec').count()==21;assert 'Preserved data snapshot.' in fallback.locator('body').inner_text();fallback.close()
    attempts=mock_transport.call_count;frame.locator('#f12-report').click();assert mock_transport.call_count==attempts
   assert not errors,errors;assert not outside,outside;assert not any('api-key'in x for x in requests);page.screenshot(path=str(out/f'workspace-{width}.png'),full_page=True)
   results.append(dict(width=width,six_features_simulated=True,actual_auth_csrf=True,data_report_no_dispatch=True,unknown_report_fallback_and_no_retry=(width==1100),external_requests=outside,page_errors=errors));ctx.close()
  browser.close()
finally:server.shutdown();app.extensions['finder_composition_close_f9']()
(out/'report.json').write_text(json.dumps(results,indent=2));print(results)
