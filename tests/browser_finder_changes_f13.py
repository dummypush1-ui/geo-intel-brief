"""Actual loopback Chrome, same supplied F8 snapshot before/after. No refresh.
Usage OUTPUT ARCHIVE SHA ROOT. Same-snapshot case must never claim a change.
"""
import sys,json,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration import finder_binding_f8 as f8,finder_composition_f9 as f9,finder_changes_f13 as m
from integration.public_preview_builder import build_public_preview
from tests.test_code_news_coverage_binding_prep import SAMPLE
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True);b=f8.prepare({f8.FLAG:'true'},archive=sys.argv[2],expected_sha256=sys.argv[3],root=sys.argv[4]);app=build_public_preview(dict(SAMPLE,**{f9.FLAG:'true',m.FLAG:'true'}),finder_candidate_binding=b,finder_comparison_baseline=b);old=app.wsgi_app
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
   ctx.route('**/*',route);page.goto(origin+m.PAGE);assert not any(m.API in u for u in urls)
   page.locator('#system').select_option('IN');page.locator('#query button').click();page.locator('#status').filter(has_text='Comparison complete').wait_for();assert 'No difference in the compared wording' in page.locator('#result').inner_text();assert page.locator('.pair .card').count()==2;assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path=str(out/f'changes-{width}.png'),full_page=True)
   page.locator('#code').fill('999999999999');page.locator('#query button').click();page.locator('#result').filter(has_text='999999999999').wait_for();assert 'not_present_in_snapshot'in page.locator('#result').inner_text();assert not errors and not outside;assert not any('/api/finder-broker'in u for u in urls);results.append(dict(width=width,same_snapshot_no_changes=True,absence_not_deletion=True,no_auto_API=True,errors=errors,outside=outside));ctx.close()
  # A real mounted builder with no baseline must remain honest in the UI.
  app.extensions['finder_changes_f13'].before=None
  ctx=browser.new_context(viewport={'width':390,'height':1000});page=ctx.new_page();ctx.route('**/*',lambda r:r.continue_()if r.request.url.startswith(origin+'/')else r.abort());page.goto(origin+m.PAGE);page.locator('#query button').click();page.locator('#status').filter(has_text='Comparison unavailable').wait_for();assert 'second verified public snapshot' in page.locator('#result').inner_text();assert 'No comparison or change claim' in page.locator('#result').inner_text();assert page.locator('.pair').count()==0;assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path=str(out/'baseline-missing-390.png'),full_page=True);results.append(dict(missing_baseline_no_claim=True));ctx.close()
  browser.close()
finally:server.shutdown();app.extensions['finder_composition_close_f9']()
(out/'report.json').write_text(json.dumps(results,indent=2));print(results)
