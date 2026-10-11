"""Local served-copy Chrome proof, no production navigation or external request."""
import json
import sys
import threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration.news_api import create_app
from integration.finder_identity_proof_prep import FinderProof,EDITIONS,normalized_description
from integration.code_news_disk import DiskLinks
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
app=create_app(authorize=lambda r:True)
server=make_server('127.0.0.1',8791,app)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
proof=FinderProof();index=DiskLinks(root/'integration/code_news_index');results=[]
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
  context=browser.new_context(viewport={'width':390,'height':844});page=context.new_page();requests=[];errors=[]
  page.on('request',lambda r:requests.append(r.url));page.on('pageerror',lambda e:errors.append(str(e)))
  for system,si in [('HS',0),('IN',1)]:
   for code in ('090121','1006'):
    assert proof.bound(system,EDITIONS[system],code)
    url=f'http://127.0.0.1:8791/workspace/finder/offline.html#code={si}:{code}'
    page.goto(url);page.wait_for_function('typeof S!=="undefined" && S.db && S.sel!==null',timeout=40000)
    selected=page.evaluate('S.db.entries[S.sel]')
    assert selected[0]==si and selected[1]==code,selected
    resolved=index.resolve(code,system,EDITIONS[system]);assert resolved['state']=='resolved'
    assert normalized_description(selected[2])==normalized_description(resolved['items'][0]['description'])
    assert page.locator('#d-fav').count()==1
    assert page.evaluate('V.apiKey')=='' and page.evaluate('JSON.stringify(S.notes)')=='{}'
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    results.append({'system':system,'code':code,'selected_row':selected[:3],'fragment':page.url.split('#')[1]})
    if code=='090121':page.screenshot(path=f'/downloads/e1a1-{system}-mobile.png')
    page.evaluate('location.hash="#code='+str(si)+':000000"')
    page.wait_for_function('S.sel===null && S.cmpA===null && !S.showList')
    assert page.locator('#d-fav').count()==0
    # Return to a valid row, then unknown system: never fallback to HS or IN.
    page.evaluate('location.hash="#code='+str(si)+':'+code+'"');page.wait_for_function('S.sel!==null')
    page.evaluate('location.hash="#code=99:'+code+'"');page.wait_for_function('S.sel===null')
  context.close();context=browser.new_context(viewport={'width':1100,'height':850});page=context.new_page()
  page.goto('http://127.0.0.1:8791/workspace/finder/offline.html#code=0:090121')
  page.locator('#d-fav').wait_for(timeout=40000);page.screenshot(path='/downloads/e1a1-HS-desktop.png')
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  assert all(url.startswith('http://127.0.0.1:8791/workspace/finder/offline.html')for url in requests),requests
  assert not errors,errors
  browser.close()
 print(json.dumps({'browser':'headless Chrome','source':'local actually served offline copy','results':results,'unknown_code_and_system_no_fallback':True,'external_requests':0,'pageerrors':errors},indent=2))
finally:
 proof.close();index.close();server.shutdown();thread.join()
