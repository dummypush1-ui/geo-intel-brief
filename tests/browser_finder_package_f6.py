"""Inspect exact held F6 ZIP render locally: archive.zip output-directory."""
import sys,threading,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from flask import Flask,Response
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
from integration import finder_render_f5 as m
import zipfile
with zipfile.ZipFile(sys.argv[1])as archive:
 rendered=archive.read('review/public-offline.html').decode();manifest=json.loads(archive.read('manifest.json'));assert hashlib.sha256(rendered.encode()).hexdigest()==manifest['files']['review/public-offline.html']['sha256']
out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
app=Flask('f5-local');origin='http://127.0.0.1:8844'
@app.get('/candidate.html')
def candidate():return Response(rendered,mimetype='text/html')
server=make_server('127.0.0.1',8844,app,threaded=True);threading.Thread(target=server.serve_forever,daemon=True).start();results=[]
try:
 with sync_playwright()as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
  for width in (390,1100):
   context=browser.new_context(viewport={'width':width,'height':950});page=context.new_page();errors=[];requests=[];page.on('pageerror',lambda e:errors.append(str(e)))
   def route(route):
    requests.append(route.request.url)
    if not route.request.url.startswith(origin+'/candidate.html'):route.abort();return
    route.continue_()
   page.route('**/*',route);page.goto(origin+'/candidate.html#code=0:090121');page.wait_for_function('typeof S!=="undefined"&&S.db&&S.sel!==null',timeout=40000)
   assert page.evaluate('S.db.entries[S.sel][1]')=='090121';assert page.evaluate('V.apiKey')=='';assert page.evaluate('JSON.stringify(S.notes)')=='{}';assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert page.evaluate('navigator.serviceWorker.getRegistrations().then(x=>x.length)')==0
   page.screenshot(path=str(out/f'candidate-{width}.png'),full_page=True);page.screenshot(path=str(out/f'viewport-{width}.png'));assert not errors,errors;assert all(u.startswith(origin+'/candidate.html')for u in requests),requests;results.append({'width':width,'exactCoffeeSelected':True,'keysEmpty':True,'notesEmpty':True,'noNetwork':True,'noWorker':True,'errors':errors});context.close()
  browser.close()
finally:server.shutdown()
(out/'report.json').write_text(json.dumps(results,indent=2));print(results)
