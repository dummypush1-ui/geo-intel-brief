import unittest,io
from pathlib import Path
from unittest.mock import Mock,patch
from flask import Flask
from integration.public_live_builder import build_public_live_preview
from integration.code_news_coverage_binding_prep import Binding,verify_pins,PINS,VERSION
from integration.news_pages import WholeGeoPages
from integration.public_live_builder import sanitize_public_geo_rows
from tests.test_news_pages185 import Store,rows
from integration.code_news_coverage_route_prep import install as api_install
from integration.code_news_links import Links
from integration.code_news_parent_prep import Broker,ResolveQuota
ORIGIN='https://example.test';SAMPLE={'PREVIEW_PUBLIC_SAMPLE_ENABLED':'true','PREVIEW_GEO_ONLY_ENABLED':'true','PREVIEW_ACCESS_ENABLED':'false','NEWS_READ_ENABLED':'false','NEWS_EVENTS_READ_ENABLED':'false','FINDER_NETWORK_PREVIEW_ENABLED':'false','PREVIEW_ORIGIN':ORIGIN}
LIVE={**SAMPLE,'PUBLIC_NEWS_READ_ENABLED':'true','PUBLIC_NEWS_FULL_PAGES_ENABLED':'true','NEWS_STORE_MAPPING_VERIFIED':'true','PUBLIC_NEWS_DISCLOSURE_VERIFIED':'true','GEO_READONLY_CREDENTIAL_VERIFIED':'true','GEO_MONGODB_URI':'fake','PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED':'true','PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED':'true'}
class Client:
 def __init__(self):self.store=Store(rows(60));self.closes=0
 def __getitem__(self,key):return self if key=='geo_intel'else self.store
 def close(self):self.closes+=1
