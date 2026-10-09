"""227 nested original report probe. Synthetic storage, no product function patches."""
import sys, threading, json, re, os, hashlib, base64, subprocess
from pathlib import Path
from urllib.parse import urlsplit
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from integration.news_api import create_app
OUT=Path(os.environ.get('REPORT227_OUT','/tmp/report227-review'));OUT.mkdir(parents=True,exist_ok=True)
O='http://localhost:8786'
def safe_console(text):
 return re.sub(r'https?://[^\s\"\']+',lambda m:(lambda u:u.scheme+'://'+u.netloc+u.path)(urlsplit(m.group())),text)
KEY='SYNTHETIC-PLACEHOLDER-NOT-A-KEY'
SANDBOX='allow-scripts allow-same-origin allow-downloads allow-modals allow-popups'
source=(ROOT/'src/app.js').read_text()
assert hashlib.sha256(source.encode()).hexdigest()=='f8ecf57f73c28c376c4508f2ce7315f3ffad0a8a26d925a9782db6bb53e38f91'
section_source=source[source.index('function buildTemplateReport('):source.index('async function openTemplateReport(')]
sections=re.findall(r'<section class="tpl-sec"><h2><span class="tpl-num">([^<]+)</span> ([^<\'\n]+)',section_source)
sections=[(n,t.strip()) for n,t in sections]
app=create_app(authorize=lambda r:True)
server=make_server('127.0.0.1',8786,app);threading.Thread(target=server.serve_forever,daemon=True).start()
results={'started_at':datetime.now(timezone.utc).isoformat(),'source_sections':sections,'no_fix':True,'network_off':True}
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
  results['chromium_version']=b.version
  for variant in ['no-key','placeholder','blocked']:
   context=b.new_context(viewport={'width':1440,'height':1000},timezone_id='Asia/Kolkata')
   # Fixed report date and random, no keys except the literal synthetic own-key.
   context.add_init_script("window.fixturePrintCalls=0;window.print=()=>window.fixturePrintCalls++;")
   if variant=='blocked':context.add_init_script("window.open=()=>null;")
   context.add_init_script("""{ const RealDate=Date;const at=1791576000000;class FixedDate extends RealDate{constructor(...a){super(...(a.length?a:[at]));}static now(){return at;}}window.Date=FixedDate;Math.random=()=>0.25; }""")
   if variant!='no-key':context.add_init_script("localStorage.setItem('hsn-gemini-api-key','SYNTHETIC-PLACEHOLDER-NOT-A-KEY');localStorage.setItem('hsn-ai-provider','gemini');")
   aborted=[];popup_requests=[];errors=[];csp=[]
   def route(r):
    u=urlsplit(r.request.url)
    if r.request.url.startswith(O+'/'):return r.continue_()
    aborted.append({'method':r.request.method,'host':u.hostname,'path':u.path})
    r.abort()
   context.route('**/*',route)
   page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
   page.on('console',lambda m:csp.append(safe_console(m.text)) if 'Content Security Policy' in m.text else None)
   response=page.goto(O+'/workspace')
   assert response.headers['content-security-policy']=="default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-src 'self' https://www.youtube-nocookie.com"
   assert page.locator('#finder').get_attribute('sandbox')==SANDBOX
   with page.expect_response(lambda r:r.url==O+'/workspace/finder/index.html?report227=1') as rr:
    page.locator('#finder').evaluate("e=>e.src='/workspace/finder/index.html?report227=1#code=0:090121'")
   response=rr.value
   shell=response.text();scripts=[body for attrs,body in re.findall(r'<script\b([^>]*)>(.*?)</script>',shell,re.S|re.I) if body.strip() and not re.search(r'\bsrc\s*=',attrs,re.I)]
   hashes=["'sha256-"+base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()+"'" for s in scripts]
   expected="default-src 'self'; script-src 'self' "+' '.join(hashes)+"; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'self'; object-src 'none'; base-uri 'self'; form-action 'self'"
   assert response.headers['content-security-policy']==expected
   page.locator('[data-view=finder]').click();f=page.frame_locator('#finder');f.locator('#d-tpl').wait_for()
   frame=next(x for x in page.frames if '/workspace/finder/index.html' in x.url)
   if variant=='no-key':
    f.locator('#d-tpl').click();f.locator('#api-key').wait_for();assert len(context.pages)==1;assert frame.evaluate('V.needKey && V.settingsOpen && !V.busy');results['no_key_gate']=True;assert not aborted
   elif variant=='blocked':
    f.locator('#d-tpl').click();frame.wait_for_function('!V.busy && !!V.briefError');assert 'Popup blocked - allow popups for this page to open the report.' in f.locator('body').inner_text();assert f.locator('#d-tpl').is_enabled();assert len(context.pages)==1;assert not aborted;results['popup_blocked_path']=True
   else:
    with page.expect_popup() as pop:f.locator('#d-tpl').click()
    report=pop.value;report.on('request',lambda r:popup_requests.append(urlsplit(r.url).path));report.on('console',lambda m:csp.append(safe_console(m.text)) if 'Content Security Policy' in m.text else None)
    report.locator('.tpl-cover-title').wait_for(timeout=45000)
    assert report.url=='about:blank'
    assert report.evaluate("window.opener!==null && window.opener.frameElement.id==='finder' && window.opener.location.origin") == O
    titles=report.locator('.tpl-sec h2').evaluate_all("xs=>xs.map(x=>[x.querySelector('.tpl-num').textContent,x.childNodes[1].textContent.trim()])")
    assert titles==[list(s)for s in sections],titles
    f.locator('#d-tpl').wait_for(state='visible');assert f.locator('#d-tpl').is_enabled()
    results['popup_source_identity']=True
    body=report.locator('body').inner_text()
    product=frame.evaluate("pretty(S.db.entries[S.sel][2])")
    assert report.locator('.tpl-cover-title').inner_text()==product
    assert 'code 090121' in body and 'Copyright (c) 2026 Push. All rights reserved.' in body
    assert '2026-10-10' in body and '1.0 - Data edition' in body
    mode=re.search(r": '(Data edition[^']+)'",section_source).group(1)
    errornote=re.search(r"opts.aiError \? '([^']+)'",section_source).group(1)
    assert mode+errornote in body
    assert "esc(prod)" in section_source and "esc(modeLine)" in section_source
    assert report.locator('.tpl-cover-title').evaluate('e=>e.children.length')==0
    results['report_identity']={'product':product,'code':'090121','report_date':'2026-10-10','mode':mode+errornote}
    assert not aborted,aborted
    assert not popup_requests,popup_requests
    provider=[m for m in csp if "Connecting to 'https://generativelanguage.googleapis.com" in m]
    assert provider, csp
    results['provider_csp_count']=len(provider)
    results['outbound_requests']=aborted;results['popup_requests']=popup_requests
    results['response_csp_header_name']='Content-Security-Policy (enforced), no report-only header'
    assert 'content-security-policy-report-only' not in response.headers
    results['pagination_effect']={'pgnum_count':report.locator('.pgnum').count(),'positioned_sections':report.locator('.tpl-sec[style]').count()}
    before=report.evaluate('window.fixturePrintCalls');console_before=len(csp)
    button=report.get_by_role('button',name='Save as PDF / Print');button.focus();button.press('Enter')
    after=report.evaluate('window.fixturePrintCalls')
    violations=csp[console_before:]
    results['print_inline_probe']={'before':before,'after':after,'console':violations}
    assert before==after==0 and any('inline event handler' in v for v in violations)
    assert results['pagination_effect']=={'pgnum_count':0,'positioned_sections':0}
    # Control only: fresh popup document listener, no original function altered.
    console_before=len(csp)
    button.evaluate("e=>{e.removeAttribute('onclick');e.addEventListener('click',()=>window.print());}")
    control_before=report.evaluate('window.fixturePrintCalls');button.focus();button.press('Enter')
    control_after=report.evaluate('window.fixturePrintCalls')
    assert control_after==control_before+1
    assert not csp[console_before:],csp[console_before:]
    results['print_listener_control']={'before':control_before,'after':control_after,'console':csp[console_before:]}
    artifacts=[]
    for width in [1440,390]:
     report.set_viewport_size({'width':width,'height':1000})
     report.screenshot(path=str(OUT/f'popup-{width}.png'))
     artifacts.append({'file':f'popup-{width}.png','viewport':[width,1000],'captured_at':datetime.now(timezone.utc).isoformat(),'no_fix':True})
    options={'format':'A4','print_background':True,'margin':{'top':'14mm','right':'12mm','bottom':'20mm','left':'12mm'},'prefer_css_page_size':True}
    report.set_viewport_size({'width':1440,'height':1000})
    report.pdf(path=str(OUT/'report.pdf'),**options)
    subprocess.run(['pdftotext','-layout',str(OUT/'report.pdf'),str(OUT/'report.txt')],check=True)
    pages=(OUT/'report.txt').read_text().split('\f');pages=[x for x in pages if x.strip()]
    combined='\n'.join(pages)
    for n,title in sections:assert title in combined,title
    assert sections[0][1] in combined and sections[len(sections)//2][1] in combined and sections[-1][1] in combined
    subprocess.run(['pdftoppm','-scale-to','1000','-png',str(OUT/'report.pdf'),str(OUT/'margin-page')],check=True)
    selected=[1,(len(pages)+1)//2,len(pages)]
    for page_number in selected:
     subprocess.run(['pdftoppm','-f',str(page_number),'-l',str(page_number),'-scale-to','1000','-png','-singlefile',str(OUT/'report.pdf'),str(OUT/f'pdf-page-{page_number}')],check=True)
     artifacts.append({'file':f'pdf-page-{page_number}.png','page':page_number,'rendered_at':datetime.now(timezone.utc).isoformat(),'no_fix':True})
    results['pdf']={'options':options,'page_count':len(pages),'inspection_pages':selected,'all_section_titles_in_extracted_text':True,'pagination_effect':results['pagination_effect']}
    results['artifacts']=artifacts
    results['pdf']['captured_at']=datetime.now(timezone.utc).isoformat();results['errors']=errors
    results['csp_console']=csp
    assert not errors,errors
   context.close()
  b.close()
finally:
 results['finished_at']=datetime.now(timezone.utc).isoformat();(OUT/'probe.json').write_text(json.dumps(results,indent=2));server.shutdown()
print(json.dumps(results))
