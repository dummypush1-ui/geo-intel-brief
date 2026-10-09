import unittest,copy,json,hashlib
from integration.collector197_archive import pack,unpack,status,capture,ArchiveRefused
from integration.collector197_coverage import CoverageCheckpoints
from tests.test_collector197a import candidates
def Fixture():
 from tests.test_collector197a import Tests
 return Tests()
from tests.test_collector197c import inputs,cov
from collector108_prep.durable_ledger import DurableLedger
class Tests(unittest.TestCase):
 def setUp(self):
  f=Fixture();f.setUp();self.f=f;self.cp=CoverageCheckpoints(f.pc);self.job=f.ledger.submit('n'*24,100);self.key=self.job['key'];self.cp.put(self.key,1,inputs(),cov());self.row={'job':self.key,'fence':1,'record':copy.deepcopy(f.pc.rows[self.key])}
 def blob(self):return pack(self.f.c.doc,[self.row],profile='geo108',fingerprint=self.f.ledger.fp)
 def test_complete_typed_v2_roundtrip_and_status(self):
  b=self.blob();v=unpack(b);self.assertEqual(v['ledger'],self.f.c.doc);self.assertEqual(v['checkpoints'][0],self.row);s=status(b,self.key);self.assertEqual(s['classification'],'held_owner_review_required');self.assertFalse(s['capacity_released'])
 def test_missing_later_checkpoint_fails_closed(self):
  d=copy.deepcopy(self.f.c.doc);d['active']['phase']='fetch_complete';r=copy.deepcopy(self.row);r['record']=None
  with self.assertRaises(ArchiveRefused):pack(d,[r],profile='geo108',fingerprint=self.f.ledger.fp)
 def test_empty_history_retains_identity(self):
  d=copy.deepcopy(self.f.c.doc);d['active']=None;b=pack(d,[],profile='geo108',fingerprint=self.f.ledger.fp);self.assertEqual(unpack(b)['ledger']['fence'],1)
 def test_corrupt_checkpoint_hash_fence_and_job(self):
  for mutate in (lambda r:r['record'].update(input_hash='0'*64),lambda r:r.update(fence=2),lambda r:r.update(job='0'*64),lambda r:r['record'].update(coverage_hash='0'*64)):
   r=copy.deepcopy(self.row);mutate(r)
   with self.assertRaises(ArchiveRefused):pack(self.f.c.doc,[r],profile='geo108',fingerprint=self.f.ledger.fp)
 def test_active_absence_explicit_not_success(self):
  r=copy.deepcopy(self.row);r['record']=None;b=pack(self.f.c.doc,[r],profile='geo108',fingerprint=self.f.ledger.fp);self.assertFalse(status(b,self.key)['checkpoint_present'])
 def test_input_alias_cannot_change_bytes(self):
  b=self.blob();self.row['record']['fence']='2';self.assertEqual(unpack(b)['checkpoints'][0]['record']['fence'],'1')
 def test_tampered_duplicate_truncated_unknownfield(self):
  b=self.blob()
  for value in (b[:-1],b.replace(b'"schema":',b'"bad":'),b'{"body":{},"body":{},"sha256":"x"}'):
   with self.assertRaises(ArchiveRefused):unpack(value)
 def test_extra_private_or_oversized_fields_refused(self):
  d=copy.deepcopy(self.f.c.doc);d['password']='secret'
  with self.assertRaises(ArchiveRefused):pack(d,[self.row],profile='geo108',fingerprint=self.f.ledger.fp)
  r=copy.deepcopy(self.row);r['record']['inputs']=['str','x'*10001]
  with self.assertRaises(ArchiveRefused):pack(self.f.c.doc,[r],profile='geo108',fingerprint=self.f.ledger.fp)
 def test_capture_reads_only_and_detects_ledger_race(self):
  # Fake collection accepting the bounded read parameter, no mutation hooks.
  original=self.f.c.find_one;self.f.c.find_one=lambda q,**kw:original(q);cpread=self.f.pc.find_one;self.f.pc.find_one=lambda q,**kw:cpread(q)
  before=copy.deepcopy(self.f.c.doc);b=capture(self.f.ledger,self.cp);self.assertEqual(before,self.f.c.doc);self.assertEqual(unpack(b)['ledger'],before)
  n=[0]
  def race(q,**kw):
   d=original(q);n[0]+=1
   if n[0]>1:d['revision']+=1
   return d
  self.f.c.find_one=race
  with self.assertRaises(ArchiveRefused):capture(self.f.ledger,self.cp)
 def test_v1_complete_checkpoint_supported_not_invented_coverage(self):
  from collector110_prep.durable_checkpoint import DurableCheckpoints
  f=Fixture();f.setUp();j=f.ledger.submit('z'*24,100);cp=DurableCheckpoints(f.pc);cp.put(j['key'],j['fence'],inputs());r={'job':j['key'],'fence':j['fence'],'record':f.pc.rows[j['key']]};b=pack(f.c.doc,[r],profile='geo108',fingerprint=f.ledger.fp);self.assertNotIn('coverage',unpack(b)['checkpoints'][0]['record'])
 def test_full_history_no_release_no_drop(self):
  d=copy.deepcopy(self.f.c.doc);template=d['active'];d['active']=None;d['fence']=64;d['history']=[];rows=[]
  for i in range(1,65):
   j=copy.deepcopy(template);j.update(key=f'{i:064x}',fence=i,phase='failed_before_write');d['history'].append(j);rows.append({'job':j['key'],'fence':i,'record':None})
  b=pack(d,rows,profile='geo108',fingerprint=self.f.ledger.fp);self.assertEqual(len(unpack(b)['ledger']['history']),64);self.assertFalse(status(b,d['history'][0]['key'])['capacity_released'])

 def test_resource_cycle_unknownversion_nonfinite_and_bool_identity(self):
  from integration.collector197_archive import _bounded
  loop=[];loop.append(loop)
  for v in (loop,10**1000,float('nan')):
   with self.assertRaises(ValueError):_bounded(v)
  for version in (3,True):
   r=copy.deepcopy(self.row);r['record']['version']=version
   with self.assertRaises(ArchiveRefused):pack(self.f.c.doc,[r],profile='geo108',fingerprint=self.f.ledger.fp)
  r=copy.deepcopy(self.row);r['fence']=True
  with self.assertRaises(ArchiveRefused):pack(self.f.c.doc,[r],profile='geo108',fingerprint=self.f.ledger.fp)
 def test_aggregatecap_no_partial_artifact(self):
  from integration.collector197_archive import _bounded
  # Each string is within local bounds; aggregate expands conservatively.
  with self.assertRaises(ValueError):_bounded([['x'*10000]*300]*2)
 def test_completed_still_not_delivery_and_retained_unknown_held(self):
  for phase in ('completed','uncertain_after_write'):
   d=copy.deepcopy(self.f.c.doc);d['active']['phase']=phase
   if phase=='completed':d['history']=[d['active']];d['active']=None
   b=pack(d,[self.row],profile='geo108',fingerprint=self.f.ledger.fp);s=status(b,self.key)
   self.assertIn('not_delivery_proof'if phase=='completed'else'held_owner_review_required',s['classification']);self.assertFalse(s['capacity_released'])
