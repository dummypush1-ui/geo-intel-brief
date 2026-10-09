import unittest,copy
from unittest.mock import patch
from integration.replay199_collector import run_archive_cycle,archive_collector_status
from integration.replay199_adapters import ArchivedCollectorLedger
from integration.collector197_config import CollectorConfig
from integration.collector197_coverage import CoverageCheckpoints,catalog_fingerprint
from integration.collector197_job_runtime import JobRuntimeEvidence,JOB_BYTES,PARENT_BYTES,COORDINATOR_BYTES
from integration.geo_article_writer import GeoArticleWriter
from tests.test_replay199a import Client
from tests.test_collector197c import inputs,cov
from tests.test_collector197a import candidates,Checkpoints

def proof(now=100):return JobRuntimeEvidence(catalog_fingerprint(),'owner-fixture','host-fixture',now,now+100,JOB_BYTES,JOB_BYTES,0,1,PARENT_BYTES,COORDINATOR_BYTES,90,True,True,True,True)
class Tests(unittest.TestCase):
 def setUp(self):
  self.db=Client('collector');self.db.provision(0);self.core=self.db.core();self.ledger=ArchivedCollectorLedger(self.core);self.pc=Checkpoints();self.cp=CoverageCheckpoints(self.pc);self.now=100;self.calls=0
  # Exact writer object constructed from reviewed disposable article fixture.
  from tests.test_collector197a import Tests
  f=Tests();f.setUp();self.writer=f.writer
 def fetch(self,**kwargs):
  self.calls+=1;return {'candidates':candidates(),'source_states':cov()['source_states'],'all_sources_healthy':False}
 def run(self,*a,**kw):return super().run(*a,**kw)
 def cycle(self,nonce='n'*24,writer=None,**overrides):
  values=dict(ledger=self.ledger,checkpoints=self.cp,nonce=nonce,fetch=self.fetch,categories=['TRADE'],threshold=.85,clock=lambda:self.now,monotonic=lambda:0,writer=writer,runtime_evidence=lambda:proof(self.now));values.update(overrides);return run_archive_cycle(CollectorConfig(True),**values)
 def test_completed_rollover_oldnonce_no_fetch_write_and_retainedcoverage(self):
  with patch.object(GeoArticleWriter,'write',return_value={'state':'inserted','attempted':1,'inserted_count':1,'duplicate_count':0,'failed_count':0,'uncertain_count':0,'retry_safe':False})as write:
   out=self.cycle(writer=self.writer);self.assertEqual(out['state'],'completed');key=out['job'];self.db.data['collector_checkpoints197']=copy.deepcopy(self.pc.rows);self.core.rollover(expected_revision=self.db.data[self.db.sn][self.db.identity]['revision'],checkpoints=self.db.cp)
   out=self.cycle(writer=self.writer);self.assertEqual(out['state'],'replay_held');self.assertEqual(self.calls,1);self.assertEqual(write.call_count,1);status=archive_collector_status(self.ledger,self.cp,key);self.assertTrue(status['archived']);self.assertEqual(status['coverage'],cov())
   out=self.cycle(nonce='z'*24,writer=self.writer);self.assertEqual(out['state'],'completed');self.assertEqual(self.calls,2);self.assertEqual(write.call_count,2)
 def test_off_no_collaborator_access(self):
  self.assertEqual(run_archive_cycle(CollectorConfig(False),ledger=None,checkpoints=None,nonce=None,fetch=None,categories=None,threshold=None,clock=None)['state'],'disabled')
 def test_missing_provider_and_stale_proof_before_claim_fetch(self):
  for provider in (None,lambda:proof(0)):
   with self.assertRaises(ValueError):self.cycle(runtime_evidence=provider)
  self.assertEqual(self.db.starts,0);self.assertEqual(self.calls,0)
 def test_lost_claim_and_running_ack_no_fetch(self):
  for cut in (1,2):
   self.setUp();original=self.db.s.replace_one;n=[0]
   def replace(*a,**kw):
    n[0]+=1
    if n[0]==cut:self.db.fail='commit_after'
    return original(*a,**kw)
   self.db.s.replace_one=replace
   with self.assertRaises(ValueError):self.cycle()
   self.assertEqual(self.calls,0);self.assertTrue(self.core.uncertain)
 def test_lost_write_started_ack_no_write(self):
  original=self.db.s.replace_one;n=[0]
  def replace(*a,**kw):
   n[0]+=1
   if n[0]==5:self.db.fail='commit_after'
   return original(*a,**kw)
  self.db.s.replace_one=replace
  with patch.object(GeoArticleWriter,'write',side_effect=AssertionError)as write:
   with self.assertRaises(ValueError):self.cycle(writer=self.writer)
   self.assertEqual(write.call_count,0)
 def test_unknown_writer_keeps_ticket_no_refetch(self):
  with patch.object(GeoArticleWriter,'write',side_effect=RuntimeError):
   with self.assertRaises(ValueError):self.cycle(writer=self.writer)
  j=self.db.data[self.db.sn][self.db.identity]['active'];self.assertEqual(j['phase'],'uncertain_after_write');out=self.cycle();self.assertEqual(out['state'],'replay_held');self.assertEqual(self.calls,1)
 def test_provider_refresh_before_write_can_fail_no_write(self):
  n=[0]
  def provider():
   n[0]+=1
   if n[0]>=4:raise ValueError()
   return proof()
  with patch.object(GeoArticleWriter,'write',side_effect=AssertionError)as write:
   with self.assertRaises(ValueError):self.cycle(writer=self.writer,runtime_evidence=provider)
   self.assertEqual(write.call_count,0)
 def test_corrupt_archive_newnonce_fails_before_fetch(self):
  self.db.provision(1);self.core.rollover(expected_revision=0,checkpoints=self.db.cp);del self.db.data[self.db.an]['batch:1']
  with self.assertRaises(ValueError):self.cycle()
  self.assertEqual(self.calls,0)
 def test_missing_retained_checkpoint_no_falsecoverage_or_fetch(self):
  with patch.object(GeoArticleWriter,'write',return_value={'state':'inserted','attempted':1,'inserted_count':1,'duplicate_count':0,'failed_count':0,'uncertain_count':0,'retry_safe':False}):out=self.cycle(writer=self.writer)
  self.pc.rows.clear()
  with self.assertRaises(ValueError):archive_collector_status(self.ledger,self.cp,out['job'])
  with self.assertRaises(ValueError):self.cycle()
  self.assertEqual(self.calls,1)
 def test_full64_rollover_old_nonce_no_fetch_then_new65_once(self):
  with patch.object(GeoArticleWriter,'write',return_value={'state':'inserted','attempted':1,'inserted_count':1,'duplicate_count':0,'failed_count':0,'uncertain_count':0,'retry_safe':False})as write:
   for i in range(64):self.cycle(nonce=('nonce'+str(i)).ljust(24,'x'),writer=self.writer)
   d=self.db.data[self.db.sn][self.db.identity];self.assertEqual(len(d['history']),64);self.db.data['collector_checkpoints197']=copy.deepcopy(self.pc.rows);self.core.rollover(expected_revision=d['revision'],checkpoints=self.db.cp)
   self.assertEqual(self.cycle(nonce='nonce0'.ljust(24,'x'))['state'],'replay_held');self.assertEqual(self.calls,64);self.assertEqual(write.call_count,64)
   out=self.cycle(nonce='fresh'.ljust(24,'x'),writer=self.writer);self.assertEqual(out['state'],'completed');self.assertEqual(self.calls,65);self.assertEqual(self.db.data[self.db.sn][self.db.identity]['fence'],65)
 def test_old_runtime_selection_unchanged(self):
  from pathlib import Path
  root=Path(__file__).resolve().parents[1]
  for name in ('production_entry.py','public_live107.py','integration/collector197_job.py','integration/collector197_orchestrator.py'):self.assertNotIn('replay199',(root/name).read_text())
