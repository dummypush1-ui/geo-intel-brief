"""Real Chrome gates with local fixture JSON, never real providers/DB."""
import sys,threading,json,copy
from pathlib import Path
import os,tempfile
EVIDENCE=Path(os.environ.get('RELATIONSHIP_EVIDENCE_DIR') or tempfile.mkdtemp(prefix='relationship-evidence-'));EVIDENCE.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from flask import request
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
from integration.news_api import create_app
from integration.news_finder_navigation_prep import install_mount
from integration.code_news_public import install as code_install
from integration.code_news_links import Links
from integration.relationship_navigation import install
OUT=EVIDENCE;OUT.mkdir(exist_ok=True)
origin='http://127.0.0.1:8811'
raw={'geo':[dict(url='https://example.com/one',title='HS 100630 '+('Long supplied story '*20),summary='Rice reported')]}
app=create_app(reader=lambda:raw,authorize=lambda _:True,allowed_origin=origin)
@app.after_request
def shell(r):
 if request.path=='/workspace':
  r.direct_passthrough=False;r.set_data(r.get_data(as_text=True).replace('src="/workspace/finder/index.html"','src="/workspace/finder/offline.html"'))
 return r
install_mount(app);code_install(app,origin,lambda:raw);app.extensions['code_news_public'].model=Links([dict(system='HS',edition='2022',code='100630',description='Rice')],[]);install(app,origin)
server=make_server('127.0.0.1',8811,app,threaded=True);threading.Thread(target=server.serve_forever,daemon=True).start()
report=[]
framehtml='<html><body><div class="detail-head"><span class="sys-tag">HS</span></div><span class="detail-code">100630</span><span class="detail-desc">Rice</span><input id="q-main"></body></html>'
try:
 with sync_playwright()as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
  for width in [390,1100]:
   # Separate viewport cases use separate fixture quota windows, never alter production limits.
   app.extensions['code_news_public'].calls=0
   page=b.new_page(viewport={'width':width,'height':950});page.set_default_timeout(4000);errors=[];calls=[];page.on('pageerror',lambda e:errors.append(str(e)))
   mode={'value':'real'}
   def route(r):
    u=r.request.url;calls.append((u,r.request.method))
    if not u.startswith(origin):r.abort();return
    if '/workspace/finder/offline.html' in u:r.fulfill(content_type='text/html',body=framehtml);return
    if '/api/code-news-context' in u and mode['value'] in ('javascript','missingforward','wrongquery','wronglink','numericforward','partial'):
     v=app.test_client().get('/api/code-news-context?query=100630&system=HS&edition=2022',base_url=origin).json
     if mode['value']=='javascript':v['relationships'][0]['article']['url']='javascript:alert(1)'
     if mode['value']=='missingforward':del v['relationships'][0]['article']['source']
     if mode['value']=='wrongquery':v['relationships'][0]['query_code']['code']='1006'
     if mode['value']=='wronglink':v['relationships'][0]['article']['article_key']='a'*64
     if mode['value']=='numericforward':v['items'][0]['code']=100630
     if mode['value']=='partial':
      v['relationships'].append(copy.deepcopy(v['relationships'][0]));v['relationships'][1]['article']['url']='javascript:alert(1)'
     r.fulfill(json=v);return
    if '/api/news-code-context' in u:
     if mode['value']=='slow':
      import time;time.sleep(.4);r.continue_();return
     if mode['value']=='old':r.fulfill(status=404,json={'state':'article_unavailable_in_supplied_page'});return
     if mode['value']=='quota':r.fulfill(status=429,json={'state':'rate_limited'});return
     if mode['value']=='badtype':r.fulfill(content_type='text/html',body='{}');return
     if mode['value']=='large':r.fulfill(content_type='application/json',body=' '*250001+'{}');return
     if mode['value'] in ('titleattack','urlattack','evidenceattack'):
      v=app.test_client().get('/api/news-code-context?project=geo&article_key='+u.split('article_key=')[1],base_url=origin).json
      if mode['value']=='evidenceattack':v['items'][0]['evidence']='<script>window.__xss=1</script>'
      elif mode['value']=='titleattack':v['items'][0]['targets'][0]['description']='<img src=x onerror=window.__xss=1>'
      else:v['items'][0]['targets'][0]['code']='../100630'
      r.fulfill(json=v);return
     if mode['value'] in ('missing','wrongarticle'):
      v=app.test_client().get('/api/news-code-context?project=geo&article_key='+u.split('article_key=')[1],base_url=origin).json
      if mode['value']=='missing':del v['scope']
      else:v['items'][0]['article_key']='a'*64
      r.fulfill(json=v);return
     if mode['value']=='extra':
      v=app.test_client().get('/api/news-code-context?project=geo&article_key='+u.split('article_key=')[1],base_url=origin).json;v['extra']='attack';r.fulfill(json=v);return
    r.continue_()
   page.route('**/*',route);page.goto(origin+'/workspace');page.locator('[data-view=geo]').click();page.get_by_role('button',name='Check reported codes').first.wait_for()
   before=len([x for x in calls if '/api/news-code-context' in x[0] or '/api/code-news-context' in x[0]])
   page.get_by_role('button',name='Check reported codes').first.click();page.locator('#news-results').get_by_text('Reported code mention, not verified classification: HS 100630',exact=True).first.wait_for()
   for state,text in [('old','This story is unavailable'),('quota','Shared relationship limit'),('badtype','Invalid response type'),('large','Response too large'),('extra','Invalid relationship response'),('missing','Invalid relationship response'),('wrongarticle','Article identity changed')]:
    mode['value']=state;page.get_by_role('button',name='Check reported codes').first.click();page.locator('#news-results .story').first.locator('p').filter(has_text=text).wait_for();assert page.locator('#news-results .story').first.get_by_text('Reported code mention, not verified classification: HS 100630',exact=True).count()==0;count=len([x for x in calls if '/api/news-code-context' in x[0]]);page.wait_for_timeout(150);assert len([x for x in calls if '/api/news-code-context' in x[0]])==count
   mode['value']='slow'
   page.get_by_role('button',name='Check reported codes').first.click(no_wait_after=True)
   page.locator('[data-view=finder]').click()
   page.wait_for_timeout(550)
   assert page.locator('#news-results').get_by_text('Reported code mention, not verified classification: HS 100630',exact=True).count()==0
   page.locator('[data-view=geo]').click();page.get_by_role('button',name='Check reported codes').first.wait_for()
   mode['value']='titleattack';page.get_by_role('button',name='Check reported codes').first.click();page.locator('#news-results').get_by_text('HS 100630 | 2022 | <img src=x onerror=window.__xss=1>',exact=True).wait_for();assert page.locator('#news-results img').count()==0
   mode['value']='evidenceattack';page.get_by_role('button',name='Check reported codes').first.click();page.locator('#news-results').get_by_text('Reported code mention, not verified classification: <script>window.__xss=1</script>',exact=True).wait_for();assert page.locator('#news-results script').count()==0
   mode['value']='urlattack';page.get_by_role('button',name='Check reported codes').first.click();page.locator('#news-results .story').first.locator('p').filter(has_text='Invalid identity').wait_for()
   mode['value']='old';page.get_by_role('button',name='Check reported codes').first.click();page.locator('#news-results .story').first.locator('p').filter(has_text='This story is unavailable').wait_for();page.screenshot(path=str(OUT/f'old-row-{width}.png'),full_page=True)
   page.locator('[data-view=finder]').click();page.evaluate("document.querySelector('#finder').contentWindow.location.hash='code=0:100630'")
   page.wait_for_timeout(150);page.get_by_role('button',name='Check supplied-page news').wait_for();n=len([x for x in calls if '/api/code-news-context' in x[0]])
   for source,send_origin,data in [('wrong',origin,{}),('owned','https://evil.test',{'code':'100630'}),('owned',origin,{'code':'100630','extra':True})]:
    page.evaluate("([s,o,d])=>window.dispatchEvent(new MessageEvent('message',{source:s==='owned'?document.querySelector('#finder').contentWindow:window,origin:o,data:d}))",[source,send_origin,data])
   assert len([x for x in calls if '/api/code-news-context' in x[0]])==n
   page.get_by_role('button',name='Check supplied-page news').click();page.get_by_text('Latest-100 reported mentions. Not full-store or meaning-based search.',exact=True).wait_for();assert page.locator('#related a').count()==1
   page.screenshot(path=str(OUT/f'finder-related-{width}.png'),full_page=True)
   for attack,text in [('javascript','Invalid URL'),('missingforward','Invalid article'),('wrongquery','Relationship identity changed'),('wronglink','Relationship identity changed'),('numericforward','Invalid identity'),('partial','Invalid URL')]:
    # Fixture response retrieval is isolated from production quota; actual429 tested above.
    app.extensions['code_news_public'].calls=0
    mode['value']=attack;page.get_by_role('button',name='Check supplied-page news').click();page.get_by_text(text,exact=True).wait_for();assert page.locator('#related a').count()==0
   mode['value']='real'
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   assert not any('/api/related-news' in u or '/api/finder-context' in u for u,m in calls)
   assert not errors,errors
   report.append(dict(width=width,manual_only=True,old_story_unavailable=True,quota_no_retry=True,wrong_message_no_effect=True,forward_reverse=True,strict_type_bytes_keys=True,no_private_post=True));page.close()
  b.close()
finally:server.shutdown()
(OUT/'browser.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
