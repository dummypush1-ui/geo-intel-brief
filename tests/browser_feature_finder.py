"""229 current own-key report fixture. No real provider request or shared failover proof."""
from pathlib import Path
import sys,threading,json,os,re,hashlib,subprocess
from datetime import datetime,timezone
from urllib.parse import urlsplit
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from feature_finder_prep import shell as mod
APP_SHA='bcd406d75b27b053fc5716d141ca278932115f14e39eca74d19a2284fc59d313'
INDEX_SHA='e2ed3326bfb8ca0805677e026438ff412611eef712526dea17b49d6c7fa30625'
assert hashlib.sha256((root/'src/app.js').read_bytes()).hexdigest()==APP_SHA
assert hashlib.sha256((root/'index.html').read_bytes()).hexdigest()==INDEX_SHA
shell=mod.prepare_shell((root/'index.html').read_text())
OUT=Path(os.environ.get('FINDER229_OUT','/tmp/finder229-review'));OUT.mkdir(parents=True,exist_ok=True)
ORIGIN='http://127.0.0.1:8793'
PLACEHOLDER='SYNTHETIC-PLACEHOLDER-NOT-A-KEY'
class Handler(SimpleHTTPRequestHandler):
 def do_GET(self):
  if urlsplit(self.path).path=='/index.html':
   wire=shell.encode();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(wire)));self.end_headers();self.wfile.write(wire)
  else:super().do_GET()
