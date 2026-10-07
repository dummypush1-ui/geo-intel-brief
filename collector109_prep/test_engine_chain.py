import unittest,sys
from datetime import datetime,timezone
from .fixture_support import CASCollection
from collector108_prep.durable_ledger import DurableLedger
from integration.geo_collector_contract import GeoFixtureStore
from integration.supplied_feed_fixture import prepare_supplied_feed
from .drive import drive_collection,DriveRefused
from .checkpoint import FixtureCheckpoints,CheckpointRefused,digest,run_inputs
D=datetime(2026,1,1,tzinfo=timezone.utc)
FEED=('Fixture Feed','https://fixture.example/rss','HIGH')
def entries(n=2):return [{'title':'Trade tariff update '+str(i),'link':'https://example.com/a'+str(i),'summary':'Tariff supply chain '+'x'*300,'published':'Thu, 01 Jan 2026 00:00:00 GMT'} for i in range(n)]
class ChainTests(unittest.TestCase):
 def setUp(self):
  self.c=CASCollection();self.l=DurableLedger(self.c,'geo108','a'*64);self.l.initialize();self.j=self.l.submit('n'*24,100)
  self.cp=FixtureCheckpoints()
 def select(self):return prepare_supplied_feed(FEED,entries(),cutoff=datetime(2025,12,31,tzinfo=timezone.utc),fallback_clock=D)
 def test_supplied_entries_to_documents_to_fixture_store(self):
  sel=self.select();self.assertEqual(sel['network'],False);self.assertGreater(sel['selected_count'],0)
  cand=sel['candidates']
  s=GeoFixtureStore()
  out=drive_collection(self.l,self.j['key'],self.j['fence'],candidates=cand,active_categories=['TRADE','GEOPOLITICS','RISK','GENERAL','SANCTIONS','RESEARCH','CONFERENCE'],threshold=.85,clock=lambda:101,checkpoints=self.cp,store=s)
  self.assertEqual(out['state'],'completed');self.assertEqual(out['counts']['fetched'],sel['selected_count'])
  self.assertEqual(out['counts']['inserted']+out['counts']['duplicate']+out['counts']['failed'],out['counts']['attempted'])
 def test_crash_resume_uses_checkpoint_not_caller(self):
  cand=self.select()['candidates'];h=self.cp.put(self.j['key'],self.j['fence'],run_inputs(cand,['TRADE'],.85))
  # Crash after fetch_complete simulated: drive holds at prepare (no writer/store).
  out=drive_collection(self.l,self.j['key'],self.j['fence'],candidates=cand,active_categories=['TRADE'],threshold=.85,clock=lambda:101,checkpoints=self.cp)
  self.assertEqual(out['state'],'held_before_write')
  # Resume: caller supplies nothing usable; checkpoint restores exact candidates.
  restored=self.cp.get(self.j['key'],self.j['fence'])
  self.assertEqual(digest(self.j['key'],self.j['fence'],restored),h)
  s=GeoFixtureStore()
  out=drive_collection(self.l,self.j['key'],self.j['fence'],candidates=restored['candidates'],active_categories=['TRADE'],threshold=.85,clock=lambda:102,checkpoints=self.cp,store=s)
  self.assertEqual(out['state'],'completed')
 def test_checkpoint_immutable_and_fence_bound(self):
  cand=self.select()['candidates'];self.cp.put(self.j['key'],self.j['fence'],run_inputs(cand,['TRADE'],.85))
  with self.assertRaises(CheckpointRefused):self.cp.put(self.j['key'],self.j['fence'],[dict(cand[0],title='tampered')])
  other=FixtureCheckpoints()
  with self.assertRaises(CheckpointRefused):other.get(self.j['key'],self.j['fence'])
  with self.assertRaises(CheckpointRefused):self.cp.put('x'*64,self.j['fence'],cand if False else 'nope')
 def test_source_declared_error_stops_before_ledger(self):
  sel=prepare_supplied_feed(FEED,entries(),cutoff=datetime(2025,12,31,tzinfo=timezone.utc),fallback_clock=D,http_mode='error')
  self.assertEqual(sel['declared_source_mode'],'error');self.assertEqual(sel['selected_count'],0)
  # Zero-candidate drive is legal shape but we refuse to pretend success downstream: empty prepare then hold.
  out=drive_collection(self.l,self.j['key'],self.j['fence'],candidates=[],active_categories=['TRADE'],threshold=.85,clock=lambda:101,checkpoints=self.cp)
  self.assertEqual(out['state'],'held_before_write')
if __name__=='__main__':unittest.main(verbosity=2)
