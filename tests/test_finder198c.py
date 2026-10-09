import unittest,json
from unittest.mock import patch
from werkzeug.test import Client
from werkzeug.wrappers import Response
from integration.finder198_server import create_broker_server,ServerRefused
from integration.finder198_transport import FixedProxyTransport
from integration.finder198_receipts import ProxyReceiptBudget
from tests.test_finder198ba import Collection,R
from tests.test_finder198a import evidence,O,PW
from integration.accounts.service import AccountService
from integration.accounts.store import MemoryStore
class Tests(unittest.TestCase):
 def setUp(self):
  self.store=MemoryStore();self.s=AccountService(self.store,b'x'*48,lambda:101,signup_mode='closed',allowed_origins=[O]);self.c=Collection();self.c.doc.update(schema=2,receipts=[]);self.b=ProxyReceiptBudget(self.c,review=R);self.t=FixedProxyTransport({'FINDER_PROXY_BASE_URL':'https://hsn-ai-proxy.onrender.com','FINDER_PROXY_SECRET':'x'*48},enabled=True)
  for name in ('alice','bobby'):self.store.create_account(name,{'uid':name,'password':self.s.hasher.hash(PW),'created':100,'pwv':0},None,50)
  def public(e,s):return Response('PUBLIC')(e,s)
  self.public=public;self.app=create_broker_server(public,enabled=True,service=self.s,origin=O,client_identity=lambda r:'trusted',worker_evidence=evidence,clock=lambda:101,budget=self.b,transport=self.t);self.client=Client(self.app,Response)
 def login(self,c=None,name='alice'):
  c=c or self.client;csrf=c.get('/account/preauth',base_url=O).json['csrf'];r=c.post('/account/login',base_url=O,json={'username':name,'password':PW,'csrf':csrf},headers={'Origin':O});self.assertEqual(r.status_code,200);return r.json['csrf']
 def post(self,data,csrf,path='ships',c=None):return(c or self.client).post('/api/finder-broker/'+path,base_url=O,json=data,headers={'Origin':O,'X-CSRF-Token':csrf})
 def test_off_no_injected_reads(self):self.assertIs(create_broker_server(self.public),self.public)
 def test_public_unchanged_closed_route(self):
  self.assertEqual(self.client.get('/api/news',base_url=O).data,b'PUBLIC');self.assertEqual(self.client.post('/account/signup',base_url=O,json={},headers={'Origin':O}).status_code,404)
 def test_authenticated_ships_once_replay_no_hashes_or_cachedanswer(self):
  t=self.login()
  with patch.object(FixedProxyTransport,'execute',return_value={'status':200,'body':b'{"ok":true,"vessels":[]}'})as call:
   r=self.post({'nonce':'n'*24,'port':'INNSA'},t);self.assertEqual(r.status_code,200)
   r=self.post({'nonce':'n'*24,'port':'INNSA'},t);self.assertEqual(r.status_code,409);self.assertEqual(r.json['state'],'replay_status_only');self.assertNotIn('hash',r.text);self.assertEqual(call.call_count,1)
 def test_cross_uid_nonce_identity_no_otherstatus(self):
  t=self.login();other=Client(self.app,Response);u=self.login(other,'bobby')
  with patch.object(FixedProxyTransport,'execute',return_value={'status':200,'body':b'{}'})as call:
   self.post({'nonce':'n'*24,'port':'INNSA'},t);r=self.post({'nonce':'n'*24,'port':'INNSA'},u,c=other);self.assertEqual(r.status_code,409);self.assertNotIn('replay_status_only',r.text);self.assertEqual(call.call_count,1)
 def test_missing_session_origin_csrf_no_budget(self):
  r=self.post({'nonce':'n'*24,'port':'INNSA'},'bad');self.assertEqual(r.status_code,401);self.assertEqual(self.c.writes,0)
  self.login();self.assertEqual(self.post({'nonce':'n'*24,'port':'INNSA'},'bad').status_code,403);self.assertEqual(self.c.writes,0)
 def test_ai_catalog_disabled_and_extra_url_headers_refused(self):
  t=self.login()
  with patch.object(FixedProxyTransport,'execute',side_effect=AssertionError):
   self.assertEqual(self.post({'nonce':'n'*24,'provider':'groq','model':'invented','prompt':'hello'},t,'ai').status_code,409)
   self.assertEqual(self.post({'nonce':'n'*24,'port':'INNSA','url':'https://evil.example'},t).status_code,400)
  self.assertEqual(self.c.writes,0)
 def test_revoked_uid_before_receipt_and_transport(self):
  t=self.login();self.store.sessions.clear()
  with patch.object(FixedProxyTransport,'execute',side_effect=AssertionError):self.assertEqual(self.post({'nonce':'n'*24,'port':'INNSA'},t).status_code,401)
  self.assertEqual(self.c.writes,0)
 def test_v2_preflight_not_v1(self):
  from integration.finder198_v2_preflight import inspect_budget_v2
  from integration.finder198_budget import inspect_budget,BudgetRefused
  from tests.test_collector197b_preflight import Client as MC,Cursor
  c=MC();c.grants=[{'resource':{'db':'geo_intel','collection':'finder_budget198'},'actions':['find','listIndexes','update']}]
  self.c.list_indexes=lambda **kw:Cursor([{'key':{'_id':1}}]);c.db.get_collection=lambda *a,**kw:self.c
  self.assertIs(inspect_budget_v2(c),self.c)
  with self.assertRaises(BudgetRefused):inspect_budget(c)
