import unittest,copy
from collector122_prep.packing import pack_synthetic
from collector122_prep.receipt_state import prepare_state,transition,coverage,ReceiptRefused
R={'title':'T','summary':'x'*5000,'url':'https://example.com/a'}
class Tests(unittest.TestCase):
 def plan(self):return pack_synthetic([R],synthetic=True)
 def test_plan_mutations(self):
  mutations=[lambda p:p.update(sent=True),lambda p:p['pieces'][0].update(payload='tamper'),lambda p:p['pieces'][0].update(utf16_units=1),lambda p:p['manifest'][0].update(required_piece_indices=[0]),lambda p:p['manifest'][0].update(required_piece_indices=[0,0]),lambda p:p['manifest'][0].update(article_index=True),lambda p:p['pieces'][1].update(part=1),lambda p:p['pieces'].append(copy.deepcopy(p['pieces'][0])),lambda p:p['manifest'][0].update(record_sha256='0'*64)]
  for mutate in mutations:
   p=self.plan();mutate(p)
   with self.assertRaises(ReceiptRefused):prepare_state(p)
 def test_state_mutations(self):
  mutations=[lambda s:s.update(delivery=True),lambda s:s['states'].pop(),lambda s:s['states'][0].update(piece_index=True),lambda s:s['states'][0].update(digest='0'*64),lambda s:s['states'][0].update(message_id=2),lambda s:s['states'][0].update(state='acknowledged'),lambda s:s['states'][0].update(state='mystery'),lambda s:s['plan']['manifest'][0].update(required_piece_indices=[100])]
  for mutate in mutations:
   s=prepare_state(self.plan());mutate(s)
   for f in (coverage,lambda s:transition(s,0,'begin')):
    with self.assertRaises(ReceiptRefused):f(s)
 def test_duplicate_message_id_refused(self):
  s=prepare_state(self.plan());s=transition(s,0,'begin');s=transition(s,0,'ack',message_id=1);s=transition(s,1,'begin')
  with self.assertRaises(ReceiptRefused):transition(s,1,'ack',message_id=1)
 def test_empty_and_immutability(self):
  self.assertEqual(coverage(prepare_state(pack_synthetic([],synthetic=True)))['articles'],[])
  s=prepare_state(self.plan());old=copy.deepcopy(s);transition(s,0,'begin');self.assertEqual(s,old)
 def test_invalid_types(self):
  for p in (None,[],{}, {'scope':'inactive_synthetic_full_record_packing'}):
   with self.assertRaises(ReceiptRefused):prepare_state(p)
  for s in (None,[],{}):
   with self.assertRaises(ReceiptRefused):coverage(s)
