import unittest,threading
from datetime import datetime,timezone
from unittest.mock import patch
from .test_drive import row
from .fixture_support import CASCollection
from collector108_prep.durable_ledger import DurableLedger,LedgerRefused
from .checkpoint import FixtureCheckpoints,CheckpointRefused,digest,run_inputs
from .drive import drive_collection,DriveRefused,_receipt

class CountingWriter:
 def __init__(self,receipt=None):self.calls=0;self.receipt=receipt
 def write(self,docs,stamp):
  self.calls+=1
  return self.receipt if self.receipt is not None else {'state':'inserted','attempted':len(docs),'inserted_count':len(docs),'duplicate_count':0,'failed_count':0,'uncertain_count':0,'retry_safe':False}

class Safety(unittest.TestCase):
 def setUp(self):
  self.c=CASCollection();self.l=DurableLedger(self.c,'geo108','a'*64);self.l.initialize();self.j=self.l.submit('n'*24,100);self.cp=FixtureCheckpoints()
 def call(self,**kw):
  args=dict(candidates=[row()],active_categories=['TRADE'],threshold=.85,clock=lambda:101,checkpoints=self.cp)
  args.update(kw)
  return drive_collection(self.l,self.j['key'],args.pop('fence',self.j['fence']),**args)
 def started(self):
  self.call()
  self.l.advance(self.j['key'],self.j['fence'],'write_started',101,{'attempted':1})
 def test_write_started_wrong_fence_no_write(self):
  self.started();w=CountingWriter()
  with self.assertRaises(DriveRefused):self.call(fence=self.j['fence']+1,writer=w)
  self.assertEqual(w.calls,0)
 def test_write_started_expired_no_write(self):
  self.started();w=CountingWriter()
  with self.assertRaises(DriveRefused):self.call(clock=lambda:999,writer=w)
  self.assertEqual(w.calls,0)
 def test_two_resume_drivers_zero_new_writes(self):
  self.started();w=CountingWriter();errors=[]
  def run():
   try:self.call(writer=w)
   except DriveRefused:errors.append(1)
  threads=[threading.Thread(target=run) for _ in range(2)]
  for t in threads:t.start()
  for t in threads:t.join()
  self.assertEqual(w.calls,0);self.assertEqual(len(errors),2)
 def test_crash_after_ticket_no_resume_write(self):
  self.call();original=self.l.advance
  def crash(key,fence,phase,now,counts):
   result=original(key,fence,phase,now,counts)
   if phase=='write_started':raise KeyboardInterrupt()
   return result
  w=CountingWriter()
  with patch.object(self.l,'advance',side_effect=crash):
   with self.assertRaises(KeyboardInterrupt):self.call(writer=w)
  with self.assertRaises(DriveRefused):self.call(writer=w)
  self.assertEqual(w.calls,0)
 def test_concurrent_prepare_only_one_writer(self):
  self.call();barrier=threading.Barrier(2);original=self.l.advance;w=CountingWriter();results=[]
  def synchronize(key,fence,phase,now,counts):
   if phase=='write_started':barrier.wait(timeout=5)
   return original(key,fence,phase,now,counts)
  def run():
   try:results.append(self.call(writer=w))
   except (LedgerRefused,DriveRefused):results.append('refused')
  with patch.object(self.l,'advance',side_effect=synchronize):
   ts=[threading.Thread(target=run) for _ in range(2)]
   for t in ts:t.start()
   for t in ts:t.join()
  self.assertEqual(w.calls,1);self.assertIn('refused',results)
 def test_receipt_malformed_always_latches(self):
  malformed=[{}, {'state':'mystery'}, {'state':'uncertain','attempted':1,'uncertain_count':True}]
  valid=CountingWriter().write([1],None)
  for field,value in [('attempted',True),('attempted',0),('inserted_count',2),('inserted_count',0),('failed_count',-1),('uncertain_count',True),('state','unknown'),('retry_safe',1)]:
   malformed.append(dict(valid,**{field:value}))
  for receipt in malformed:
   self.setUp();w=CountingWriter(receipt);out=self.call(writer=w)
   self.assertEqual(out['state'],'uncertain_after_write',receipt)
   with self.assertRaises(DriveRefused):self.call(writer=w)
   self.assertEqual(w.calls,1)
 def test_valid_receipt_states_and_accounting(self):
  for state,i,d,f,n in [('empty',0,0,0,0),('inserted',2,0,0,2),('duplicates',1,1,0,2),('partial',0,1,1,2)]:
   self.assertIsNotNone(_receipt({'state':state,'attempted':n,'inserted_count':i,'duplicate_count':d,'failed_count':f,'uncertain_count':0,'retry_safe':n==0},n))
 def test_expiry_between_ticket_and_write_no_write(self):
  self.call();w=CountingWriter();clocks=iter([101,101,999,999])
  out=self.call(clock=lambda:next(clocks),writer=w)
  self.assertEqual(w.calls,0);self.assertEqual(out['state'],'reconciliation_required')
 def test_checkpoint_datetime_literal_collision_fixed(self):
  d=datetime(2026,1,1,tzinfo=timezone.utc)
  self.assertNotEqual(digest(self.j['key'],1,[d]),digest(self.j['key'],1,[{'__dt__':d.isoformat()}]))
  self.assertNotEqual(digest(self.j['key'],1,[True]),digest(self.j['key'],1,[1]))
  self.assertNotEqual(digest(self.j['key'],1,[1.0]),digest(self.j['key'],1,[1]))
 def test_checkpoint_nonfinite_and_invalid_keys_refuse(self):
  for v in (float('nan'),float('inf'),float('-inf'),{1:'x'},{'a':1,2:3}):
   with self.assertRaises(CheckpointRefused):digest(self.j['key'],1,[v])
 def test_resume_inputs_settings_and_candidates_cannot_change(self):
  self.call();w=CountingWriter()
  for kw in ({'threshold':.8},{'active_categories':['GENERAL']},{'candidates':[row('https://other.example/a')]}):
   with self.assertRaises(DriveRefused):self.call(writer=w,**kw)
  self.assertEqual(w.calls,0)
 def test_resume_missing_checkpoint_refuses(self):
  self.call();w=CountingWriter()
  with self.assertRaises(DriveRefused):self.call(checkpoints=FixtureCheckpoints(),writer=w)
  self.assertEqual(w.calls,0)
 def test_prepare_error_terminal_before_write(self):
  w=CountingWriter()
  with patch('collector109_prep.drive.prepare_geo_documents',side_effect=ValueError()):
   with self.assertRaises(DriveRefused):self.call(writer=w)
  self.assertEqual(w.calls,0);self.assertEqual(self.l.status(self.j['key'])['phase'],'failed_before_write')
 def test_checkpoint_put_does_not_replace_existing_row(self):
  inputs=run_inputs([row()],['TRADE'],.85);self.cp.put(self.j['key'],1,inputs);old=self.cp._rows[self.j['key']]
  self.cp.put(self.j['key'],1,inputs);self.assertIs(self.cp._rows[self.j['key']],old)

if __name__=='__main__':unittest.main(verbosity=2)
