import unittest
from integration.accounts import AccountService,MemoryStore,Hasher
from integration.accounts.http_fixture import create_fixture_app
O='https://fixture.example'
class HttpFixtureTests(unittest.TestCase):
 def setUp(self):
  self.store=MemoryStore();self.svc=AccountService(self.store,b'f'*48,lambda:1800000000,hasher=Hasher(n=1024),signup_mode='open',allowed_origins=[O]);self.c=create_fixture_app(self.svc,O,lambda r:'fixture-client').test_client()
 def get(self,path):return self.c.get(path,base_url=O)
 def post(self,action,data,headers=None):return self.c.post('/account/'+action,base_url=O,headers=headers if headers is not None else {'Origin':O},json=data)
 def signup(self):
  csrf=self.get('/account/preauth').json['csrf'];return self.post('signup',{'username':'alice','password':'correct horse battery','invite':'','csrf':csrf})
 def test_cookie_only_session_save_export_logout(self):
  r=self.signup();self.assertEqual(r.status_code,200);self.assertNotIn('session_token',r.json);self.assertIn('Secure',r.headers['Set-Cookie']);csrf=r.json['csrf']
  self.assertEqual(self.get('/account/whoami').json['username'],'alice')
  r=self.post('save-settings',{'csrf':csrf,'channels':[],'watchlist':[],'version':0});self.assertEqual(r.status_code,200)
  r=self.post('export',{'csrf':csrf});self.assertNotIn('password',r.text);self.assertEqual(r.json['data']['username'],'alice')
  self.assertEqual(self.post('logout',{'csrf':csrf}).status_code,200);self.assertEqual(self.get('/account/whoami').status_code,401)
 def test_origin_body_and_host_guards(self):
  self.assertEqual(self.post('signup',{},{}).status_code,403)
  self.assertEqual(self.c.get('/account/preauth',base_url='https://evil.example').status_code,403)
  self.assertEqual(self.c.post('/account/login',base_url=O,headers={'Origin':O},data='x'*16385,content_type='application/json').status_code,413)
  self.assertEqual(self.c.post('/account/login',base_url=O,headers={'Origin':O},data='{"x":1,"x":2}',content_type='application/json').status_code,400)
  self.assertEqual(self.c.post('/account/login',base_url=O,headers={'Origin':O},data='{}',content_type='text/plain').status_code,415)
 def test_closed_signup_and_existing_preview_unchanged(self):
  self.svc.mode='closed';self.assertFalse(self.signup().json['ok']);self.assertEqual(self.store.users,{})
  from integration.news_api import create_app
  self.assertEqual(create_app().test_client().get('/workspace').status_code,403)

 def test_other_browser_csrf_password_delete_and_revision(self):
  r=self.signup();csrf=r.json['csrf'];other=create_fixture_app(self.svc,O,lambda r:'other-fixture').test_client()
  r=other.post('/account/logout',base_url=O,headers={'Origin':O},json={'csrf':csrf});self.assertEqual(r.status_code,401)
  self.assertEqual(self.post('save-settings',{'csrf':csrf,'channels':[],'watchlist':[],'version':1}).status_code,409)
  self.assertEqual(self.post('delete',{'csrf':csrf,'password':'incorrect password'}).status_code,401)
  self.assertEqual(self.post('delete',{'csrf':csrf,'password':'correct horse battery'}).status_code,200);self.assertEqual(self.store.users,{})
 def test_server_client_resolver_cannot_be_overridden_in_body(self):
  t=self.get('/account/preauth').json['csrf']
  r=self.post('signup',{'username':'alice','password':'correct horse battery','invite':'','csrf':t,'client':'spoof'});self.assertEqual(r.status_code,400)
  self.assertEqual(self.store.users,{})
 def test_missing_length_and_nested_invalid(self):
  r=self.c.post('/account/login',base_url=O,headers={'Origin':O},content_type='application/json',environ_overrides={'CONTENT_LENGTH':''});self.assertEqual(r.status_code,413)
  t=self.get('/account/preauth').json['csrf'];r=self.post('signup',{'username':{},'password':[],'invite':'','csrf':t});self.assertFalse(r.json['ok'])

 def test_review_cookie_clear_and_json404405(self):
  r=self.signup();self.assertTrue(any('__Host-gib_pre=' in c and 'Max-Age=0' in c for c in r.headers.getlist('Set-Cookie')))
  self.assertEqual(self.get('/unknown').json['error'],'not_found')
  self.assertEqual(self.get('/account/login').json['error'],'method_not_allowed')
  self.c.delete_cookie('__Host-gib_session',domain='fixture.example')
  r=self.post('logout',{'csrf':'invalid'});self.assertEqual(r.status_code,401);self.assertTrue(any('__Host-gib_session=' in c and 'Max-Age=0' in c for c in r.headers.getlist('Set-Cookie')))
