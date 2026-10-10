import unittest,tempfile,shutil,json
from pathlib import Path
from unittest.mock import patch
from integration.code_news_disk import DiskLinks
from integration.code_news_links import Refused
from integration.code_news_public import Service
ROOT=Path(__file__).resolve().parents[1]
class Disk(unittest.TestCase):
 def test_real_states_index(self):
  m=DiskLinks(ROOT/'integration/code_news_index');self.addCleanup(m.close)
  self.assertEqual(m.resolve('100630','HS','2022')['state'],'resolved');self.assertEqual(m.resolve('010129','ZA')['state'],'conflicting_source_rows');self.assertEqual(m.resolve('030290','CN')['state'],'unusable_description');self.assertEqual(m.resolve('10','HS')['state'],'not_in_link_model')
 def test_tampered_index_refused(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);shutil.copy(ROOT/'integration/code_news_index/manifest.json',p/'manifest.json');(p/'codes.idx').write_bytes(b'bad');(p/'rows.jsonl').write_bytes(b'bad')
   with self.assertRaises(Refused):DiskLinks(p)
 def test_failure_does_not_repeat_large_load(self):
  s=Service(ROOT,lambda:{'geo':[]})
  with patch('integration.code_news_public.DiskLinks',side_effect=Refused('bad'))as load:
   for _ in range(2):self.assertEqual(s.run(lambda m:({},200))[1],503)
   self.assertEqual(load.call_count,1)
 def test_nonblocking_lock(self):
  s=Service(ROOT,lambda:{'geo':[]});s.lock.acquire()
  try:self.assertEqual(s.run(lambda m:({},200))[1],429)
  finally:s.lock.release()
