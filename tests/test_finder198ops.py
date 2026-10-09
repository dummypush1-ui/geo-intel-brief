import unittest,copy,hashlib,json
from integration.finder198_ops import pack,unpack,capture,classify,OpsRefused
from integration.finder198_receipts import ProxyReceiptBudget
from tests.test_finder198ba import Collection,R
class Tests(unittest.TestCase):
 def setUp(self):
  self.c=Collection();self.c.doc.update(schema=2,receipts=[]);self.b=ProxyReceiptBudget(self.c,review=R);self.r=self.b.claim('n'*24,'a'*64,'b'*64,100)['receipt']
 def check(self,phase):
  s=classify(pack(self.c.doc),self.r['nonce_hash']);self.assertEqual(s['phase'],phase)
  for name in ('retry_safe','refund','active_cleared','capacity_released','answer_available'):self.assertFalse(s[name])
 def test_reserved_classification_not_proof_unsent(self):self.check('reserved')
 def test_started_unknown_hold_never_release(self):
  self.r=self.b.start(self.r,101);self.check('send_started');self.b.hold(self.r,102);self.check('unknown_held');self.assertIsNotNone(unpack(pack(self.c.doc))['budget']['active'])
 def test_complete_no_answer_refund_delivery_claim(self):
  self.r=self.b.start(self.r,101);self.b.finish(self.r,102,status=500,response_hash='c'*64,response_bytes=20);self.check('complete');self.assertEqual(unpack(pack(self.c.doc))['budget']['calls'],1)
 def test_raw_document_all_fields_equal_no_alias(self):
  data=pack(self.c.doc);v=unpack(data);self.assertEqual(v['budget'],self.c.doc);self.c.doc['revision']+=1;self.assertNotEqual(v['budget'],self.c.doc)
 def test_v1_unknown_schema_extra_private_refused(self):
  for change in (lambda d:d.update(schema=1),lambda d:d.update(password='bad'),lambda d:d.update(schema=True)):
   d=copy.deepcopy(self.c.doc);change(d)
   with self.assertRaises(OpsRefused):pack(d)
 def test_active_missing_or_orphan_refused(self):
  for change in (lambda d:d.update(active=None),lambda d:d.update(receipts=[])):
   d=copy.deepcopy(self.c.doc);change(d)
   with self.assertRaises(OpsRefused):pack(d)
 def test_duplicate_identity_and_unknown_metadata_refused(self):
  d=copy.deepcopy(self.c.doc);d['receipts'].append(d['receipts'][0])
  with self.assertRaises(OpsRefused):pack(d)
  d=copy.deepcopy(self.c.doc);d['receipts'][0]['response_hash']='d'*64
  with self.assertRaises(OpsRefused):pack(d)
 def test_tampered_truncated_duplicate_json(self):
  data=pack(self.c.doc)
  for bad in (data[:-1],data.replace(b'"schema":2',b'"schema":3'),b'{"body":{},"body":{},"sha256":"x"}'):
   with self.assertRaises(OpsRefused):unpack(bad)
 def test_capture_no_mutations_and_visible_race(self):
  before=copy.deepcopy(self.c.doc);writes=self.c.writes;self.assertEqual(unpack(capture(self.b))['budget'],before);self.assertEqual(self.c.writes,writes)
  original=self.c.find_one;n=[0]
  def read(*a,**kw):
   d=original(*a,**kw);n[0]+=1
   if n[0]>1:d['revision']+=1
   return d
  self.c.find_one=read
  with self.assertRaises(OpsRefused):capture(self.b)
 def test_full64_no_capacity_release(self):
  d=copy.deepcopy(self.c.doc);template=d['receipts'][0];d.update(active=None,fence=64,calls=60);d['receipts']=[]
  for i in range(1,65):
   r=copy.deepcopy(template);r.update(nonce_hash=f'{i:064x}',fence=i,phase='complete',status=200,response_hash='c'*64);d['receipts'].append(r)
  data=pack(d);self.assertEqual(len(unpack(data)['budget']['receipts']),64);self.assertFalse(classify(data,d['receipts'][0]['nonce_hash'])['capacity_released'])
 def test_absence_not_lifetime_or_replay_permission(self):
  with self.assertRaises(OpsRefused):classify(pack(self.c.doc),'f'*64)
 def test_oversized_nonplain_recursive_refused(self):
  d=copy.deepcopy(self.c.doc);d['receipts'][0]['nonce_hash']='x'*10001
  with self.assertRaises(OpsRefused):pack(d)
  with self.assertRaises(OpsRefused):unpack(b'x'*131073)
 def test_no_route_or_mutation_import(self):
  from pathlib import Path
  s=(Path(__file__).resolve().parents[1]/'integration/finder198_ops.py').read_text()
  for word in ('.replace_one(','.update_one(','.delete_one(','.claim(','.start(','.finish(','.hold('):self.assertNotIn(word,s)
