import re,unittest
from werkzeug.security import generate_password_hash
from integration.preview_access import PreviewAccess,create_preview_from_env
class PreviewAccessTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.hash=generate_password_hash('fixture-only-password')
 def setUp(self):
  self.access=PreviewAccess('https://preview.example',self.hash)
  self.app=self.access.build('fixture-only-session-key-'+'a'*48)
  self.c=self.app.test_client();self.base='https://preview.example'
 def get(self,path):return self.c.get(path,base_url=self.base)
 def post(self,path,data=None,origin=None):return self.c.post(path,base_url=self.base,data=data,headers={'Origin':origin or self.base})
 def token(self):return re.search(r'name="csrf" value="([^"]+)"',self.get('/login').text)[1]
 def test_deny_default_and_health(self):
  c=create_preview_from_env({}).test_client();self.assertEqual(c.get('/workspace').status_code,403);self.assertEqual(c.get('/login').status_code,403);self.assertEqual(c.get('/health').status_code,200)
 def test_login_private_assets_and_logout(self):
  self.assertEqual(self.get('/workspace').status_code,403)
  r=self.post('/login',{'csrf':self.token(),'password':'fixture-only-password'});self.assertEqual(r.status_code,303)
  self.assertIn('Secure',r.headers['Set-Cookie']);self.assertIn('HttpOnly',r.headers['Set-Cookie']);self.assertIn('SameSite=Strict',r.headers['Set-Cookie'])
  for path in ['/workspace','/workspace/branding/icon-48.png']:
   response=self.get(path);self.assertEqual(response.status_code,200);response.close()
  self.assertEqual(self.post('/logout').status_code,303);self.assertEqual(self.get('/workspace').status_code,403)
 def test_bad_password_token_origin(self):
  t=self.token();self.assertEqual(self.post('/login',{'csrf':t,'password':'wrong'}).status_code,401)
  self.assertEqual(self.post('/login',{'csrf':'wrong','password':'fixture-only-password'}).status_code,403)
  self.assertEqual(self.post('/login',{'csrf':t,'password':'fixture-only-password'},'https://evil.example').status_code,403)
 def test_rate_limit(self):
  t=self.token()
  for _ in range(10):self.assertEqual(self.post('/login',{'csrf':t,'password':'wrong'}).status_code,401)
  self.assertEqual(self.post('/login',{'csrf':t,'password':'wrong'}).status_code,429)
  self.assertEqual(self.post('/login',{'csrf':t,'password':'fixture-only-password'}).status_code,429)
 def test_invalid_config_fails_closed(self):
  for origin in ['http://preview.example','https://user@preview.example','https://preview.example/a']:
   with self.assertRaises(ValueError):PreviewAccess(origin,self.hash)
  with self.assertRaises(ValueError):self.access.build('short')
  with self.assertRaises(ValueError):create_preview_from_env({'PREVIEW_ACCESS_ENABLED':'true'})
 def test_no_collection_routes(self):
  self.post('/login',{'csrf':self.token(),'password':'fixture-only-password'})
  for p in ['/collect','/send-digest']:self.assertEqual(self.post(p).status_code,404)

 def test_missing_origin_and_expired_session(self):
  t=self.token()
  self.assertEqual(self.c.post('/login',base_url=self.base,data={'csrf':t,'password':'fixture-only-password'}).status_code,403)
  self.post('/login',{'csrf':t,'password':'fixture-only-password'})
  self.assertNotIn('Set-Cookie',self.get('/api/news').headers)
  with self.c.session_transaction(base_url=self.base) as session:session['preview_issued_at']=0
  self.assertEqual(self.get('/workspace').status_code,403)
 def test_tampered_cookie(self):
  self.post('/login',{'csrf':self.token(),'password':'fixture-only-password'})
  self.c.set_cookie('__Host-merged-preview','tampered',domain='preview.example')
  self.assertEqual(self.get('/workspace').status_code,403)

 def test_referrer_and_form_action(self):
  response=self.get('/health');self.assertEqual(response.headers['Referrer-Policy'],'same-origin');self.assertIn("form-action 'self'",response.headers['Content-Security-Policy'])
