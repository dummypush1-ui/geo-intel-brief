import unittest,sys,threading
from .fixture_support import CASCollection
from collector108_prep.durable_ledger import DurableLedger,LedgerRefused
from integration.geo_collector_contract import GeoFixtureStore
from .drive import drive_collection,DriveRefused
from .checkpoint import FixtureCheckpoints
D=__import__('datetime').datetime(2026,1,1,tzinfo=__import__('datetime').timezone.utc)
def row(url='https://example.com/news'):return {'title':'Trade tariff order','url':url,'source':'Fixture','summary':'Supply chain tariff '+'x'*400,'published':D,'credibility':'HIGH'}
class Tests(unittest.TestCase):
 def setUp(self):
  self.c=CASCollection();self.l=DurableLedger(self.c,'geo108','a'*64);self.l.initialize()
  self.j=self.l.submit('n'*24,100);self.cp=FixtureCheckpoints()
 def drive(self,**kw):return drive_collection(self.l,self.j['key'],self.j['fence'],candidates=kw.pop('candidates',[row()]),active_categories=['TRADE'],threshold=.85,clock=lambda:101,checkpoints=self.cp,**kw)
 def test_full_cycle_fixture_store_completed_counts(self):
  s=GeoFixtureStore();out=self.drive(store=s)
  self.assertEqual(out['state'],'completed');self.assertEqual(out['counts']['inserted'],1)
  self.assertEqual(self.l.status(self.j['key'])['phase'],'completed')
 def test_hold_without_writer_is_honest(self):
  out=self.drive();self.assertEqual(out['state'],'held_before_write')
  self.assertEqual(self.l.status(self.j['key'])['phase'],'prepare_complete')
 def test_resume_after_simulated_crash_between_phases(self):
  # Drive partway (hold), then a fresh adapter resumes from durable phase.
  self.drive()
  l2=DurableLedger(self.c,'geo108','a'*64);s=GeoFixtureStore()
  out=drive_collection(l2,self.j['key'],self.j['fence'],candidates=[row()],active_categories=['TRADE'],threshold=.85,clock=lambda:102,checkpoints=self.cp,store=s)
  self.assertEqual(out['state'],'completed');self.assertEqual(len(s.snapshot()),1)
 def test_wrong_fence_never_drives(self):
  with self.assertRaises(LedgerRefused):drive_collection(self.l,self.j['key'],self.j['fence']+1,candidates=[row()],active_categories=['TRADE'],threshold=.85,clock=lambda:101,checkpoints=self.cp,store=GeoFixtureStore())
  self.assertEqual(self.l.status(self.j['key'])['phase'],'accepted')
 def test_uncertain_writer_latches_no_retry(self):
  class Bad:
   def write(self,docs,clock):return {'state':'uncertain','attempted':len(docs),'uncertain_count':len(docs)}
  out=self.drive(writer=Bad());self.assertEqual(out['state'],'uncertain_after_write')
  with self.assertRaises(DriveRefused):self.drive(writer=Bad())
  with self.assertRaises(LedgerRefused):self.l.submit('q'*24,102)
 def test_completed_job_not_drivable_and_replay(self):
  self.drive(store=GeoFixtureStore())
  with self.assertRaises(DriveRefused):self.drive(store=GeoFixtureStore())
  r=self.l.submit('n'*24,150);self.assertEqual(r['phase'],'completed')
 def test_writer_exception_marks_uncertain_not_failed_before_write(self):
  class Explode:
   def write(self,docs,clock):raise RuntimeError('driver')
  out=self.drive(writer=Explode());self.assertEqual(out['state'],'uncertain_after_write')
 def test_malformed_candidates_refuse_before_ledger_advance(self):
  with self.assertRaises(DriveRefused):self.drive(candidates='notalist')
  self.assertEqual(self.l.status(self.j['key'])['phase'],'accepted')
if __name__=='__main__':unittest.main(verbosity=2)
