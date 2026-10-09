import unittest,json
from dataclasses import replace
from unittest.mock import patch
from werkzeug.test import Client
from werkzeug.wrappers import Response
from integration.finder198_auth import create_finder_auth,SingleWorkerEvidence,AuthRefused
from integration.accounts.service import AccountService
from integration.accounts.store import MemoryStore
from integration.accounts.passwords import Hasher
O='https://gate.example';PW='correct horse battery'
def evidence():return SingleWorkerEvidence(1,100,200,'host-observation','owner-scope-reference')
class Tests(unittest.TestCase):
 def setUp(self):
  self.now=[101];self.store=MemoryStore();self.s=AccountService(self.store,b'x'*48,lambda:self.now[0],signup_mode='closed',allowed_origins=[O]);self.public_calls=[]
  self.store.create_account('alice',{'uid':'alice','password':self.s.hasher.hash(PW),'created':100,'pwv':0},None,50)
  def public(env,start):self.public_calls.append(env['PATH_INFO']);return Response('PUBLIC',200)(env,start)
  self.public=public;self.app=create_finder_auth(public,enabled=True,service=self.s,origin=O,client_identity=lambda r:'trusted-peer',worker_evidence=evidence,clock=lambda:self.now[0]);self.c=Client(self.app,Response)
 def get(self,path,**kw):return self.c.get(path,base_url=O,**kw)
 def login(self):
  pre=self.get('/account/preauth').json['csrf'];r=self.c.post('/account/login',base_url=O,json={'username':'alice','password':PW,'csrf':pre},headers={'Origin':O});self.assertEqual(r.status_code,200);return r
 def test_public_unchanged_signedout_and_expired_provider(self):
  for p in ('/','/health','/workspace','/api/news','/workspace/finder/index.html','/api/finder-context'):
   self.assertEqual(self.get(p).data,b'PUBLIC')
  self.now[0]=200;self.assertEqual(self.get('/health').data,b'PUBLIC');self.assertEqual(self.get('/account/preauth').status_code,503)
 def test_off_no_service_provider_reads(self):
  self.assertIs(create_finder_auth(self.public),self.public)
  self.assertIs(create_finder_auth(self.public,worker_evidence=lambda:(_ for _ in ()).throw(AssertionError())),self.public)
 def test_multiworker_stale_badtypes_refused(self):
  for v in (replace(evidence(),workers=2),replace(evidence(),workers=True),replace(evidence(),expires_at=101),replace(evidence(),expires_at=221),replace(evidence(),host_reference='')):
   with self.assertRaises(AuthRefused):create_finder_auth(self.public,enabled=True,worker_evidence=lambda:v,clock=lambda:101)
 def test_enabled_no_provider_defaultdeny(self):
  with self.assertRaises(AuthRefused):create_finder_auth(self.public,enabled=True)
 def test_closed_account_allowlist(self):
  for p in ('/account/signup','/account/settings','/account/save-settings','/account/export','/account/change-password','/account/delete','/account/preview'):
   self.assertEqual(self.get(p).status_code,404);self.assertEqual(self.c.post(p,base_url=O,json={},headers={'Origin':O}).status_code,404)
 def test_login_session_cookie_whoami_logout(self):
  r=self.login();self.assertNotIn('session_token',r.json)
  for cookie in r.headers.getlist('Set-Cookie'):
   self.assertTrue(all(v in cookie for v in ('Secure','HttpOnly','SameSite=Strict','Path=/')))
  self.assertEqual(self.get('/account/whoami').json['username'],'alice')
  self.assertEqual(self.c.post('/account/logout',base_url=O,json={'csrf':r.json['csrf']},headers={'Origin':O}).status_code,200)
  self.assertEqual(self.get('/account/whoami').status_code,401)
 def test_broker_no_session_or_origin_csrf_then_held_no_public(self):
  self.assertEqual(self.get('/api/finder-broker/ai',headers={'Origin':O}).status_code,401)
  t=self.login().json['csrf']
  self.assertEqual(self.get('/api/finder-broker/ai').status_code,403)
  self.assertEqual(self.get('/api/finder-broker/ai',headers={'Origin':O,'X-CSRF-Token':'bad'}).status_code,403)
  r=self.get('/api/finder-broker/ai',headers={'Origin':O,'X-CSRF-Token':t});self.assertEqual(r.status_code,503);self.assertEqual(r.json['error'],'broker_not_wired');self.assertEqual(self.public_calls,[])
 def test_host_query_encoded_boundary_and_no_forwardedtrust(self):
  self.assertEqual(self.c.get('/account/preauth',base_url='https://evil.example',headers={'X-Forwarded-Host':'gate.example','X-Forwarded-Proto':'https'}).status_code,403)
  self.assertEqual(self.get('/account/preauth?q=1').status_code,403)
  self.assertEqual(self.get('/account/%70reauth').status_code,403)
  self.assertEqual(self.get('/account/preauth',headers={'X-Forwarded-For':'fake'}).status_code,200)
 def test_collaborator_closed_mode_default_hasher(self):
  self.s.mode='open'
  with self.assertRaises(ValueError):create_finder_auth(self.public,enabled=True,service=self.s,origin=O,client_identity=lambda r:'trusted',worker_evidence=evidence,clock=lambda:101)
 def test_store_error_holds_before_broker(self):
  t=self.login().json['csrf'];self.store.touch_session=lambda *a:(_ for _ in ()).throw(ValueError('PRIVATE'))
  r=self.get('/api/finder-broker/ai',headers={'Origin':O,'X-CSRF-Token':t});self.assertEqual(r.status_code,503);self.assertNotIn('PRIVATE',r.text)
 def test_second_service_same_store_refused(self):
  other=AccountService(self.store,b'x'*48,lambda:101,signup_mode='closed',allowed_origins=[O])
  with self.assertRaises(AuthRefused):create_finder_auth(self.public,enabled=True,service=other,origin=O,client_identity=lambda r:'trusted',worker_evidence=evidence,clock=lambda:101)
 def test_bound_limiter_swap_and_worker_change_hold(self):
  from integration.accounts.limiter import Limiter
  self.s.limiter=Limiter(self.store,self.s.secret,self.s.clock)
  self.assertEqual(self.get('/account/preauth').status_code,503)
 def test_login_body_duplicate_and_wrongorigin(self):
  self.assertEqual(self.c.post('/account/login',base_url=O,json={},headers={}).status_code,403)
  r=self.c.post('/account/login',base_url=O,data='{"username":"alice","username":"bobby","password":"x","csrf":"y"}',content_type='application/json',headers={'Origin':O})
  self.assertEqual(r.status_code,400)
