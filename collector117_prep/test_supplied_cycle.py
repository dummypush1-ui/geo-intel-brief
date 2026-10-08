import unittest,hashlib
from datetime import datetime,timezone
from unittest.mock import patch
from .supplied_cycle import compose_cycle,CycleRefused
from collector115_prep.profile import compile_profile
D=datetime(2026,1,1,tzinfo=timezone.utc)
RSS=b'<rss><channel><item><title>Trade</title><link>https://example.com/a</link><pubDate>Thu, 01 Jan 2026 00:00:00 GMT</pubDate></item></channel></rss>'
F=compile_profile({})['feeds']
def proof(b):return {'bytes':b,'input_sha256':hashlib.sha256(b).hexdigest(),'wire_bytes':len(b)}
class Tests(unittest.TestCase):
 def test_bad_source_continues_next(self):
  r=compose_cycle({}, {F[0][1]:proof(b'<!DOCTYPE rss SYSTEM "https://example.com/external">'+RSS),F[1][1]:proof(RSS)},clock=D)
  self.assertEqual(r['refused_count'],1);self.assertEqual(len(r['candidates']),1);self.assertEqual(r['candidates'][0]['source'],'BBC Business');self.assertEqual(len(r['source_states']),25)
 def test_missing_never_healthy(self):
  r=compose_cycle({}, {},clock=D);self.assertFalse(r['all_sources_healthy_verified']);self.assertTrue(all(x['state']=='not_supplied'for x in r['source_states']))
 def test_bad_hash_whole_input_preflight(self):
  p=proof(RSS);p['input_sha256']='0'*64
  with patch('collector117_prep.supplied_cycle.compose_supplied')as parser:
   with self.assertRaises(CycleRefused):compose_cycle({}, {F[0][1]:proof(RSS),F[1][1]:p},clock=D)
   parser.assert_not_called()
 def test_extra_feeds_omission_explicit(self):
  r=compose_cycle({}, {},clock=D);self.assertIn('extra_rss_feeds_parity',r['profile']['pending_gates'])
 def test_aggregate_preflight(self):
  p=proof(b'x'*1048576)
  with patch('collector117_prep.supplied_cycle.compose_supplied')as parser:
   with self.assertRaises(CycleRefused):compose_cycle({}, {F[n][1]:p for n in range(5)},clock=D)
   parser.assert_not_called()
 def test_source_drift_not_disguised(self):
  from collector115_prep.composition import CompositionRefused
  with patch('collector117_prep.supplied_cycle.compose_supplied',side_effect=CompositionRefused('drift')):
   with self.assertRaises(CompositionRefused):compose_cycle({}, {F[0][1]:proof(RSS)},clock=D)
if __name__=='__main__':unittest.main()

class IntegrityTests(unittest.TestCase):
 def test_source_pin_drift_loud(self):
  from .supplied_cycle import InstallationRefused
  with patch('collector117_prep.supplied_cycle.json.loads',return_value={'collector115_prep/profile.py':'0'*64}):
   with self.assertRaises(InstallationRefused):compose_cycle({}, {},clock=D)
 def test_missing_isolation_binary_loud(self):
  from .supplied_cycle import InstallationRefused
  with patch('collector117_prep.supplied_cycle.parser_installation.BWRAP','/missing/bwrap'):
   with self.assertRaises(InstallationRefused):compose_cycle({}, {},clock=D)
 def test_launch_oserror_not_disguised_as_source(self):
  with patch('collector117_prep.supplied_cycle.compose_supplied',side_effect=OSError('runtime unavailable')):
   with self.assertRaises(OSError):compose_cycle({}, {F[0][1]:proof(RSS)},clock=D)
 def test_bozoflag_separate(self):
  r=compose_cycle({}, {F[0][1]:proof(RSS[:-6])},clock=D)
  self.assertEqual(r['bozo_count'],1);self.assertFalse(r['all_sources_healthy_verified'])
