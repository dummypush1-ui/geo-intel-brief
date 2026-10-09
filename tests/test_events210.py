import unittest
from pathlib import Path
from integration.news_api import create_app
from integration.public_preview_builder import build_public_preview
from integration.dashboard_snapshots import DashboardSnapshots
ROOT=Path(__file__).parents[1]
class Events210(unittest.TestCase):
 def test_private_auth_and_existing_route(self):
  self.assertEqual(create_app().test_client().get('/api/dashboard-snapshots?project=geo').status_code,403)
  c=create_app(authorize=lambda r:True).test_client();self.assertEqual(c.get('/api/dashboard-snapshots?project=geo').json['state'],'snapshot_readers_unwired')
 def test_public_assets_and_unwired_no_disclosure(self):
  env={'PREVIEW_PUBLIC_SAMPLE_ENABLED':'true','PREVIEW_GEO_ONLY_ENABLED':'true','PREVIEW_ACCESS_ENABLED':'false','NEWS_READ_ENABLED':'false','NEWS_EVENTS_READ_ENABLED':'false','FINDER_NETWORK_PREVIEW_ENABLED':'false','PREVIEW_ORIGIN':'https://preview.example'}
  c=build_public_preview(env).test_client()
  for asset in ('workspace.js','workspace.css'):
   self.assertEqual(c.get('/workspace/assets/'+asset,base_url='https://preview.example').status_code,200)
  html=c.get('/workspace',base_url='https://preview.example').text;self.assertIn('id="events-panel"',html);self.assertNotIn('id="events-panel" open',html)
  out=c.get('/api/dashboard-snapshots?project=geo',base_url='https://preview.example').json;self.assertEqual(out['state'],'snapshot_readers_unwired');self.assertNotIn('panels',out)
 def test_empty_and_validation_no_new_read(self):
  calls=[]
  def read():calls.append(1);return {'observed_at':'2026-10-09T00:00:00Z','items':[]}
  snap=DashboardSnapshots({'geo_events':read},True,{'geo_events':['example.com']})
  out=create_app(authorize=lambda r:True,dashboard_snapshot_reader=snap).test_client().get('/api/dashboard-snapshots?project=geo').json
  self.assertEqual(calls,[1]);self.assertEqual(out['panels']['geo_events']['items'],[])
 def test_no_new_assets_or_relative_date_parsing(self):
  s=(ROOT/'integration/ui/workspace.js').read_text();self.assertNotIn('Upcoming events',s);self.assertNotIn("new Date(item.event_date)",s)
  self.assertIn('eventSnapshotValue',s);self.assertIn("'Events in snapshot'",s);self.assertIn("url.startsWith('https:')",s)
