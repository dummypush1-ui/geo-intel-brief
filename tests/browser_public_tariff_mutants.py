"""Pins validate first; response/module injection is test-only."""
import sys,os,tempfile,json,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
from urllib.parse import urlsplit
from datetime import datetime,timezone
from integration.public_preview_builder import build_public_preview
from integration.tariff_evidence import TariffEvidenceSnapshot
from integration import public_tariff_evidence as t
from tests.test_code_news_public import env
OUT=Path(os.environ.get('TARIFF_EVIDENCE_DIR')or tempfile.mkdtemp(prefix='tariff-mutants-'));OUT.mkdir(exist_ok=True)
origin='https://preview.example';app=build_public_preview(dict(env(),PUBLIC_TARIFF_EVIDENCE_ENABLED='true'))
row=dict(id='fixture',jurisdiction='IN',nomenclature='HSN',edition='fixture',codes=['100630'],document_id='Fixture',source_url='https://www.indiabudget.gov.in/doc/cen/cus0326.pdf',published_date='2026-02-01',effective_dates=['2026-04-01'],excerpt='Fixture',conditions='Fixture only',review_state='candidate',reviewed_at=None)
fixture=t.Service(TariffEvidenceSnapshot('2026-10-04T00:00:00Z',[row]),now=lambda:datetime(2026,10,13,tzinfo=timezone.utc)).run('')[0]
source=(Path(__file__).resolve().parents[1]/'integration/ui/public_tariff_evidence.js').read_text()
cases=[('bytes','bytes>MAX','bytes>MAX+1000000','large','Evidence response too large'),('type',"if(!/^application\\/json(?:\\s*;|$)/i.test(r.headers.get('content-type')||''))",'if(false)','type','Invalid evidence response'),('rowkeys',"!exact(r,['id','jurisdiction','nomenclature','edition','codes','document_id','source_url','published_date','effective_dates','excerpt','conditions','review_state','reviewed_at'])",'false','extra','Invalid evidence'),('source',"u.protocol!=='https:'||!hosts[r.jurisdiction]?.includes(u.hostname)",'false','source','Invalid source'),('date',"!date(r.published_date)",'false','date','Invalid evidence'),('rates','[v.current_rates_verified,v.legal_effect_independently_verified,v.network,v.delivery,v.polling].some(x=>x!==false)','false','rates','Invalid evidence response')]
results=[]
with sync_playwright()as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
 for name,old,new,attack,expected in cases:
  assert source.count(old)==1,(name,source.count(old));outcomes=[]
  for mutated in [False,True]:
   p=b.new_page();p.set_default_timeout(5000)
   def route(r):
    u=r.request.url
    if not u.startswith(origin):r.abort();return
    if t.ASSET in u:r.fulfill(content_type='application/javascript',body=source.replace(old,new)if mutated else source);return
    if t.API in u:
     v=copy.deepcopy(fixture)
     if attack=='extra':v['items'][0]['private']='secret'
     if attack=='source':v['items'][0]['source_url']='https://evil.example/x'
     if attack=='date':v['items'][0]['published_date']='2026-02-30'
     if attack=='rates':v['current_rates_verified']=True
     r.fulfill(content_type='text/html'if attack=='type'else'application/json',body=(' '*250001 if attack=='large'else'')+json.dumps(v));return
    z=urlsplit(u);res=app.test_client().open(z.path,base_url=origin);r.fulfill(status=res.status_code,headers=dict(res.headers),body=res.data)
   p.route('**/*',route);p.goto(origin+t.PAGE);p.get_by_role('button',name='Check supplied evidence').click();p.wait_for_function("!document.querySelector('#tariff-form button').disabled")
   outcomes.append(expected in p.locator('#tariff-status').inner_text());p.close()
  assert outcomes==[True,False],(name,outcomes);results.append(dict(mutant=name,killed=True))
 b.close()
print(results);(OUT/'mutants.json').write_text(json.dumps(results,indent=2))
