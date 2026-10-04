import unittest
from datetime import datetime,timezone
from pathlib import Path
from integration.stream_fixture_app import create_stream_fixture
NOW=datetime(2026,10,5,tzinfo=timezone.utc);O='http://localhost:8783'
RAW=(Path(__file__).resolve().parents[1]/'intelligence/brics/config/streams.yaml').read_bytes()
class StreamFixtureComposition(unittest.TestCase):
 def app(self,allow=True):return create_stream_fixture(RAW,NOW,authorize=lambda r:allow,allowed_origin=O)
 def test_private_and_source_fidelity(self):
  c=self.app(False).test_client()
  for p in ('/api/brics/streams','/workspace/brics-streams','/api/dashboard-snapshots?project=brics'):self.assertEqual(c.get(p,base_url=O).status_code,403)
  r=self.app().test_client().get('/api/brics/streams',base_url=O);self.assertEqual(len(r.json['streams']),5);self.assertFalse(r.json['persistence']);self.assertEqual(r.json['streams'][-1]['name'],'republiclive');self.assertEqual(r.headers['Cache-Control'],'no-store')
 def test_ram_copy_edits_original_capture_unchanged(self):
  c=self.app().test_client();r=c.delete('/api/brics/streams',base_url=O,headers={'Origin':O},json={'name':'ANI NEWS'});self.assertEqual(r.status_code,200)
  self.assertEqual(len(c.get('/api/brics/streams',base_url=O).json['streams']),4)
  panel=c.get('/api/dashboard-snapshots?project=brics',base_url=O).json['panels']['brics_streams'];self.assertEqual(len(panel['items']),5);self.assertEqual(panel['observed_at'],NOW.isoformat());self.assertTrue(all(x['availability']=='not_checked' for x in panel['items']))
  self.assertEqual((Path(__file__).resolve().parents[1]/'intelligence/brics/config/streams.yaml').read_bytes(),RAW)
 def test_explicit_auth_origin_and_no_copy_to_players(self):
  with self.assertRaises(ValueError):create_stream_fixture(RAW,NOW,authorize=None,allowed_origin=O)
  with self.assertRaises(ValueError):create_stream_fixture(RAW,NOW,authorize=lambda r:True,allowed_origin=None)
  c=self.app().test_client();self.assertEqual(c.post('/api/brics/streams',base_url=O,json={'name':'X','country':'India','link':'abcdefghijk'}).status_code,403)
  self.assertEqual(c.get('/health',base_url=O).json,{'state':'staging','collection':False,'mail':False,'scraper':False})

 def test_origin_host_and_nonbool_auth_fail_closed(self):
  for origin in ('https://evil.example','null',O+'/',O.upper()):
   c=self.app().test_client();r=c.delete('/api/brics/streams',base_url=O,headers={'Origin':origin},json={'name':'ANI NEWS'});self.assertEqual(r.status_code,403,origin)
  c=self.app().test_client();self.assertEqual(c.get('/api/brics/streams',base_url='http://evil.example').status_code,403)
  for callback in (lambda r:'yes',lambda r:1,lambda r:[],lambda r:(_ for _ in ()).throw(RuntimeError('SECRET'))):
   c=create_stream_fixture(RAW,NOW,authorize=callback,allowed_origin=O).test_client();r=c.get('/api/brics/streams',base_url=O);self.assertEqual(r.status_code,403);self.assertNotIn('SECRET',r.text)
 def test_source_hash_and_future_capture(self):
  import hashlib
  from datetime import timedelta
  app=self.app();self.assertEqual(app.config['STREAM_FIXTURE_SOURCE_SHA256'],hashlib.sha256(RAW).hexdigest())
  with self.assertRaises(ValueError):create_stream_fixture(RAW,datetime.now(timezone.utc)+timedelta(days=1),authorize=lambda r:True,allowed_origin=O)
