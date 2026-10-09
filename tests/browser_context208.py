"""Local actual merged workspace/Finder with intercepted responses, no live reads."""
import sys,threading,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration.news_api import create_app
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
app=create_app(reader=lambda:{'geo':[],'brics':[]},authorize=lambda req:True)
server=make_server('127.0.0.1',0,app,threaded=True);threading.Thread(target=server.serve_forever,daemon=True).start();origin='http://127.0.0.1:'+str(server.server_port)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome-stable',headless=True,args=['--no-sandbox'])
 results=[]
 for width in (390,1280):
  page=b.new_page(viewport={'width':width,'height':900});calls=[];external=[];errors=[];mode=['ok'];held=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  def route(r):
   if not r.request.url.startswith(origin+'/'):external.append(r.request.url);return r.abort()
   if r.request.url.endswith('/api/related-news'):
    calls.append(r.request.post_data_json)
    if mode[0]=='held':held.append(r);return
    if mode[0]=='error':return r.fulfill(status=400,json={'error':'Invalid read context'})
   r.continue_()
  page.route('**/*',route);page.goto(origin+'/workspace');page.locator('[data-view="finder"]').click()
  frame=page.frame_locator('#finder');frame.locator('.detail-desc').wait_for(timeout=30000) if False else None
  page.locator('#finder').evaluate('(e)=>e.src=e.src.split("#")[0]+"#code=0:010619"')
  frame.locator('.detail-desc').wait_for(timeout=30000)
  page.locator('#related-excerpt-note:not([hidden])').wait_for()
  page.wait_for_function('() => document.querySelector("#related-status").textContent.startsWith("No matching stories")')
  full=frame.locator('.detail-desc').text_content();assert len(full)==252
  payload=calls[-1];assert payload=={'code':'010619','system':'HS','country':'','product_terms':[full[:200]]},payload
  page.locator('#related-excerpt-detail summary').focus();page.keyboard.press('Enter');assert page.locator('#related-excerpt-detail').get_attribute('open') is not None
  assert page.locator('#related-excerpt-text').text_content()==full[:200]
  assert frame.locator('.detail-desc').text_content()==full
  page.locator('#related-excerpt-detail').scroll_into_view_if_needed();page.screenshot(path=f'/downloads/context208-{width}.png',full_page=True)
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  # Prefix remains plain text, unbroken wrap, rejected controls are not repaired.
  finder=page.frames[1]
  finder.evaluate('text=>document.querySelector(".detail-desc").textContent=text','<script>'+('x'*240)+'&lt;')
  page.wait_for_function('() => document.querySelector("#related-excerpt-text").textContent.startsWith("<script>")');assert page.locator('#related-excerpt-text script').count()==0
  finder.evaluate('text=>document.querySelector(".detail-desc").textContent=text','x'*240)
  page.wait_for_function('() => document.querySelector("#related-excerpt-text").textContent==="x".repeat(200)');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  finder.evaluate('text=>document.querySelector(".detail-desc").textContent=text','DEL\x7f'+'x'*220)
  page.wait_for_function('() => document.querySelector("#related-status").textContent.includes("News is unavailable")');assert calls[-1]['product_terms'][0].startswith('DEL\x7f');assert page.locator('#related-excerpt-note').is_visible()
  # Error resets signature: unchanged DOM can be retried, no automatic retry loop.
  count=len(calls);finder.evaluate('document.body.appendChild(document.createElement("span"))')
  page.wait_for_function('() => document.querySelector("#related-status").textContent.includes("News is unavailable")');page.wait_for_timeout(100);assert len(calls)>count
  finder.evaluate('text=>document.querySelector(".detail-desc").textContent=text','a\ud800'+'x'*220)
  page.wait_for_function('() => document.querySelector("#related-status").textContent.includes("News is unavailable")');page.wait_for_timeout(100)
  assert '\ud800' in calls[-1]['product_terms'][0]
  finder.evaluate('document.querySelector(".detail-desc").textContent="😀".repeat(150)')
  page.wait_for_function('() => document.querySelector("#related-excerpt-note").hidden');page.wait_for_function('() => document.querySelector("#related-status").textContent.startsWith("No matching stories")')
  assert len(calls[-1]['product_terms'][0])==150
  # Short -> long -> short stale reply order, then long replay.
  mode[0]='held';finder.evaluate('document.querySelector(".detail-desc").textContent="l".repeat(240)');page.wait_for_timeout(100);assert held
  longroute=held.pop();mode[0]='ok';finder.evaluate('document.querySelector(".detail-desc").textContent="short description"')
  page.wait_for_function('() => document.querySelector("#related-excerpt-note").hidden');page.wait_for_function('() => document.querySelector("#related-status").textContent.startsWith("No matching stories")')
  longroute.fulfill(status=400,json={'error':'stale synthetic error'});page.wait_for_timeout(100);assert page.locator('#related-status').text_content().startswith('No matching stories')
  finder.evaluate('document.querySelector(".detail-desc").textContent="l".repeat(240)');page.locator('#related-excerpt-note:not([hidden])').wait_for();page.wait_for_function('() => document.querySelector("#related-status").textContent.startsWith("No matching stories")')
  # Actual short Finder code clears both parent notice and excerpt.
  finder.evaluate('location.hash="#code=0:090121"');page.wait_for_function('() => document.querySelector("#related-excerpt-note").hidden');assert page.locator('#related-excerpt-text').text_content()==''
  assert not external and not errors,(external,errors)
  results.append({'width':width,'actual_long_description_length':len(full),'one_term_200':True,'full_detail_preserved':True,'plain_text_notice':True,'stale_response_ignored':True,'external_requests':external,'page_errors':errors});page.close()
 b.close();print(json.dumps(results))
server.shutdown()
