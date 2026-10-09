import copy,unittest
from dataclasses import replace
from unittest.mock import patch
from collector113_prep.feed_composition import original_catalog
from collector108_prep.durable_ledger import DurableLedger
from integration.collector197_coverage import CoverageCheckpoints,CoverageRefused,coverage_hash,catalog_fingerprint
from integration.collector197_runtime_evidence import RuntimeEvidence,EvidenceRefused
from integration.collector197_orchestrator import run_cycle
from integration.collector197_config import CollectorConfig
from tests.test_collector197a import Checkpoints,candidates,Tests as _Base

def cov():return {'catalog':catalog_fingerprint(),'source_states':[{'index':i,'state':'unstarted'}for i in range(len(original_catalog()))],'all_sources_healthy':False}
def inputs():return {'candidates':candidates(),'active_categories':['TRADE'],'threshold':.85}
def evidence():return RuntimeEvidence(catalog_fingerprint(),'owner-channel-ref','host-probe-ref',100,200,1536*1024*1024,121,True,True,True)
def _base_factory():
 from tests.test_collector197a import Tests
 return Tests()
del _Base
class CoverageTests(unittest.TestCase):
 def setUp(self):self.c=Checkpoints();self.cp=CoverageCheckpoints(self.c);self.key='a'*64
 def test_atomic_roundtrip_reinstantiated_bson(self):
  from bson import BSON
  self.cp.put(self.key,1,inputs(),cov());self.c.rows[self.key]=BSON(BSON.encode(self.c.rows[self.key])).decode()
  self.assertEqual(CoverageCheckpoints(self.c).get(self.key,1),{'inputs':inputs(),'coverage':cov()})
 def test_coverage_mutation_refused(self):
  self.cp.put(self.key,1,inputs(),cov());self.c.rows[self.key]['coverage_hash']='0'*64
  with self.assertRaises(CoverageRefused):self.cp.get(self.key,1)
 def test_input_mutation_refused(self):
  self.cp.put(self.key,1,inputs(),cov());self.c.rows[self.key]['input_hash']='0'*64
  with self.assertRaises(CoverageRefused):self.cp.get(self.key,1)
 def test_immutable_coverage_different_refused(self):
  self.cp.put(self.key,1,inputs(),cov());v=cov();v['source_states'][0]['state']='selected'
  with self.assertRaises(CoverageRefused):self.cp.put(self.key,1,inputs(),v)
 def test_closed_full_catalog_states(self):
  for mutate in (lambda v:v['source_states'].pop(),lambda v:v.update(all_sources_healthy=True),lambda v:v.update(catalog='b'*64),lambda v:v['source_states'][0].update(index=True)):
   v=cov();mutate(v)
   with self.assertRaises(CoverageRefused):self.cp.put(self.key,1,inputs(),v)
 def test_unknown_version_refused(self):
  self.cp.put(self.key,1,inputs(),cov());self.c.rows[self.key]['version']=1
  with self.assertRaises(CoverageRefused):self.cp.get(self.key,1)
 def test_unacknowledged_no_success(self):
  from types import SimpleNamespace
  self.c.update_one=lambda *a,**kw:SimpleNamespace(acknowledged=False)
  with self.assertRaises(CoverageRefused):self.cp.put(self.key,1,inputs(),cov())
 def test_hash_domain_separated(self):
  from collector109_prep.checkpoint import digest
  self.assertNotEqual(coverage_hash(self.key,1,cov()),digest(self.key,1,cov()))
 def test_fence_wrong_refused(self):
  self.cp.put(self.key,1,inputs(),cov())
  with self.assertRaises(CoverageRefused):self.cp.get(self.key,2)

class OrchestratorTests(unittest.TestCase):
 def test_coverage_checkpoint_before_prepare_replay_readback(self):
  b=_base_factory();b.setUp();cp=CoverageCheckpoints(b.pc)
  def fetch(**kw):return {'candidates':candidates(),'source_states':cov()['source_states'],'all_sources_healthy':False}
  kw=dict(ledger=b.ledger,checkpoints=cp,nonce='n'*24,fetch=fetch,categories=['TRADE'],threshold=.85,clock=lambda:100,monotonic=lambda:0)
  out=run_cycle(CollectorConfig(True),**kw);self.assertEqual(out['coverage'],cov())
  kw['fetch']=lambda **kw:(_ for _ in ()).throw(AssertionError())
  out=run_cycle(CollectorConfig(True),**kw);self.assertEqual(out['coverage'],cov());self.assertEqual(out['state'],'replay_held')
 def test_no_envelope_cannot_write(self):
  b=_base_factory();b.setUp()
  with self.assertRaises(ValueError):run_cycle(CollectorConfig(True),ledger=b.ledger,checkpoints=CoverageCheckpoints(b.pc),nonce='n'*24,fetch=lambda **kw:candidates(),categories=['TRADE'],threshold=.85,clock=lambda:100,monotonic=lambda:0,writer=b.writer)
  self.assertEqual(b.c.doc['history'][0]['phase'],'failed_before_write')

