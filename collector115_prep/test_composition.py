import hashlib,unittest
from datetime import datetime,timezone
from unittest.mock import patch
from .composition import compose_supplied,CompositionRefused
from .profile import ProfileRefused,compile_profile
D=datetime(2026,1,1,tzinfo=timezone.utc)
RSS=b'<rss><channel><item><title>Trade tariff</title><link>https://example.com/a</link><pubDate>Thu, 01 Jan 2026 00:00:00 GMT</pubDate></item></channel></rss>'
def proof(b=RSS):return {'bytes':b,'input_sha256':hashlib.sha256(b).hexdigest(),'wire_bytes':len(b)}
class Tests(unittest.TestCase):
 def test_original_catalog_and_source_states(self):
  url=compile_profile({})['feeds'][0][1]
  r=compose_supplied({}, {url:proof()},clock=D)
  self.assertEqual(len(r['candidates']),1);self.assertEqual(r['candidates'][0]['source'],'BBC World')
  self.assertEqual(len(r['source_states']),25);self.assertEqual(r['source_states'][1]['state'],'not_supplied')
  self.assertFalse(r['all_sources_healthy_verified']);self.assertFalse(r['network'])
 def test_bad_hash_before_parser(self):
  url=compile_profile({})['feeds'][0][1];p=proof();p['input_sha256']='0'*64
  with patch('collector115_prep.composition.parse_supplied_bytes')as parser:
   with self.assertRaises(CompositionRefused):compose_supplied({}, {url:p},clock=D)
   parser.assert_not_called()
 def test_unlisted_evidence(self):
  with self.assertRaises(CompositionRefused):compose_supplied({}, {'https://unknown.example/rss':proof()},clock=D)
 def test_large_config_stops_before_parse(self):
  with self.assertRaises(ProfileRefused):compose_supplied({'MAX_ITEMS_PER_FEED':'101'},{},clock=D)
 def test_empty_does_not_fake_health(self):
  r=compose_supplied({}, {},clock=D)
  self.assertEqual(r['candidates'],[]);self.assertTrue(all(x['state']=='not_supplied'for x in r['source_states']))
if __name__=='__main__':unittest.main()

class ChainTests(unittest.TestCase):
 def test_catalog_bytes_to_durable_fixture_drive(self):
  from collector115_prep.composition import prepare_checkpoint_input
  from collector108_prep.durable_ledger import DurableLedger
  from collector109_prep.fixture_support import CASCollection
  from collector109_prep.checkpoint import FixtureCheckpoints
  from collector111_prep.drive_durable import drive_collection
  from integration.geo_collector_contract import GeoFixtureStore
  url=compile_profile({})['feeds'][0][1]
  r=prepare_checkpoint_input({}, {url:proof()},clock=D)
  self.assertFalse(r['live_write_ready']);b=r['checkpoint_input']
  c=CASCollection();ledger=DurableLedger(c,'geo108','a'*64);ledger.initialize();job=ledger.submit('n'*24,100)
  cp=FixtureCheckpoints()
  out=drive_collection(ledger,job['key'],job['fence'],candidates=b['candidates'],active_categories=b['active_categories'],threshold=b['threshold'],clock=lambda:101,checkpoints=cp,store=GeoFixtureStore())
  self.assertEqual(out['state'],'completed');self.assertEqual(out['counts']['fetched'],1)
 def test_no_backup_adapter_never_ready(self):
  from collector115_prep.composition import prepare_checkpoint_input
  r=prepare_checkpoint_input({}, {},clock=D)
  self.assertIn('enable_telegram_backup_adapter',r['pending_gates']);self.assertFalse(r['live_write_ready'])
 def test_original_first_n_not_first_n_valid(self):
  url=compile_profile({})['feeds'][0][1]
  blob=b'<rss><channel><item><title>No link</title></item><item><title>Trade</title><link>https://example.com/a</link></item></channel></rss>'
  r=compose_supplied({'MAX_ITEMS_PER_FEED':'1'}, {url:proof(blob)},clock=D)
  self.assertEqual(r['candidates'],[])
 def test_unknown_timezone_held_without_fallback(self):
  url=compile_profile({})['feeds'][0][1]
  blob=b'<rss><channel><item><title>Trade</title><link>https://example.com/a</link><pubDate>Jan 1 2026 01:00 XYZ</pubDate></item></channel></rss>'
  r=compose_supplied({}, {url:proof(blob)},clock=D)
  self.assertEqual(r['source_states'][0]['date_fallbacks'],0)
  self.assertEqual(r['candidates'],[])
 def test_supplied_order_cannot_override_catalog(self):
  feeds=compile_profile({})['feeds'];r=compose_supplied({}, {feeds[1][1]:proof(),feeds[0][1]:proof()},clock=D)
  self.assertEqual([a['source']for a in r['candidates']],['BBC World','BBC Business'])
