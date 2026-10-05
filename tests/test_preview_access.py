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
  
  t=re.search(r'value="([^"]+)"',self.get('/private-session').text)[1]
  self.assertEqual(self.post('/logout',{'csrf':t}).status_code,303);self.assertEqual(self.get('/workspace').status_code,403)
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
 def test_unicode_tokens_fixed403_logout_origin(self):
  self.assertEqual(self.post('/login',{'csrf':'தமிழ்','password':'x'}).status_code,403)
  self.post('/login',{'csrf':self.token(),'password':'fixture-only-password'})
  t=re.search(r'value="([^"]+)"',self.get('/private-session').text)[1]
  self.assertEqual(self.post('/logout',{'csrf':t},'https://evil.example').status_code,403)
  self.assertEqual(self.post('/logout',{'csrf':'தமிழ்'}).status_code,403)
  self.assertEqual(self.get('/workspace').status_code,200)
 def test_parallel_password_hash_single_slot_and_atomic_reservation(self):
  from unittest.mock import patch
  import threading
  started=threading.Event();release=threading.Event();statuses=[];calls=[]
  def hashcheck(*a):calls.append(1);started.set();release.wait(5);return True
  def attempt():
   c=self.app.test_client();r=c.get('/login',base_url=self.base);token=re.search(r'value="([^"]+)"',r.text)[1]
   statuses.append(c.post('/login',base_url=self.base,headers={'Origin':self.base},data={'csrf':token,'password':'fixture'}).status_code)
  with patch('integration.preview_access.check_password_hash',side_effect=hashcheck):
   first=threading.Thread(target=attempt);first.start();self.assertTrue(started.wait(2))
   threads=[threading.Thread(target=attempt) for _ in range(23)]
   for t in threads:t.start()
   for t in threads:t.join(5);self.assertFalse(t.is_alive())
   release.set();first.join(5)
  self.assertEqual(len(calls),1);self.assertEqual(statuses.count(429),23);self.assertEqual(statuses.count(303),1);self.assertEqual(len(self.access.attempts),1)
 def test_access_import_does_not_import_news_app(self):
  import subprocess,sys
  p=subprocess.run([sys.executable,'-c',"import integration.preview_access,sys;assert 'integration.news_api' not in sys.modules"],capture_output=True,text=True)
  self.assertEqual(p.returncode,0,p.stderr)

 def test_logout_revokes_replayed_signed_cookie_http_only(self):
  self.post('/login',{'csrf':self.token(),'password':'fixture-only-password'})
  captured=self.c.get_cookie('__Host-merged-preview',domain='preview.example').value
  token=re.search(r'value="([^"]+)"',self.get('/private-session').text)[1]
  self.assertEqual(self.post('/logout',{'csrf':token}).status_code,303)
  self.c.set_cookie('__Host-merged-preview',captured,domain='preview.example')
  self.assertEqual(self.get('/workspace').status_code,403)
 def test_origin_canonicalization(self):
  for origin in ['https://preview.example:bad','https://preview.example:99999','https://preview.example:443','https://Preview.example','https://preview.example\\evil','https://preview.example/evil','https://preview.example?x=1']:
   with self.assertRaises(ValueError):PreviewAccess(origin,self.hash)
 def test_oversized_no_reservation(self):
  self.assertEqual(self.post('/login',{'csrf':self.token(),'password':'x'*1025}).status_code,400)
  self.assertEqual(self.access.attempts,[])
