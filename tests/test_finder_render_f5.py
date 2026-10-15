import hashlib,unittest
from pathlib import Path
from unittest.mock import patch
from integration import finder_render_f5 as m
from integration.finder_offline import shell,OFFLINE_SHA
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def test_off_and_flags(self):
  with patch.object(m,'_candidate_safety_shell',side_effect=AssertionError):self.assertIsNone(m.prepare({}));self.assertIsNone(m.prepare({m.FLAG:'false'}))
  for value in ('TRUE','yes','1',''):
   with self.assertRaises(m.Held):m.prepare({m.FLAG:value})
 def test_hash_cap_unicode_and_seam_fail(self):
  for source,pin in [('x','0'*64),('\ud800','0'*64),('x','bad'),('x',hashlib.sha256(b'x').hexdigest())]:
   with self.assertRaises(m.Held):m.prepare({m.FLAG:'true'},source=source,source_sha256=pin)
 def test_baseline_byte_exact_and_source_unchanged(self):
  original=(ROOT/'offline.html').read_text();report,result=m.prepare({m.FLAG:'true'},source=original,source_sha256=OFFLINE_SHA);self.assertEqual(result,shell(original));self.assertFalse(report['runtime_repin']);self.assertEqual(hashlib.sha256((ROOT/'offline.html').read_bytes()).hexdigest(),OFFLINE_SHA)
 def test_bad_invariant_holds(self):
  with patch.object(m,'_candidate_safety_shell',return_value='<html>not safe</html>'),self.assertRaises(m.Held):m.prepare({m.FLAG:'true'},source='x',source_sha256=hashlib.sha256(b'x').hexdigest())
 def test_each_safety_invariant_and_provider_independently(self):
  source=(ROOT/'offline.html').read_text();rendered=shell(source)
  variants={
   'localStorage':rendered+'localStorage',
   'fetch':rendered.replace("const fetch = async()=>{throw new Error('Offline snapshot: live network disabled');};",''),
   'storage':rendered.replace('const OFFLINE_STORE = {getItem(){return null;},setItem(){},removeItem(){}};',''),
   'scroll':rendered.replace('finder-shortlist-scroll','removed-scroll'),
   'csv':rendered.replace('const probe = text.replace','const other = text.replace'),
   'csp':rendered.replace('Content-Security-Policy','Removed-Policy'),
   'connect':rendered.replace("connect-src 'none'","connect-src https:"),
  }
  for name in ('AI_PROXY_URL','AIS_PROXY_URL','BUILTIN_GEMINI_KEYS','BUILTIN_GROQ_KEYS','BUILTIN_MISTRAL_KEYS','BUILTIN_NVIDIA_KEYS'):
   variants[name]=rendered.replace("const "+name+" = ''","const "+name+" = 'unsafe'")
   self.assertNotEqual(variants[name],rendered,name)
  for name,bad in variants.items():
   with self.subTest(name=name),patch.object(m,'_candidate_safety_shell',return_value=bad),self.assertRaises(m.Held):m.prepare({m.FLAG:'true'},source=source,source_sha256=OFFLINE_SHA)
 def test_valid_source_flags_hash_cap_and_runtime_pin(self):
  source=(ROOT/'offline.html').read_text()
  for value in ('TRUE','yes','1',''):
   with self.subTest(value=value),self.assertRaises(m.Held):m.prepare({m.FLAG:value},source=source,source_sha256=OFFLINE_SHA)
  with self.assertRaises(m.Held):m.prepare({m.FLAG:'true'},source=source,source_sha256='0'*64)
  oversized='x'*(40*1024*1024+1)
  with self.assertRaises(m.Held):m.prepare({m.FLAG:'true'},source=oversized,source_sha256=hashlib.sha256(oversized.encode()).hexdigest())
  report,_=m.prepare({m.FLAG:'true'},source=source,source_sha256=OFFLINE_SHA);self.assertIs(report['writes'],False)
  with self.assertRaisesRegex(ValueError,'requires review'):shell(source+' ')
if __name__=='__main__':unittest.main()
