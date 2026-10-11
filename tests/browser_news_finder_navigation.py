import json,sys,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration.news_api import create_app
from integration.code_news_coverage_ui_prep import install
from integration.news_finder_navigation_prep import FLAG,LABELS
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
app=create_app(authorize=lambda r:True);install(app,{'PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED':'true',FLAG:'true'},coverage_available=True)
server=make_server('127.0.0.1',8793,app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
target={'system':'HS','edition':'2022','code':'090121','description':'Coffee'}
reply={'state':'complete_mutable_read','items':[],'scan_complete':True,'evidence_complete':False,'evidence_scope':'bounded_explicit_mentions_only_not_all_commodity_news','coverage_gap':False,'articles_checked':0,'articles_refused_mentions_limit':0,'articles_unreadable':0,'articles_checked_this_page':0,'articles_refused_this_page':0,'articles_unreadable_this_page':0,'rows_consumed_this_page':0,'parent_pages':1,'public_rows_received':0,'total_count':None,'coverage_message':'No gaps recorded','consistency':'mutable_read_not_snapshot','scope':None,'next_cursor':None,'manifest':'a'*64,'matcher_version':'v1'}
report=[]
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
  for width in (390,1100):
   page=b.new_page(viewport={'width':width,'height':950});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   mode={'value':'ready'};requests=[]
   def route(r):
    requests.append(r.request.post_data)
    if mode['value']=='error':r.fulfill(status=503,content_type='application/json',body='{}');return
    data=dict(reply);state=mode['value'];t=dict(target)
    if state=='wrongtarget':t['code']='1006'
    data['finder_navigation']={'state':'ready'if state in ('ready','wrongtarget')else'unavailable','target':{k:t[k]for k in ('system','edition','code')},'url':'/workspace/finder/offline.html#code=0:'+t['code']if state in ('ready','wrongtarget')else None,'label':LABELS['HS']if state in ('ready','wrongtarget')else'Finder link unavailable','edition_verified':False}
    r.fulfill(status=200,content_type='application/json',body=json.dumps(data))
   page.route('**/api/code-news-coverage',route)
   page.goto('http://127.0.0.1:8793/workspace/code-news-coverage');page.wait_for_timeout(150);assert not requests
   for k in ('system','edition','code'):page.locator('#'+k).fill(target[k])
   for state in ('ready','unavailable','error','wrongtarget'):
    mode['value']=state;page.locator('#start').click();page.wait_for_timeout(150)
    count=page.locator('#finder-navigation a').count();assert count==(1 if state=='ready'else 0),(state,count)
    if state=='ready':
     assert page.locator('#finder-navigation a').get_attribute('rel')=='noreferrer'
     assert page.locator('#finder-navigation a').get_attribute('referrerpolicy')=='no-referrer'
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    if state!='wrongtarget':page.screenshot(path=f'/downloads/e1a2-{state}-{width}.png',full_page=True)
    report.append({'width':width,'state':state,'link_count':count})
   mode['value']='ready';page.locator('#start').click();page.wait_for_timeout(100);page.locator('#code').fill('1006');assert page.locator('#finder-navigation a').count()==0
   page.locator('#code').fill('090121');page.locator('#start').click();page.wait_for_timeout(100)
   page.evaluate('window.dispatchEvent(new PageTransitionEvent("pageshow",{persisted:true}))');assert page.locator('#finder-navigation a').count()==0
   page.locator('#start').click();page.wait_for_timeout(100)
   page.evaluate('Object.defineProperty(document,"hidden",{configurable:true,value:true});document.dispatchEvent(new Event("visibilitychange"))');assert page.locator('#finder-navigation a').count()==0
   assert not errors,errors;page.close()
  b.close()
 print(json.dumps(report,indent=2))
finally:server.shutdown();thread.join()
