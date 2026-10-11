import hashlib
import io
import unittest
from pathlib import Path
from threading import Thread, Event
from unittest.mock import patch, Mock
from pypdf import PdfReader
from integration import public_weekly_pdf as w
from integration.public_preview_builder import build_public_preview
from integration.public_live_builder import build_public_live_preview
from integration import news_finder_navigation_prep as nav
from tests.test_code_news_coverage_binding_prep import SAMPLE, LIVE, ORIGIN, Client, Binding

PATH=w.PATH+'?start=2026-10-01&end=2026-10-05'
RAW={'geo':[{'title':'Fixture publication','url':'https://example.com/a','published':'2026-10-02T00:00:00Z','summary':'Supplied only','_id':'PRIVATE_SENTINEL','telegram_url':'PRIVATE_SENTINEL'}]}

class Tests(unittest.TestCase):
 def setUp(self):
  with w._RATE_LOCK:w._STARTS.clear()
 def sample(self,**kwargs):return build_public_preview(dict(SAMPLE,**{w.FLAG:'true'},**kwargs))
 def request(self,app,path=PATH,method='get'):return getattr(app.test_client(),method)(path,base_url=ORIGIN)
 def test_sample_no_items_and_public_disclosures(self):
  app=self.sample();r=self.request(app);self.assertEqual(r.status_code,200)
  text=''.join(p.extract_text() for p in PdfReader(io.BytesIO(r.data)).pages)
  self.assertIn('No supplied news items',text);self.assertIn('does not mean nothing happened',' '.join(text.split()))
  h=self.request(app,'/workspace/weekly').text
  for s in ['PUBLIC SUPPLIED NEWS','Latest-100','India time','exclusive','publication','No tariff','?', '10 download starts','not no events']:self.assertIn(s,h)
  self.assertNotIn('PRIVATE STAGING',h);self.assertIn('/workspace/weekly',self.request(app,'/workspace').text)
  self.assertEqual(r.headers['Referrer-Policy'],'no-referrer')
 def test_OFF_base_bytes_and_view_identity(self):
  # Base builders are checked in fixture snapshots added by this unit.
  for name,builder in [('sample',build_public_preview),('live',build_public_live_preview)]:
   namespace={};source=Path(__file__).parent/'fixtures'/('weekly_base_'+name+'.txt');exec(compile(source.read_text(),str(source),'exec'),namespace)
   old=namespace['build_public_preview' if name=='sample'else'build_public_live_preview']
   env=SAMPLE if name=='sample'else dict(LIVE,PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED='false',PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED='false',PUBLIC_NEWS_FULL_PAGES_ENABLED='false')
   def make(fn):return fn(env)if name=='sample'else fn(env,client_factory=lambda *a,**k:Client())
   a,b=make(old),make(builder)
   for path in list(w.PATHS)+['/workspace']:
    for method in ['get','head','post']:
     x,y=self.request(a,path,method),self.request(b,path,method)
     self.assertEqual((x.status_code,x.data,dict(x.headers)),(y.status_code,y.data,dict(y.headers)))
   self.assertEqual(a.view_functions['weekly_download'].__code__,b.view_functions['weekly_download'].__code__)
 def test_flags_before_factory(self):
  for env in [dict(SAMPLE,**{w.FLAG:'yes'}),{w.FLAG:'true'}]:
   factory=Mock()
   with self.assertRaises(ValueError):build_public_live_preview(env,client_factory=factory)
   factory.assert_not_called()
 def test_HEAD_and_validation_no_read_no_admission(self):
  app=self.sample();reader=Mock(side_effect=AssertionError('read'));w.install(app,reader) if False else None
  with patch.object(w,'_admit',side_effect=AssertionError('rate')),patch('integration.weekly_report.build_weekly_report',side_effect=AssertionError('pdf')):
   self.assertEqual(self.request(app,PATH,'head').status_code,200)
   for query in ['','?start=2026-10-01','?start=2026-10-01&end=2026-10-01','?start=2026-02-30&end=2026-03-01','?start=2026-10-01&end=2026-12-01','?start=2026-10-01&end=2026-10-05&x=1','?start=2026-10-01&start=2026-10-01&end=2026-10-05']:
    self.assertEqual(self.request(app,w.PATH+query).status_code,400)
  self.assertEqual(len(w._STARTS),0)
 def test_host_methods_query_range(self):
  app=self.sample();c=app.test_client()
  self.assertEqual(c.get(PATH,base_url='https://wrong.test').status_code,403)
  for verb in ['post','delete','options']:self.assertEqual(self.request(app,PATH,verb).status_code,403)
  self.assertEqual(self.request(app,'/workspace/weekly?x=1').status_code,400)
  r=c.get(PATH,base_url=ORIGIN,headers={'Range':'bytes=0-8'});self.assertEqual(r.status_code,200);self.assertTrue(r.data.startswith(b'%PDF-1.4'))
 def test_rate_rolling_and_global(self):
  self.assertEqual([w._admit(0)for _ in range(10)],[0]*10);self.assertEqual(w._admit(0),60);self.assertEqual(w._admit(59.1),1);self.assertEqual(w._admit(60),0)
  a,b=self.sample(),self.sample()
  with patch.object(w,'_admit',return_value=17),patch.object(w,'_bounded_rows',side_effect=AssertionError('read')):
   for app in [a,b]:
    r=self.request(app);self.assertEqual(r.status_code,429);self.assertEqual(r.headers['Retry-After'],'17')
 def test_exact_one_reader_release_errors_and_output(self):
  from integration.news_api import create_app
  for result in [RAW,None,{'geo':[None]},{'geo':[{}]*101}]:
   reader=Mock(return_value=result);app=create_app(authorize=lambda r:True);w.install(app,reader);r=self.request(app);reader.assert_called_once_with();self.assertEqual(r.status_code,200 if result is RAW else 503)
  for pdf in [b'bad','wrong',b'%PDF-1.4'+b'x'*w.MAX_PDF]:
   reader=Mock(return_value=RAW);app=create_app(authorize=lambda r:True)
   with patch('integration.weekly_report.build_weekly_report',return_value=pdf):w.install(app,reader);self.assertEqual(self.request(app).status_code,503)
  app=self.sample();self.assertEqual(self.request(app).status_code,200)
 def test_public_101_valid_rows_rejected_not_sliced(self):
  from integration.news_api import create_app
  raw={'geo':[dict(RAW['geo'][0],url='https://example.com/'+str(i))for i in range(101)]}
  reader=Mock(return_value=raw);app=create_app(authorize=lambda r:True);w.install(app,reader)
  with patch('integration.weekly_report.build_weekly_report',side_effect=AssertionError('oversize must not render')):
   r=self.request(app);self.assertEqual(r.status_code,503);reader.assert_called_once_with()
 def test_public_score_bounds_HTTP503(self):
  from integration.news_api import create_app
  for score in [float('nan'),float('inf'),float('-inf'),10**13,-10**13]:
   reader=Mock(return_value={'geo':[dict(RAW['geo'][0],score=score)]});app=create_app(authorize=lambda r:True);w.install(app,reader)
   r=self.request(app);self.assertEqual(r.status_code,503);reader.assert_called_once_with()
 def test_public_strict_UTF8_HTTP503(self):
  from integration.news_api import create_app
  reader=Mock(return_value={'geo':[dict(RAW['geo'][0],summary='bad'+chr(0xd800))]});app=create_app(authorize=lambda r:True);w.install(app,reader)
  r=self.request(app);self.assertEqual(r.status_code,503);reader.assert_called_once_with()
 def test_no_store_all_four_feature_paths(self):
  app=self.sample()
  for path in w.PATHS:
   query=PATH if path==w.PATH else path
   for method in ['get','head']:
    r=self.request(app,query,method);self.assertEqual(r.status_code,200);self.assertEqual(r.headers['Cache-Control'],'no-store')
  for code in [400,429,503]:
   if code==400:r=self.request(app,w.PATH)
   elif code==429:
    with patch.object(w,'_admit',return_value=60):r=self.request(app)
   else:
    with patch.object(w,'_bounded_rows',side_effect=ValueError()):r=self.request(app)
   self.assertEqual(r.status_code,code);self.assertEqual(r.headers['Cache-Control'],'no-store')
 def test_hostile_values_no_stringification(self):
  class Evil:
   def __str__(self):raise AssertionError('str')
  for key,value in [('title','x'*2049),('summary','x'*8001),('title',Evil()),('score',{}),('score',True),('published','not-a-date'),('url','javascript:alert(1)'),('url','http://example.com/a'),('source',{})]:
   row=dict(RAW['geo'][0],**{key:value})
   with self.assertRaises((ValueError,UnicodeError)):w._bounded_rows({'geo':[row]})
  rows=w._bounded_rows(RAW);self.assertNotIn('PRIVATE_SENTINEL',repr(rows))
 def test_PDF_safe_actions_and_link_caps(self):
  from integration.weekly_report import build_weekly_report
  from datetime import datetime,timezone
  rows=w._bounded_rows({'geo':[dict(RAW['geo'][0],url='https://example.com/'+str(i)) for i in range(100)]})
  pdf=build_weekly_report(rows,[],period_start=datetime(2026,10,1,tzinfo=timezone.utc),period_end=datetime(2026,10,5,tzinfo=timezone.utc),generated_at=datetime(2026,10,6,tzinfo=timezone.utc))
  for bad in [b'/JavaScript',b'/Launch',b'PRIVATE_SENTINEL',b'/URI (http:',b'/URI (javascript:']:self.assertNotIn(bad,pdf)
  reader=PdfReader(io.BytesIO(pdf));ann=[a.get_object()for p in reader.pages for a in p.get('/Annots',[])];self.assertLessEqual(len(ann),25)
  for a in ann:self.assertTrue(a['/A']['/URI'].startswith('https://'));self.assertLessEqual(len(a['/A']['/URI']),500)
 def test_shared_slots_two_apps_and_release(self):
  from integration.news_api import create_app
  entered=Event();release=Event();lock=w.Lock();calls=[];readers=[]
  def build(*a,**kw):
   with lock:
    calls.append(1)
    if len(calls)==2:entered.set()
   release.wait(5);return b'%PDF-1.4'
  apps=[]
  with patch('integration.weekly_report.build_weekly_report',side_effect=build):
   for _ in range(3):
    reader=Mock(return_value=RAW);readers.append(reader);app=create_app(authorize=lambda r:True);w.install(app,reader);apps.append(app)
   ts=[Thread(target=lambda app=app:self.request(app))for app in apps[:2]]
   for t in ts:t.start()
   try:self.assertTrue(entered.wait(3));self.assertEqual(self.request(apps[2]).status_code,429);readers[2].assert_not_called()
   finally:
    release.set()
    for t in ts:t.join()
  self.assertEqual(self.request(apps[2]).status_code,200)
 def test_mount_drift_seam_pin_and_OFF(self):
  from integration.news_api import create_app
  app=create_app(authorize=lambda r:True);app.view_functions['weekly_download']=lambda:None
  with self.assertRaises(ValueError):w.install(app,Mock())
  app=create_app(authorize=lambda r:True)
  for rule in app.url_map.iter_rules():
   if rule.endpoint=='weekly_download':rule.methods.add('POST')
  with self.assertRaises(ValueError):w.install(app,Mock())
  with patch.object(w,'PINS',{'integration/news_api.py':'0'*64}):
   with self.assertRaises(ValueError):self.sample()
  with patch.object(w,'verify_pins',side_effect=AssertionError('off pins')):build_public_preview(SAMPLE)
  with patch.object(w.Path,'read_text',return_value='PRIVATE STAGING PRIVATE STAGING'):
   with self.assertRaises(ValueError):w.install(create_app(authorize=lambda r:True),Mock())
 def test_combined_real_pins_Finder_coverage_weather(self):
  client=Client()
  for r in client.store.rows:r.update(title='HS090121;',summary='')
  env=dict(LIVE,**{w.FLAG:'true',nav.FLAG:'true','PUBLIC_WEATHER_UI_ENABLED':'true','PUBLIC_WEATHER_ENABLED':'true','OPEN_METEO_TERMS_ACK':'2026-10-11/noncommercial','PUBLIC_WEATHER_NONCOMMERCIAL':'true','PUBLIC_WEATHER_CAPACITY_REVIEWED':'true','PUBLIC_WEATHER_SINGLE_WORKER_VERIFIED':'true'})
  with patch('integration.public_live_builder.ReadOnlyNewsReader',return_value=lambda:RAW):
   app=build_public_live_preview(env,client_factory=lambda *a,**k:client,coverage_binding_provider=lambda:Binding(True,True,True,True,'fixture-owner','fixture-deployment'))
  self.addCleanup(app.extensions['coverage_close'])
  self.assertEqual(hashlib.sha256((w.ROOT/'integration/news_api.py').read_bytes()).hexdigest(),nav.VIEW_SHA)
  self.assertTrue(nav.mounted(app))
  h={'Origin':ORIGIN,'Sec-Fetch-Site':'same-origin','Sec-Fetch-Mode':'cors','Sec-Fetch-Dest':'empty'}
  r=app.test_client().post('/api/code-news-coverage',base_url=ORIGIN,json={'system':'HS','edition':'2022','code':'090121'},headers=h)
  self.assertEqual(r.status_code,200);self.assertEqual(r.json['finder_navigation']['state'],'ready')
  self.assertEqual(self.request(app,'/workspace/weather').status_code,200);self.assertEqual(self.request(app).status_code,200)
