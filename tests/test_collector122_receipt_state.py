import unittest
from collector122_prep.packing import pack_synthetic
from collector122_prep.receipt_state import prepare_state,transition,coverage,ReceiptRefused
R={'title':'Trade','url':'https://example.com/a','summary':'x'*5000,'published':'2026-01-01T00:00:00+00:00'}
class Tests(unittest.TestCase):
 def state(self):return prepare_state(pack_synthetic([R],synthetic=True))
 def test_all_pieces_required(self):
  s=self.state();s=transition(s,0,'begin');s=transition(s,0,'ack',message_id=10)
  c=coverage(s);self.assertFalse(c['articles'][0]['complete']);self.assertTrue(c['checkpoint_retention_required'])
  s=transition(s,1,'begin');s=transition(s,1,'ack',message_id=11)
  self.assertTrue(coverage(s)['articles'][0]['complete']);self.assertFalse(coverage(s)['ready_for_live'])
 def test_unknown_latched_no_replay(self):
  s=transition(self.state(),0,'begin');s=transition(s,0,'uncertain')
  for event in ('begin','ack','known_failure','retry','unlock'):
   with self.assertRaises(ReceiptRefused):transition(s,0,event)
  self.assertTrue(coverage(s)['articles'][0]['unknown'])
 def test_failure_visible_not_complete(self):
  s=transition(self.state(),0,'begin');s=transition(s,0,'known_failure')
  self.assertFalse(coverage(s)['articles'][0]['complete'])
 def test_no_ack_before_begin_or_false_id(self):
  with self.assertRaises(ReceiptRefused):transition(self.state(),0,'ack',message_id=10)
  s=transition(self.state(),0,'begin')
  with self.assertRaises(ReceiptRefused):transition(s,0,'ack',message_id=True)
if __name__=='__main__':unittest.main()
