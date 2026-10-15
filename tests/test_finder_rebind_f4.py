import hashlib,json,unittest
from pathlib import Path
from unittest.mock import patch
from integration import finder_rebind_f4 as m
from scripts.build_finder_identity_proof import derive_records,offline_identities
class Tests(unittest.TestCase):
 def pins(self):return {n:hashlib.sha256((m.ROOT/n).read_bytes()).hexdigest()for n in ('index.html','offline.html','sw.js','data.d6d1b417562b.js')}
 def test_off_before_io(self):
  with patch.object(Path,'read_bytes',side_effect=AssertionError):self.assertIsNone(m.prepare({}));self.assertIsNone(m.prepare({m.FLAG:'false'}))
  for value in ('TRUE','yes','1',''):
   with self.assertRaises(m.Held):m.prepare({m.FLAG:value})
 def test_closed_pin_paths_hashes_byte_and_filename(self):
  for pins in ({},dict(self.pins(),bad='0'*64),dict(self.pins(),**{'index.html':'0'*64}),dict(self.pins(),**{'index.html':'bad'})):
   with self.assertRaises(m.Held):m.source_check(m.ROOT,pins)
  with patch.object(m,'MAX_TOTAL',1),self.assertRaises(m.Held):m.source_check(m.ROOT,self.pins())
 def test_explicit_edition_not_old_global_and_multiplicity(self):
  editions={'HS':'2022','IN':'snapshot:123456789abc'};a={'system':'IN','edition':editions['IN'],'code':'12345678','description':'Exact Case'};b=dict(a,state='resolved')
  proof,reasons=derive_records([a],[b],editions);self.assertEqual(len(proof),45)
  self.assertEqual(derive_records([a,a],[b],editions)[0],b'');self.assertEqual(derive_records([a],[dict(b,description='exact case')],editions)[0],b'');self.assertEqual(derive_records([a],[dict(b,edition='snapshot:d6d1b417562b')],editions)[0],b'')
  tags=[('HS','HS','x','x'),('IN','IN','x','x')];self.assertEqual(list(offline_identities([[1,'12345678','Exact Case',None,'12','']],tags,editions))[0]['edition'],editions['IN'])
 def test_real_old_baseline_reproduces_existing_index_proof_no_writes(self):
  pins=self.pins();before={n:hashlib.sha256((m.ROOT/n).read_bytes()).hexdigest()for n in pins};report,artifacts=m.prepare({m.FLAG:'true'},pins=pins)
  for n,raw in artifacts.items():self.assertEqual(raw,(m.ROOT/n).read_bytes(),n)
  self.assertEqual(report['state'],'held_consumer_artifacts_not_rebound');self.assertEqual(report['editions']['IN'],'snapshot:d6d1b417562b');self.assertFalse(report['auto_repin']);self.assertEqual(before,self.pins())
 def test_symlink_extra_key_and_handler_or_system_drift(self):
  with patch.object(Path,'is_symlink',return_value=True),self.assertRaises(m.Held):m.source_check(m.ROOT,self.pins())
  for pins in ({1:'0'*64},dict(self.pins(),**{'../offline.html':'0'*64})):
   with self.assertRaises(m.Held):m.source_check(m.ROOT,pins)
  with patch.object(m,'source_systems',return_value=[('HS','HS','x','x')]*22),self.assertRaisesRegex(m.Held,'system labels'):m.prepare({m.FLAG:'true'},pins=self.pins())
 def test_candidate_payload_parity_and_group_caps(self):
  rows=[[0,'1234','Synthetic',None,'12','']]
  with patch.object(m,'decode_payload',side_effect=[(rows,'x'),([], 'x')]),self.assertRaisesRegex(m.Held,'diagnostic mismatch'):m.prepare({m.FLAG:'true'},pins=self.pins())
  fake={'system':'HS','edition':'2022','code':'1234','description':'Synthetic'}
  with patch.object(m,'decode_payload',return_value=(rows,'x')),patch.object(m,'extract',return_value={}),patch.object(m,'model_rows',return_value=[fake]*101),patch.object(m,'omission_ledger',return_value=[]),self.assertRaisesRegex(m.Held,'group cap'):m.prepare({m.FLAG:'true'},pins=self.pins())
  large=dict(fake,description='x'*65536)
  with patch.object(m,'decode_payload',return_value=(rows,'x')),patch.object(m,'extract',return_value={}),patch.object(m,'model_rows',return_value=[large]),patch.object(m,'omission_ledger',return_value=[]),self.assertRaisesRegex(m.Held,'group cap'):m.prepare({m.FLAG:'true'},pins=self.pins())
 def test_generated_identity_tamper_and_duplicate_seam(self):
  real=Path.read_text
  for mode in ('sw','reference','offline','seam'):
   def text(path,*a,**kw):
    original=real(path,*a,**kw)
    if mode=='sw'and path.name=='sw.js':return original.replace('hsn-data-d6d1b417562b','hsn-data-000000000000')
    if mode=='reference'and path.name=='index.html':return original.replace("data.src = './data.d6d1b417562b.js'","data.src = './data.000000000000.js'")
    if mode=='offline'and path.name=='offline.html':return original.replace('var DATA_B64 = "','var MISSING_DATA = "',1)
    if mode=='seam'and path.name=='index.html':return original+m.FRAGMENT
    return original
   with self.subTest(mode=mode),patch.object(Path,'read_text',text),self.assertRaises(m.Held):m.prepare({m.FLAG:'true'},pins=self.pins())
 def test_filename_hash_and_write_report(self):
  pins={n:'0'*64 for n in self.pins()}
  with patch.object(Path,'read_bytes',return_value=b'x'),patch.object(m,'sha',return_value='0'*64),self.assertRaisesRegex(m.Held,'filename identity'):m.source_check(m.ROOT,pins)
  report,_=m.prepare({m.FLAG:'true'},pins=self.pins());self.assertIs(report['writes'],False)
if __name__=='__main__':unittest.main()
