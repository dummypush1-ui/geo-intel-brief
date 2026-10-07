import unittest,hashlib
from datetime import datetime,timezone
from unittest.mock import patch
from .network_selection import select_installed_source,SelectionRefused
from collector126_prep.extra_profile import ExtraFeedsRefused
D=datetime(2026,1,1,tzinfo=timezone.utc);U='https://example.com/custom'
B=b'<rss><channel><item><title>Trade</title><link>https://example.com/a</link><pubDate>Thu, 01 Jan 2026 00:00:00 GMT</pubDate></item></channel></rss>'
R={'bytes':B,'input_sha256':hashlib.sha256(B).hexdigest(),'wire_bytes':len(B),'url':U,'peer':'8.8.8.8','tls_hostname_verified':True,'delivery':False}
class Tests(unittest.TestCase):
 def test_configured_extra_actual_parser(self):
  with patch('collector127_prep.network_selection.run_fetch',return_value=R)as f:
   x=select_installed_source({'EXTRA_RSS_FEEDS':' , '+U+' ,' },U,clock=D,reviewed_extra_urls=(U,))
   self.assertEqual(x['source'],'Custom');self.assertEqual(x['candidates'][0]['credibility'],'MEDIUM');self.assertEqual(f.call_args.args[0][-1],('Custom',U,'MEDIUM'));self.assertFalse(x['live_write_ready']);self.assertIn('installation_allowlist_owner_review',x['pending_gates'])
 def test_unapproved_no_fetch(self):
  with patch('collector127_prep.network_selection.run_fetch')as f:
   with self.assertRaises(ExtraFeedsRefused):select_installed_source({'EXTRA_RSS_FEEDS':U},U,clock=D)
   f.assert_not_called()
 def test_allowlisted_not_configured_no_fetch(self):
  with patch('collector127_prep.network_selection.run_fetch')as f:
   with self.assertRaises(SelectionRefused):select_installed_source({},U,clock=D,reviewed_extra_urls=(U,))
   f.assert_not_called()
