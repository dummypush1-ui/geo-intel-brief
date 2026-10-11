import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from integration import finder_identity_proof_prep as p
from scripts.build_finder_identity_proof import derive_records, generate

def row(system='HS', edition='2022', code='090121', description='Coffee; roasted', state='resolved'):
 return dict(system=system, edition=edition, code=code, description=description, state=state)

class BindingTests(unittest.TestCase):
 def test_single_equal_normalized(self):
  a=row(description='Cafe\u0301\t roasted'); b=row(description='Caf\u00e9 roasted')
  payload, _=derive_records([a],[b]);self.assertEqual(len(payload),p.RECORD.size)
 def test_traps(self):
  a=row()
  traps=[([a,a],[a]),([a],[a,a]),([a],[row(description='Other')]),([a],[row(state='conflicting_source_rows')]),
   ([a],[]),([],[a]),([row(edition='2021')],[row(edition='2021')]),([row(system='US')],[row(system='US')]),
   ([row(code='09')],[row(code='09')]),([row(description='\x00')],[row(description='\x00')]),
   ([a],[row(edition='2021')]),([a],[row(system='IN',edition=p.EDITIONS['IN'])])]
  for offline,index in traps:
   with self.subTest(offline=offline,index=index):self.assertEqual(derive_records(offline,index)[0],b'')
 def test_list_parity_is_not_proof(self):
  duplicate=[row(),row()]
  self.assertEqual(duplicate,list(duplicate))
  self.assertEqual(derive_records(duplicate,list(duplicate))[0],b'')
 def test_supplement_not_offline(self):
  self.assertEqual(derive_records([], [row(system='US',edition='snapshot:d6d1b417562b',code='98010010')])[0],b'')
  self.assertEqual(derive_records([], [row(code='98010010')])[0],b'')
 def test_reproducible_artifact(self):
  payload, report=generate()
  self.assertEqual(payload,(p.ROOT/p.ARTIFACT).read_bytes())
  self.assertEqual(hashlib.sha256(payload).hexdigest(),p.ARTIFACT_SHA)
  self.assertEqual(report['bound_count'],28672);self.assertEqual(report['offline_rows'],340232)
  self.assertFalse(report['fragment_has_edition']);self.assertFalse(report['labels_verified'])
 def test_real_lookup_and_wrong_identity(self):
  proof=p.FinderProof()
  try:
   for system in ('HS','IN'):
    result=proof.bound(system,p.EDITIONS[system],'090121')
    self.assertEqual(result['system'],system);self.assertFalse(result['edition_verified']);self.assertNotIn('href',result)
   for args in [('HS','2021','090121'),('US','2022','090121'),('HS','2022','000000'),('HS','2022','09'),('HS','2022',90121)]:
    self.assertIsNone(proof.bound(*args))
  finally:proof.close()
  self.assertIsNone(proof.bound('HS','2022','090121'));proof.close()
 def fixture(self,folder):
  payload,_=derive_records([row()],[row()]);path=Path(folder)/p.ARTIFACT;path.parent.mkdir(parents=True);path.write_bytes(payload)
  return path,payload
 def test_drift_shortread_closed_and_cleanup(self):
  with tempfile.TemporaryDirectory() as folder:
   path,payload=self.fixture(folder)
   with patch.object(p,'verify_sources'),patch.object(p,'ARTIFACT_SHA',hashlib.sha256(payload).hexdigest()):
    proof=p.FinderProof(folder)
    with patch.object(p,'verify_sources',side_effect=p.Unavailable('drift')):self.assertIsNone(proof.bound('HS','2022','090121'))
    with patch.object(p.os,'pread',return_value=b''):self.assertIsNone(proof.bound('HS','2022','090121'))
    path.write_bytes(b'x'*len(payload));self.assertIsNone(proof.bound('HS','2022','090121'));proof.close()
   path.write_bytes(payload)
   with patch.object(p,'verify_sources'),patch.object(p,'ARTIFACT_SHA','0'*64):
    with self.assertRaises(p.Unavailable):p.FinderProof(folder)
 def test_replacement_drift(self):
  with tempfile.TemporaryDirectory() as folder:
   path,payload=self.fixture(folder)
   with patch.object(p,'verify_sources'),patch.object(p,'ARTIFACT_SHA',hashlib.sha256(payload).hexdigest()):
    proof=p.FinderProof(folder);replacement=path.with_suffix('.new');replacement.write_bytes(payload);replacement.replace(path)
    self.assertIsNone(proof.bound('HS','2022','090121'));proof.close()
 def test_concurrent_reads_and_close(self):
  from concurrent.futures import ThreadPoolExecutor
  proof=p.FinderProof()
  with ThreadPoolExecutor(max_workers=4) as pool:
   outputs=list(pool.map(lambda _:proof.bound('HS','2022','090121'),range(16)))
  self.assertTrue(all(result['code']=='090121' for result in outputs))
  proof.close();self.assertIsNone(proof.bound('HS','2022','090121'))
 def test_init_failure_closes_descriptor(self):
  with tempfile.TemporaryDirectory() as folder:
   self.fixture(folder);original=p.os.close;closed=[]
   def close(fd):closed.append(fd);original(fd)
   with patch.object(p,'verify_sources'),patch.object(p,'ARTIFACT_SHA','0'*64),patch.object(p.os,'close',side_effect=close):
    with self.assertRaises(p.Unavailable):p.FinderProof(folder)
   self.assertEqual(len(closed),1)
 def test_source_drift(self):
  with tempfile.TemporaryDirectory() as folder:
   target=Path(folder)/'source';target.write_bytes(b'original')
   with patch.object(p,'PINS',{'source':hashlib.sha256(b'original').hexdigest()}):
    p.verify_sources(folder);target.write_bytes(b'changed')
    with self.assertRaises(p.Unavailable):p.verify_sources(folder)
 def test_runtime_no_decode_and_bounded_pread(self):
  reads=[];original=p.os.pread
  def pread(fd,n,offset):reads.append(n);return original(fd,n,offset)
  with patch.object(p.os,'pread',side_effect=pread):
   proof=p.FinderProof();self.assertIsNotNone(proof.bound('HS','2022','090121'));proof.close()
  self.assertLessEqual(max(reads),p.CHUNK)
  self.assertNotIn('json',p.__dict__);self.assertNotIn('gzip',p.__dict__)

if __name__=='__main__':unittest.main()
