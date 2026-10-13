import unittest
from unittest.mock import Mock,patch
from integration import public_tariff_evidence as t
from integration.public_preview_builder import build_public_preview
from tests.test_code_news_public import env
class Tests(unittest.TestCase):
 def app(self):return build_public_preview(dict(env(),PUBLIC_TARIFF_EVIDENCE_ENABLED='true'))
 def test_unconnected_exact_no_zero(self):
  c=self.app().test_client();r=c.get(t.API,base_url='https://preview.example')
  self.assertEqual(r.json['message'],t.NOT_CONNECTED);self.assertNotIn('total_supplied',r.json);self.assertNotIn('items',r.json)
  self.assertIn(t.NOT_CONNECTED,c.get(t.PAGE,base_url='https://preview.example').text)
 def test_query_method_origin_HEAD(self):
  app=self.app();c=app.test_client()
  for query in ['x=y','jurisdiction=IN&jurisdiction=US','jurisdiction=ZZ','jurisdiction=%49N','jurisdiction='+'x'*40]:self.assertEqual(c.get(t.API+'?'+query,base_url='https://preview.example').status_code,400)
  for path in t.PATHS:
   self.assertEqual(c.post(path,base_url='https://preview.example').status_code,403);self.assertEqual(c.get(path,base_url='https://evil.example').status_code,403)
  with patch.object(app.extensions['public_tariff_evidence'],'run',side_effect=AssertionError('IO')):self.assertEqual(c.head(t.API,base_url='https://preview.example').status_code,200)
 def test_headers_and_nav(self):
  c=self.app().test_client()
  for path in t.PATHS:
   for method in ['get','head']:
    r=getattr(c,method)(path,base_url='https://preview.example');self.assertEqual(r.status_code,200);self.assertEqual(r.headers['Cache-Control'],'no-store');self.assertEqual(r.headers['Referrer-Policy'],'no-referrer');self.assertEqual(r.headers['X-Content-Type-Options'],'nosniff')
  self.assertIn('Supplied tariff documents',c.get('/workspace',base_url='https://preview.example').text)
  self.assertNotIn('https://',c.get(t.PAGE,base_url='https://preview.example').text)
 def test_flag_pin_before_client(self):
  for e in [{t.FLAG:'bad'},{t.FLAG:'true'}]:
   with self.assertRaises(ValueError):t.prepare(e)
  with patch.object(t,'PINS',dict(t.PINS,**{'integration/ui/public_tariff_evidence.js':'0'*64})),self.assertRaises(ValueError):self.app()
 def test_OFF_bytes(self):
  a=build_public_preview(env());b=build_public_preview(dict(env(),PUBLIC_TARIFF_EVIDENCE_ENABLED='false'))
  for path in ['/workspace','/workspace/weekly',t.PAGE,t.API]:
   for method in ['get','head']:
    x=getattr(a.test_client(),method)(path,base_url='https://preview.example');y=getattr(b.test_client(),method)(path,base_url='https://preview.example');self.assertEqual((x.status_code,x.data,dict(x.headers)),(y.status_code,y.data,dict(y.headers)))
 def test_quota_not_auto_retry(self):
  s=t.Service(clock=lambda:100)
  for _ in range(10):self.assertEqual(s.run('')[1],200)
  self.assertEqual(s.run(''),({'state':'rate_limited'},429))
 def test_exact_snapshot_identity(self):
  with self.assertRaises(ValueError):t.Service(object())
  from integration.tariff_evidence import TariffEvidenceSnapshot
  class Sub(TariffEvidenceSnapshot):pass
  with self.assertRaises(ValueError):t.Service(Sub('2026-10-04T00:00:00Z',[]))
 def test_snapshot_fields_dates_URL_revalidated(self):
  from integration.tariff_evidence import TariffEvidenceSnapshot
  from datetime import datetime,timezone
  row=dict(id='fixture',jurisdiction='IN',nomenclature='HSN',edition='fixture',codes=['100630'],document_id='Fixture <script>bad</script>',source_url='https://www.indiabudget.gov.in/doc/cen/cus0326.pdf',published_date='2026-02-01',effective_dates=['2026-04-01'],excerpt='<img src=x>',conditions='Fixture only; no legal scope inferred',review_state='candidate',reviewed_at=None)
  snap=TariffEvidenceSnapshot('2026-10-04T00:00:00Z',[row]);s=t.Service(snap,now=lambda:datetime(2026,10,13,tzinfo=timezone.utc));v,status=s.run('IN');self.assertEqual(status,200);self.assertFalse(v['current_rates_verified']);self.assertFalse(v['legal_effect_independently_verified'])
  for changes in [{'unknown':'secret'},{'source_url':'https://evil.example/x'},{'published_date':'2026-02-30'},{'codes':['a'*100]},{'conditions':'x'*1001}]:
   snap._items=[dict(row,**changes)]
   with self.assertRaises(ValueError):t.Service(snap)
  s.snapshot._items[0]['source_url']='https://evil.example/x';self.assertEqual(s.run('')[1],503)
 def test_mounted_nav_derived_from_actual_route(self):
  a=self.app();c=a.test_client();a.view_functions['tariff_workspace']=lambda:'drift'
  self.assertNotIn('Supplied tariff documents</a>',c.get('/workspace',base_url='https://preview.example').text)
 def test_combined_live_flags_header_order(self):
  from integration.public_live_builder import build_public_live_preview
  from tests.test_code_news_coverage_binding_prep import LIVE,Client
  flags=dict(LIVE,PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED='false',PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED='false',PUBLIC_CODE_NEWS_ENABLED='true',PUBLIC_CODE_NEWS_SCOPE_REVIEWED='true',PUBLIC_RELATIONSHIP_NAV_ENABLED='true',PUBLIC_TARIFF_EVIDENCE_ENABLED='true',PUBLIC_WEEKLY_PDF_ENABLED='true',PUBLIC_WEEKLY_FULL_STORE_ENABLED='true',PUBLIC_AI_ANSWERS_ENABLED='true',PUBLIC_MAP_ENABLED='true',PUBLIC_MAP_M2_ENABLED='true',PUBLIC_BRICS_STREAMS_ENABLED='true')
  app=build_public_live_preview(flags,client_factory=lambda *a,**k:Client());self.addCleanup(app.extensions['whole_news_pages'].close);c=app.test_client()
  for path in ['/workspace','/workspace/weekly']:
   r=c.get(path,base_url=LIVE['PREVIEW_ORIGIN']);self.assertEqual(r.status_code,200);self.assertIn('Supplied tariff documents',r.text);self.assertEqual(int(r.headers['Content-Length']),len(r.data));self.assertEqual(r.headers['Cache-Control'],'no-store');self.assertEqual(r.headers['X-Content-Type-Options'],'nosniff')
  r=c.get(t.API,base_url=LIVE['PREVIEW_ORIGIN']);self.assertEqual(r.json['message'],t.NOT_CONNECTED);self.assertEqual(r.headers['Referrer-Policy'],'no-referrer')
 def test_HTTP_guard_mutants(self):
  from pathlib import Path
  source=Path(t.__file__).read_text()
  cases=[("b'%' in request.query_string",'False','jurisdiction=%49N')]
  for old,new,query in cases:
   self.assertEqual(source.count(old),1);ns={'__name__':'tariffmutant','__file__':t.__file__};exec(compile(source.replace(old,new),'mutant','exec'),ns)
   from integration.news_api import create_app
   app=create_app(authorize=lambda _:True);ns['install'](app,'https://preview.example')
   self.assertEqual(app.test_client().get(t.API+'?'+query,base_url='https://preview.example').status_code,200)
   self.assertEqual(self.app().test_client().get(t.API+'?'+query,base_url='https://preview.example').status_code,400)
 def test_weekly_navOFFbyte_equality_and_noPDFmapping(self):
  flags=dict(env(),PUBLIC_WEEKLY_PDF_ENABLED='true')
  a=build_public_preview(flags);b=build_public_preview(dict(flags,PUBLIC_TARIFF_EVIDENCE_ENABLED='false'))
  for path in ['/workspace','/workspace/weekly']:
   for method in ['get','head']:
    x=getattr(a.test_client(),method)(path,base_url='https://preview.example');y=getattr(b.test_client(),method)(path,base_url='https://preview.example');self.assertEqual((x.status_code,x.data,dict(x.headers)),(y.status_code,y.data,dict(y.headers)))
  c=build_public_preview(dict(flags,PUBLIC_TARIFF_EVIDENCE_ENABLED='true')).test_client()
  self.assertIn('Supplied tariff documents',c.get('/workspace/weekly',base_url='https://preview.example').text)
 def test_no_store_all_paths_errors(self):
  c=self.app().test_client()
  for path in list(t.PATHS)+[t.API+'?jurisdiction=XX',t.PAGE+'?x=y']:
   r=c.get(path,base_url='https://preview.example');self.assertEqual(r.headers['Cache-Control'],'no-store')
 def test_mount_replaced_or_duplicate_refused(self):
  from integration.news_api import create_app
  for bad in ['view','duplicate']:
   a=create_app(authorize=lambda _:True)
   if bad=='view':a.view_functions['tariff_workspace']=lambda:'wrong'
   else:a.add_url_rule('/duplicate',endpoint='tariff_workspace',methods=['GET'])
   with self.assertRaises(ValueError):t.install(a,'https://preview.example')
 def wrapper(self):
  # Invoke own guard to avoid equivalent mutants from original globalguard.
  from integration.news_api import create_app
  a=create_app(authorize=lambda _:True);t.install(a,'https://preview.example')
  return a,next(h for h in a.before_request_funcs[None]if h.__module__==t.__name__ and h.__name__=='guard')
 def test_wrapper_boundary_queries_host_method(self):
  a,guard=self.wrapper()
  cases=[(t.API+'?jurisdiction=XX','GET','https://preview.example',400),(t.API+'?jurisdiction='+('x'*40),'GET','https://preview.example',400),(t.API+'?x=y','GET','https://preview.example',400),(t.API+'?jurisdiction=IN&jurisdiction=US','GET','https://preview.example',400),(t.PAGE+'?x=y','GET','https://preview.example',400),(t.PAGE,'POST','https://preview.example',403),(t.PAGE,'GET','https://evil.example',403)]
  for path,method,base,status in cases:
   with a.test_request_context(path,method=method,base_url=base):self.assertEqual(guard()[1],status)
 def test_encoded_size_cap(self):
  a=self.app()
  with patch.object(a.extensions['public_tariff_evidence'],'run',return_value=({'x':'a'*250001},200)):
   r=a.test_client().get(t.API,base_url='https://preview.example');self.assertEqual(r.status_code,503);self.assertEqual(r.json,{'state':'evidence_unavailable'})
 def test_exact_flags_and_both_weekly_nav_branches(self):
  for value in ['TRUE','1','', 'false ']:
   with self.assertRaises(ValueError):t.prepare(dict(env(),**{t.FLAG:value}))
  self.assertFalse(t.prepare(dict(env(),**{t.FLAG:'false'})));self.assertTrue(t.prepare(dict(env(),**{t.FLAG:'true'})))
  for weekly in [False,True]:
   flags=dict(env(True),PUBLIC_TARIFF_EVIDENCE_ENABLED='true',PUBLIC_RELATIONSHIP_NAV_ENABLED='true',PUBLIC_WEEKLY_PDF_ENABLED='true'if weekly else'false',PUBLIC_MAP_ENABLED='true',PUBLIC_MAP_M2_ENABLED='true')
   a=build_public_preview(flags);c=a.test_client();r=c.get(t.PAGE,base_url='https://preview.example');self.assertEqual('/workspace/weekly' in r.text,weekly)
   for path in ['/workspace']+(['/workspace/weekly']if weekly else[]):
    r=c.get(path,base_url='https://preview.example');self.assertEqual(r.text.count('<a href="/workspace/tariffs">Supplied tariff documents</a>'),1);self.assertEqual(r.text.count('<a href="/workspace/code-news">Reported code-news</a>'),1)
