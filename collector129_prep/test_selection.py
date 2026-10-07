import unittest
from datetime import datetime,timezone
from .supplied_feed import prepare_supplied_feed,FeedRefused
D=datetime(2026,1,1,tzinfo=timezone.utc);F=('Fixture','https://example.com/rss','HIGH')
def rows(n):return [{'title':'Trade'+str(i),'link':'https://example.com/'+str(i),'summary':'Tariff','description':'note','published':D.isoformat(),'updated':D.isoformat()}for i in range(n)]
class Tests(unittest.TestCase):
 def select(self,entries,cap=200):return prepare_supplied_feed(F,entries,cutoff=D,fallback_clock=D,max_items=cap)
 def test_dense200_all(self):
  x=self.select(rows(200));self.assertEqual(len(x['candidates']),200);self.assertEqual(x['candidates'][-1]['title'],'Trade199');self.assertFalse(x['network'])
 def test_original_slice_before_filter(self):
  r=rows(150);r[0]['title']=''
  x=self.select(r,101);self.assertEqual(len(x['candidates']),100);self.assertEqual(x['candidates'][-1]['title'],'Trade100')
 def test_default50(self):self.assertEqual(len(prepare_supplied_feed(F,rows(150),cutoff=D,fallback_clock=D)['candidates']),50)
 def test_overcap_refuses_not_silent(self):
  for r,cap in ((rows(201),200),(rows(1),201),(rows(1),True)):
   with self.assertRaises(FeedRefused):self.select(r,cap)
 def test_combined_budget_refuses(self):
  r=rows(200)
  for row in r:row['summary']='x'*10000;row['description']='x'*10000
  with self.assertRaises(FeedRefused):self.select(r)
 def test_source_pin_unchanged(self):
  from unittest.mock import patch
  with patch('collector129_prep.supplied_feed.PINS',{'intelligence/geo/collectors/rss.py':'0'*64}):
   with self.assertRaises(FeedRefused):self.select(rows(1))
 def test_missing_source_fails_not_skips(self):
  from unittest.mock import patch
  from tempfile import TemporaryDirectory
  from pathlib import Path
  with TemporaryDirectory()as directory,patch('collector129_prep.supplied_feed.ROOT',Path(directory)):
   with self.assertRaises(FileNotFoundError):self.select(rows(1))
 def test_exact_inventory_hashes(self):
  import json,hashlib
  from pathlib import Path
  base=Path(__file__).resolve().parent
  inv=json.loads((base/'inventory.json').read_text())
  self.assertEqual(set(inv['files']),{'supplied_feed.py','SELECTION-DESIGN.md','__init__.py'})
  for name,h in inv['files'].items():self.assertEqual(h,hashlib.sha256((base/name).read_bytes()).hexdigest())
