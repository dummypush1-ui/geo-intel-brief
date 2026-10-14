import unittest
from unittest.mock import Mock,patch
from datetime import datetime,timezone,timedelta
from integration.brics_news_boundary import BricsFixtureReader,Service,project
from integration import public_brics_news as b
from integration.public_preview_builder import build_public_preview
from integration.public_live_builder import build_public_live_preview
from tests.test_code_news_public import env
from tests.test_code_news_coverage_binding_prep import LIVE,Client
NOW=datetime(2026,10,13,12,tzinfo=timezone.utc)
ROW=dict(url='https://fixture.invalid/brics',title='BRICS sanctions summit',summary='Fixture only',source='Fixture',country='IN',category='SANCTIONS',collected_at='2026-10-13T11:00:00')
def reader(rows):return BricsFixtureReader(lambda:rows,object(),('sanctions','coup'))
class Tests(unittest.TestCase):
 def test_unconnected(self):self.assertEqual(Service().run()[0]['state'],'source_not_connected');self.assertNotIn('items',Service().run()[0])
 def test_exact_type_identity_noGeo(self):
  with self.assertRaises(ValueError):Service(Mock())
  x=reader([])
  with self.assertRaises(ValueError):Service(x,geo_identity=x.source_identity)
  geo=Mock(side_effect=AssertionError('Geo touched'))
  bad=BricsFixtureReader(lambda:(_ for _ in ()).throw(RuntimeError('SECRET')),object(),('coup',));self.assertEqual(Service(bad,geo_identity=geo).run()[1],503);geo.assert_not_called();self.assertNotIn('SECRET',str(Service(bad).run()))
 def test_projection_unknown_notGeo(self):
  raw=dict(ROW,password='SECRET',risk_level='LOW',credibility='HIGH',extra={'private':'SECRET'})
  d,status=Service(reader([raw]),now=lambda:NOW).run();self.assertEqual(status,200);r=d['items'][0];self.assertEqual(r['corroboration_state'],'unknown, not cleared');self.assertIsNone(r['corroboration_count']);self.assertNotIn('risk_level',r);self.assertNotIn('SECRET',str(d));self.assertTrue(r['critical_keyword_match']);self.assertEqual(len(d['critical_24h_keys']),1)
 def test_dates(self):
  self.assertEqual(project(ROW,('sanctions',))['collected_at'],'2026-10-13T11:00:00Z')
  for date in ['2026-10-13T11:00:00','2026-02-30','bad']:
   self.assertEqual(Service(reader([dict(ROW,published=date)])).run()[1],503)
  d=project(dict(ROW,published='2026-10-13T16:30:00+05:30'),('sanctions',));self.assertEqual(d['published_at'],'2026-10-13T11:00:00Z')
  for date in ['2026-10-14T00:00:00Z','2026-10-12T12:00:00Z']:
   self.assertEqual(Service(reader([dict(ROW,collected_at=date)]),now=lambda:NOW).run()[0]['critical_24h_keys'],[])
  self.assertEqual(Service(reader([dict(ROW,collected_at=None)]),now=lambda:NOW).run()[0]['critical_time_unknown_count'],1)
 def test_corrob_and_sanitize(self):
  d=project(dict(ROW,title='BRICS\x00 <script>x</script>',corroborated_by=['A','A','B']),('coup',));self.assertNotIn('\x00',d['title']);self.assertIn('<script>',d['title']);self.assertEqual(d['corroboration_count'],2)
  for val in ['x',{},[None],['x']*31]:self.assertEqual(Service(reader([dict(ROW,corroborated_by=val)])).run()[1],503)
 def test_limits_failclosed(self):
  for rr in [[ROW]*101,[dict(ROW,summary='x'*8001)],[dict(ROW,url='javascript:alert(1)')],[dict(ROW,published={})],{},[dict(ROW,summary='x'*8000)]*100]:
   self.assertEqual(Service(reader(rr)).run()[1],503)
 def test_factory_gates(self):
  for extra in [{b.FLAG:'TRUE'},{b.FLAG:'true','PREVIEW_PUBLIC_SAMPLE_ENABLED':'false'}]:
   with self.assertRaises(ValueError):build_public_live_preview(dict(LIVE,**extra),client_factory=lambda *a,**k:self.fail('factory before gate'))
 def test_production_unwired(self):
  for app in [build_public_preview(dict(env(),**{b.FLAG:'true'})),build_public_live_preview(dict(LIVE,PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED='false',PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED='false',**{b.FLAG:'true'}),client_factory=lambda *a,**k:Client())]:
   if app.extensions.get('whole_news_pages'):self.addCleanup(app.extensions['whole_news_pages'].close)
   self.assertIsNone(app.extensions['public_brics_news'].reader);c=app.test_client();r=c.get(b.API,base_url=app.config.get('NOT_AN_ORIGIN',LIVE['PREVIEW_ORIGIN']) if app.extensions.get('whole_news_pages') else 'https://preview.example');self.assertEqual(r.json['state'],'source_not_connected')
 def test_OFF_byte_and_seeds_separate(self):
  flags=dict(env(),PUBLIC_BRICS_STREAMS_ENABLED='true');a=build_public_preview(flags);off=build_public_preview(dict(flags,**{b.FLAG:'false'}));on=build_public_preview(dict(flags,**{b.FLAG:'true'}))
  for path in ['/workspace','/api/brics/streams','/workspace/brics-streams',b.PAGE,b.API]:
   for method in ('get','head'):
    x=getattr(a.test_client(),method)(path,base_url='https://preview.example');y=getattr(off.test_client(),method)(path,base_url='https://preview.example');self.assertEqual((x.status_code,x.data,dict(x.headers)),(y.status_code,y.data,dict(y.headers)))
  self.assertEqual(a.test_client().get('/api/brics/streams',base_url='https://preview.example').data,on.test_client().get('/api/brics/streams',base_url='https://preview.example').data)
  html=on.test_client().get('/workspace',base_url='https://preview.example').text;self.assertIn('BRICS news</a>',html);self.assertIn('BRICS streams</a>',html)
 def test_routes_noIO_HEAD_origin_query(self):
  app=build_public_preview(dict(env(),**{b.FLAG:'true'}));c=app.test_client()
  with patch.object(app.extensions['public_brics_news'],'run',side_effect=AssertionError('IO')):self.assertEqual(c.head(b.API,base_url='https://preview.example').status_code,200)
  for path in b.PATHS:
   self.assertEqual(c.post(path,base_url='https://preview.example').status_code,403);self.assertEqual(c.get(path,base_url='https://evil.example').status_code,403);self.assertEqual(c.get(path+'?x=y',base_url='https://preview.example').status_code,400)
  app.view_functions['public_brics_news_page']=lambda:'replaced';self.assertNotIn('BRICS news</a>',c.get('/workspace',base_url='https://preview.example').text)

 def test_runtime_type_revalidation(self):
  service=Service(reader([]));service.reader=Mock();self.assertEqual(service.run()[1],503)
 def test_projection_case_and_unknown_never_leak(self):
  r=project(dict(ROW,TITLE='not canonical',Corroborated_By=['not canonical'],url_secret='SECRET'),('sanctions',));self.assertEqual(r['title'],ROW['title']);self.assertIsNone(r['corroboration_count']);self.assertNotIn('SECRET',str(r))
 def test_separate_proof_of_keyword_and_relevance(self):
  r=project(dict(ROW,title='Domestic sports sanctions',summary=''),('sanctions',));self.assertTrue(r['critical_keyword_match']);self.assertFalse(r['brics_relevant']);self.assertEqual(Service(reader([dict(ROW,title='Domestic sports sanctions',summary='')]),now=lambda:NOW).run()[0]['critical_24h_keys'],[])
 def test_pin_refusal(self):
  with patch.object(b,'PINS',dict(b.PINS,**{'integration/brics_news_boundary.py':'0'*64})),self.assertRaises(ValueError):build_public_live_preview(dict(LIVE,**{b.FLAG:'true'}),client_factory=lambda *a,**k:self.fail('factory before pins'))

 def test_nav_startup_seam(self):
  with patch.object(b.Path,'read_text',return_value='drift'),self.assertRaises(ValueError):build_public_live_preview(dict(LIVE,**{b.FLAG:'true'}),client_factory=lambda *a,**k:self.fail('factory before nav seam'))
 def test_mounted_url_rule(self):
  app=build_public_preview(dict(env(),**{b.FLAG:'true'}));self.assertTrue(b.mounted(app))
  with patch.object(app.url_map,'iter_rules',return_value=iter([])):self.assertFalse(b.mounted(app))
 def test_combined_every_nav_once(self):
  flags=dict(LIVE,PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED='false',PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED='false',PUBLIC_NEWS_SEARCH_PROGRESS_ENABLED='true',PUBLIC_BRICS_NEWS_ENABLED='true',PUBLIC_CODE_NEWS_ENABLED='true',PUBLIC_CODE_NEWS_SCOPE_REVIEWED='true',PUBLIC_RELATIONSHIP_NAV_ENABLED='true',PUBLIC_TARIFF_EVIDENCE_ENABLED='true',PUBLIC_WEEKLY_PDF_ENABLED='true',PUBLIC_WEEKLY_FULL_STORE_ENABLED='true',PUBLIC_AI_ANSWERS_ENABLED='true',PUBLIC_MAP_ENABLED='true',PUBLIC_MAP_M2_ENABLED='true',PUBLIC_BRICS_STREAMS_ENABLED='true')
  app=build_public_live_preview(flags,client_factory=lambda *a,**k:Client());self.addCleanup(app.extensions['whole_news_pages'].close);c=app.test_client();html=c.get('/workspace',base_url=LIVE['PREVIEW_ORIGIN'])
  for link in ['/workspace/brics-news','/workspace/brics-streams','/workspace/weekly','/workspace/tariffs','/workspace/ai-answers','/workspace/map','/workspace/code-news']:self.assertEqual(html.text.count('href="'+link+'"'),1,link)
  for path in ['/workspace',b.PAGE,b.API,b.ASSET]:
   r=c.get(path,base_url=LIVE['PREVIEW_ORIGIN']);self.assertEqual(r.status_code,200);self.assertEqual(r.headers['Cache-Control'],'no-store');self.assertEqual(r.headers['X-Content-Type-Options'],'nosniff');self.assertEqual(int(r.headers['Content-Length']),len(r.data))
  js=c.get('/workspace/assets/workspace.js',base_url=LIVE['PREVIEW_ORIGIN']).text;self.assertIn('attachReportedCodes',js);self.assertIn('1250000',js)
 def test_duplicate_mount(self):
  app=build_public_preview(dict(env(),**{b.FLAG:'true'}))
  with self.assertRaises(ValueError):b.install(app,'https://preview.example')
 def test_public_wrapper_mutants(self):
  from pathlib import Path
  from flask import Response,request
  from integration.news_api import create_app
  source=Path(b.__file__).read_text()
  cases=[("r.headers['Cache-Control']='no-store'","r.headers['Cache-Control']='public'","cache"),("request.host_url.rstrip('/')!=origin","False","host"),("hooks.insert(0,headers)","hooks.append(headers)","order"),("env.get('PREVIEW_PUBLIC_SAMPLE_ENABLED')!='true'","False","composition"),("if value not in ('true','false'):","if False:","exact"),("if any(r.rule in PATHS for r in app.url_map.iter_rules()):","if False:","duplicate")]
  for old,new,kind in cases:
   self.assertEqual(source.count(old),1);ns={'__name__':'b2mutant','__file__':b.__file__};exec(compile(source.replace(old,new),kind,'exec'),ns)
   if kind=='composition':self.assertTrue(ns['prepare']({b.FLAG:'true'}));continue
   if kind=='exact':self.assertTrue(ns['prepare']({b.FLAG:'TRUE','PREVIEW_PUBLIC_SAMPLE_ENABLED':'true'}));continue
   app=create_app(authorize=lambda _:True);app.after_request_funcs[None]=[]
   @app.after_request
   def overwrite(r):
    if request.path==b.API:r.headers['Cache-Control']='public'
    return r
   ns['install'](app,'https://preview.example');c=app.test_client()
   if kind=='cache':self.assertEqual(c.get(b.API,base_url='https://preview.example').headers['Cache-Control'],'public')
   if kind=='order':self.assertEqual(c.get(b.API,base_url='https://preview.example').headers['Cache-Control'],'public')
   if kind=='host':self.assertEqual(c.get(b.API,base_url='https://evil.example').status_code,200)
   if kind=='duplicate':
    # Route-rule collision is the mutation; remove endpoint names to avoid Flask's independent endpoint gate.
    app.view_functions.pop('public_brics_news_page');app.view_functions.pop('public_brics_news_get');app.view_functions.pop('public_brics_news_asset');ns['install'](app,'https://preview.example');self.assertEqual(sum(r.rule==b.PAGE for r in app.url_map.iter_rules()),2)
  # Hook order production overwrites an earlier cache mutator.
  app=create_app(authorize=lambda _:True)
  @app.after_request
  def earlier(r):r.headers['Cache-Control']='public';return r
  b.install(app,'https://preview.example');self.assertEqual(app.test_client().get(b.API,base_url='https://preview.example').headers['Cache-Control'],'no-store')