class EvidenceTests(unittest.TestCase):
 def test_valid_reference_record(self):self.assertTrue(evidence().validate(101)['runtime_bwrap'])
 def test_expiry_memory_timeout_no_boolean_pass(self):
  for v in (replace(evidence(),expires_at=101),replace(evidence(),available_memory_bytes=512*1024*1024),replace(evidence(),wsgi_timeout_seconds=120),replace(evidence(),bwrap_pid_namespace=1)):
   with self.assertRaises(EvidenceRefused):v.validate(101)
 def test_true_no_provider_no_public_or_client(self):
  from production_entry import build_production_app
  with self.assertRaises(EvidenceRefused):build_production_app({'COLLECTION_ENABLED':'true'},public_builder=lambda e:(_ for _ in ()).throw(AssertionError()))
 def test_no_environment_shortcut(self):
  from production_entry import build_production_app
  with self.assertRaises(EvidenceRefused):build_production_app({'COLLECTION_ENABLED':'true','RUNTIME_VERIFIED':'true'},public_builder=lambda e:None)
 def test_dispatch_public_routes_unchanged(self):
  from integration.collector197_dispatcher import CollectorDispatcher
  public=lambda e,s:'public';collector=lambda e,s:'collector';d=CollectorDispatcher(public,collector)
  for path in ('/','/workspace','/health','/api/collective','/api/news'):
   self.assertEqual(d({'PATH_INFO':path},None),'public')
  for path in ('/api/collect','/api/collect/status/a'):
   self.assertEqual(d({'PATH_INFO':path},None),'collector')

class ProductionCompositionTests(unittest.TestCase):
 def test_real_dispatch_owner_boundary_public_unchanged(self):
  from flask import Flask,jsonify
  from production_entry import build_production_app
  from tests.test_collector197b_preflight import Client
  c=Client();c.close=lambda:None;public=Flask('public_fixture')
  @public.get('/health')
  def health():return jsonify(public=True)
  @public.get('/workspace')
  def workspace():return 'home'
  seen=[]
  def builder(env):seen.append(env);return public
  env={'COLLECTION_ENABLED':'true','GEO_WRITER_MONGODB_URI':'fixture','COLLECTOR_TRIGGER_SECRET':'x'*48,'COLLECTOR_PROFILE_FINGERPRINT':'a'*64,'GEO_MONGODB_URI':'reader'}
  app=build_production_app(env,builder,runtime_evidence=evidence,collector_client_factory=lambda uri:c,clock=lambda:101)
  client=app.test_client()
  self.assertTrue(client.get('/health').json['public'])
  self.assertEqual(client.get('/workspace').data,b'home')
  self.assertEqual(client.post('/api/collect',json={}).status_code,401)
  self.assertEqual(client.get('/api/collect/status/a').status_code,401)
  self.assertEqual(seen[0]['GEO_MONGODB_URI'],'reader');self.assertEqual(seen[0]['COLLECTION_ENABLED'],'false')
  self.assertEqual(env['COLLECTION_ENABLED'],'true')
 def test_expired_evidence_before_ledger_on_request(self):
  from flask import Flask
  from production_entry import build_production_app
  from tests.test_collector197b_preflight import Client
  clock=[101];c=Client();c.close=lambda:None
  env={'COLLECTION_ENABLED':'true','GEO_WRITER_MONGODB_URI':'fixture','COLLECTOR_TRIGGER_SECRET':'x'*48,'COLLECTOR_PROFILE_FINGERPRINT':'a'*64}
  app=build_production_app(env,lambda e:Flask('expiry_fixture'),runtime_evidence=evidence,collector_client_factory=lambda uri:c,clock=lambda:clock[0])
  clock[0]=200
  r=app.test_client().post('/api/collect',json={'nonce':'n'*24,'timestamp':200},headers={'Authorization':'Bearer '+'x'*48})
  self.assertEqual(r.status_code,503);self.assertEqual(r.json['error'],'runtime_evidence_unavailable')
