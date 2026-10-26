import unittest,json,csv,io,hashlib,subprocess,tempfile,shutil
from pathlib import Path
from unittest.mock import patch,Mock
from flask import Flask
from werkzeug.test import EnvironBuilder
from integration import news_export_e2 as m
from integration.news_export.original_contract import GEO_FIELDS
from tests.test_geo_snapshot import Client,row,R
from tests.test_code_news_coverage_binding_prep import SAMPLE,LIVE,ORIGIN,Client as ReadClient
from integration.public_live_builder import build_public_live_preview
from integration.public_preview_builder import build_public_preview
ENV={**LIVE,'PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED':'false','PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED':'false',m.FLAG:'true'}
class Tests(unittest.TestCase):
 def binding(self,c=None):return m.SourceBinding(c or Client([]),dict(R),GEO_FIELDS)
 def app(self,c=None):
  a=Flask('e2');m.install(a,ORIGIN,self.binding(c));self.addCleanup(a.extensions['geo_original_export_close']);return a
 def test_flag_and_disclosure_gates_before_effects(self):
  self.assertIsNone(m.prepare({}));self.assertIsNone(m.prepare({m.FLAG:'false'}))
  c=Client([]);b=self.binding(c)
  for v in ('TRUE','yes','1',''):
   with self.assertRaises(ValueError):m.prepare({m.FLAG:v},b)
  for k in m.DEPENDENCIES:
   with self.assertRaises(ValueError):m.prepare({**ENV,k:'false'},b)
  self.assertEqual(c.sessions,[])
  with self.assertRaises(ValueError):m.prepare({},b)
  with self.assertRaises(ValueError):m.prepare(ENV)
  with self.assertRaises(ValueError):m.prepare(ENV,m.SourceBinding(c,R,('title',)))
  for k in R:
   r=dict(R);del r[k]
   with self.assertRaises(ValueError):m.prepare(ENV,m.SourceBinding(c,r,GEO_FIELDS))
  self.assertEqual(c.sessions,[]);self.assertIsNot(m.prepare(ENV,b).review,b.review)
 def test_guard_headers_head_and_validation_no_io(self):
  c=Client([]);a=self.app(c);t=a.test_client()
  for path in [m.PATH,m.PATH+'?category=ENERGY']:
   r=t.head(path,base_url=ORIGIN);self.assertEqual(r.status_code,200);self.assertEqual(r.data,b'');self.assertNotIn('Content-Length',r.headers);self.assertEqual(r.headers['X-Export-Readiness'],'metadata-only-not-source-readiness')
  self.assertEqual(c.sessions,[])
  for path in [m.PATH+'?q=x',m.PATH+'?category=x&category=y',m.PATH+'?_method=GET']:
   self.assertEqual(t.get(path,base_url=ORIGIN).status_code,400)
  self.assertEqual(c.sessions,[])
  for verb in ['post','delete','options','put']:
   self.assertEqual(getattr(t,verb)(m.PATH,base_url=ORIGIN).status_code,403)
  self.assertEqual(t.get(m.PATH,base_url='https://evil.test').status_code,403)
  r=t.get(m.PATH,base_url=ORIGIN,headers={'Range':'bytes=0-5','If-None-Match':'*','X-HTTP-Method-Override':'GET'});self.assertEqual(r.status_code,400)
  for k,v in [('Referrer-Policy','no-referrer'),('X-Content-Type-Options','nosniff'),('Content-Security-Policy',"default-src 'none'; frame-ancestors 'none'")]:self.assertEqual(r.headers[k],v)
  self.assertIn('no-store',r.headers['Cache-Control']);self.assertNotIn('ETag',r.headers);self.assertNotIn('Accept-Ranges',r.headers)
 def test_501_original_rows_complete_digest_no_private(self):
  c=Client([dict(row(n),category='ENERGY',secret='PRIVATE')for n in range(501,0,-1)]);r=self.app(c).test_client().get(m.PATH,base_url=ORIGIN)
  self.assertEqual(r.status_code,200);data=r.data;records=list(csv.reader(io.StringIO(data.decode(),newline='')))
  self.assertEqual(tuple(records[0]),GEO_FIELDS);self.assertEqual(len(records),503);self.assertEqual(records[-1][0],'EXPORT_COMPLETE');self.assertEqual(records[-1][2:4],['501','501']);self.assertNotIn(b'PRIVATE',data)
  footer=data.rsplit(b'EXPORT_COMPLETE,',1);self.assertEqual(records[-1][4],hashlib.sha256(footer[0]).hexdigest());self.assertEqual(c.session.ends,1);self.assertEqual(len(c.finds),3);self.assertTrue(all(x.closed for x in c.cursors))
 def test_head_busy_unstarted_close_crossapp_admission(self):
  c=Client([row(2),row(1)]);a=self.app(c);t=a.test_client();r=t.get(m.PATH,base_url=ORIGIN,buffered=False)
  second=self.app().test_client();self.assertEqual(second.get(m.PATH,base_url=ORIGIN).status_code,429);self.assertEqual(t.head(m.PATH,base_url=ORIGIN).status_code,200)
  r.close();r.close();self.assertEqual(c.session.ends,1);self.assertEqual(second.get(m.PATH,base_url=ORIGIN,buffered=True).status_code,200)
  env=EnvironBuilder(path=m.PATH,base_url=ORIGIN).get_environ();it=a.wsgi_app(env,lambda *x:None);it.close();self.assertEqual(second.get(m.PATH,base_url=ORIGIN,buffered=True).status_code,200)
 def test_start_response_failure_releases_and_redacts(self):
  c=Client([row(1)]);a=self.app(c);env=EnvironBuilder(path=m.PATH,base_url=ORIGIN).get_environ()
  def fail(*a):raise RuntimeError('transport failed')
  with self.assertRaises(RuntimeError):a.wsgi_app(env,fail)
  self.assertEqual(c.session.ends,1);self.assertEqual(self.app().test_client().get(m.PATH,base_url=ORIGIN,buffered=True).status_code,200)
  bad=Client([],True);r=self.app(bad).test_client().get(m.PATH,base_url=ORIGIN);self.assertEqual(r.status_code,503);self.assertNotIn('secret',r.text);self.assertEqual(bad.session.ends,1)
 def test_late_error_not_claimed_complete(self):
  class Late(Client):
   def find(self,*a,**k):
    c=super().find(*a,**k)
    if len(self.finds)==3:c.fail=True
    return c
  c=Late([row(n)for n in range(501,0,-1)]);r=self.app(c).test_client().get(m.PATH,base_url=ORIGIN);self.assertIn(b'EXPORT_INCOMPLETE,source unavailable',r.data);self.assertNotIn(b'EXPORT_COMPLETE',r.data);self.assertEqual(c.session.ends,1)
 def test_shutdown_session_and_collision(self):
  c=Client([row(1)]);a=self.app(c);r=a.test_client().get(m.PATH,base_url=ORIGIN,buffered=False);a.extensions['geo_original_export_close']();a.extensions['geo_original_export_close']();r.close();self.assertEqual(c.session.ends,1);self.assertEqual(a.test_client().get(m.PATH,base_url=ORIGIN).status_code,503)
  with self.assertRaises(ValueError):m.install(a,ORIGIN,self.binding())
 def test_builder_gates_and_explicit_mount(self):
  f=Mock()
  with self.assertRaises(ValueError):build_public_live_preview(ENV,client_factory=f)
  f.assert_not_called()
  with self.assertRaises(ValueError):build_public_preview({**SAMPLE,m.FLAG:'true'})
  c=Client([row(1)]);a=build_public_live_preview(ENV,client_factory=lambda *a,**k:ReadClient(),geo_export_binding=self.binding(c));self.addCleanup(a.extensions['geo_original_export_close']);self.addCleanup(a.extensions['whole_news_pages'].close);self.assertEqual(c.sessions,[])
  r=a.test_client().get(m.PATH,base_url=ORIGIN);self.assertEqual(r.status_code,200);self.assertIn(b'News1',r.data)
 def test_off_parity_against_frozen_builders(self):
  root=Path(__file__).resolve().parents[1]
  for name,builder,env in [('preview',build_public_preview,SAMPLE),('live',build_public_live_preview,{**LIVE,'PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED':'false','PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED':'false'})]:
   ns={'__file__':str(root/'integration'/('public_'+name+'_builder.py'))};text=(root/'tests/fixtures'/('context_d4_base_live.txt' if name=='live' else 'export_e2_base_'+name+'.txt')).read_text();exec(compile(text,ns['__file__'],'exec'),ns);old=ns['build_public_preview'if name=='preview'else'build_public_live_preview'];make=lambda b:b(env)if name=='preview'else b(env,client_factory=lambda *a,**k:ReadClient())
   a,b=make(old),make(builder);self.addCleanup(a.extensions['whole_news_pages'].close)if name=='live'else None;self.addCleanup(b.extensions['whole_news_pages'].close)if name=='live'else None
   for path in ['/workspace','/api/news-export.csv',m.PATH,'/api/export-full.csv']:
    for verb in ['get','head','options','post']:
     x,y=getattr(a.test_client(),verb)(path,base_url=ORIGIN),getattr(b.test_client(),verb)(path,base_url=ORIGIN)
     self.assertEqual((x.status_code,x.data,dict(x.headers)),(y.status_code,y.data,dict(y.headers)))
