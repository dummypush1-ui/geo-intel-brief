import unittest,hashlib
from collector122_prep.packing import pack_synthetic,PackingRefused,units
R={'title':'Trade','url':'https://example.com/a','summary':'text','published':'2026-01-01T00:00:00+00:00'}
class Tests(unittest.TestCase):
 def test_oversize_lossless(self):
  r=pack_synthetic([dict(R,summary='x'*10000)],synthetic=True)
  self.assertGreater(len(r['pieces']),1);self.assertTrue(all(p['utf16_units']<=3500 for p in r['pieces']))
  joined=''.join(p['payload']for p in r['pieces'])
  self.assertEqual(hashlib.sha256(joined.encode()).hexdigest(),r['manifest'][0]['record_sha256'])
  self.assertTrue(joined.endswith('x'*10000));self.assertFalse(r['sent'])
 def test_unicode_no_surrogate_split(self):
  r=pack_synthetic([dict(R,summary='😀'*5000)],synthetic=True)
  self.assertTrue(all(units(p['text'])<=3500 for p in r['pieces']))
  self.assertTrue(''.join(p['payload']for p in r['pieces']).endswith('😀'*5000))
 def test_all_piece_manifest(self):
  r=pack_synthetic([R,dict(R,summary='x'*5000)],synthetic=True)
  self.assertEqual([p['article_index']for p in r['pieces']],[0,1,1])
  self.assertEqual(r['manifest'][1]['required_piece_indices'],[1,2])
 def test_synthetic_flag_and_caps(self):
  for kw in ({},{'synthetic':True,'unit_limit':4096},{'synthetic':True,'unit_limit':1}):
   with self.assertRaises(PackingRefused):pack_synthetic([R],**kw)
if __name__=='__main__':unittest.main()
