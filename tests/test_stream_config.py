import unittest,hashlib
from datetime import datetime,timezone
from pathlib import Path
from integration.stream_config import configured_streams,StreamConfigError
from integration.dashboard_snapshots import DashboardSnapshots
from integration.brics_streams import FixtureStreams
NOW=datetime(2026,10,5,tzinfo=timezone.utc)
class StreamConfigTests(unittest.TestCase):
 def test_original_preserved_configuration_and_fixture_copy(self):
  raw=(Path(__file__).resolve().parents[1]/'intelligence/brics/config/streams.yaml').read_bytes();d=configured_streams(raw,NOW);self.assertEqual(len(d['items']),5);self.assertEqual(d['sha256'],hashlib.sha256(raw).hexdigest());self.assertEqual(d['items'][-1]['video_id'],'jndNegut8RY');self.assertFalse(d['persistence'])
  store=FixtureStreams(d['items']);store.remove(d['items'][0]['name']);self.assertEqual(len(d['items']),5);self.assertEqual(len(store.load()),4)
  gate=DashboardSnapshots({'brics_streams':lambda:d},True,{'brics_streams':['www.youtube.com']});panel=gate('brics')['panels']['brics_streams'];self.assertEqual(len(panel['items']),5);self.assertTrue(all(x['availability']=='not_checked' for x in panel['items']))
 def test_unsafe_yaml_and_envelopes(self):
  for s in ['streams: []\nstreams: []','streams: &x []','streams: *x','streams: !!python/object/apply:os.system [echo]','%YAML 1.1\n---\nstreams: []','streams: [[[[[[]]]]]]','streams: {}','streams: []\npassword: secret','streams: []\n---\nstreams: []','streams: [{1: value}]']:
   with self.assertRaises(StreamConfigError):configured_streams(s.encode(),NOW)
 def test_bad_scalar_ids_duplicate_names_and_budget(self):
  rows=['{name: x, type: video, video_id: abcdefghijk, private: secret}','{name: x, type: video, video_id: [abc]}','{name: x, type: video, video_id: nope}']
  for r in rows:
   with self.assertRaises(StreamConfigError):configured_streams(('streams: ['+r+']').encode(),NOW)
  with self.assertRaises(StreamConfigError):configured_streams(b'streams: [{name: X, type: video, video_id: abcdefghijk}, {name: x, type: video, video_id: abcdefghijk}]',NOW)
  for raw in (b'',b'x'*16385,b'\xff','streams: []'):
   with self.assertRaises(StreamConfigError):configured_streams(raw,NOW)
 def test_channel_empty_and_bad_time(self):
  d=configured_streams(('streams: [{name: A, type: channel, channel_id: UC'+'a'*22+'}]').encode(),NOW);self.assertIn('/channel/UC',d['items'][0]['watch_url'])
  self.assertEqual(configured_streams(b'streams: []',NOW)['items'],[])
  with self.assertRaises(StreamConfigError):configured_streams(b'streams: []',datetime(2026,10,5))

 def test_indentless_depth_before_constructor(self):
  from unittest.mock import patch
  raw=b'streams:\n- a:\n  - b: x\n'
  with patch('integration.stream_config.yaml.load',side_effect=AssertionError('constructor must not run')):
   with self.assertRaises(StreamConfigError):configured_streams(raw,NOW)
 def test_extreme_clock_overflow_redacted(self):
  from datetime import timedelta
  for dt in [datetime.min.replace(tzinfo=timezone(timedelta(hours=14))),datetime.max.replace(tzinfo=timezone(timedelta(hours=-12)))]:
   with self.assertRaises(StreamConfigError):configured_streams(b'streams: []',dt)
