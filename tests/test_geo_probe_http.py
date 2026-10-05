import unittest,re,time,threading,importlib,json
from unittest.mock import patch
from werkzeug.security import generate_password_hash
from integration.geo_sample_probe import _result
import integration.geo_probe_http as m
SECRET='mongodb://sentinel-private'
ORIGIN='https://preview.example.com'
PASSWORD='abcdefghijklmnopqrst'
class Tests(unittest.TestCase):
 def setUp(self):m._LAST=None
 def app(self,executor=None,clock=lambda:1000):return m.create_probe_app(origin=ORIGIN,password_hash=generate_password_hash(PASSWORD),session_key='k'*64,uri=SECRET,executor=executor or (lambda u:_result('empty',0,{k:{'compatible':0,'incompatible':0,'missing':0} for k in ('created_at','published','score')})),clock=clock)
 def login(self,c):
  r=c.get('/login',base_url=ORIGIN);token=re.search('value="([^"]+)"',r.text)[1]
  self.assertEqual(c.post('/login',base_url=ORIGIN,headers={'Origin':ORIGIN},data={'csrf':token,'password':PASSWORD}).status_code,303)
  r=c.get('/db-check',base_url=ORIGIN);self.assertEqual(r.status_code,200);return re.search('value="([^"]+)"',r.text)[1]
 def test_auth_all_paths_and_method(self):
  c=self.app().test_client()
  for p in ['/db-check','/unknown','/workspace']:
   for method in ['GET','POST','HEAD','OPTIONS','DELETE']:
    r=c.open(p,method=method,base_url=ORIGIN);self.assertEqual(r.status_code,403);self.assertNotIn(SECRET,r.text);self.assertIn('no-store',r.headers['Cache-Control'])
 def test_login_and_exact_post(self):
  c=self.app().test_client();token=self.login(c)
  r=c.post('/db-check',base_url=ORIGIN,headers={'Origin':ORIGIN},data={'csrf':token});self.assertEqual(r.status_code,200);self.assertEqual(r.json['state'],'empty');self.assertNotIn(SECRET,r.text);self.assertEqual(r.headers['X-Robots-Tag'],'noindex, nofollow')
  self.assertEqual(c.post('/db-check',base_url=ORIGIN,headers={'Origin':ORIGIN},data={'csrf':token}).status_code,429)
 def test_csrf_origin_query_content(self):
  calls=[];c=self.app(lambda u:calls.append(u)).test_client();token=self.login(c)
  for path,headers,data in [('/db-check',{}, {'csrf':token}),('/db-check',{'Origin':'https://wrong.invalid'},{'csrf':token}),('/db-check',{'Origin':ORIGIN},{'csrf':'bad'}),('/db-check?uri=bad',{'Origin':ORIGIN},{'csrf':token}),('/db-check',{'Origin':ORIGIN},{'csrf':token,'uri':'bad'})]:
   self.assertIn(c.post(path,base_url=ORIGIN,headers=headers,data=data).status_code,[400,403])
  self.assertEqual(c.post('/db-check',base_url=ORIGIN,headers={'Origin':ORIGIN},json={'csrf':token}).status_code,403);self.assertEqual(calls,[])
 def test_failure_fixed_and_cooldown_cross_instances(self):
  def bad(u):raise RuntimeError(SECRET)
  c=self.app(bad).test_client();token=self.login(c)
  r=c.post('/db-check',base_url=ORIGIN,headers={'Origin':ORIGIN},data={'csrf':token});self.assertEqual(r.status_code,503);self.assertNotIn(SECRET,r.text)
  other=self.app().test_client();token=self.login(other);self.assertEqual(other.post('/db-check',base_url=ORIGIN,headers={'Origin':ORIGIN},data={'csrf':token}).status_code,429)
 def test_busy_control_lock_cleanup_and_resume(self):
  c=self.app().test_client();token=self.login(c);m._LOCK.acquire()
  try:self.assertEqual(c.post('/db-check',base_url=ORIGIN,headers={'Origin':ORIGIN},data={'csrf':token}).status_code,429)
  finally:m._LOCK.release()
  def interrupt(u):raise KeyboardInterrupt()
  c=self.app(interrupt).test_client();token=self.login(c)
  with self.assertRaises(KeyboardInterrupt):c.post('/db-check',base_url=ORIGIN,headers={'Origin':ORIGIN},data={'csrf':token})
  self.assertTrue(m._LOCK.acquire(False));m._LOCK.release()
 def test_bad_executor_result_and_off_import(self):
  c=self.app(lambda u:{'uri':u}).test_client();token=self.login(c);r=c.post('/db-check',base_url=ORIGIN,headers={'Origin':ORIGIN},data={'csrf':token});self.assertEqual(r.status_code,503);self.assertNotIn(SECRET,r.text)
  with patch('subprocess.Popen',side_effect=AssertionError('effect')):importlib.reload(m)
 def test_unicode_csrf_fixed403(self):
  c=self.app().test_client();self.login(c)
  self.assertEqual(c.post('/db-check',base_url=ORIGIN,headers={'Origin':ORIGIN},data={'csrf':'தமிழ்'}).status_code,403)

 def test_logout_browser_form_and_replay_revocation(self):
  c=self.app().test_client();self.login(c)
  captured=c.get_cookie('__Host-merged-preview',domain='preview.example.com').value
  r=c.get('/db-check',base_url=ORIGIN);token=re.search(r'action="/logout"><input[^>]+value="([^"]+)"',r.text)[1]
  self.assertEqual(c.post('/logout',base_url=ORIGIN,headers={'Origin':ORIGIN},data={'csrf':token}).status_code,303)
  c.set_cookie('__Host-merged-preview',captured,domain='preview.example.com')
  self.assertEqual(c.get('/db-check',base_url=ORIGIN).status_code,403)
