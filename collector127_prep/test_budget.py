import unittest,hashlib
from unittest.mock import patch
from datetime import datetime,timezone
from .network_selection import select_installed_source
from collector115_prep.profile import compile_profile
from collector123_prep.parser_runner import parse_supplied_bytes,ParserRefused
D=datetime(2026,1,1,tzinfo=timezone.utc);URL=compile_profile({})['feeds'][0][1]
B=b'<rss><channel><item><title>Trade</title><link>https://example.com/a</link><pubDate>Thu, 01 Jan 2026 00:00:00 GMT</pubDate></item></channel></rss>'
R={'bytes':B,'input_sha256':hashlib.sha256(B).hexdigest(),'wire_bytes':len(B),'url':URL,'peer':'8.8.8.8','tls_hostname_verified':True,'delivery':False}
class Tests(unittest.TestCase):
 def test_smoke_mock_fetch_actual_isolated_parser(self):
  with patch('collector127_prep.network_selection.run_fetch',return_value=R):
   x=select_installed_source({},URL,clock=D);self.assertEqual(x['state'],'selected');self.assertFalse(x['live_write_ready'])
 def test_remaining_budget_forwarded(self):
  with patch('collector127_prep.network_selection.time.monotonic',side_effect=[0,1,20,21]),patch('collector127_prep.network_selection.run_fetch',return_value=R)as f,patch('collector127_prep.network_selection.parse_supplied_bytes',return_value={'entries':[],'entry_count':0,'bozo':False})as p:
   x=select_installed_source({},URL,clock=D);self.assertEqual(f.call_args.kwargs['timeout'],20);self.assertEqual(p.call_args.kwargs['timeout'],5);self.assertEqual(x['state'],'selected_empty')
 def test_no_parser_when_fetch_exhausts_budget(self):
  with patch('collector127_prep.network_selection.time.monotonic',side_effect=[0,1,26]),patch('collector127_prep.network_selection.run_fetch',return_value=R),patch('collector127_prep.network_selection.parse_supplied_bytes')as p:
   self.assertEqual(select_installed_source({},URL,clock=D)['state'],'combined_budget_expired');p.assert_not_called()
 def test_discard_selection_after_expiry(self):
  with patch('collector127_prep.network_selection.time.monotonic',side_effect=[0,1,22,25]),patch('collector127_prep.network_selection.run_fetch',return_value=R),patch('collector127_prep.network_selection.parse_supplied_bytes',return_value={'entries':[],'entry_count':0,'bozo':False}):
   self.assertEqual(select_installed_source({},URL,clock=D)['state'],'combined_budget_expired')
 def test_invalid_parser_timeout_before_subprocess(self):
  for n in (True,0,11,float('nan'),float('inf'),'1'):
   with patch('collector123_prep.parser_runner.subprocess.Popen')as p:
    with self.assertRaises(ParserRefused):parse_supplied_bytes(B,timeout=n)
    p.assert_not_called()