if __name__=='__main__':unittest.main()

class LifecycleFailures(unittest.TestCase):
 def test_after_request_failure_cleans_transferred_stream(self):
  c=Client([row(1)]);a=Flask('e2-fault');m.install(a,ORIGIN,m.SourceBinding(c,R,GEO_FIELDS));self.addCleanup(a.extensions['geo_original_export_close'])
  @a.after_request
  def broken(response):
   if response.status_code==200:raise RuntimeError('private hook')
   return response
  r=a.test_client().get(m.PATH,base_url=ORIGIN);self.assertEqual(r.status_code,500);self.assertEqual(c.session.ends,1)
  other=Flask('e2-other');m.install(other,ORIGIN,m.SourceBinding(Client([]),R,GEO_FIELDS));self.addCleanup(other.extensions['geo_original_export_close']);self.assertEqual(other.test_client().get(m.PATH,base_url=ORIGIN,buffered=True).status_code,200)

class MoreSafety(unittest.TestCase):
 def test_source_pin_drift_before_client_factory(self):
  factory=Mock();original=Path.read_bytes
  def read(p):return b'drift'if str(p).endswith('news_export/geo_snapshot.py')else original(p)
  with patch.object(Path,'read_bytes',read):
   with self.assertRaisesRegex(ValueError,'source drift'):build_public_live_preview(ENV,client_factory=factory,geo_export_binding=m.SourceBinding(Client([]),R,GEO_FIELDS))
  factory.assert_not_called()
 def test_binding_copy_and_category_filter_not_search(self):
  review=dict(R);c=Client([dict(row(3),category='FOOD'),dict(row(2),category='ENERGY'),dict(row(1),category='ENERGY')]);a=Flask('e2-copy');m.install(a,ORIGIN,m.SourceBinding(c,review,GEO_FIELDS));self.addCleanup(a.extensions['geo_original_export_close']);review['mapping']=('other','private')
  r=a.test_client().get(m.PATH+'?category=ENERGY',base_url=ORIGIN,buffered=True);self.assertEqual(r.status_code,200);data=r.data;self.assertIn(b'News2',data);self.assertNotIn(b'News3',data);records=list(csv.reader(io.StringIO(data.decode(),newline='')));self.assertEqual(records[-1][2:4],['2','3'])
 def test_no_source_constructor_io_and_no_raw_client_close(self):
  class Poison:
   def __getattr__(self,k):raise AssertionError('unexpected client effect')
  a=Flask('e2-poison');m.install(a,ORIGIN,m.SourceBinding(Poison(),R,GEO_FIELDS));self.assertEqual(a.test_client().head(m.PATH,base_url=ORIGIN).status_code,200);a.extensions['geo_original_export_close']()
 def test_cancel_before_header_releases(self):
  a=Flask('e2-cancel');m.install(a,ORIGIN,m.SourceBinding(Client([]),R,GEO_FIELDS));self.addCleanup(a.extensions['geo_original_export_close']);a.testing=True
  with patch.object(m,'create_geo_original_stream',side_effect=KeyboardInterrupt()):
   with self.assertRaises(KeyboardInterrupt):a.test_client().get(m.PATH,base_url=ORIGIN)
  r=a.test_client().get(m.PATH,base_url=ORIGIN,buffered=True);self.assertEqual(r.status_code,200)

