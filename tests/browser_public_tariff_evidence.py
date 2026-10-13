"""Chrome fixture-only passive page, no official document fetch."""
import sys,json,tempfile,os,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
from urllib.parse import urlsplit
from datetime import datetime,timezone
from integration.public_preview_builder import build_public_preview
from integration.tariff_evidence import TariffEvidenceSnapshot
from integration import public_tariff_evidence as t
from tests.test_code_news_public import env
OUT=Path(os.environ.get('TARIFF_EVIDENCE_DIR')or tempfile.mkdtemp(prefix='tariff-evidence-'));OUT.mkdir(exist_ok=True)
origin='https://preview.example';app=build_public_preview(dict(env(),PUBLIC_TARIFF_EVIDENCE_ENABLED='true'))
row=dict(id='fixture',jurisdiction='IN',nomenclature='HSN',edition='fixture',codes=['100630'],document_id='Fixture <script>bad</script>',source_url='https://www.indiabudget.gov.in/doc/cen/cus0326.pdf',published_date='2026-02-01',effective_dates=['2026-04-01'],excerpt='<img src=x onerror=window.__xss=1>',conditions='Fixture only; legal scope not inferred',review_state='candidate',reviewed_at=None)
fixture=t.Service(TariffEvidenceSnapshot('2026-10-04T00:00:00Z',[row]),now=lambda:datetime(2026,10,13,tzinfo=timezone.utc)).run('')[0]
source=(Path(__file__).resolve().parents[1]/'integration/ui/public_tariff_evidence.js').read_text();results=[]
with sync_playwright()as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
 for width in [390,1100]:
  p=b.new_page(viewport={'width':width,'height':950});p.set_default_timeout(5000);calls=[];errors=[];mode={'value':'real'};p.on('pageerror',lambda e:errors.append(str(e)))
  def route(r):
   calls.append(r.request.url)
   if not r.request.url.startswith(origin):r.abort();return
   if t.API in r.request.url and mode['value']!='real':
    v=copy.deepcopy(fixture)
    if mode['value']=='quota':r.fulfill(status=429,json={'state':'rate_limited'});return
    if mode['value']=='type':r.fulfill(content_type='text/html',body='{}');return
    if mode['value']=='large':r.fulfill(content_type='application/json',body=' '*250001+'{}');return
    if mode['value']=='source':v['items'][0]['source_url']='javascript:alert(1)'
    if mode['value']=='date':v['items'][0]['published_date']='2026-02-30'
    if mode['value']=='extra':v['items'][0]['private']='secret'
    if mode['value']=='review':v['current_rates_verified']=True
    r.fulfill(json=v);return
   u=urlsplit(r.request.url);res=app.test_client().open(u.path+('?' +u.query if u.query else ''),method=r.request.method,base_url=origin,data=r.request.post_data,headers=r.request.headers)
   r.fulfill(status=res.status_code,headers=dict(res.headers),body=res.data)
  p.route('**/*',route);p.goto(origin+t.PAGE);assert len([u for u in calls if t.API in u])==0
  p.get_by_role('button',name='Check supplied evidence').click();p.get_by_text(t.NOT_CONNECTED,exact=True).wait_for();assert p.locator('#tariff-items').inner_text()==''
  mode['value']='fixture';p.get_by_role('button',name='Check supplied evidence').click();p.get_by_text(row['document_id'],exact=True).wait_for();assert p.locator('#tariff-items img,#tariff-items script').count()==0
  assert p.locator('#tariff-items a').get_attribute('rel')=='noopener noreferrer';assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
  p.screenshot(path=str(OUT/f'tariff-{width}.png'),full_page=True)
  for attack,text in [('quota','Shared limit:'),('type','Invalid evidence response'),('large','Evidence response too large'),('source','Invalid source'),('date','Invalid evidence'),('extra','Invalid evidence'),('review','Invalid evidence response')]:
   mode['value']=attack;p.get_by_role('button',name='Check supplied evidence').click();p.locator('#tariff-status').filter(has_text=text).wait_for();assert p.locator('#tariff-items a').count()==0
   count=len([u for u in calls if t.API in u]);p.wait_for_timeout(100);assert len([u for u in calls if t.API in u])==count
  assert not errors,errors;results.append(dict(width=width,manual_only=True,unconnected_not_zero=True,xss_literal=True,attacks_refused=True,no_retry=True));p.close()
 b.close()
print(results);(OUT/'browser.json').write_text(json.dumps(results,indent=2))
