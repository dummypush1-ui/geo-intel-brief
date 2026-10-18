"""Local actual Chrome/PDF regression. No deployment, credentials or providers.
Usage: python tests/browser_finder_report_f11.py OUTPUT [ARCHIVE SHA256 ROOT]
Without source arguments, creates the existing synthetic held F9 fixture.
Requires Playwright, Chrome, Poppler and Pillow. All traffic stays loopback.
"""
import sys,json,threading,subprocess,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration import finder_binding_f8 as f8,finder_composition_f9 as f9,finder_report_f11 as f11,finder_device_f10 as f10
from integration.public_preview_builder import build_public_preview
from tests.test_code_news_coverage_binding_prep import SAMPLE
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
from PIL import Image,ImageOps,ImageDraw
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True);fixture=None
if len(sys.argv)==5:b=f8.prepare({f8.FLAG:'true'},archive=sys.argv[2],expected_sha256=sys.argv[3],root=sys.argv[4])
else:
 from tests import test_finder_composition_f9 as fixture
 fixture.Tests.setUpClass();b=fixture.Tests.binding
app=build_public_preview(dict(SAMPLE,**{f9.FLAG:'true',f11.FLAG:'true',f10.FLAG:'true'}),finder_candidate_binding=b);old=app.wsgi_app

def proxy(env,start):env['HTTP_HOST']='example.test';env['wsgi.url_scheme']='https';return old(env,start)
app.wsgi_app=proxy;server=make_server('127.0.0.1',0,app,threaded=True);threading.Thread(target=server.serve_forever,daemon=True).start();origin='http://127.0.0.1:'+str(server.server_port);results=[]

def pdf_check(path,shortlist=False):
 text=subprocess.check_output(['pdftotext','-layout',str(path),'-'],text=True);pages=text.rstrip('\f\n').split('\f');assert all(len(p.strip())>30 for p in pages),'blank/sparse page'
 if shortlist:assert len(pages)==1
 else:
  assert 5<=len(pages)<=16,len(pages)
  for label in ('Contents','20 FAQ','How to use this report','This report is research support, not legal, tax or customs advice.'):assert label in pages[0],label
  for label in ('Preserved data snapshot.','Dataset position','21 represented systems (dataset: 22 systems)','Duty / rate rows for this product: 21 (dataset: 22 systems)'):assert label in text,label
  for claim in ('For a full AI-written','automatically every week','exact official data','Verified position'):assert claim not in text,claim
  assert 'Product-specific research is not included.' in text
 subprocess.run(['pdftoppm','-scale-to','1000','-png',str(path),str(path.with_suffix(''))],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 images=sorted(path.parent.glob(path.stem+'-*.png'));thumbs=[];coverage=[]
 for png in images:
  im=Image.open(png).convert('RGB');gray=ImageOps.grayscale(im);ink=sum(n for i,n in enumerate(gray.histogram())if i<220)/(im.width*im.height);assert ink>.003,(png,ink);coverage.append(round(ink,4));im.thumbnail((300,425));thumbs.append(im.copy())
 sheet=Image.new('RGB',(320*3,455*((len(thumbs)+2)//3)),'#ddd');draw=ImageDraw.Draw(sheet)
 for i,im in enumerate(thumbs):x=(i%3)*320+10;y=(i//3)*455+25;sheet.paste(im,(x,y));draw.text((x,y-18),str(i+1),fill='black')
 sheet.save(path.with_suffix('.contact.png'));return {'pages':len(pages),'ink_coverage':coverage}
try:
 with sync_playwright()as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
  for width in (390,1100):
   ctx=browser.new_context(viewport={'width':width,'height':1000});page=ctx.new_page();errors=[];outside=[];requests=[]
   ctx.on('page',lambda p:p.on('pageerror',lambda e:errors.append(str(e))))
   page.on('pageerror',lambda e:errors.append(str(e)))
   def route(r):
    requests.append(r.request.url)
    if r.request.url.startswith(origin+'/')or r.request.url.startswith('blob:'):r.continue_()
    else:outside.append(r.request.url);r.abort()
   ctx.route('**/*',route)
   for system in (0,1):
    page.goto(origin+'/workspace/finder/offline.html#code='+str(system)+':090121');page.wait_for_function('()=>typeof S!=="undefined"&&S.db&&S.sel!==null')
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert page.evaluate('V.apiKey')==''
    with page.expect_popup()as popup:page.locator('#d-tpl').click()
    report=popup.value;report.wait_for_function('()=>document.__templateReport228?.complete===true');assert report.locator('.tpl-sec').count()==21
    assert report.locator('.tpl-contents li').count()==21
    assert page.locator('#api-key').count()==0;assert not page.evaluate('V.needKey')
    report.evaluate('()=>{window.__prints=0;window.print=()=>window.__prints++}');report.locator('#tpl-print').click();assert report.evaluate('window.__prints')==1
    path=out/f'report-{system}-{width}.pdf';report.pdf(path=str(path),format='A4',print_background=True,prefer_css_page_size=True);stats=pdf_check(path);report.close()
    results.append(dict(width=width,system=system,no_key=True,all_21_sections=True,**stats))
   # Actual blocked popup reports a recoverable message, never key setup.
   page.evaluate('()=>{window.open=()=>null}');page.locator('#d-tpl').click();assert 'Popup blocked' in page.evaluate('V.briefError');assert not page.evaluate('V.needKey')
   page.reload();page.wait_for_function('()=>typeof S!=="undefined"&&S.db&&S.sel!==null');page.locator('#d-short').click();page.locator('#d-back').click();page.locator('#open-sl').click()
   page.evaluate('()=>{window.__prints=0;window.print=()=>window.__prints++}');page.locator('#sl-print').click();assert page.evaluate('window.__prints')==1
   path=out/f'shortlist-{width}.pdf';page.pdf(path=str(path),format='A4',print_background=True);stats=pdf_check(path,True);results.append(dict(width=width,shortlist=True,**stats))
   assert not outside,outside;assert not errors,errors;assert not any('/api/'in u for u in requests),requests
   assert page.evaluate('()=>caches.keys()')==[];assert page.evaluate('()=>navigator.serviceWorker.getRegistrations().then(x=>x.length)')==0
   results.append(dict(width=width,outside=outside,page_errors=errors,API_requests=[]));ctx.close()
  browser.close()
finally:
 server.shutdown();app.extensions['finder_composition_close_f9']()
 if fixture:fixture.Tests.tearDownClass()
(out/'report.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
