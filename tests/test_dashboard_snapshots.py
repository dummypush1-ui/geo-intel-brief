import unittest
from integration.dashboard_snapshots import DashboardSnapshots
from integration.news_api import create_app
STAMP='2026-10-02T00:00:00Z'
class DashboardSnapshotTests(unittest.TestCase):
 def reader(self,key,rows,stamp=STAMP):return DashboardSnapshots({key:lambda:{'observed_at':stamp,'items':rows}},True)
 def test_unavailable_not_empty_claim(self):
  d=DashboardSnapshots({},True)('geo');self.assertEqual(d['panels']['geo_events']['state'],'unavailable')
  d=self.reader('geo_events',[])('geo');self.assertEqual(d['panels']['geo_events']['state'],'supplied_snapshot')
 def test_events_exact_fields_safe_links(self):
  rows=[{'_id':'secret','name':'<script>x</script>','source_url':'https://example.com/a','event_date':'2026-10-03','description':'x'},{'name':'bad','source_url':'javascript:x','event_date':'2026-10-03'}]
  d=self.reader('geo_events',rows)('geo')['panels']['geo_events'];self.assertEqual(d['rejected_count'],1);self.assertNotIn('_id',d['items'][0]);self.assertEqual(d['items'][0]['name'],'<script>x</script>')
 def test_source_status_no_naive_time_or_defaults(self):
  d=self.reader('brics_sources',[{'name':'A','url':'https://example.com/a','last_status':'ok','last_checked':'2026-10-02T00:00:00','last_count':True}])('brics')['panels']['brics_sources']['items'][0]
  self.assertIsNone(d['last_checked']);self.assertIsNone(d['last_count'])
 def test_stream_link_not_live_embed(self):
  r=self.reader('brics_streams',[{'name':'A','watch_url':'https://example.com/a','embed_url':'https://evil.com','video_id':'private'}])('brics')['panels']['brics_streams']['items'][0]
  self.assertEqual(r['availability'],'not_checked');self.assertNotIn('embed_url',r)
 def test_invalid_bounded_snapshot_fails_unavailable(self):
  for rows,stamp in [([{}]*1001,STAMP),([], '2026-10-02')]:self.assertEqual(self.reader('geo_events',rows,stamp)('geo')['panels']['geo_events']['state'],'unavailable')
 def test_verified_true_only(self):
  for value in [False,1,'true']:
   with self.assertRaises(ValueError):DashboardSnapshots({},value)
 def test_guard_route_and_redaction(self):
  self.assertEqual(create_app().test_client().get('/api/dashboard-snapshots?project=geo').status_code,403)
  c=create_app(authorize=lambda r:True).test_client();self.assertEqual(c.get('/api/dashboard-snapshots').status_code,400);self.assertEqual(c.get('/api/dashboard-snapshots?project=geo').json['state'],'snapshot_readers_unwired')
  def bad(project):raise RuntimeError('private password')
  c=create_app(authorize=lambda r:True,dashboard_snapshot_reader=bad).test_client();r=c.get('/api/dashboard-snapshots?project=geo');self.assertEqual(r.status_code,503);self.assertNotIn('password',r.text)
