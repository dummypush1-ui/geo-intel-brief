import hashlib,json,subprocess,unittest
from pathlib import Path
from unittest.mock import patch,Mock
from integration import public_brics_streams as b,public_weekly_pdf as w,news_finder_navigation_prep as nav
from integration.public_preview_builder import build_public_preview
from integration.public_live_builder import build_public_live_preview
from integration.news_api import create_app
from tests.test_code_news_coverage_binding_prep import SAMPLE,LIVE,ORIGIN,Client,Binding

class Tests(unittest.TestCase):
 def app(self,**kw):return build_public_preview(dict(SAMPLE,**{b.FLAG:'true'},**kw))
 def req(self,app,path=b.API,method='get'):return getattr(app.test_client(),method)(path,base_url=ORIGIN)
 def test_fixed_seed_and_no_embed(self):
  app=self.app();r=self.req(app);self.assertEqual(r.status_code,200);self.assertLessEqual(len(r.data),32768)
  self.assertEqual([(x['name'],x['video'])for x in r.json['streams']],list(b.SEEDS));self.assertEqual(sum(x['compulsory']for x in r.json['streams']),1)
  self.assertFalse(r.json['availability_verified']);self.assertNotIn('embed_url',r.text)
  for x in r.json['streams']:self.assertEqual(x['watch_url'],'https://www.youtube.com/watch?v='+x['video'])
 def test_flags_and_pins_before_client(self):
  for env in [dict(SAMPLE,**{b.FLAG:'bad'}),{b.FLAG:'true'}]:
   factory=Mock()
   with self.assertRaises(ValueError):build_public_live_preview(env,client_factory=factory)
   factory.assert_not_called()
  with patch.object(b,'PINS',{'integration/news_api.py':'0'*64}):
   with self.assertRaises(ValueError):self.app()
  with patch.object(b,'SEEDS',(('x','bad'),)):
   with self.assertRaises(ValueError):self.app()
  with patch.object(b,'prepare',wraps=b.prepare),patch.object(b,'seed_rows',side_effect=AssertionError('off seed')):build_public_preview(SAMPLE)
 def test_OFF_base_equal_and_identity(self):
  for name,builder in [('sample',build_public_preview),('live',build_public_live_preview)]:
   ns={};p=Path(__file__).parent/'fixtures'/('brics_base_'+name+'.txt');exec(compile(p.read_text(),str(p),'exec'),ns);old=ns['build_public_preview'if name=='sample'else'build_public_live_preview']
   env=SAMPLE if name=='sample'else dict(LIVE,PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED='false',PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED='false',PUBLIC_NEWS_FULL_PAGES_ENABLED='false')
   a=old(env)if name=='sample'else old(env,client_factory=lambda *a,**k:Client());new=builder(env)if name=='sample'else builder(env,client_factory=lambda *a,**k:Client())
   for path in list(b.PATHS)+['/workspace']:
    for method in ['get','head','post','delete','options']:
     x,y=self.req(a,path,method),self.req(new,path,method);self.assertEqual((x.status_code,x.data,dict(x.headers)),(y.status_code,y.data,dict(y.headers)))
   # create_app generates closure objects each time; exact original code identity
   # and a same-app no-install check prove OFF never wraps/replaces any view.
   for endpoint in ['brics_stream_get','brics_stream_workspace','assets']:self.assertIs(a.view_functions[endpoint].__code__,new.view_functions[endpoint].__code__)
  captured={}
  def capture(*a,**k):
   app=create_app(*a,**k);captured.update(app=app,views=dict(app.view_functions));return app
  with patch('integration.public_preview_builder.create_app',side_effect=capture):app=build_public_preview(SAMPLE)
  for endpoint in ['brics_stream_get','brics_stream_workspace','assets']:self.assertIs(app.view_functions[endpoint],captured['views'][endpoint])
 def test_methods_host_queries_HEAD_no_work(self):
  app=self.app()
  for path in b.PATHS:
   for verb in ['post','delete','options']:self.assertEqual(self.req(app,path,verb).status_code,403)
   for q in ['?x=1','?x=','?x=a&x=b']:self.assertEqual(self.req(app,path+q).status_code,400)
   self.assertEqual(app.test_client().get(path,base_url='https://evil.test').status_code,403)
   with patch.object(Path,'read_text',side_effect=AssertionError('HEAD IO')),patch.object(b,'seed_rows',side_effect=AssertionError('HEAD seed')):
    r=self.req(app,path,'head');self.assertEqual(r.status_code,200);self.assertEqual(r.data,b'')
 def test_headers_allpaths_noAPIframe(self):
  app=self.app()
  for path in b.PATHS:
   r=self.req(app,path);self.assertEqual(r.headers['Cache-Control'],'no-store');self.assertEqual(r.headers['Referrer-Policy'],'no-referrer');self.assertEqual(r.headers['X-Content-Type-Options'],'nosniff')
   if path==b.API:self.assertNotIn('frame-src',r.headers['Content-Security-Policy'])
   else:self.assertIn('frame-src https://www.youtube-nocookie.com;',r.headers['Content-Security-Policy'])
 def test_wrapper_and_header_orders_bothways(self):
  for order in [0,1]:
   app=create_app(authorize=lambda r:True);nav.install_mount(app)
   if order==0:b.install(app);w.install(app,lambda:{'geo':[]})
   else:w.install(app,lambda:{'geo':[]});b.install(app)
   self.assertTrue(nav.mounted(app))
   for name,source in [('weekly.js','public_weekly.js'),('weekly.css','public_weekly.css'),('brics_streams.js','public_brics_streams.js'),('brics_streams.css','public_brics_streams.css')]:
    self.assertEqual(self.req(app,'/workspace/assets/'+name).data,(b.ROOT/'integration/ui'/source).read_bytes())
   self.assertEqual(self.req(app,'/workspace/assets/unknown.js').status_code,404)
   r=self.req(app,'/api/weekly-report.pdf?start=2026-10-01&end=2026-10-05');self.assertNotIn('frame-src',r.headers['Content-Security-Policy'])
   self.assertIn('frame-src https://www.youtube-nocookie.com;',self.req(app,b.PAGE).headers['Content-Security-Policy'])
 def test_mount_and_shell_seam_mutants(self):
  app=create_app(authorize=lambda r:True);app.view_functions['brics_stream_get']=lambda:None
  with self.assertRaises(ValueError):b.install(app)
  app=create_app(authorize=lambda r:True)
  for r in app.url_map.iter_rules():
   if r.endpoint=='brics_stream_get':r.methods.add('POST')
  with self.assertRaises(ValueError):b.install(app)
  with patch.object(Path,'read_text',return_value='wrong'):
   with self.assertRaises(ValueError):b.install(create_app(authorize=lambda r:True))
 def test_python_JS_parity_vector_matrix(self):
  from integration.brics_streams import video_id
  from integration.youtube_links import youtube_watch,supplied_video_watch
  vectors=json.loads((Path(__file__).parent/'fixtures/brics_url_vectors.json').read_text())
  for v in vectors:self.assertEqual(video_id(v['input']),v['public']);self.assertEqual(youtube_watch(v['input']),v['watch_helper']);self.assertEqual(supplied_video_watch(v['input']),v['bare_helper'])
  subprocess.run(['node','tests/brics_public_parity.mjs'],cwd=b.ROOT,check=True)
 def test_combined_flags_realFinder_ready(self):
  client=Client()
  for r in client.store.rows:r.update(title='HS090121;',summary='')
  env=dict(LIVE,**{b.FLAG:'true',w.FLAG:'true',nav.FLAG:'true','PUBLIC_WEATHER_UI_ENABLED':'true'})
  with patch('integration.public_live_builder.ReadOnlyNewsReader',return_value=lambda:{'geo':[]}):app=build_public_live_preview(env,client_factory=lambda *a,**k:client,coverage_binding_provider=lambda:Binding(True,True,True,True,'fixture-owner','fixture-deployment'))
  self.addCleanup(app.extensions['coverage_close']);self.assertEqual(hashlib.sha256((b.ROOT/'integration/news_api.py').read_bytes()).hexdigest(),nav.VIEW_SHA)
  headers={'Origin':ORIGIN,'Sec-Fetch-Site':'same-origin','Sec-Fetch-Mode':'cors','Sec-Fetch-Dest':'empty'}
  r=app.test_client().post('/api/code-news-coverage',base_url=ORIGIN,headers=headers,json={'system':'HS','edition':'2022','code':'090121'});self.assertEqual(r.json['finder_navigation']['state'],'ready')
  for path in [b.API,b.PAGE,'/workspace/weather','/api/weekly-report.pdf?start=2026-10-01&end=2026-10-05']:self.assertEqual(self.req(app,path).status_code,200)

 def test_actual_JS_UI_browser_mutation_gate(self):
  import sys
  subprocess.run([sys.executable,'tests/browser_public_brics.py'],cwd=b.ROOT,check=True,stdout=subprocess.DEVNULL,timeout=90)