class Tests(unittest.TestCase):
 def binding(self):return Binding(True,True,True,True,'fixture-owner-scope','fixture-deployment')
 def test_default_off_and_UIonly_no_factory(self):
  for env in [SAMPLE,dict(SAMPLE,PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED='true')]:
   factory=Mock(side_effect=AssertionError('client'))
   # sample builder intentionally refuses any non-None client factory, so poison actual default.
   with patch('integration.public_live_builder.create_public_geo_client',factory),patch('integration.code_news_coverage_binding_prep.verify_pins',side_effect=AssertionError('pins')):app=build_public_live_preview(env)
   c=app.test_client();r=c.get('/workspace/code-news-coverage',base_url=ORIGIN)
   self.assertEqual(r.status_code,200 if env.get('PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED')=='true'else 404)
   if r.status_code==200:self.assertIn('data-coverage-available="false"',r.text)
   self.assertEqual(c.post('/api/code-news-coverage',base_url=ORIGIN).status_code,404);factory.assert_not_called()
 def test_badflags_beforedelegation_and_pins_before_factory(self):
  for key in ['PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED','PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED']:
   with self.assertRaises(ValueError):build_public_live_preview(dict(SAMPLE,**{key:'yes'}))
  factory=Mock();provider=Mock(return_value=self.binding())
  with self.assertRaises(ValueError):build_public_live_preview(LIVE,client_factory=factory)
  with patch('integration.code_news_coverage_binding_prep.verify_pins',side_effect=ValueError('secret')):
   with self.assertRaises(ValueError):build_public_live_preview(LIVE,client_factory=factory,coverage_binding_provider=provider)
  factory.assert_not_called();provider.assert_not_called()
 def test_actualpins_and_shared_pages_narrowPOST_close(self):
  pins=verify_pins();self.assertEqual(pins.manifest,PINS['integration/code_news_index/manifest.json']);self.assertEqual(pins.matcher_version,VERSION)
  client=Client();app=build_public_live_preview(LIVE,client_factory=lambda *a,**k:client,coverage_binding_provider=self.binding);self.addCleanup(app.extensions['coverage_close']);broker=app.extensions['code_news_coverage_broker'];self.assertIs(broker.pages,app.extensions['whole_news_pages']);self.assertIs(broker.pages.admission,broker.ledger)
  c=app.test_client();self.assertIn('data-coverage-available="true"',c.get('/workspace/code-news-coverage',base_url=ORIGIN).text)
  h={'Origin':ORIGIN,'Sec-Fetch-Site':'same-origin','Sec-Fetch-Mode':'cors','Sec-Fetch-Dest':'empty'};r=c.post('/api/code-news-coverage',base_url=ORIGIN,json={'system':'HS','edition':'2022','code':'8517'},headers=h);self.assertEqual(r.status_code,200);self.assertEqual(c.post('/api/news',base_url=ORIGIN,headers=h).status_code,403)
  self.assertEqual(r.headers['Referrer-Policy'],'no-referrer');self.assertEqual(r.headers['Content-Security-Policy'],"default-src 'none'; frame-ancestors 'none'")
  self.assertEqual(c.head('/api/code-news-coverage',base_url=ORIGIN).status_code,200);self.assertEqual(c.options('/api/code-news-coverage',base_url=ORIGIN).status_code,204)
  app.extensions['coverage_close']();app.extensions['coverage_close']();self.assertEqual(client.closes,1);self.assertTrue(broker.pages.stopped.is_set());self.assertTrue(broker.model.closed)
 def test_actual_HEAD_OPTIONS_Newslock_IOpoison(self):
  pages=WholeGeoPages(Store(rows(1)),sanitize_public_geo_rows,verified=True,start_cleaner=False);self.addCleanup(pages.close);model=Links([],[]);broker=Broker(pages,model,'a'*64,'v1',resolve_quota=ResolveQuota());app=Flask('head');api_install(app,ORIGIN,broker,{'PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED':'true'});c=app.test_client();pages.lock.acquire()
  try:
   with patch.object(model,'resolve',side_effect=AssertionError('index')),patch.object(pages,'_page_locked',side_effect=AssertionError('source')),patch('pathlib.Path.read_text',side_effect=AssertionError('file')),patch.object(broker,'page',side_effect=AssertionError('page')) as page:
    self.assertEqual(c.head('/api/code-news-coverage').status_code,200);self.assertEqual(c.options('/api/code-news-coverage').status_code,204);page.assert_not_called()
  finally:pages.lock.release()

 def test_headers_after_hooks_before_and_after(self):
  from integration.code_news_coverage_route_prep import install
  app=Flask('order')
  @app.after_request
  def before(r):r.headers['Referrer-Policy']='same-origin';r.headers['Content-Security-Policy']='bad-before';return r
  b=Mock();b.head.return_value=({},200);install(app,ORIGIN,b,{'PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED':'true'})
  @app.after_request
  def after(r):r.headers['Referrer-Policy']='unsafe-url';r.headers['Content-Security-Policy']='bad-after';return r
  response=app.test_client().head('/api/code-news-coverage');self.assertEqual(response.headers['Referrer-Policy'],'no-referrer');self.assertEqual(response.headers['Content-Security-Policy'],"default-src 'none'; frame-ancestors 'none'")
 def test_pin_drift_no_factory_provider(self):
  from integration.code_news_coverage_binding_prep import ROOT
  factory=Mock();provider=Mock(return_value=self.binding());original=Path.open
  def read(path,*a,**k):
   if str(path).endswith('code_news_links.py'):return io.BytesIO(b'changed')
   return original(path,*a,**k)
  with patch('pathlib.Path.open',read):
   with self.assertRaises(ValueError):build_public_live_preview(LIVE,client_factory=factory,coverage_binding_provider=provider)
  factory.assert_not_called();provider.assert_not_called()
 def test_startup_failure_cleanup_order(self):
  order=[];pages=Mock();pages.admission=None;pages.close.side_effect=lambda:order.append('pages');model=Mock();model.close.side_effect=lambda:order.append('model');client=Client();client.close=lambda:order.append('client')
  with patch('integration.news_pages.WholeGeoPages',return_value=pages),patch('integration.code_news_disk.DiskLinks',return_value=model),patch('integration.public_live_builder.create_app',side_effect=RuntimeError('private')):
   with self.assertRaisesRegex(ValueError,'Public composition unavailable'):build_public_live_preview(LIVE,client_factory=lambda *a,**k:client,coverage_binding_provider=self.binding)
  self.assertEqual(order,['pages','model','client'])

 def test_shutdown_order_once_and_entry_provider(self):
  client=Client();app=build_public_live_preview(LIVE,client_factory=lambda *a,**k:client,coverage_binding_provider=self.binding);broker=app.extensions['code_news_coverage_broker'];order=[];pc=broker.pages.close;mc=broker.model.close;cc=client.close
  broker.pages.close=lambda:(order.append('pages'),pc())[-1];broker.model.close=lambda:(order.append('model'),mc())[-1];client.close=lambda:(order.append('client'),cc())[-1]
  app.extensions['coverage_close']();app.extensions['coverage_close']();self.assertEqual(order,['pages','model','client'])
  from production_entry import build_production_app
  builder=Mock(return_value=Flask('entry'));provider=Mock();build_production_app({},public_builder=builder,coverage_binding_provider=provider);builder.assert_called_once_with({},coverage_binding_provider=provider)
 def test_fake_builder_real_stream_no_constructor_requests(self):
  client=Client()
  for row in client.store.rows:row['title']='HS8517;';row['summary']=''
  app=build_public_live_preview(LIVE,client_factory=lambda *a,**k:client,coverage_binding_provider=self.binding);self.addCleanup(app.extensions['coverage_close']);self.assertEqual(client.store.calls,[]);broker=app.extensions['code_news_coverage_broker'];self.assertEqual(broker.ledger.rows,{})
  c=app.test_client();h={'Origin':ORIGIN,'Sec-Fetch-Site':'same-origin','Sec-Fetch-Mode':'cors','Sec-Fetch-Dest':'empty'};r=c.post('/api/code-news-coverage',base_url=ORIGIN,json={'system':'HS','edition':'2022','code':'8517'},headers=h);counts=[len(r.json['items'])]
  for _ in range(2):r=c.post('/api/code-news-coverage',base_url=ORIGIN,json={k:r.json[k]for k in ['scope','manifest','matcher_version']},headers=h);counts.append(len(r.json['items']))
  self.assertEqual(counts,[25,25,10]);self.assertEqual(len(client.store.calls),1);self.assertEqual(r.json['state'],'complete_mutable_read')

 def test_live_OFF_paths404_before_globalguard(self):
  env=dict(LIVE,PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED='false',PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED='false');client=Client();app=build_public_live_preview(env,client_factory=lambda *a,**k:client);self.addCleanup(app.extensions['whole_news_pages'].close);c=app.test_client()
  for path in ['/api/code-news-coverage','/workspace/code-news-coverage','/workspace/assets/code_news_contract.js']:
   self.assertEqual(c.head(path,base_url=ORIGIN).status_code,404);self.assertEqual(c.get(path,base_url=ORIGIN).status_code,404)
 def old_builder(self):
  namespace={};fixture=Path(__file__).parent/'fixtures'/'public_live_builder_before_coverage.txt';exec(compile(fixture.read_text(),str(fixture),'exec'),namespace);return namespace['build_public_live_preview']
 def test_OFF_old_app_routes_headers_bytes(self):
  old=self.old_builder();env=dict(LIVE,PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED='false',PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED='false',PUBLIC_NEWS_FULL_PAGES_ENABLED='false');clients=[Client(),Client()];apps=[old(env,client_factory=lambda *a,**k:clients[0]),build_public_live_preview(env,client_factory=lambda *a,**k:clients[1])]
  self.assertEqual(sorted((r.rule,sorted(r.methods))for r in apps[0].url_map.iter_rules()),sorted((r.rule,sorted(r.methods))for r in apps[1].url_map.iter_rules()))
  for path in ['/workspace','/workspace/assets/workspace.js','/workspace/assets/workspace.css','/api/news-stats','/api/source-health','/health']:
   responses=[app.test_client().get(path,base_url=ORIGIN)for app in apps];self.assertEqual(responses[0].status_code,responses[1].status_code);self.assertEqual(responses[0].data,responses[1].data);self.assertEqual(dict(responses[0].headers),dict(responses[1].headers))
 def test_OFF_failure_error_client_handling_old_equal(self):
  old=self.old_builder();env=dict(LIVE,PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED='false',PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED='false')
  for builder in [old,build_public_live_preview]:
   client=Client()
   with patch('integration.public_live_builder.create_app',side_effect=RuntimeError('same-message')) if builder is build_public_live_preview else patch.dict(builder.__globals__,create_app=Mock(side_effect=RuntimeError('same-message'))):
    with self.assertRaisesRegex(RuntimeError,'same-message'):builder(env,client_factory=lambda *a,**k:client)
   self.assertEqual(client.closes,0)
 def test_mount_failure_stages_fd_no_partial(self):
  import os
  stages=['integration.news_pages.WholeGeoPages','integration.code_news_disk.DiskLinks','integration.public_live_builder.create_app','integration.code_news_coverage_broker_prep.CoverageBroker','integration.code_news_coverage_route_prep.install','integration.code_news_coverage_ui_prep.install']
  for stage in stages:
   before=len(list(Path('/proc/self/fd').iterdir()));client=Client()
   with patch(stage,side_effect=RuntimeError('private')):
    with self.assertRaisesRegex(ValueError,'Public composition unavailable'):build_public_live_preview(LIVE,client_factory=lambda *a,**k:client,coverage_binding_provider=self.binding)
   self.assertEqual(client.closes,1,stage);self.assertEqual(len(list(Path('/proc/self/fd').iterdir())),before,stage)
 def test_duplicate_atexit_pages_safe(self):
  callbacks=[];client=Client()
  with patch('atexit.register',side_effect=lambda callback:callbacks.append(callback)):app=build_public_live_preview(LIVE,client_factory=lambda *a,**k:client,coverage_binding_provider=self.binding)
  self.assertEqual(len(callbacks),2)
  for callback in reversed(callbacks):callback()
  for callback in callbacks:callback()
  self.assertEqual(client.closes,1);self.assertTrue(app.extensions['code_news_coverage_broker'].model.closed)
 def test_globalguard_method_matrix_API_UI_on_off(self):
  for api in [False,True]:
   for ui in [False,True]:
    env=dict(LIVE,PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED=str(api).lower(),PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED=str(ui).lower());client=Client();app=build_public_live_preview(env,client_factory=lambda *a,**k:client,coverage_binding_provider=self.binding if api else None);c=app.test_client()
    if api:self.addCleanup(app.extensions['coverage_close'])
    else:self.addCleanup(app.extensions['whole_news_pages'].close)
    h={'Origin':ORIGIN,'Sec-Fetch-Site':'same-origin','Sec-Fetch-Mode':'cors','Sec-Fetch-Dest':'empty'}
    for method in ['PUT','PATCH','DELETE','POST']:
     response=c.open('/api/code-news-coverage',method=method,base_url=ORIGIN,headers=h,json={'system':'HS','edition':'2022','code':'8517'})
     self.assertEqual(response.status_code,200 if api and method=='POST'else 403 if api else 404,(api,ui,method,'API'))
     for path in ['/workspace/code-news-coverage','/workspace/assets/code_news_coverage.js','/workspace/assets/code_news_coverage.css','/workspace/assets/code_news_contract.js']:
      self.assertEqual(c.open(path,method=method,base_url=ORIGIN,headers=h).status_code,403 if ui else 404,(api,ui,method,path))
 def test_live_UIonly_availability_false_actualHTML(self):
  env=dict(LIVE,PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED='false');client=Client();app=build_public_live_preview(env,client_factory=lambda *a,**k:client);self.addCleanup(app.extensions['whole_news_pages'].close);response=app.test_client().get('/workspace/code-news-coverage',base_url=ORIGIN)
  self.assertEqual(response.status_code,200);self.assertIn('data-coverage-available="false"',response.text);self.assertIn('Coverage unavailable',response.text);self.assertNotIn('code_news_coverage_broker',app.extensions)
 def test_each_binding_review_false_beforefactory(self):
  from dataclasses import replace
  for field in ['single_worker','source_timeout_reviewed','memory_reviewed','abuse_reviewed']:
   factory=Mock(side_effect=AssertionError('client'));provider=lambda:replace(self.binding(),**{field:False})
   with self.assertRaisesRegex(ValueError,'Coverage binding unavailable'):build_public_live_preview(LIVE,client_factory=factory,coverage_binding_provider=provider)
   factory.assert_not_called()

 def test_wrong_Host_refused_explicitOrigin(self):
  client=Client();app=build_public_live_preview(LIVE,client_factory=lambda *a,**k:client,coverage_binding_provider=self.binding);self.addCleanup(app.extensions['coverage_close'])
  self.assertEqual(app.test_client().head('/api/code-news-coverage',base_url='https://wrong.test',headers={'Origin':ORIGIN}).status_code,403)
