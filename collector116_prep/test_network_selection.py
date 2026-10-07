import hashlib,unittest
from datetime import datetime,timezone
from unittest.mock import patch
from .network_selection import select_installed_source,SelectionRefused
from collector114_prep.runner import FetchRefused
from collector115_prep.profile import compile_profile
D=datetime(2026,1,1,tzinfo=timezone.utc)
RSS=b'<rss><channel><item><title>Trade tariff</title><link>https://example.com/a</link><pubDate>Thu, 01 Jan 2026 00:00:00 GMT</pubDate></item></channel></rss>'
URL=compile_profile({})['feeds'][0][1]
def result(blob=RSS):return {'bytes':blob,'input_sha256':hashlib.sha256(blob).hexdigest(),'wire_bytes':len(blob),'url':URL,'peer':'8.8.8.8','tls_hostname_verified':True,'delivery':False}
class Tests(unittest.TestCase):
 def test_mock_network_bytes_real_isolated_parser_selection(self):
  with patch('collector116_prep.network_selection.run_fetch',return_value=result())as f:
   r=select_installed_source({},URL,clock=D)
   self.assertEqual(r['state'],'selected');self.assertEqual(r['candidates'][0]['source'],'BBC World');self.assertFalse(r['live_write_ready']);self.assertFalse(r['source_healthy_verified'])
   self.assertEqual(f.call_args.kwargs['timeout'],20)
 def test_fetch_failure_no_parser(self):
  with patch('collector116_prep.network_selection.run_fetch',side_effect=FetchRefused('fixture')),patch('collector116_prep.network_selection.parse_supplied_bytes')as p:
   self.assertEqual(select_installed_source({},URL,clock=D)['state'],'fetch_refused');p.assert_not_called()
 def test_parser_failure_visible(self):
  with patch('collector116_prep.network_selection.run_fetch',return_value=result(b'<!DOCTYPE rss>'+RSS)):
   self.assertEqual(select_installed_source({},URL,clock=D)['state'],'parse_refused')
 def test_no_request_selected_source(self):
  with patch('collector116_prep.network_selection.run_fetch')as f:
   with self.assertRaises(SelectionRefused):select_installed_source({},'https://unknown.example/rss',clock=D)
   f.assert_not_called()
 def test_hash_mismatch_before_parse(self):
  r=result();r['input_sha256']='0'*64
  with patch('collector116_prep.network_selection.run_fetch',return_value=r),patch('collector116_prep.network_selection.parse_supplied_bytes')as p:
   with self.assertRaises(SelectionRefused):select_installed_source({},URL,clock=D)
   p.assert_not_called()
 def test_bozo_not_healthy(self):
  with patch('collector116_prep.network_selection.run_fetch',return_value=result(RSS[:-6])):
   r=select_installed_source({},URL,clock=D);self.assertEqual(r['state'],'parsed_bozo_unverified');self.assertFalse(r['source_healthy_verified'])
if __name__=='__main__':unittest.main()
