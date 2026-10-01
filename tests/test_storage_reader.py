import unittest
from integration.storage_reader import ReadOnlyNewsReader
from integration.news_view import views
class FakeReadStore:
 def __init__(self,rows):self.rows=rows;self.calls=[]
 def find(self,query,projection=None):self.calls.append(('find',query));return self
 def sort(self,key,direction):self.calls.append(('sort',key,direction));return self
 def limit(self,limit):self.calls.append(('limit',limit));self.n=limit;return self
 def __iter__(self):return iter(self.rows[:self.n])
class ReaderTests(unittest.TestCase):
 def test_verified_mapping_required(self):
  with self.assertRaises(ValueError):ReadOnlyNewsReader({'geo':FakeReadStore([])})
 def test_shared_collection_not_assumed(self):
  store=FakeReadStore([])
  with self.assertRaises(ValueError):ReadOnlyNewsReader({'geo':store,'brics':store},verified=True)
 def test_only_reads_and_bounded(self):
  geo=FakeReadStore([{'_id':'object','title':'a','url':'https://example.invalid/a'}]);brics=FakeReadStore([{'_id':'mongo','id':'urlhash','title':'b','url':'https://example.invalid/b'}])
  rows=ReadOnlyNewsReader({'geo':geo,'brics':brics},verified=True,limit=25)();normalized=views(rows)
  self.assertEqual(normalized[1]['legacy_id'],'urlhash');self.assertEqual(normalized[1]['mongo_id'],'mongo');self.assertEqual(normalized[0]['legacy_id'],'object')
  self.assertEqual(geo.calls,[('find',{}),('sort','created_at',-1),('limit',25)])
  self.assertEqual(brics.calls,[('find',{}),('sort','collected_at',-1),('limit',25)])
  self.assertNotIn('project',geo.rows[0])
 def test_unknown_or_unbounded(self):
  for stores,limit in [({'wrong':FakeReadStore([])},10),({'geo':FakeReadStore([])},0),({'geo':FakeReadStore([])},1001)]:
   with self.assertRaises(ValueError):ReadOnlyNewsReader(stores,verified=True,limit=limit)
