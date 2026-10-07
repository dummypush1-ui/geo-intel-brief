import unittest
from .extra_profile import compile_installed_profile,ExtraFeedsRefused
from collector115_prep.profile import compile_profile,ProfileRefused
from collector113_prep.transport_policy import TransportRefused
from collector109_prep.fetch_stage import FetchRefused
U='https://example.com/custom'
class Tests(unittest.TestCase):
 def test_default_preserved(self):
  self.assertEqual(compile_installed_profile({})['feeds'],compile_profile({})['feeds'])
 def test_original_trim_empty_and_custom_labels(self):
  p=compile_installed_profile({'EXTRA_RSS_FEEDS':' , '+U+' , ,' },reviewed_extra_urls=(U,))
  self.assertEqual(p['feeds'][-1],('Custom',U,'MEDIUM'));self.assertEqual(p['configured_extra_count'],1);self.assertFalse(p['production_ready']);self.assertFalse(p['allowlist_authority_verified'])
 def test_missing_allowlist(self):
  with self.assertRaises(ExtraFeedsRefused):compile_installed_profile({'EXTRA_RSS_FEEDS':U})
 def test_duplicates_refused_not_silent_dedupe(self):
  with self.assertRaises(ExtraFeedsRefused):compile_installed_profile({'EXTRA_RSS_FEEDS':U+','+U},reviewed_extra_urls=(U,))
 def test_unsafe_unused_manifest(self):
  for u in ('http://example.com/rss','https://127.0.0.1/rss','https://user:pass@example.com/rss','https://example.com/rss#x','https://example.com:444/rss'):
   with self.assertRaises((ExtraFeedsRefused,TransportRefused,FetchRefused,ValueError)):compile_installed_profile({},reviewed_extra_urls=(u,))
 def test_duplicate_existing_default(self):
  u=compile_profile({})['feeds'][0][1]
  with self.assertRaises(FetchRefused):compile_installed_profile({'EXTRA_RSS_FEEDS':u},reviewed_extra_urls=(u,))
 def test_projection_above100_refused_not_truncated(self):
  with self.assertRaises(ProfileRefused):compile_installed_profile({'MAX_ITEMS_PER_FEED':'101'})
 def test_manifest_and_input_shapes(self):
  for m in ([U],(U,U),(True,)):
   with self.assertRaises(ExtraFeedsRefused):compile_installed_profile({},reviewed_extra_urls=m)
  for s in ([],{'EXTRA_RSS_FEEDS':True}):
   with self.assertRaises(ExtraFeedsRefused):compile_installed_profile(s)
