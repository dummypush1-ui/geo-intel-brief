import unittest
from .profile import compile_profile,ProfileRefused,defaults
class Tests(unittest.TestCase):
 def test_original_defaults(self):
  p=compile_profile({});self.assertEqual(p['max_items'],40);self.assertEqual(p['timeout'],20);self.assertEqual(p['lookback_hours'],48);self.assertEqual(len(p['feeds']),25)
  self.assertFalse(p['source_flags']['ENABLE_FULL_TEXT']);self.assertFalse(p['source_flags']['ENABLE_GNEWS']);self.assertFalse(p['source_flags']['ENABLE_TELEGRAM_BACKUP'])
  self.assertNotIn('enable_telegram_backup_adapter',p['pending_gates']);self.assertFalse(p['production_ready'])
 def test_config_limit_not_silent_truncate(self):
  for k,v in [('MAX_ITEMS_PER_FEED','101'),('MAX_ITEMS_PER_FEED','0'),('REQUEST_TIMEOUT','31'),('LOOKBACK_HOURS','999'),('DEDUPE_THRESHOLD','nan'),('ACTIVE_CATEGORIES','WRONG')]:
   with self.assertRaises(ProfileRefused):compile_profile({k:v})
 def test_flags_not_silently_disabled(self):
  p=compile_profile({'ENABLE_FULL_TEXT':'true','ENABLE_GNEWS':'TRUE'})
  self.assertTrue(p['source_flags']['ENABLE_FULL_TEXT']);self.assertTrue(p['source_flags']['ENABLE_GNEWS']);self.assertFalse(p['production_ready'])
 def test_no_request_url_or_secret(self):
  for k in ('EXTRA_RSS_FEEDS','MONGODB_URI','TRIGGER_SECRET','writer','url'):
   with self.assertRaises(ProfileRefused):compile_profile({k:'x'})
if __name__=='__main__':unittest.main()
