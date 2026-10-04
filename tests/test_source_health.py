import unittest
from datetime import datetime, timezone
from integration.source_health import SourceHealthSnapshot
from integration.news_api import create_app
NOW=datetime(2026,10,5,tzinfo=timezone.utc)
def data():return {'observed_at':'2026-10-04T23:00:00Z','items':[{'name':'Fixture source','project':'geo','status':'error','count':0,'checked_at':'2026-10-04T22:59:00Z','error_code':'http_error'}]}
class SourceHealthTests(unittest.TestCase):
 def test_capture_and_isolation(self):
  d=data();s=SourceHealthSnapshot(d);d['items'][0]['name']='changed';v=s.view(NOW);self.assertEqual(v['items'][0]['name'],'Fixture source');self.assertTrue(v['not_live_status']);self.assertEqual(v['age_seconds'],3600);v['items'].clear();self.assertEqual(len(s.view(NOW)['items']),1)
 def test_no_raw_error_or_subclass_hooks(self):
  d=data();d['items'][0]['error_code']='secret-token';self.assertRaises(ValueError,SourceHealthSnapshot,d)
  class Rows(list):
   def __iter__(self):raise AssertionError('hook')
  d=data();d['items']=Rows(d['items']);self.assertRaises(ValueError,SourceHealthSnapshot,d)
 def test_future_checks_and_snapshots(self):
  d=data();d['observed_at']='2026-10-06T00:00:00Z';self.assertRaises(ValueError,SourceHealthSnapshot(d).view,NOW)
  d=data();d['items'][0]['checked_at']='2026-10-05T00:00:00Z';self.assertRaises(ValueError,SourceHealthSnapshot(d).view,NOW)
 def test_count_and_zone(self):
  for k,v in [('count',True),('checked_at','2026-10-04'),('status','healthy-now')]:
   d=data();d['items'][0][k]=v;self.assertRaises(ValueError,SourceHealthSnapshot,d)
 def test_private_empty_unwired_and_reader_type(self):
  self.assertEqual(create_app().test_client().get('/api/source-health').status_code,403)
  c=create_app(authorize=lambda r:True).test_client();self.assertEqual(c.get('/api/source-health').json['state'],'source_health_unwired')
  c=create_app(authorize=lambda r:True,source_health_snapshot=lambda: data()).test_client();self.assertEqual(c.get('/api/source-health').status_code,503)
 def test_cap(self):
  d=data();d['items']*=101;v=SourceHealthSnapshot(d).view(NOW);self.assertEqual(len(v['items']),100);self.assertTrue(v['truncated']);self.assertEqual(v['total_supplied'],101)

 def test_exact_keys_and_consistent_status(self):
  class Key(str):pass
  d=data();d[Key('items')]=d.pop('items');self.assertRaises(ValueError,SourceHealthSnapshot,d)
  d=data();d['items'][0][Key('name')]=d['items'][0].pop('name');self.assertRaises(ValueError,SourceHealthSnapshot,d)
  d=data();d['items'][0]['status']='ok';self.assertRaises(ValueError,SourceHealthSnapshot,d)
