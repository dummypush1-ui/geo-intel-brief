import unittest,hashlib
from pathlib import Path
from unittest.mock import patch,Mock
from integration import relationship_navigation as n
from integration.public_preview_builder import build_public_preview
from tests.test_code_news_public import env

class Tests(unittest.TestCase):
 def app(self):
  e=dict(env(True),**{n.FLAG:'true'});a=build_public_preview(e)
  from integration.code_news_links import Links
  from tests.test_code_news_public import CAT
  a.extensions['code_news_public'].model=Links(CAT,[])
  a.extensions['code_news_public'].reader=lambda:{'geo':[{'url':'https://example.com/one','title':'HS 100630 tariff news'}]}
  return a
 def test_asset_mount_and_private_paths_removed(self):
  a=self.app();c=a.test_client();js=c.get('/workspace/assets/workspace.js',base_url='https://preview.example').text
  self.assertIn('attachReportedCodes',js);self.assertIn('manualFinderContext',js)
  for path in ['/api/related-news','/api/finder-context']:
   self.assertNotIn(path,js);self.assertIn(c.post(path,base_url='https://preview.example').status_code,(403,404))
  r=c.get(n.ASSET,base_url='https://preview.example');self.assertEqual(r.status_code,200);self.assertEqual(r.headers['Cache-Control'],'no-store');self.assertEqual(r.headers['Referrer-Policy'],'no-referrer')
  self.assertIn('/workspace/code-news',c.get('/workspace',base_url='https://preview.example').text)
 def test_each_seam_mutant_fails(self):
  raw=(n.ROOT/'integration/ui/workspace.js').read_text()
  for seam in ["    if(article.article_key && ['geo','brics'].includes(article.project)) {",'    container.append(row);','async function syncContext() {',"frame.addEventListener('load', () => {"]:
   with self.assertRaises(ValueError):n.transform(raw.replace(seam,'',1))
 def test_pin_and_dependencies_before_client(self):
  for name in n.PINS:
   with patch.object(n,'PINS',dict(n.PINS,**{name:'0'*64})),self.assertRaises(ValueError):self.app()
  for env0 in [{n.FLAG:'yes'},{n.FLAG:'true'}]:
   with self.assertRaises(ValueError):n.prepare(env0)
 def test_off_exact_bytes(self):
  namespace={};path=Path(__file__).parent/'fixtures'/'relationship_base_sample.txt';exec(compile(path.read_text(),str(path),'exec'),namespace)
  old=namespace['build_public_preview'](env(True));new=build_public_preview(env(True))
  for path in ['/workspace','/workspace/assets/workspace.js','/workspace/countries','/workspace/map','/workspace/code-news']:
   a=old.test_client().get(path,base_url='https://preview.example');b=new.test_client().get(path,base_url='https://preview.example')
   self.assertEqual((a.status_code,a.data,dict(a.headers)),(b.status_code,b.data,dict(b.headers)))
 def test_combined_flags_live_mounts_headers(self):
  from integration.public_live_builder import build_public_live_preview
  from tests.test_code_news_coverage_binding_prep import LIVE,Client,ORIGIN
  e=dict(LIVE,PUBLIC_CODE_NEWS_ENABLED='true',PUBLIC_CODE_NEWS_SCOPE_REVIEWED='true',PUBLIC_AI_ANSWERS_ENABLED='true',PUBLIC_WEEKLY_PDF_ENABLED='true',PUBLIC_WEEKLY_FULL_STORE_ENABLED='true',PUBLIC_NEWS_FULL_PAGES_ENABLED='true',PUBLIC_BRICS_STREAMS_ENABLED='true',PUBLIC_WEATHER_UI_ENABLED='true',PUBLIC_WEATHER_ENABLED='true',OPEN_METEO_TERMS_ACK='2026-10-11/noncommercial',PUBLIC_WEATHER_NONCOMMERCIAL='true',PUBLIC_WEATHER_CAPACITY_REVIEWED='true',PUBLIC_WEATHER_SINGLE_WORKER_VERIFIED='true',PUBLIC_MAP_ENABLED='true',PUBLIC_MAP_M2_ENABLED='true',PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED='false',PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED='false',**{n.FLAG:'true'})
  client=Client();app=build_public_live_preview(e,client_factory=lambda *a,**k:client);self.addCleanup(app.extensions['whole_news_pages'].close)
  for path in ['/workspace','/workspace/weather','/workspace/ai-answers','/workspace/weekly','/workspace/countries','/workspace/map','/workspace/brics-streams','/workspace/code-news']:
   r=app.test_client().get(path,base_url=ORIGIN);self.assertEqual(r.status_code,200,path);self.assertIn('Content-Security-Policy',r.headers)
  self.assertTrue(app.extensions['public_weekly_full_store']);self.assertTrue(app.extensions['relationship_navigation'])
  js=app.test_client().get('/workspace/assets/workspace.js',base_url=ORIGIN).text;self.assertIn('attachReportedCodes',js);self.assertNotIn('/api/related-news',js)
  for path in ['/api/related-news','/api/finder-context']:
   self.assertIn(app.test_client().post(path,base_url=ORIGIN).status_code,(403,404))
 def test_shell_ON_only_nav_diff_and_OFF_equal(self):
  from tests.test_code_news_coverage_binding_prep import SAMPLE
  flags=dict(PUBLIC_CODE_NEWS_ENABLED='true',PUBLIC_CODE_NEWS_SCOPE_REVIEWED='true',PUBLIC_AI_ANSWERS_ENABLED='true',PUBLIC_WEEKLY_PDF_ENABLED='true',PUBLIC_BRICS_STREAMS_ENABLED='true',PUBLIC_WEATHER_UI_ENABLED='true',PUBLIC_MAP_ENABLED='true',PUBLIC_MAP_M2_ENABLED='true')
  a=build_public_preview(dict(SAMPLE,**flags));b=build_public_preview(dict(SAMPLE,**flags,**{n.FLAG:'true'}))
  for path in list(n.SHELLS)+['/workspace/map']:
   x=a.test_client().get(path,base_url=SAMPLE['PREVIEW_ORIGIN']);y=b.test_client().get(path,base_url=SAMPLE['PREVIEW_ORIGIN'])
   self.assertEqual(x.status_code,200,path);self.assertEqual(y.status_code,200,path)
   self.assertEqual(y.text.replace('<a href="/workspace/code-news">Reported code-news</a>','',1),x.text,path)
  with patch.object(n,'PINS',dict(n.PINS,**{'integration/ui/countries.html':'0'*64})),self.assertRaises(ValueError):build_public_preview(dict(SAMPLE,**flags,**{n.FLAG:'true'}))
 def test_mounted_requirement_and_private_path_mutant(self):
  from integration.news_api import create_app
  a=create_app(authorize=lambda _:True)
  with self.assertRaises(ValueError):n.install(a,'https://preview.example')
  raw=(n.ROOT/'integration/ui/workspace.js').read_text()
  self.assertNotIn('/api/finder-context',n.transform(raw));self.assertNotIn('/api/related-news',n.transform(raw))
  with self.assertRaises(ValueError):n.transform(raw+'\nfetch("/api/related-news");')
 def test_coverage_link_mounted_at_request_time(self):
  a=self.app();c=a.test_client();url='https://preview.example'
  self.assertNotIn('Whole-store code coverage',c.get('/workspace',base_url=url).text)
  a.extensions['code_news_coverage_broker']=object()
  self.assertIn('Whole-store code coverage',c.get('/workspace',base_url=url).text)
  a.extensions.pop('code_news_coverage_broker')
  self.assertNotIn('Whole-store code coverage',c.get('/workspace',base_url=url).text)


 def test_late_shell_seam_refuses_render(self):
  from flask import Response
  a=self.app();hook=next(h for h in a.after_request_funcs[None] if h.__name__=='served_copy' and h.__module__==n.__name__)
  with a.test_request_context('/workspace/countries',base_url='https://preview.example'),self.assertRaises(ValueError):hook(Response('<html>drift</html>',mimetype='text/html'))
 def test_fake_finder_mount_refused(self):
  from integration.news_api import create_app
  from integration.news_finder_navigation_prep import install_mount,MARKER
  from integration.code_news_public import install as ci
  a=create_app(authorize=lambda _:True);ci(a,'https://preview.example',lambda:{'geo':[]});install_mount(a)
  a.extensions[MARKER]=object()
  with self.assertRaises(ValueError):n.install(a,'https://preview.example')
 def test_private_sources_unchanged(self):
  import subprocess
  for path in ['integration/news_api.py','integration/ui/workspace.js']:
   old=subprocess.check_output(['git','show','80cb330c36b4e1635dd5debae242f03930f3f02f:'+path])
   self.assertEqual((n.ROOT/path).read_bytes(),old)
 def test_startup_workspace_seam_before_factory(self):
  from integration.public_live_builder import build_public_live_preview
  from tests.test_code_news_coverage_binding_prep import LIVE
  original=Path.read_text
  def read(p,*a,**k):return '<html></html>' if p==n.ROOT/'integration/ui/workspace.html' else original(p,*a,**k)
  factory=Mock(side_effect=AssertionError('Client must not start'))
  with patch.object(Path,'read_text',read),self.assertRaises(ValueError):build_public_live_preview(dict(LIVE,PUBLIC_CODE_NEWS_ENABLED='true',**{n.FLAG:'true'}),client_factory=factory)
  factory.assert_not_called()
 def test_transformed_GET_HEAD_lengths_headers(self):
  a=self.app();c=a.test_client();url='https://preview.example'
  for path in ['/workspace','/workspace/assets/workspace.js',n.ASSET,'/workspace/countries','/workspace/code-news']:
   get=c.get(path,base_url=url);head=c.head(path,base_url=url)
   self.assertEqual(get.status_code,200,path);self.assertEqual(head.status_code,200,path)
   self.assertEqual(int(get.headers['Content-Length']),len(get.data));self.assertEqual(head.data,b'')
   if path in [n.ASSET,'/workspace/assets/workspace.js']:self.assertEqual(int(head.headers['Content-Length']),len(get.data))
   else:self.assertNotIn('Content-Length',head.headers)
   for r in [get,head]:self.assertEqual(r.headers['Cache-Control'],'no-store');self.assertEqual(r.headers['X-Content-Type-Options'],'nosniff')
   for h in ['Content-Security-Policy','Referrer-Policy']:self.assertEqual(get.headers[h],head.headers[h])
 def test_all_nav_shell_policies_unchanged(self):
  from tests.test_code_news_coverage_binding_prep import SAMPLE
  flags=dict(PUBLIC_CODE_NEWS_ENABLED='true',PUBLIC_CODE_NEWS_SCOPE_REVIEWED='true',PUBLIC_AI_ANSWERS_ENABLED='true',PUBLIC_WEEKLY_PDF_ENABLED='true',PUBLIC_BRICS_STREAMS_ENABLED='true',PUBLIC_WEATHER_UI_ENABLED='true',PUBLIC_MAP_ENABLED='true',PUBLIC_MAP_M2_ENABLED='true')
  a=build_public_preview(dict(SAMPLE,**flags));b=build_public_preview(dict(SAMPLE,**flags,**{n.FLAG:'true'}))
  for path in list(n.SHELLS)+['/workspace/map','/workspace','/workspace/assets/workspace.js']:
   for method in ['get','head']:
    x=getattr(a.test_client(),method)(path,base_url=SAMPLE['PREVIEW_ORIGIN']);y=getattr(b.test_client(),method)(path,base_url=SAMPLE['PREVIEW_ORIGIN'])
    for h in ['Cache-Control','Referrer-Policy','X-Content-Type-Options','Content-Security-Policy']:self.assertEqual(x.headers.get(h),y.headers.get(h),(path,method,h))
 def test_quota_copy_matches_broker_behavior(self):
  from integration.code_news_public import Service
  s=Service('.',lambda:{'geo':[]},model=object(),clock=lambda:100)
  js=(n.ROOT/'integration/ui/relationship_navigation.js').read_text()
  for i in range(10):self.assertEqual(s.run(lambda _:({},200))[1],200)
  self.assertEqual(s.run(lambda _:({},200)),({'state':'rate_limited'},429))
  self.assertIn('10 manual requests per minute per process, across all visitors',js)
 def test_editions_match_mounted_catalogue_and_geo_copy(self):
  from integration.news_finder_navigation_prep import EDITIONS
  js=(n.ROOT/'integration/ui/relationship_navigation.js').read_text()
  for system,edition in EDITIONS.items():self.assertIn(system+":'"+edition+"'",js)
  app=self.app();model=app.extensions['code_news_public'].model
  self.assertEqual(model.resolve('100630','HS',EDITIONS['HS'])['state'],'resolved')
  self.assertIn('BRICS rows have no relationship button',app.test_client().get('/workspace',base_url='https://preview.example').text)
