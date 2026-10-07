import unittest,copy
from types import SimpleNamespace
from bson import BSON
from collector109_prep.fixture_support import CASCollection
from collector108_prep.durable_ledger import DurableLedger,LedgerRefused
from collector110_prep.durable_checkpoint import DurableCheckpoints
from datetime import datetime,timezone
from .drive_durable import drive_collection,DriveRefused
class BsonCheckpointCollection:
 def __init__(self):
  self.row=None;self.write_concern=SimpleNamespace(document={'w':'majority','j':True,'wtimeout':5000});self.read_concern=SimpleNamespace(document={'level':'majority'})
 def update_one(self,q,u,upsert=False):
  if self.row is None:self.row=BSON.encode(u['$setOnInsert'])
  return SimpleNamespace(acknowledged=True)
 def find_one(self,q):return BSON(self.row).decode()if self.row else None

def inputs():return [{'title':'Trade tariff order','url':'https://example.com/news','source':'Fixture','summary':'Supply chain tariff '+'x'*400,'published':datetime(2026,1,1,tzinfo=timezone.utc),'credibility':'HIGH'}]
class Tests(unittest.TestCase):
 def setUp(self):
  self.lc=CASCollection();self.l=DurableLedger(self.lc,'geo108','a'*64);self.l.initialize();self.j=self.l.submit('n'*24,100);self.cc=BsonCheckpointCollection();self.cp=DurableCheckpoints(self.cc)
 def call(self,**kw):
  a=dict(candidates=inputs(),active_categories=['TRADE'],threshold=.85,clock=lambda:101,checkpoints=self.cp);a.update(kw)
  return drive_collection(self.l,self.j['key'],self.j['fence'],**a)
 def test_hold_and_new_adapters_resume_same_inputs(self):
  self.assertEqual(self.call()['state'],'held_before_write')
  self.l=DurableLedger(self.lc,'geo108','a'*64);self.cp=DurableCheckpoints(self.cc)
  self.assertEqual(self.call()['state'],'held_before_write')
 def test_wrong_inputs_no_write(self):
  self.call();w=SimpleNamespace(write=lambda *a:(_ for _ in()).throw(AssertionError('Must not call')))
  with self.assertRaises(DriveRefused):self.call(threshold=.8,writer=w)
 def test_no_checkpoint_resume_refuses(self):
  self.call();self.cp=DurableCheckpoints(BsonCheckpointCollection())
  with self.assertRaises(DriveRefused):self.call()
 def test_budget_refuses_before_ledger_mutation(self):
  before=self.lc.calls
  for c in ([{'summary':'x'*10001}],[[[]]*1000]*1000):
   with self.assertRaises(DriveRefused):self.call(candidates=c)
  self.assertEqual(self.lc.calls,before+2) # status reads only
  self.assertEqual(self.l.status(self.j['key'])['phase'],'accepted')
 def test_store_unacknowledged_stops_before_running(self):
  self.cc.update_one=lambda *a,**k:SimpleNamespace(acknowledged=False)
  with self.assertRaises(DriveRefused):self.call()
  self.assertEqual(self.l.status(self.j['key'])['phase'],'accepted')
 def test_started_never_retries_after_adapter_restart(self):
  self.call();self.l.advance(self.j['key'],self.j['fence'],'write_started',101,{'attempted':1})
  self.l=DurableLedger(self.lc,'geo108','a'*64);self.cp=DurableCheckpoints(self.cc)
  w=SimpleNamespace(write=lambda *a:(_ for _ in()).throw(AssertionError('Must not call')))
  with self.assertRaises(DriveRefused):self.call(writer=w)
if __name__=='__main__':unittest.main(verbosity=2)