class ReviewerChecks(unittest.TestCase):
 def binding(self,review=None,client=None):return m.SourceBinding(Client([])if client is None else client,dict(R)if review is None else review,GEO_FIELDS)
 def test_flag_full_dependencies_and_exact_source_review(self):
  for v in ('TRUE','yes','1',''):
   with self.assertRaises(ValueError):m.prepare({**ENV,m.FLAG:v},self.binding())
  variants=[{**R,'extra':True},{**R,'mapping':('other','articles')}]+[{**R,k:False}for k in ('read_only','snapshot_supported','index_explain_verified')]
  for review in variants:
   with self.assertRaises(ValueError):m.prepare(ENV,self.binding(review))
  with self.assertRaises(ValueError):m.prepare(ENV,m.SourceBinding(None,dict(R),GEO_FIELDS))
 def test_pin_keyset_extra_missing(self):
  original=json.loads((m.ROOT/'integration/news_export_e2/pins.json').read_text())
  for pins in [{**original,'extra': 'a'*64},{k:v for k,v in original.items()if not k.endswith('/export.py')}]:
   with patch.object(m.json,'loads',return_value=pins):
    with self.assertRaisesRegex(ValueError,'Exact export source pins'):m.prepare(ENV,self.binding())
 def test_next_exception_closes_frees_slot(self):
  class Broken:
   def __init__(self):self.closes=0
   def __next__(self):raise RuntimeError('source failure')
   def close(self):self.closes+=1
  a=Flask('next-failure');m.install(a,ORIGIN,self.binding());self.addCleanup(a.extensions['geo_original_export_close']);a.testing=True;b=Broken()
  with patch.object(m,'create_geo_original_stream',return_value=b):
   with self.assertRaises(RuntimeError):a.test_client().get(m.PATH,base_url=ORIGIN)
  self.assertEqual(b.closes,1);self.assertEqual(a.test_client().get(m.PATH,base_url=ORIGIN,buffered=True).status_code,200)
 def test_success_headers_final_after_hook(self):
  a=Flask('headers')
  @a.after_request
  def before(r):r.headers['Cache-Control']='public';r.headers['Content-Security-Policy']='bad-before';r.headers['ETag']='x';r.headers['Last-Modified']='x';r.headers['Accept-Ranges']='bytes';return r
  m.install(a,ORIGIN,self.binding());self.addCleanup(a.extensions['geo_original_export_close'])
  @a.after_request
  def after(r):r.headers['Cache-Control']='public-after';r.headers['Content-Security-Policy']='bad-after';return r
  r=a.test_client().get(m.PATH,base_url=ORIGIN,buffered=True);self.assertEqual(r.status_code,200)
  self.assertEqual(r.headers['Cache-Control'],'private, no-store, max-age=0');self.assertEqual(r.headers['Content-Security-Policy'],"default-src 'none'; frame-ancestors 'none'")
  for k in ('ETag','Accept-Ranges','Last-Modified'):self.assertNotIn(k,r.headers)
