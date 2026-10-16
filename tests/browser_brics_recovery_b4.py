"""Local intercepted iframe playback events. No provider availability claim."""
import json,sys,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration.public_preview_builder import build_public_preview
from integration import brics_recovery_b4 as m,public_brics_streams as base
from tests.test_code_news_coverage_binding_prep import SAMPLE
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
app=build_public_preview(dict(SAMPLE,**{base.FLAG:'true',m.FLAG:'true'}));old=app.wsgi_app
def proxy(env,start):env['HTTP_HOST']='example.test';env['wsgi.url_scheme']='https';return old(env,start)
app.wsgi_app=proxy;server=make_server('127.0.0.1',8846,app,threaded=True);threading.Thread(target=server.serve_forever,daemon=True).start();origin='http://127.0.0.1:8846';reports=[]
try:
 with sync_playwright()as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
  for width in (320,390,1100):
   context=browser.new_context(viewport={'width':width,'height':950});page=context.new_page();errors=[];loads=[];outside=[];writes=[];page.on('pageerror',lambda e:errors.append(str(e)))
   def route(r):
    u=r.request.url
    if r.request.method not in ('GET','HEAD'):writes.append(u)
    if u.startswith(m.base.ROOT.as_uri()):raise AssertionError('filesystem URL')
    if u.startswith('https://www.youtube-nocookie.com/embed/'):
     loads.append(u);r.fulfill(content_type='text/html',body='''<!doctype html><body style="margin:0;background:#182c40;color:white;font:16px sans-serif;display:grid;place-items:center;height:100vh">OFFLINE PROVIDER FIXTURE<br>Playback unverified<script>window.handshakes=[];addEventListener('message',e=>{try{if(JSON.parse(e.data).event==='listening')window.handshakes.push(JSON.parse(e.data));}catch{}});</script>''')
    elif u.startswith(origin+'/'):r.continue_()
    else:outside.append(u);r.abort()
   page.route('**/*',route);page.goto(origin+base.PAGE);page.wait_for_function('()=>document.querySelectorAll("iframe").length===6');page.wait_for_function('()=>Array.from(document.querySelectorAll("iframe")).every(f=>f.src.includes("enablejsapi=1&origin="))')
   def emit(selector,body):
    handle=page.locator(selector).element_handle().content_frame();handle.evaluate('(body)=>parent.postMessage(JSON.stringify(body),"*")',body)
   page.locator('iframe').first.wait_for();page.wait_for_timeout(150)
   assert all('enablejsapi=1' in url for url in loads)
   for element in page.locator('iframe').element_handles():
    observed=element.content_frame().evaluate('window.handshakes');assert len(observed)==1 and observed[0]['id']==element.get_attribute('id')
   # Wrong origin, wrong source, malformed, oversized and non-ended state do not act.
   page.evaluate('''()=>{const f=document.querySelector('#selected iframe');for(const e of [new MessageEvent('message',{origin:'https://evil.test',source:f.contentWindow,data:'{"event":"onStateChange","info":0}'}),new MessageEvent('message',{origin:'https://www.youtube-nocookie.com',source:window,data:'{"event":"onStateChange","info":0}'})])dispatchEvent(e);}''')
   for body in ({'event':'onStateChange','info':1},{'event':'onError','info':'100'}):emit('#selected iframe',body)
   assert page.locator('.player-recovery').count()==0
   # A real cross-origin fixture iframe is the sender. Only selected frame fails.
   before=len(loads);page.locator('#wall iframe').evaluate_all('(fs)=>fs.forEach((f,i)=>f.dataset.keep="mini"+i)');emit('#selected iframe',{'event':'infoDelivery','info':{'playerState':0}});page.locator('#selected .player-recovery').wait_for();assert page.locator('iframe').count()==5;assert len(loads)==before;assert page.locator('#wall iframe').evaluate_all('(fs)=>fs.every((f,i)=>f.dataset.keep==="mini"+i)')
   page.screenshot(path=str(out/f'ended-selected-{width}.png'));page.get_by_role('button',name='Add a new feed',exact=True).click();assert page.locator('#name').evaluate('(e)=>document.activeElement===e');page.get_by_role('button',name='Retry selected player',exact=True).click();page.wait_for_function('()=>document.querySelectorAll("iframe").length===6');assert len(loads)==before+1
   # Mini error held through unrelated list repaint; manual retry only one frame.
   emit('#wall article:nth-child(2) iframe',{'event':'onError','info':150});page.locator('#wall article:nth-child(2) .player-recovery').wait_for();before=len(loads)
   page.locator('#name').fill('<script>literal</script>');page.locator('#link').fill('abcdefghijk');page.get_by_role('button',name='Add extra channel',exact=True).evaluate('(e)=>e.click()');page.wait_for_function('()=>document.querySelectorAll("#wall article").length===6');assert len(loads)==before;assert page.locator('#wall article:nth-child(2) iframe').count()==0
   page.screenshot(path=str(out/f'error-mini-{width}.png'),full_page=True);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   page.get_by_role('button',name='Retry mini player',exact=True).scroll_into_view_if_needed();page.wait_for_timeout(150);page.locator('#wall article:nth-child(2)').screenshot(path=str(out/f'mini-panel-{width}.png'));page.get_by_role('button',name='Retry mini player',exact=True).click();page.wait_for_function('()=>document.querySelectorAll("iframe").length===6');assert len(loads)==before+1
   # Stopped players cannot be restarted by a delayed/stale event or old retry.
   emit('#selected iframe',{'event':'onStateChange','info':0});page.locator('#selected .player-recovery').wait_for();retry=page.get_by_role('button',name='Retry selected player',exact=True).element_handle();page.get_by_role('button',name='Stop players',exact=True).click();assert page.locator('iframe').count()==0;before=len(loads);retry.evaluate('(button)=>button.click()');assert page.locator('iframe').count()==0 and len(loads)==before
   page.get_by_role('button',name='Start default players',exact=True).click();page.wait_for_function('()=>document.querySelectorAll("iframe").length===6');assert page.locator('.player-recovery').count()==0
   # Selection replaces only hero, stale held controls cannot replace new hero.
   emit('#selected iframe',{'event':'onError','info':100});page.locator('#selected .player-recovery').wait_for();retry=page.get_by_role('button',name='Retry selected player',exact=True).element_handle();page.get_by_role('button',name='Select DW News',exact=True).click();page.wait_for_function('()=>document.querySelector("#selected h2").textContent==="DW News"');before=len(loads);retry.evaluate('(button)=>button.click()');assert page.locator('#selected h2').text_content()=='DW News'and len(loads)==before
   page.evaluate("dispatchEvent(new PageTransitionEvent('pagehide'))");emit('#selected iframe',{'event':'onStateChange','info':0});page.wait_for_timeout(50);assert page.locator('.player-recovery').count()==0
   page.evaluate("dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}))");emit('#selected iframe',{'event':'onStateChange','info':0});page.locator('#selected .player-recovery').wait_for();assert page.locator('.player-recovery').count()==1
   assert not errors,errors;assert not outside,outside;assert not writes,writes
   reports.append({'width':width,'wrong_origin_source_refused':True,'selected_only_retry':True,'mini_only_retry':True,'unrelated_render_no_retry':True,'stale_retry_after_stop_or_select_refused':True,'overflow':False,'errors':errors,'provider_playback_verified':False});context.close()
  browser.close()
finally:server.shutdown()
(out/'report.json').write_text(json.dumps(reports,indent=2));print(json.dumps(reports,indent=2))
