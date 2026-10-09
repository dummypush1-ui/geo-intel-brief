import unittest,copy
from unittest.mock import patch
from werkzeug.test import Client as HTTPClient
from werkzeug.wrappers import Response
from tests import test_native200ba as setup
from tests.test_replay199cb import proof
from tests.test_collector197a import candidates
from tests.test_collector197c import cov
from integration.native200_admission_preflight import VALIDATORS
from integration.native200_admission_core import AdmissionArchiveCore
from integration.native200_admission_adapters import AdmissionProxyReceiptBudget
from integration.native200_admission_store import AdmissionStore
from integration.native201_ledger import NativeCheckpointCollectorLedger
from integration.native201_coverage import NativeCoverageCheckpoints
from integration.native201_collector import run_native_cycle,native_collector_status
from integration.native201_broker import create_native_broker_server,proxy_request_native
from integration.native201_composition import build_native_composition
from integration.collector197_config import CollectorConfig
from integration.finder198_transport import FixedProxyTransport
from integration.geo_article_writer import GeoArticleWriter
class Tests(unittest.TestCase):
 setup_server=setup.Tests.setup_server
 def setUp(self):
  self.patch=patch('integration.native200_preflight.VALIDATORS',VALIDATORS);self.patch.start();self.addCleanup(self.patch.stop)
  self.s,self.c,self.f,self.key=self.setup_server('collector',count=0);self.core=AdmissionArchiveCore(self.c,family='collector',fingerprint='a'*64,enabled=True);self.ledger=NativeCheckpointCollectorLedger(self.core);self.cp=NativeCoverageCheckpoints(AdmissionStore(self.core.provider,'collector_checkpoints197'));self.calls=0
  from tests.test_collector197a import Tests as WriterFixture
  fixture=WriterFixture();fixture.setUp();self.writer=fixture.writer
 def fetch(self,**kw):self.calls+=1;return {'candidates':candidates(),'source_states':cov()['source_states'],'all_sources_healthy':False}
 def cycle(self,**kw):
  values=dict(ledger=self.ledger,checkpoints=self.cp,nonce='n'*24,fetch=self.fetch,categories=['TRADE'],threshold=.85,clock=lambda:100,monotonic=lambda:0,writer=None,runtime_evidence=lambda:proof());values.update(kw);return run_native_cycle(CollectorConfig(True),**values)
 def broker(self):
  s,c,f,key=self.setup_server(count=0);s.data[f.sn][f.identity]['last_clock']=100;core=AdmissionArchiveCore(c,family='broker',enabled=True);b=AdmissionProxyReceiptBudget(core);t=FixedProxyTransport({'FINDER_PROXY_BASE_URL':'https://hsn-ai-proxy.onrender.com','FINDER_PROXY_SECRET':'x'*48},enabled=True);return s,c,f,key,core,b,t
 def test_native_cycle_complete_atomic_checkpoint_replay_rollover(self):
  with patch.object(GeoArticleWriter,'write',return_value={'state':'inserted','attempted':1,'inserted_count':1,'duplicate_count':0,'failed_count':0,'uncertain_count':0,'retry_safe':False})as write:
   out=self.cycle(writer=self.writer);self.assertEqual(out['state'],'completed');self.core.rollover(expected_revision=self.s.data[self.f.sn][self.f.identity]['revision'],checkpoints=self.cp.c);self.assertEqual(self.cycle(writer=self.writer)['state'],'replay_held');self.assertEqual(self.calls,1);self.assertEqual(write.call_count,1);status=native_collector_status(self.ledger,self.cp,out['job']);self.assertTrue(status['archived']);self.assertEqual(status['coverage'],cov())
 def test_off_runtime_proof_bad_envelope_before_io(self):
  self.assertEqual(run_native_cycle(CollectorConfig(False),ledger=None,checkpoints=None,nonce=None,fetch=None,categories=None,threshold=None,clock=None)['state'],'disabled')
  with self.assertRaises(ValueError):self.cycle(runtime_evidence=None)
  self.assertEqual(self.calls,0)
  with self.assertRaises(ValueError):self.cycle(fetch=lambda **kw:{'candidates':[]})
  self.assertFalse(self.s.data['collector_checkpoints197'])
 def test_write_start_unknown_no_article_write_and_no_refetch(self):
  self.s.fail=lambda d:d.get('update')==self.f.sn and d['updates'][0]['u']['active']and d['updates'][0]['u']['active']['phase']=='write_started'
  with patch.object(GeoArticleWriter,'write',side_effect=AssertionError)as write:
   with self.assertRaises(ValueError):self.cycle(writer=self.writer)
   self.assertEqual(write.call_count,0);self.assertEqual(self.cycle()['state'],'replay_held');self.assertEqual(self.calls,1)
 def test_writer_unknown_phase_held_not_refetch(self):
  with patch.object(GeoArticleWriter,'write',side_effect=RuntimeError):
   with self.assertRaises(ValueError):self.cycle(writer=self.writer)
  self.assertEqual(self.s.data[self.f.sn][self.f.identity]['active']['phase'],'uncertain_after_write');self.assertEqual(self.cycle()['state'],'replay_held');self.assertEqual(self.calls,1)
 def test_broker_known_ack_before_transport_replay_no_resend(self):
  s,c,f,key,core,b,t=self.broker()
  with patch.object(FixedProxyTransport,'execute',return_value={'status':200,'body':b'{}'})as call:
   out=proxy_request_native(b,t,nonce='n'*24,operation='ships',port='ALL',principal_hash='e'*64,clock=lambda:100);self.assertEqual(out['state'],'complete');core.rollover(expected_revision=3);self.assertEqual(proxy_request_native(b,t,nonce='n'*24,operation='ships',port='ALL',principal_hash='e'*64,clock=lambda:100)['state'],'replay_status_only');self.assertEqual(call.call_count,1)
 def test_broker_start_unknown_no_transport(self):
  s,c,f,key,core,b,t=self.broker();s.fail=lambda d:d.get('update')==f.sn and d['updates'][0]['u']['receipts'][-1]['phase']=='send_started'
  with patch.object(FixedProxyTransport,'execute',side_effect=AssertionError)as call:
   with self.assertRaises(ValueError):proxy_request_native(b,t,nonce='n'*24,operation='ships',port='ALL',principal_hash='e'*64,clock=lambda:100)
   self.assertEqual(call.call_count,0)
 def test_native_composition_auth_before_db_status_and_public(self):
  s,c,f,key,core,b,t=self.broker()
  from integration.accounts.service import AccountService
  from integration.accounts.store import MemoryStore
  from tests.test_finder198a import O,PW,evidence
  store=MemoryStore();service=AccountService(store,b'x'*48,lambda:100,signup_mode='closed',allowed_origins=[O]);store.create_account('alice',{'uid':'alice','password':service.hasher.hash(PW),'created':100,'pwv':0},None,50);public=lambda e,s:Response('PUBLIC')(e,s)
  app=build_native_composition(public,enabled=True,ledger=self.ledger,checkpoints=self.cp,status_secret='s'*48,job_evidence=lambda:proof(),clock=lambda:100,service=service,origin=O,client_identity=lambda r:'trusted',worker_evidence=evidence,budget=b,transport=t);h=HTTPClient(app,Response);before=len(self.s.commands)
  self.assertEqual(h.get('/api/collect/status/'+'a'*64).status_code,401);self.assertEqual(len(self.s.commands),before);self.assertEqual(h.get('/workspace').data,b'PUBLIC');self.assertIs(build_native_composition(public),public)
  out=self.cycle();r=h.get('/api/collect/status/'+out['job'],headers={'Authorization':'Bearer '+'s'*48});self.assertEqual(r.status_code,200);self.assertEqual(r.json['coverage'],cov());self.assertEqual(r.headers['Cache-Control'],'no-store')
 def test_old_gates_and_production_remain_unselected(self):
  from integration.replay199_composition import build_archive_composition
  from integration.replay199_broker import proxy_request_archive
  from pathlib import Path
  with self.assertRaises(ValueError):build_archive_composition(lambda e,s:[],enabled=True,ledger=self.ledger,checkpoints=self.cp)
  s,c,f,key,core,b,t=self.broker()
  with self.assertRaises(ValueError):proxy_request_archive(b,t,nonce='n'*24,operation='ships',port='ALL',principal_hash='e'*64,clock=lambda:100)
  for name in('production_entry.py','public_live107.py','integration/collector197_job.py'):self.assertNotIn('native201',(Path(__file__).resolve().parents[1]/name).read_text())
 def test_broker_http_auth_scope_catalog_closed(self):
  s,c,f,key,core,b,t=self.broker()
  from integration.accounts.service import AccountService
  from integration.accounts.store import MemoryStore
  from tests.test_finder198a import O,PW,evidence
  store=MemoryStore();service=AccountService(store,b'x'*48,lambda:100,signup_mode='closed',allowed_origins=[O]);store.create_account('alice',{'uid':'alice','password':service.hasher.hash(PW),'created':100,'pwv':0},None,50)
  h=HTTPClient(create_native_broker_server(lambda e,s:Response('PUBLIC')(e,s),enabled=True,service=service,origin=O,client_identity=lambda r:'trusted',worker_evidence=evidence,clock=lambda:100,budget=b,transport=t),Response)
  csrf=h.get('/account/preauth',base_url=O).json['csrf'];r=h.post('/account/login',base_url=O,json={'username':'alice','password':PW,'csrf':csrf},headers={'Origin':O});headers={'Origin':O,'X-CSRF-Token':r.json['csrf']}
  with patch.object(FixedProxyTransport,'execute',return_value={'status':200,'body':b'{}'})as call:
   body={'nonce':'n'*24,'port':'ALL'};self.assertEqual(h.post('/api/finder-broker/ships',base_url=O,json=body,headers=headers).status_code,200);r=h.post('/api/finder-broker/ships',base_url=O,json=body,headers=headers);self.assertEqual(r.status_code,409);self.assertEqual(set(r.json),{'ok','state','phase','status','response_bytes','cached_answer'});self.assertEqual(call.call_count,1)
   self.assertEqual(h.post('/api/finder-broker/ships',base_url=O,json={'nonce':'z'*24,'port':'ALL','url':'https://evil.invalid'},headers=headers).status_code,409)
   self.assertEqual(h.post('/api/finder-broker/ai',base_url=O,json={'nonce':'z'*24,'provider':'groq','model':'invented','prompt':'hello'},headers=headers).status_code,409);self.assertEqual(call.call_count,1)
 def test_expired_broker_response_unknown_global_held(self):
  s,c,f,key,core,b,t=self.broker();clock=[100]
  def execute(*args):clock[0]=130;return {'status':200,'body':b'{}'}
  with patch.object(FixedProxyTransport,'execute',side_effect=execute)as call:
   with self.assertRaises(ValueError):proxy_request_native(b,t,nonce='n'*24,operation='ships',port='ALL',principal_hash='e'*64,clock=lambda:clock[0])
   self.assertEqual(s.data[f.sn][f.identity]['active']['phase'],'unknown_held');clock[0]=700
   with self.assertRaises(ValueError):proxy_request_native(b,t,nonce='z'*24,operation='ships',port='ALL',principal_hash='e'*64,clock=lambda:clock[0])
   self.assertEqual(call.call_count,1)
 def test_cross_client_checkpoint_before_source_mutation(self):
  s,c,f,key,core,b,t=self.broker();wrong=NativeCoverageCheckpoints(AdmissionStore(core.provider,'collector_checkpoints197'));before=len(self.s.commands)
  with self.assertRaises(ValueError):self.cycle(checkpoints=wrong)
  self.assertEqual(len(self.s.commands),before);self.assertEqual(self.calls,0)
 def test_missing_retained_checkpoint_no_status_or_refetch(self):
  out=self.cycle();self.s.data['collector_checkpoints197'].clear()
  with self.assertRaises(ValueError):native_collector_status(self.ledger,self.cp,out['job'])
  with self.assertRaises(ValueError):self.cycle()
  self.assertEqual(self.calls,1)
