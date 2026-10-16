"""Local real held candidate composition. No deployed activation/providers."""
import sys,json,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration import finder_binding_f8 as f8,finder_composition_f9 as m
from integration.public_preview_builder import build_public_preview
from tests.test_code_news_coverage_binding_prep import SAMPLE
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
binding=f8.prepare({f8.FLAG:'true'},archive=sys.argv[1],expected_sha256=sys.argv[2],root=sys.argv[3]);out=Path(sys.argv[4]);out.mkdir(parents=True,exist_ok=True)
env=dict(SAMPLE,**{m.FLAG:'true','PUBLIC_AI_ANSWERS_ENABLED':'true','PUBLIC_NEWS_FINDER_LINKS_ENABLED':'true','PUBLIC_CODE_NEWS_ENABLED':'true','PUBLIC_CODE_NEWS_SCOPE_REVIEWED':'true','PUBLIC_RELATIONSHIP_NAV_ENABLED':'true','PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED':'true'})
app=build_public_preview(env,finder_candidate_binding=binding);old=app.wsgi_app
def proxy(env,start):env['HTTP_HOST']='example.test';env['wsgi.url_scheme']='https';return old(env,start)
app.wsgi_app=proxy;server=make_server('127.0.0.1',8849,app,threaded=True);threading.Thread(target=server.serve_forever,daemon=True).start();origin='http://127.0.0.1:8849';results=[]
try:
 with sync_playwright()as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
  for width in (390,1100):
   context=browser.new_context(viewport={'width':width,'height':950});page=context.new_page();errors=[];outside=[];requests=[];page.on('pageerror',lambda e:errors.append(str(e)))
   def route(r):
    requests.append(r.request.url)
    if r.request.url.startswith(origin+'/'):r.continue_()
    else:outside.append(r.request.url);r.abort()
   page.route('**/*',route);page.goto(origin+'/workspace/finder/offline.html#code=0:090121');page.wait_for_function('()=>typeof S!=="undefined"&&S.db&&S.sel!==null')
   assert page.evaluate('S.db.entries[S.sel][1]')=='090121';assert page.evaluate('V.apiKey')=='';assert page.evaluate('JSON.stringify(S.notes)')=='{}';assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert page.evaluate('()=>navigator.serviceWorker.getRegistrations().then(r=>r.length)')==0
   page.screenshot(path=str(out/f'offline-{width}.png'));assert not errors,errors;assert not outside,outside;assert not any('/api/'in u for u in requests),requests
   results.append({'width':width,'coffee_selected':True,'keys_notes_empty':True,'provider_requests':0,'automatic_API_requests':0,'workers':0,'errors':errors,'runtime_deployed':False});context.close()
  browser.close()
finally:server.shutdown();app.extensions['finder_composition_close_f9']()
(out/'report.json').write_text(json.dumps(results,indent=2));print(results)
