"""Actual loopback Chrome, preserved real F8 snapshot only. No refresh/provider.
Usage OUTPUT ARCHIVE SHA ROOT.
"""
import sys,json,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration import finder_binding_f8 as f8,finder_composition_f9 as f9,finder_trend_f16 as m
from integration.public_preview_builder import build_public_preview
from tests.test_code_news_coverage_binding_prep import SAMPLE
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True);b=f8.prepare({f8.FLAG:'true'},archive=sys.argv[2],expected_sha256=sys.argv[3],root=sys.argv[4]);app=build_public_preview(dict(SAMPLE,**{f9.FLAG:'true',m.FLAG:'true','PUBLIC_FINDER_DATA_REPORT_ENABLED':'true','PUBLIC_FINDER_PROXY_FEATURES_ENABLED':'true'}),finder_candidate_binding=b);old=app.wsgi_app
def proxy(env,start):env['HTTP_HOST']='example.test';env['wsgi.url_scheme']='https';return old(env,start)
app.wsgi_app=proxy;server=make_server('127.0.0.1',0,app,threaded=True);threading.Thread(target=server.serve_forever,daemon=True).start();origin='http://127.0.0.1:'+str(server.server_port);results=[]
try:
 with sync_playwright()as p:
  browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
  for width in (390,1100):
   ctx=browser.new_context(viewport={'width':width,'height':1000});page=ctx.new_page();errors=[];outside=[];urls=[];page.on('pageerror',lambda e:errors.append(str(e)))
   def route(r):
    urls.append(r.request.url)
    if r.request.url.startswith(origin+'/'):r.continue_()
    else:outside.append(r.request.url);r.abort()
   ctx.route('**/*',route)
   for system,code in [(1,'09012110'),(1,'0901'),(0,'090121')]:
    page.goto(origin+'/workspace/finder/offline.html#code='+str(system)+':'+code);
    try:page.locator('#f16-trend').wait_for(timeout=10000)
    except Exception:
     print('DEBUG',system,code,errors,page.evaluate('({sel:S.sel,exists:!!document.getElementById("d-tpl"),root:!!document.getElementById("root")})'),flush=True);raise
    page.locator('#f16-trend summary').click();text=page.locator('#f16-trend').inner_text();assert 'Package SHA256'in text and b.package_sha256 in text;assert page.locator('#d-tpl').count()==1;assert page.locator('#f12-report').count()==1;
    if not page.evaluate('document.documentElement.scrollWidth<=innerWidth'):page.screenshot(path=str(out/'overflow.png'),full_page=True);print('OVERFLOW',page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth,bad:[...document.querySelectorAll("#f16-trend *")].filter(e=>e.getBoundingClientRect().right>innerWidth).slice(0,10).map(e=>[e.tagName,e.className,e.getBoundingClientRect().width])})'),flush=True)
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert page.locator('#f16-trend').count()==1
    if system==0:assert 'Foreign or chapter/heading codes'in text
    elif code=='0901':assert 'at least six digits'in text
    else:
     page.locator('#f16-from').select_option('2021');page.locator('#f16-to').select_option('2025');assert 'Changes use the chosen From year' in page.locator('#f16-trend').inner_text();assert 'USD' in text and 'net weight' in text;page.locator('#f16-trend').screenshot(path=str(out/f'trend-{width}.png'))
   assert not errors and not outside;assert not any('/api/finder-broker'in u for u in urls);results.append(dict(width=width,real_F8=True,exact_parent_nonIndia=True,no_broker_calls=True,errors=errors,outside=outside));ctx.close()
  browser.close()
finally:server.shutdown();app.extensions['finder_composition_close_f9']()
(out/'report.json').write_text(json.dumps(results,indent=2));print(results)
