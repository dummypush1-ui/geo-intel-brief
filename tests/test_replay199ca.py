import unittest,copy
from unittest.mock import patch
from werkzeug.test import Client as HTTPClient
from werkzeug.wrappers import Response
from integration.replay199_broker import create_archive_broker_server
from integration.replay199_adapters import ArchivedProxyReceiptBudget
from integration.finder198_transport import FixedProxyTransport
from integration.accounts.service import AccountService
from integration.accounts.store import MemoryStore
from tests.test_finder198a import O,PW,evidence
from tests.test_replay199a import Client
class Tests(unittest.TestCase):
 def setUp(self):
  self.db=Client('broker');self.db.provision(0);self.db.data[self.db.sn][self.db.identity]['last_clock']=100;self.core=self.db.core();self.b=ArchivedProxyReceiptBudget(self.core);self.t=FixedProxyTransport({'FINDER_PROXY_BASE_URL':'https://hsn-ai-proxy.onrender.com','FINDER_PROXY_SECRET':'x'*48},enabled=True)
  self.store=MemoryStore();self.s=AccountService(self.store,b'x'*48,lambda:100,signup_mode='closed',allowed_origins=[O])
  for name in ('alice','bobby'):self.store.create_account(name,{'uid':name,'password':self.s.hasher.hash(PW),'created':100,'pwv':0},None,50)
  self.public=lambda e,s:Response('PUBLIC')(e,s)
  self.app=create_archive_broker_server(self.public,enabled=True,service=self.s,origin=O,client_identity=lambda r:'trusted',worker_evidence=evidence,clock=lambda:100,budget=self.b,transport=self.t);self.client=HTTPClient(self.app,Response);self.csrf=self.login(self.client,'alice')
 def login(self,c,name):
  csrf=c.get('/account/preauth',base_url=O).json['csrf'];r=c.post('/account/login',base_url=O,json={'username':name,'password':PW,'csrf':csrf},headers={'Origin':O});self.assertEqual(r.status_code,200);return r.json['csrf']
 def post(self,nonce='n'*24,port='ALL',c=None,csrf=None):return(c or self.client).post('/api/finder-broker/ships',base_url=O,json={'nonce':nonce,'port':port},headers={'Origin':O,'X-CSRF-Token':csrf or self.csrf})
 def test_synthetic_http_rollover_oldnonce_replay_no_secondsend_newnonce_once(self):
  with patch.object(FixedProxyTransport,'execute',return_value={'status':200,'body':b'{"vessels":[]}'})as call:
   self.assertEqual(self.post().status_code,200);self.core.rollover(expected_revision=3)
   r=self.post();self.assertEqual(r.status_code,409);self.assertFalse(r.json['cached_answer']);self.assertEqual(call.call_count,1)
   self.assertEqual(self.post(nonce='z'*24).status_code,200);self.assertEqual(call.call_count,2)
   self.assertEqual(set(r.json),{'ok','state','phase','status','response_bytes','cached_answer'})
 def test_cross_uid_oldnonce_and_wrong_operation_no_disclosure(self):
  other=HTTPClient(self.app,Response);token=self.login(other,'bobby')
  with patch.object(FixedProxyTransport,'execute',return_value={'status':200,'body':b'{}'})as call:
   self.post();self.core.rollover(expected_revision=3);r=self.post(c=other,csrf=token);self.assertEqual(r.status_code,409);self.assertNotIn('phase',r.json);self.assertEqual(call.call_count,1)
 def test_archive_corrupt_newnonce_before_transport(self):
  with patch.object(FixedProxyTransport,'execute',return_value={'status':200,'body':b'{}'})as call:
   self.post();self.core.rollover(expected_revision=3);del self.db.data[self.db.an]['batch:1'];self.assertEqual(self.post(nonce='z'*24).status_code,409);self.assertEqual(call.call_count,1)
 def test_claim_and_start_lost_ack_no_transport(self):
  for cut in ('claim','start'):
   self.setUp();original=self.db.s.replace_one;n=[0]
   def replace(*args,**kwargs):
    n[0]+=1
    if n[0]==(1 if cut=='claim'else 2):self.db.fail='commit_after'
    return original(*args,**kwargs)
   self.db.s.replace_one=replace
   with patch.object(FixedProxyTransport,'execute',side_effect=AssertionError):self.assertEqual(self.post().status_code,409)
   self.assertTrue(self.core.uncertain);self.assertIsNotNone(self.db.data[self.db.sn][self.db.identity]['active'])
 def test_finish_lost_ack_no_response_or_resend(self):
  original=self.db.s.replace_one;n=[0]
  def replace(*args,**kwargs):
   n[0]+=1
   if n[0]==3:self.db.fail='commit_after'
   return original(*args,**kwargs)
  self.db.s.replace_one=replace
  with patch.object(FixedProxyTransport,'execute',return_value={'status':200,'body':b'{"answer":"synthetic"}'})as call:
   self.assertEqual(self.post().status_code,409);self.assertEqual(call.call_count,1);self.assertEqual(self.post().status_code,409);self.assertEqual(call.call_count,1)
 def test_auth_before_archive_missingcsrf_revoked(self):
  self.store.sessions.clear()
  with patch.object(FixedProxyTransport,'execute',side_effect=AssertionError):self.assertEqual(self.post().status_code,401)
  self.assertEqual(self.db.starts,0)
 def test_empty_ai_catalog_closed_body_routes_public_off(self):
  self.assertIs(create_archive_broker_server(self.public),self.public);self.assertEqual(self.client.get('/workspace',base_url=O).data,b'PUBLIC')
  with patch.object(FixedProxyTransport,'execute',side_effect=AssertionError):
   r=self.client.post('/api/finder-broker/ai',base_url=O,json={'nonce':'n'*24,'provider':'groq','model':'invented','prompt':'hello'},headers={'Origin':O,'X-CSRF-Token':self.csrf});self.assertEqual(r.status_code,409)
   r=self.client.post('/api/finder-broker/ships',base_url=O,json={'nonce':'n'*24,'port':'ALL','url':'https://evil.example'},headers={'Origin':O,'X-CSRF-Token':self.csrf});self.assertEqual(r.status_code,409)
  self.assertEqual(self.db.starts,0)
 def test_old_selected_files_unchanged(self):
  from pathlib import Path
  import subprocess
  root=Path(__file__).resolve().parents[1]
  # Source fixture test must work without git metadata in the indexed export.
  self.assertNotIn('replay199',(root/'production_entry.py').read_text());self.assertNotIn('replay199',(root/'public_live107.py').read_text());self.assertNotIn('replay199',(root/'integration/collector197_job.py').read_text())
 def test_full64_rollover_oldnonce_then_new_once_laterwindow(self):
  from integration.replay199_broker import proxy_request_archive
  from integration.replay199_adapters import ArchivedProxyReceiptBudget
  c=Client('broker');c.provision(0);c.data[c.sn][c.identity]['last_clock']=100;core=c.core();budget=ArchivedProxyReceiptBudget(core);clock=[100];principal='e'*64
  with patch.object(FixedProxyTransport,'execute',return_value={'status':200,'body':b'{}'})as call:
   for i in range(64):
    clock[0]=100+i*600;proxy_request_archive(budget,self.t,nonce=('nonce'+str(i)).ljust(24,'x'),operation='ships',port='ALL',principal_hash=principal,clock=lambda:clock[0])
   core.rollover(expected_revision=192);out=proxy_request_archive(budget,self.t,nonce='nonce0'.ljust(24,'x'),operation='ships',port='ALL',principal_hash=principal,clock=lambda:clock[0]);self.assertEqual(out['state'],'replay_status_only');self.assertEqual(call.call_count,64)
   clock[0]+=600;proxy_request_archive(budget,self.t,nonce='fresh'.ljust(24,'x'),operation='ships',port='ALL',principal_hash=principal,clock=lambda:clock[0]);self.assertEqual(call.call_count,65);self.assertEqual(c.data[c.sn][c.identity]['fence'],65)
 def test_expired_unknown_global_active_not_released(self):
  clock=[100];from integration.replay199_broker import proxy_request_archive
  def execute(plan,body):clock[0]=130;return {'status':200,'body':b'{}'}
  with patch.object(FixedProxyTransport,'execute',side_effect=execute)as call:
   with self.assertRaises(ValueError):proxy_request_archive(self.b,self.t,nonce='n'*24,operation='ships',port='ALL',principal_hash='e'*64,clock=lambda:clock[0])
   clock[0]=700
   with self.assertRaises(ValueError):proxy_request_archive(self.b,self.t,nonce='z'*24,operation='ships',port='ALL',principal_hash='e'*64,clock=lambda:clock[0])
   self.assertEqual(call.call_count,1);self.assertEqual(self.db.data[self.db.sn][self.db.identity]['active']['phase'],'unknown_held')
