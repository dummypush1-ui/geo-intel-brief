import unittest
from integration.project_reports import combined_reports
class ProjectReportTests(unittest.TestCase):
 def test_preserve_builder_contract(self):
  d=combined_reports({p:lambda p=p:{'html':'<p>'+p+' original content</p>','ids':['same'],'critical_count':1} for p in ('finder','geo','brics')})
  self.assertEqual(d['critical_count'],3);self.assertEqual(d['project_ids'],{'finder':['same'],'geo':['same'],'brics':['same']})
 def test_missing_project_rejected(self):
  with self.assertRaises(ValueError):combined_reports({})
 def test_objectid_roundtrip_and_sanitize(self):
  from bson import ObjectId
  from integration.project_reports import original_ids
  identity=ObjectId('507f1f77bcf86cd799439011')
  d=combined_reports({p:lambda p=p:{'html':'<script>bad</script><p>Good</p>','ids':[identity] if p=='geo' else ['1']} for p in ('finder','geo','brics')})
  self.assertEqual(original_ids(d,'geo'),[identity]);self.assertEqual(type(original_ids(d,'geo')[0]),ObjectId);self.assertNotIn('bad',d['html'])
