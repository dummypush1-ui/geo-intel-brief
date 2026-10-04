import sys,threading,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration.news_api import create_app
from integration.tariff_evidence import TariffEvidenceSnapshot
from integration.finder_index import FinderIndex
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
row={'id':'fixture-1','jurisdiction':'IN','nomenclature':'HSN','edition':'Fixture only','codes':['21069051'],'document_id':'Fixture notification <img src=x>','source_url':'https://www.indiabudget.gov.in/doc/cen/cus0326.pdf','published_date':'2026-02-01','effective_dates':['2026-04-01','2026-05-01'],'excerpt':'<script>bad</script> Fixture text, not a live tariff claim.','conditions':'Fixture only, legal scope not interpreted','review_state':'candidate','reviewed_at':None}
snap=TariffEvidenceSnapshot('2026-10-04T00:00:00Z',[row]);index=FinderIndex([[0,'21069051','Fixture code',None,None,None]],[{'tag':'IN','name':'India'}])
news={'geo':[{'title':'Fixture HSN21069051 news','url':'https://example.com/a','country':'India'}],'brics':[]}
app=create_app(authorize=lambda r:True,tariff_evidence_snapshot=snap,reader=lambda:news,finder_context_reader=index.for_article,finder_base='http://127.0.0.1:8773/workspace/finder/index.html',finder_index_verified=True)
server=make_server('127.0.0.1',8773,app);threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':980});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.route('**/*',lambda r:r.continue_() if r.request.url.startswith('http://127.0.0.1:8773/') else r.abort())
 page.goto('http://127.0.0.1:8773/workspace/tariffs');page.get_by_text('Fixture notification <img src=x>',exact=True).wait_for();assert page.locator('#tariff-items img,#tariff-items script').count()==0;assert '2026-04-01, 2026-05-01' in page.locator('#tariff-items').inner_text();assert 'Candidate - not reviewed' in page.locator('#tariff-items').inner_text();page.screenshot(path='/downloads/tariff-evidence-desktop.png',full_page=True);page.set_viewport_size({'width':390,'height':844});page.screenshot(path='/downloads/tariff-evidence-mobile.png',full_page=True);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.locator('#tariff-jurisdiction').select_option('US');page.get_by_role('button',name='Load evidence',exact=True).click();page.get_by_text('No supplied records for this jurisdiction. This does not mean no tariff changes.',exact=True).wait_for()
 page.route('**/api/tariff-evidence?*',lambda r:r.fulfill(status=503,json={'error':'unavailable'}));page.get_by_role('button',name='Load evidence',exact=True).click();page.get_by_text('Tariff evidence unavailable. Coverage cannot be checked.',exact=True).wait_for()
 page.route('**/api/tariff-evidence?*',lambda r:r.fulfill(json={'state':'tariff_evidence_unwired','items':[]}));page.get_by_role('button',name='Load evidence',exact=True).click();page.get_by_text('Official evidence reader is not connected. No tariff-change coverage can be claimed.',exact=True).wait_for()
 page.goto('http://127.0.0.1:8773/workspace/countries');page.locator('#country-label').fill('India');page.get_by_role('button',name='Load country',exact=True).click();page.get_by_role('button',name='Find matching trade codes').click();page.get_by_text('Explicit HS/HSN mention: 21069051',exact=True).wait_for();assert page.locator('.finder-matches a').get_attribute('href').endswith('#code=0:21069051');assert not errors;print(json.dumps({'errors':errors,'dates_separate':True,'candidate_visible':True,'xss_literal':True,'coverage_states_distinct':True,'explicit_code_reason':True,'mobile_no_overflow':True}));b.close()
server.shutdown()
