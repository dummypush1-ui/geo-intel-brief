import unittest
from werkzeug.test import Client
from werkzeug.wrappers import Response
from integration.accounts import AccountService,MemoryStore,Hasher
from integration.accounts.merged_fixture import create_merged_fixture,FixtureNews
from integration.accounts.service import COOKIE_NAME,SESSION_ABS
O='https://fixture.example';PASSWORD='correct horse battery'
class Tests(unittest.TestCase):
 def setUp(self):
  self.now=1800000000;self.store=MemoryStore();self.svc=AccountService(self.store,b'x'*48,lambda:self.now,hasher=Hasher(n=1024),signup_mode='closed',allowed_origins=[O]);self.store.create_account('alice',{'uid':'uidfixture','password':self.svc.hasher.hash(PASSWORD),'pwv':1,'created':self.now},None,50)
  self.app=create_merged_fixture(self.svc,origin=O,client_identity=lambda r:'fixture-client',reader=FixtureNews([]));self.c=Client(self.app,Response)
 def get(self,p,**kw):return self.c.get(p,base_url=O,**kw)
 def post(self,a,d,origin=O):return self.c.post('/account/'+a,base_url=O,headers={'Origin':origin},json=d)
 def login(self):
  csrf=self.get('/account/preauth').json['csrf'];r=self.post('login',{'username':'alice','password':PASSWORD,'csrf':csrf});self.assertEqual(r.status_code,200);return r.json['csrf']
 def test_login_workspace_assets_api_and_signup_closed(self):
  for p in ['/workspace','/api/news','/api/weekly-report.pdf','/workspace/assets/workspace.js']:self.assertEqual(self.get(p).status_code,403)
  csrf=self.get('/account/preauth').json['csrf'];self.assertFalse(self.post('signup',{'username':'bob','password':PASSWORD,'invite':'','csrf':csrf}).json['ok'])
  self.login();r=self.get('/workspace');self.assertEqual(r.status_code,200);r.close();self.assertEqual(self.get('/api/news').status_code,200)
 def test_logout_replay_and_expiry(self):
  csrf=self.login();cookie=self.c.get_cookie(COOKIE_NAME,domain='fixture.example').value;self.assertEqual(self.post('logout',{'csrf':csrf}).status_code,200);self.c.set_cookie(COOKIE_NAME,cookie,domain='fixture.example');self.assertEqual(self.get('/workspace').status_code,403)
  self.login();self.now+=SESSION_ABS+1;self.assertEqual(self.get('/api/news').status_code,403)
 def test_methods_aliases_prefixes_and_cross_origin(self):
  csrf=self.login()
  for p in ['/workspace-evil','/workspace/../workspace','/workspace//map','/api/%6eews','/account/login/evil']:
   self.assertIn(self.get(p).status_code,[403,404])
  for method in ['POST','HEAD','OPTIONS','DELETE']:self.assertEqual(self.c.open('/workspace',method=method,base_url=O).status_code,403)
  self.assertEqual(self.post('logout',{'csrf':csrf},'https://evil.example').status_code,403)
 def test_delete_fences_and_no_old_preview_cookie(self):
  self.c.set_cookie('__Host-merged-preview','fake',domain='fixture.example');self.assertEqual(self.get('/workspace').status_code,403)
  csrf=self.login();self.assertEqual(self.post('delete',{'csrf':csrf,'password':PASSWORD}).status_code,200);self.assertEqual(self.get('/workspace').status_code,403)
  from integration.news_api import create_app
  old=Client(create_app(),Response);self.assertEqual(old.get('/workspace',base_url=O,headers={'Cookie':COOKIE_NAME+'=anything'}).status_code,403)
 def test_factory_negative_no_effects_and_forwarded_client(self):
  calls=[]
  for reader in [lambda: calls.append(1),object(),None]:
   with self.assertRaises(ValueError):create_merged_fixture(self.svc,origin=O,client_identity=lambda r:'x',reader=reader)
  self.assertEqual(calls,[])
  for origin in ['https://Fixture.example','https://fixture.example:443','https://fixture.example:bad','https://fixture.example\\evil']:
   with self.assertRaises(ValueError):create_merged_fixture(self.svc,origin=origin,client_identity=lambda r:'x',reader=FixtureNews([]))
  self.svc.mode='open';self.assertEqual(self.get('/account/preauth').status_code,403)
 def test_password_change_revokes_other_browser(self):
  csrf=self.login();other=Client(self.app,Response);t=other.get('/account/preauth',base_url=O).json['csrf'];self.assertEqual(other.post('/account/login',base_url=O,headers={'Origin':O},json={'username':'alice','password':PASSWORD,'csrf':t}).status_code,200)
  self.assertEqual(self.post('change-password',{'csrf':csrf,'old':PASSWORD,'new':'new correct horse battery'}).status_code,200)
  self.assertEqual(other.get('/api/news',base_url=O).status_code,403);self.assertEqual(self.get('/api/news').status_code,200)
 def test_forged_forwarded_cannot_choose_client_or_host(self):
  seen=[];app=create_merged_fixture(self.svc,origin=O,client_identity=lambda r:seen.append('trusted') or 'fixture-only',reader=FixtureNews([]));c=Client(app,Response);t=c.get('/account/preauth',base_url=O).json['csrf']
  self.assertEqual(c.post('/account/login',base_url=O,headers={'Origin':O,'X-Forwarded-For':'evil','X-Forwarded-Host':'evil'},json={'username':'alice','password':PASSWORD,'csrf':t}).status_code,200);self.assertEqual(seen,['trusted'])
  self.assertEqual(c.get('/workspace',base_url='https://evil.example',headers={'X-Forwarded-Host':'fixture.example','X-Forwarded-Proto':'https'}).status_code,403)
 def test_navigation_and_protected_original_assets(self):
  self.assertEqual(self.get('/merged-login').status_code,200);self.assertEqual(self.get('/fixture-navigation').status_code,403);self.login()
  for p in ['/fixture-navigation','/workspace/assets/workspace.js','/workspace/branding/icon-48.png','/workspace/finder/index.html']:
   r=self.get(p);self.assertEqual(r.status_code,200,p);r.close()
 def test_production_store_reader_refused(self):
  original=self.svc.store;self.svc.store=object()
  with self.assertRaises(ValueError):create_merged_fixture(self.svc,origin=O,client_identity=lambda r:'x',reader=FixtureNews([]))
  self.svc.store=original
  class Sub(FixtureNews):pass
  with self.assertRaises(ValueError):create_merged_fixture(self.svc,origin=O,client_identity=lambda r:'x',reader=Sub([]))
 def test_post_read_routes_stream_reads_and_body_bounds(self):
  self.login()
  for p in ['/workspace/brics-streams','/api/brics/streams']:
   r=self.get(p);self.assertNotEqual(r.status_code,403);r.close()
  for p,d in [('/api/related-news',{'product_terms':['steel']}),('/api/finder-context',{'project':'geo','article_key':'0'*64})]:
   r=self.c.post(p,base_url=O,headers={'Origin':O},json=d);self.assertIn(r.status_code,[200,404]);self.assertEqual(self.c.post(p,base_url=O,json=d).status_code,403)
   self.assertEqual(self.c.post(p,base_url=O,headers={'Origin':O},data='{"x":1,"x":2}',content_type='application/json').status_code,400)
  for bad_key in ['missing','A'*64,'0'*63]:
   self.assertEqual(self.c.post('/api/finder-context',base_url=O,headers={'Origin':O},json={'project':'geo','article_key':bad_key}).status_code,400)
  self.assertEqual(self.c.post('/api/brics/streams',base_url=O,headers={'Origin':O},json={}).status_code,403)
 def test_offline_worker_routes_disabled_and_revoke_all_classes(self):
  csrf=self.login()
  for p in ['/workspace/finder/offline.html','/workspace/finder/offline-sw.js','/workspace/finder/offline-control.js','/workspace/finder/sw.js','/workspace/finder/manifest.webmanifest']:self.assertEqual(self.get(p).status_code,403)
  self.post('logout',{'csrf':csrf})
  for p in ['/workspace','/workspace/assets/workspace.js','/workspace/branding/icon-48.png','/workspace/finder/index.html','/api/weekly-report.pdf','/api/export.csv','/api/news','/fixture-navigation']:self.assertEqual(self.get(p).status_code,403,p)
 def test_idle_invalid_and_real_counterpart_gates(self):
  self.login();valid=self.c.get_cookie(COOKIE_NAME,domain='fixture.example').value;self.now+=8*86400;self.assertEqual(self.get('/api/news').status_code,403)
  self.c.set_cookie(COOKIE_NAME,'invalid',domain='fixture.example');self.assertEqual(self.get('/workspace').status_code,403)
  from integration.preview_access import PreviewAccess
  from werkzeug.security import generate_password_hash
  import re
  old=PreviewAccess(O,generate_password_hash('fixture-only-password')).build('k'*64);c=old.test_client();t=re.search(r'value="([^"]+)"',c.get('/login',base_url=O).text)[1];self.assertEqual(c.post('/login',base_url=O,headers={'Origin':O},data={'csrf':t,'password':'fixture-only-password'}).status_code,303)
  oldcookie=c.get_cookie('__Host-merged-preview',domain='fixture.example').value
  self.c.set_cookie('__Host-merged-preview',oldcookie,domain='fixture.example');self.assertEqual(self.get('/workspace').status_code,403)
  self.login();valid=self.c.get_cookie(COOKIE_NAME,domain='fixture.example').value
  counterpart=old.test_client();counterpart.set_cookie(COOKIE_NAME,valid,domain='fixture.example');self.assertEqual(counterpart.get('/workspace',base_url=O).status_code,403)
 def test_login_headers_and_subclasses(self):
  for p in ['/merged-login','/account/preview']:
   r=self.get(p);self.assertEqual(r.headers['X-Content-Type-Options'],'nosniff');self.assertEqual(r.headers['X-Robots-Tag'],'noindex, nofollow');self.assertEqual(r.headers['Referrer-Policy'],'no-referrer');self.assertIn("base-uri 'none'",r.headers['Content-Security-Policy'])
  self.assertEqual(self.get('/account/login').status_code,403)
  class StoreSub(MemoryStore):pass
  original=self.svc.store;self.svc.store=StoreSub()
  with self.assertRaises(ValueError):create_merged_fixture(self.svc,origin=O,client_identity=lambda r:'x',reader=FixtureNews([]))
  self.svc.store=original
  class ServiceSub(AccountService):pass
  svc=ServiceSub(self.store,b'x'*48,lambda:self.now,hasher=Hasher(n=1024),signup_mode='closed',allowed_origins=[O])
  with self.assertRaises(ValueError):create_merged_fixture(svc,origin=O,client_identity=lambda r:'x',reader=FixtureNews([]))
 def test_denied_affordances_visibly_labelled(self):
  self.login()
  for path in ['/workspace','/workspace/finder/index.html','/workspace/brics-streams']:
   r=self.get(path);self.assertEqual(r.status_code,200);self.assertIn('offline installation / Store public snapshot is disabled here',r.text);self.assertIn('BRICS add/remove writes are disabled',r.text);r.close()
