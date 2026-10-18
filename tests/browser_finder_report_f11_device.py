"""F11 device profile vs original F8 safe render, actual local Chrome. No providers."""
import json,sys,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration import finder_binding_f8 as f8,finder_composition_f9 as f9,finder_device_f10 as m
from integration.public_preview_builder import build_public_preview
from tests.test_code_news_coverage_binding_prep import SAMPLE
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
b=f8.prepare({f8.FLAG:'true'},archive=sys.argv[1],expected_sha256=sys.argv[2],root=sys.argv[3]);out=Path(sys.argv[4]);out.mkdir(parents=True,exist_ok=True)
app=build_public_preview(dict(SAMPLE,**{f9.FLAG:'true',m.FLAG:'true','PUBLIC_FINDER_DATA_REPORT_ENABLED':'true','PUBLIC_AI_ANSWERS_ENABLED':'true'}),finder_candidate_binding=b);d=app.extensions[m.KEY];old=app.wsgi_app
# Only the loopback test server maps the public origin guard to its test host.
def proxy(env,start):env['HTTP_HOST']='example.test';env['wsgi.url_scheme']='https';return old(env,start)
other=build_public_preview(dict(SAMPLE,**{f9.FLAG:'true',m.FLAG:'true'}),finder_candidate_binding=b);od=other.extensions[m.KEY];other_wsgi=other.wsgi_app
def combined(env,start):
 env['HTTP_HOST']='example.test';env['wsgi.url_scheme']='https'
 return (other_wsgi if env.get('PATH_INFO','').startswith(od.base)else old)(env,start)
app.wsgi_app=combined;server=make_server('127.0.0.1',8851,app,threaded=True);threading.Thread(target=server.serve_forever,daemon=True).start();origin='http://127.0.0.1:8851';results=[];assert d.digest!=od.digest and d.base!=od.base and d.cache!=od.cache
try:
 with sync_playwright()as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
  for width in (390,1100):
   context=browser.new_context(viewport={'width':width,'height':1000});page=context.new_page();errors=[];outside=[];urls=[];page.on('pageerror',lambda e:errors.append(str(e)))
   def route(r):
    urls.append(r.request.url)
    if r.request.url.startswith(origin+'/'):r.continue_()
    else:outside.append(r.request.url);r.abort()
   # Routing disables HTTP cache but not service-worker CacheStorage.
   context.route('**/*',route);page.goto(origin+d.base);page.wait_for_selector('#save');assert page.evaluate('()=>navigator.serviceWorker.getRegistrations().then(x=>x.length)')==0;assert page.evaluate('()=>caches.keys()')==[];assert not any('snapshot.html'in u for u in urls)
   page.goto(origin+od.base);page.click('#save');page.wait_for_function("()=>document.getElementById('status').textContent.startsWith('This public snapshot is saved')");page.goto(origin+d.base);
   page.evaluate("localStorage.setItem('provider-fixture','do-not-change')");page.screenshot(path=str(out/f'device-before-{width}.png'))
   page.click('#save');page.wait_for_function("()=>document.getElementById('status').textContent.startsWith('This public snapshot is saved')",timeout=60000)
   assert set(page.evaluate('()=>caches.keys()'))=={d.cache,od.cache};assert set(page.evaluate('()=>navigator.serviceWorker.getRegistrations().then(x=>x.map(r=>r.scope))'))=={origin+d.base,origin+od.base}
   page.screenshot(path=str(out/f'device-saved-{width}.png'));context.set_offline(True);page.goto(origin+d.base+'snapshot.html#code=0:090121');page.wait_for_function('()=>typeof S!=="undefined"&&S.db&&S.sel!==null');assert page.evaluate('S.db.entries[S.sel][1]')=='090121';assert page.evaluate('V.apiKey')=='';assert page.evaluate('JSON.stringify(S.notes)')=='{}';assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path=str(out/f'device-offline-{width}.png'))
   with page.expect_popup()as popup:page.locator('#d-tpl').click()
   report=popup.value;report.wait_for_function('()=>document.__templateReport228?.complete===true');assert report.locator('.tpl-sec').count()==21;assert 'Preserved data snapshot.' in report.locator('body').inner_text();report.close()
   context.set_offline(False);page.goto(origin+d.base);page.click('#clear');page.wait_for_function("()=>document.getElementById('status').textContent.startsWith('This snapshot was cleared')");assert page.evaluate('()=>caches.keys()')==[od.cache];assert page.evaluate('()=>navigator.serviceWorker.getRegistrations().then(x=>x.map(r=>r.scope))')==[origin+od.base];assert page.evaluate("localStorage.getItem('provider-fixture')")=='do-not-change';assert not outside,outside;assert not errors,errors
   context.set_offline(True);page.goto(origin+od.base+'snapshot.html#code=0:090121');page.wait_for_function('()=>typeof S!=="undefined"&&S.db&&S.sel!==null');assert page.evaluate('S.db.entries[S.sel][1]')=='090121';context.set_offline(False)
   assert not any('/api/'in u for u in urls),urls;results.append({'width':width,'no_automatic_storage':True,'manual_save':True,'offline_coffee':True,'manual_clear':True,'same_F8_original_and_F11_profiles_coexist_clear_preserves_original_offline':True,'offline_no_key_report_all_21_sections':True,'keys_untouched':True,'errors':errors,'provider_requests':outside});context.close()
  browser.close()
finally:server.shutdown();app.extensions['finder_composition_close_f9']();other.extensions['finder_composition_close_f9']()
(out/'report.json').write_text(json.dumps(results,indent=2));print(results)
