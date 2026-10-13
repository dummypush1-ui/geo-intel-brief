"""Real Chrome mutant tests on the served JS module, no pin bypass claim."""
import sys,json,threading
from pathlib import Path
import os,tempfile
EVIDENCE=Path(os.environ.get('RELATIONSHIP_EVIDENCE_DIR') or tempfile.mkdtemp(prefix='relationship-evidence-'));EVIDENCE.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server
from integration.news_api import create_app
from integration.code_news_public import install as code_install
from integration.news_finder_navigation_prep import install_mount
from integration.relationship_navigation import install
from integration.code_news_links import Links
origin='http://127.0.0.1:8812';raw={'geo':[dict(url='https://example.com/one',title='HS 100630 reported',summary='Rice')]}
app=create_app(reader=lambda:raw,authorize=lambda _:True,allowed_origin=origin)
install_mount(app);code_install(app,origin,lambda:raw);app.extensions['code_news_public'].model=Links([dict(system='HS',edition='2022',code='100630',description='Rice')],[]);install(app,origin)
server=make_server('127.0.0.1',8812,app,threaded=True);threading.Thread(target=server.serve_forever,daemon=True).start()
source=(Path(__file__).resolve().parents[1]/'integration/ui/relationship_navigation.js').read_text()
cases=[('bytes','size>MAX_BYTES','size>MAX_BYTES+1000000','large','Response too large'),('type',"if(!/^application\\/json(?:\\s*;|$)/i.test(r.headers.get('content-type')||''))",'if(false)','badtype','Invalid response type'),('identity','!identity.test(t.code)','false','badcode','Invalid identity'),('codetype','!plain(t.code,12)','false','numericcode','Invalid identity'),('articlekey',"if(r.article_key!==a.article_key)",'if(false)','wrongarticle','Article identity changed'),('exactkeys',"keys(v,['state','items','scope','not_exhaustive','vocabulary_state','no_matches_not_no_related_news'])",'true','extra','Invalid relationship response')]
results=[]
try:
 with sync_playwright()as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
  for name,old,new,attack,expected in cases:
   assert source.count(old)==1,(name,source.count(old))
   outcomes=[]
   for mutated in [False,True]:
    app.extensions['code_news_public'].calls=0
    page=b.new_page(viewport={'width':390,'height':900});page.set_default_timeout(3000)
    def route(r):
     u=r.request.url
     if not u.startswith(origin):r.abort();return
     if '/relationship_navigation.js' in u:r.fulfill(content_type='application/javascript',body=source.replace(old,new)if mutated else source);return
     if '/api/news-code-context' in u:
      key=u.split('article_key=')[1];v=app.test_client().get('/api/news-code-context?project=geo&article_key='+key,base_url=origin).json
      if attack=='numericcode':v['items'][0]['targets'][0]['code']=100630
      if attack=='wrongarticle':v['items'][0]['article_key']='a'*64
      if attack=='badcode':v['items'][0]['targets'][0]['code']='../100630'
      if attack=='extra':v['extra']='attack'
      body=(' '*250001 if attack=='large'else'')+json.dumps(v)
      r.fulfill(content_type='text/html'if attack=='badtype'else'application/json',body=body);return
     if '/workspace/finder/' in u:r.fulfill(content_type='text/html',body='<html><body>Fixture</body></html>');return
     r.continue_()
    page.route('**/*',route);page.goto(origin+'/workspace');page.locator('[data-view=geo]').click();page.get_by_role('button',name='Check reported codes').first.click()
    page.wait_for_function("[...document.querySelectorAll('#news-results .story button')].some(b=>b.textContent==='Check reported codes'&&!b.disabled)")
    rejected=expected in page.locator('#news-results .story').first.inner_text();outcomes.append(rejected);page.close()
   assert outcomes==[True,False],(name,outcomes)
   results.append(dict(mutant=name,original_rejects=True,mutant_wrongly_accepts=True,killed=True))
  b.close()
finally:server.shutdown()
(EVIDENCE/'mutants.json').write_text(json.dumps(results,indent=2));print(results)
