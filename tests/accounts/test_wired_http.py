import unittest,json,hashlib
from werkzeug.test import Client
from werkzeug.wrappers import Response
from integration.accounts.wired_http import create_wired_http,PRIVATE_NEWS_GET,PRIVATE_NEWS_POST
from integration.accounts.service import AccountService,SESSION_IDLE,COOKIE_NAME
from integration.accounts.store import MemoryStore
from integration.accounts.passwords import Hasher
from integration.accounts.mongo_store import MongoAccountStore
from test_mongo_account_store import Client as FakeMongo,R
O='https://wired.example';PASSWORD='correct horse battery'
class WiredTests(unittest.TestCase):
 def setup(self,mongo=False):
  self.now=[1800000000];self.db=FakeMongo() if mongo else None;self.store=MongoAccountStore(self.db,review=R,clock=lambda:self.now[0]) if mongo else MemoryStore();self.s=AccountService(self.store,b'w'*48,lambda:self.now[0],signup_mode='closed',allowed_origins=[O]);self.calls=[]
  for name in ('alice','bobby'):self.store.create_account(name,{'uid':name,'password':self.s.hasher.hash(PASSWORD),'created':self.now[0],'pwv':0},None,50)
  self.app=create_wired_http(self.s,origin=O,client_identity=lambda r:'trusted-client',reader=lambda:self.calls.append(1) or {'geo':[]});self.c=Client(self.app,Response)
 def setUp(self):self.setup()
 def get(self,p,c=None,**kw):return (c or self.c).get(p,base_url=O,**kw)
 def post(self,p,d,c=None,headers=None):return (c or self.c).post('/account/'+p,base_url=O,json=d,headers={'Origin':O} if headers is None else headers)
 def login(self,name='alice',c=None):
  t=self.get('/account/preauth',c).json['csrf'];r=self.post('login',{'username':name,'password':PASSWORD,'csrf':t},c);self.assertEqual(r.status_code,200);return r
 def test_all_private_routes_signedout_before_reader(self):
  for p in PRIVATE_NEWS_GET|{'/workspace/assets/workspace.js','/workspace/branding/logo.svg','/workspace/finder/index.html','/account/settings','/account/whoami'}:self.assertEqual(self.get(p).status_code,403,p)
  for p in PRIVATE_NEWS_POST:self.assertEqual(self.c.post(p,base_url=O,json={},headers={'Origin':O}).status_code,403)
  self.assertEqual(self.calls,[]);self.assertEqual(self.get('/health').status_code,404);self.assertEqual(self.get('/account/preview').status_code,404)
 def test_cookie_hash_and_settings_isolation_cas_export(self):
  r=self.login();t=r.json['csrf'];cookies=r.headers.getlist('Set-Cookie');self.assertTrue(all('HttpOnly' in x and 'Secure' in x and 'SameSite=Strict' in x and 'Path=/' in x for x in cookies));self.assertNotIn('session_token',r.json);self.assertNotEqual(self.store.get_user('alice')['password'],PASSWORD);self.assertTrue(self.s.hasher.parse(self.store.get_user('alice')['password']))
  self.assertEqual(self.post('save-settings',{'csrf':t,'channels':[{'name':'BBC','video':'abcdefghijk'}],'watchlist':[],'version':0}).status_code,200);self.assertEqual(self.post('save-settings',{'csrf':t,'channels':[],'watchlist':[],'version':0}).status_code,409)
  other=Client(self.app,Response);u=self.login('bobby',other).json['csrf'];self.assertEqual(self.get('/account/settings',other).json['settings']['version'],0);self.assertEqual(self.get('/account/settings').json['settings']['version'],1)
  exported=self.post('export',{'csrf':u},other).json;self.assertEqual(exported['data']['username'],'bobby');self.assertNotIn('BBC',json.dumps(exported));self.assertNotIn('password',json.dumps(exported));self.assertNotIn('csrf',json.dumps(exported));self.assertTrue(self.get('/account/settings').json['settings']['channels'][0]['compulsory'])
  self.assertEqual(self.post('save-settings',{'csrf':t,'channels':[],'watchlist':[],'version':1,'uid':'bobby'}).status_code,400)
 def test_csrf_origin_host_forwarded_boundary(self):
  self.assertEqual(self.post('login',{'username':'alice','password':PASSWORD,'csrf':'bad'}).status_code,403);self.assertEqual(self.post('login',{},headers={}).status_code,403)
  self.assertEqual(self.c.get('/account/preauth',base_url='https://evil.example',headers={'X-Forwarded-Host':'wired.example','X-Forwarded-Proto':'https'}).status_code,403)
  r=self.login();self.assertEqual(self.get('/api/news',headers={'X-Forwarded-For':'evil','X-Forwarded-Host':'evil','X-Forwarded-Proto':'http'}).status_code,200)
  self.assertEqual(self.post('logout',{'csrf':'bad'}).status_code,403)
  for t in (None,'bad','☃'):
   headers={'Origin':O};
   if t is not None:headers['X-CSRF-Token']=t
   self.assertEqual(self.c.post('/api/related-news',base_url=O,json={},headers=headers).status_code,403)
 def test_news_logout_expiry_password_fences(self):
  t=self.login().json['csrf'];self.assertEqual(self.get('/api/news').status_code,200);self.assertEqual(self.post('logout',{'csrf':t}).status_code,200);self.assertEqual(self.get('/api/news').status_code,403)
  self.login();self.now[0]+=SESSION_IDLE+1;self.assertEqual(self.get('/api/news').status_code,403)
  self.now[0]=1800000000;t=self.login().json['csrf'];other=Client(self.app,Response);self.login(c=other);self.assertEqual(self.post('change-password',{'csrf':t,'old':PASSWORD,'new':'another correct horse battery'}).status_code,200);self.assertEqual(self.get('/api/news',other).status_code,403);self.assertEqual(self.get('/api/news').status_code,200)
 def test_mongo_construction_zero_calls_and_http_disposable(self):
  db=FakeMongo();st=MongoAccountStore(db,review=R,clock=lambda:1800000000);s=AccountService(st,b'z'*48,lambda:1800000000,signup_mode='closed',allowed_origins=[O]);create_wired_http(s,origin=O,client_identity=lambda r:'c',reader=lambda:{'geo':[]});self.assertEqual(db.calls,[]);self.assertEqual(db.sessions,[])
  self.setup(True);self.login();self.assertEqual(self.get('/api/news').status_code,200);self.db.fail_commit=True;self.assertEqual(self.get('/api/news').status_code,403);self.assertEqual(self.calls,[1]);self.assertNotIn('secret',self.get('/account/settings').text)
 def test_full_collaborator_and_origin_rejection(self):
  for o in ('http://wired.example','https://wired.example:443','https://wired.example/','null','https://*.example','https://user@wired.example'):
   with self.assertRaises(ValueError):create_wired_http(self.s,origin=o,client_identity=lambda r:'c',reader=lambda:{})
  old=self.s.hasher;self.s.hasher=Hasher(n=1024)
  with self.assertRaises(ValueError):create_wired_http(self.s,origin=O,client_identity=lambda r:'c',reader=lambda:{})
  self.s.hasher=old;self.s.limiter.store=MemoryStore()
  with self.assertRaises(ValueError):create_wired_http(self.s,origin=O,client_identity=lambda r:'c',reader=lambda:{})
 def test_no_mutating_legacy_surface(self):
  self.login()
  for p in ('/mark-emailed','/critical','/weekly','/api/brics/streams'):self.assertEqual(self.c.post(p,base_url=O,json={},headers={'Origin':O}).status_code,404)
  self.assertEqual(self.c.delete('/api/brics/streams',base_url=O,headers={'Origin':O}).status_code,405)
