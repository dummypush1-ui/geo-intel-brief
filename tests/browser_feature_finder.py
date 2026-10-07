from pathlib import Path
import sys, threading, json, importlib.util
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from feature_finder_prep import shell as mod
shell=mod.prepare_shell((root/'index.html').read_text())
class Handler(SimpleHTTPRequestHandler):
 def do_GET(self):
  if self.path.split('?')[0].split('#')[0] == '/index.html':
   wire=shell.encode();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(wire)));self.end_headers();self.wfile.write(wire)
  else:super().do_GET()
server=ThreadingHTTPServer(('127.0.0.1',8793),partial(Handler,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':1100,'height':900});calls=[];errors=[];mode=['success']
 def route(r):
  url=r.request.url
  if url.startswith('http://127.0.0.1:8793/'):return r.continue_()
  calls.append(url)
  if 'hsn-ai-proxy' not in url or '/ships' in url:return r.abort()
  if 'nvidia' in url:raise AssertionError('forbidden provider')
  provider=next((x for x in ['groq','gemini','mistral'] if '/'+x+'/' in url),None)
  if mode[0]=='failed' or provider!='mistral':return r.fulfill(status=429,json={'error':{'message':'quota reached'}},headers={'Access-Control-Allow-Origin':'*'})
  body=r.request.post_data_json or {};prompt=json.dumps(body)
  text=json.dumps({'ok':True}) if 'Fact-check' in prompt else json.dumps({'sec01a':'FIXTURE product properties. This is simulated, not live analysis.','sec02':'FIXTURE manufacturing.','sec03':'FIXTURE trade details.','sec15':'Invoice - Exporter - Record goods\nPacking list - Exporter - Record packing'})
  r.fulfill(status=200,json={'choices':[{'message':{'content':text}}]},headers={'Access-Control-Allow-Origin':'*'})
 context.route('**/*',route)
 page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://127.0.0.1:8793/index.html#code=0:090121');page.locator('#d-tpl').wait_for()
 allowed=page.evaluate('[...new Set(shuffleProviders())]');assert sorted(allowed)==['gemini','groq','mistral']
 with page.expect_popup() as pop:page.locator('#d-tpl').click()
 report=pop.value;report.get_by_text('FIXTURE product properties.',exact=False).wait_for(timeout=30000)
 assert not report.locator('.tpl-src').count();assert 'Copyright (c) 2026 Push' in report.locator('body').inner_text()
 report.screenshot(path='/downloads/finder-report-fixture.png',full_page=False)
 report.pdf(path='/downloads/finder-report-fixture.pdf',format='A4',print_background=True)
 mode[0]='failed';calls.clear()
 with page.expect_popup() as pop2:page.locator('#d-tpl').click()
 fallback=pop2.value;fallback.get_by_text('Product Research Report',exact=True).wait_for(timeout=30000)
 assert 'FIXTURE product properties' not in fallback.locator('body').inner_text()
 assert page.locator('#d-tpl').is_enabled();assert not errors
 # Abort deadline covers a response whose JSON body never completes.
 timeout_probe=page.evaluate('''async () => { const savedFetch=window.fetch,savedSetTimeout=window.setTimeout,savedClearTimeout=window.clearTimeout;let aborted=false,cleared=false;window.setTimeout=(fn,ms)=>savedSetTimeout(fn,5);window.clearTimeout=(id)=>{cleared=true;savedClearTimeout(id)};window.fetch=async (u,o)=>({ok:true,status:200,json:()=>new Promise((res,rej)=>o.signal.addEventListener('abort',()=>{aborted=true;rej(new Error('timeout'))}))});try{await mergedProviderFetch('https://example.invalid',{});return {bad:true}}catch(e){return {aborted,cleared,timedOut:e.message==='AI response timed out'}}finally{window.fetch=savedFetch;window.setTimeout=savedSetTimeout;window.clearTimeout=savedClearTimeout}}''');assert timeout_probe=={'aborted':True,'cleared':True,'timedOut':True},timeout_probe
 fallback.screenshot(path='/downloads/finder-report-fallback.png')
 # Unsupported saved NVIDIA key must not go to Gemini or any provider.
 calls.clear();page.evaluate("V.apiKey='nvapi-FIXTURE'; V.apiProvider='nvidia'")
 result=page.evaluate("aiPickText('fixture',{temperature:0,maxTokens:10}).then(()=>({bad:true})).catch(e=>({message:e.message}))")
 assert 'supports Groq, Gemini and Mistral only' in result['message'];assert not calls
 print(json.dumps({'original_ui_report_success':True,'failed_AI_static_report_fallback':True,'three_provider_allowlist':allowed,'no_external_network':True,'page_errors':errors,'unsupported_key_not_disclosed':True,'pdf_fixture_only':True}))
 browser.close()
server.shutdown()