server=ThreadingHTTPServer(('127.0.0.1',8793),partial(Handler,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start()
result={'phase':'AFTER229','started_at':datetime.now(timezone.utc).isoformat(),'source_pins':{'app':APP_SHA,'index':INDEX_SHA},'simulated':True,'outbound_successes':0,'cases':{},'artifacts':[]}
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox']);result['chromium']=browser.version
  for mode in ['no-key','success','429']:
   context=browser.new_context(viewport={'width':1100,'height':900},timezone_id='Asia/Kolkata')
   context.add_init_script("{const RealDate=Date;class FixedDate extends RealDate{constructor(...a){super(...(a.length?a:[1791576000000]));}static now(){return 1791576000000;}}window.Date=FixedDate;Math.random=()=>0.25;}window.fixturePrintCalls=0;window.print=()=>window.fixturePrintCalls++;")
   if mode!='no-key':context.add_init_script("localStorage.setItem('hsn-gemini-api-key','SYNTHETIC-PLACEHOLDER-NOT-A-KEY');localStorage.setItem('hsn-ai-provider','mistral');")
   calls=[];unexpected=[];errors=[]
   def route(r):
    u=urlsplit(r.request.url)
    if r.request.url.startswith(ORIGIN+'/'):return r.continue_()
    call={'method':r.request.method,'host':u.hostname,'path':u.path}
    if u.hostname=='api.frankfurter.dev':
     calls.append({**call,'disposition':'expected FX read aborted'});return r.abort()
    if u.hostname!='api.mistral.ai' or u.path!='/v1/chat/completions':
     unexpected.append(call);return r.abort()
    # Inspect only for synthetic-key binding, never persist headers or request body.
    assert mode!='no-key'
    assert r.request.headers.get('authorization')=='Bearer '+PLACEHOLDER
    calls.append({**call,'disposition':'mock429' if mode=='429' else 'mock-success'})
    if mode=='429':return r.fulfill(status=429,json={'error':{'message':'SIMULATED TEST quota reached'}},headers={'Access-Control-Allow-Origin':'*'})
    narrative={k:'SIMULATED TEST TEXT: '+k+' context only. This is not a verified AI answer. <b>literal marker</b> & test.' for k in ['sec01a']+[f'sec{i:02}'for i in range(2,20)]}
    narrative['sec15']='SIMULATED TEST invoice - Test issuer - Fixture only\nSIMULATED TEST packing list - Test issuer - Fixture only'
    r.fulfill(status=200,json={'choices':[{'message':{'content':json.dumps(narrative)}}]},headers={'Access-Control-Allow-Origin':'*'})
   context.route('**/*',route)
   page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(ORIGIN+'/index.html#code=0:090121');page.locator('#d-tpl').wait_for()
   assert sorted(page.evaluate('[...new Set(shuffleProviders())]'))==['gemini','groq','mistral']
   assert page.evaluate("AI_PROXY_URL==='' && ['gemini','groq','mistral','nvidia'].every(k=>builtinKeys(k).length===0)")
   if mode=='no-key':
    page.locator('#d-tpl').click();page.locator('#api-key').wait_for();assert len(context.pages)==1;assert page.evaluate('V.needKey && V.settingsOpen && !V.busy')
    result['cases'][mode]={'key_prompt':True,'no_popup':True,'ui_allowlist_enum_only':['gemini','groq','mistral'],'sanitized_calls':calls}
   else:
    with page.expect_popup() as pop:page.locator('#d-tpl').click()
    report=pop.value;report.wait_for_function('document.__templateReport228 && document.__templateReport228.complete',timeout=45000)
    text=report.locator('body').inner_text()
    assert report.evaluate('!!window.opener') and report.url=='about:blank'
    assert 'Copyright (c) 2026 Push. All rights reserved.' in text
    assert not report.locator('.tpl-src').count();assert page.locator('#d-tpl').is_enabled()
    if mode=='success':
     assert 'AI-assisted research edition' in text and 'SIMULATED TEST TEXT: sec01a' in text
     assert '<b>literal marker</b> & test.' in text
     assert not report.locator('.tpl-sec b').count()
    else:
     assert 'Data edition' in text and 'AI narrative sections were unavailable this time' in text and 'SIMULATED TEST TEXT' not in text
    report.get_by_role('button',name='Save as PDF / Print').focus();report.keyboard.press('Enter');assert report.evaluate('window.fixturePrintCalls')==1
    for width,height in [(1100,900),(390,900)]:
     report.set_viewport_size({'width':width,'height':height});report.screenshot(path=str(OUT/f'{mode}-{width}.png'))
     result['artifacts'].append({'path':f'{mode}-{width}.png','captured_at':datetime.now(timezone.utc).isoformat(),'viewport':[width,height],'phase':'AFTER229'})
    report.set_viewport_size({'width':1100,'height':900});report.emulate_media(media='print')
    options={'format':'A4','print_background':True,'margin':{'top':'14mm','right':'12mm','bottom':'20mm','left':'12mm'},'prefer_css_page_size':True}
    report.pdf(path=str(OUT/f'{mode}.pdf'),**options)
    subprocess.run(['pdftotext','-layout',str(OUT/f'{mode}.pdf'),str(OUT/f'{mode}.txt')],check=True)
    pages=[x for x in (OUT/f'{mode}.txt').read_text().split('\f')if x.strip()];selected=[1,(len(pages)+1)//2,len(pages)]
    assert 'Copyright (c) 2026 Push. All rights reserved.' in pages[-1]
    for number in selected:
     filename=f'{mode}-page-{number}'
     subprocess.run(['pdftoppm','-f',str(number),'-l',str(number),'-scale-to','1000','-png','-singlefile',str(OUT/f'{mode}.pdf'),str(OUT/filename)],check=True)
     result['artifacts'].append({'path':filename+'.png','page':number,'captured_at':datetime.now(timezone.utc).isoformat(),'phase':'AFTER229'})
    result['cases'][mode]={'original_button_popup':True,'mock_mode':mode,'print_counter':1,'pagination':report.locator('.pgnum').count(),'busy_reset':True,'page_count':len(pages),'pdf_options':options,'inspection_pages':selected,'sanitized_calls':calls}
    # Existing served-copy bounded-body timeout probe, labelled instrumented helper only.
    if mode=='success':
     probe=page.evaluate('''async()=>{const sf=window.fetch,st=window.setTimeout,sc=window.clearTimeout;let aborted=false,cleared=false;window.setTimeout=(fn,ms)=>st(fn,5);window.clearTimeout=id=>{cleared=true;sc(id)};window.fetch=async(u,o)=>({ok:true,status:200,json:()=>new Promise((res,rej)=>o.signal.addEventListener('abort',()=>{aborted=true;rej(Error('timeout'))}))});try{await mergedProviderFetch('https://example.invalid',{});return {bad:true}}catch(e){return {aborted,cleared,timedOut:e.message==='AI response timed out'}}finally{window.fetch=sf;window.setTimeout=st;window.clearTimeout=sc}}''')
     assert probe=={'aborted':True,'cleared':True,'timedOut':True};result['instrumented_body_timeout']=probe
     before=len(calls);page.evaluate("V.apiKey='nvapi-SYNTHETIC';V.apiProvider='nvidia'")
     refusal=page.evaluate("aiPickText('fixture',{temperature:0,maxTokens:10}).then(()=>({bad:true})).catch(e=>({message:e.message}))")
     assert 'supports Groq, Gemini and Mistral only' in refusal['message'] and len(calls)==before
     result['unknown_provider_refusal']={'message':refusal['message'],'no_new_request':True}
   assert not unexpected,unexpected;assert not errors,errors
   context.close()
  browser.close()
finally:
 server.shutdown();result['finished_at']=datetime.now(timezone.utc).isoformat();(OUT/'result.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
