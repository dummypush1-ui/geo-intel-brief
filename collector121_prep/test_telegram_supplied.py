import unittest
from .telegram_supplied import prepare_supplied_backup,BackupRefused
R=[{'title':'Trade','url':'https://example.com/a','summary':'text','published':'2026-01-01T00:00:00+00:00'}]
class Tests(unittest.TestCase):
 def test_synthetic_mapping_only(self):
  r=prepare_supplied_backup(R,[{'state':'ok','message_id':10}],synthetic=True)
  self.assertEqual(r['mapped_fixture_records'][0]['telegram_message_id'],10);self.assertEqual(r['mapped_fixture_records'][0]['telegram_url'],'https://t.me/fixture_channel/10');self.assertFalse(r['sent']);self.assertTrue(r['refs_are_synthetic'])
 def test_numeric_and_unrecognized_links(self):
  for chat,link in [('-1001234567890','https://t.me/c/1234567890/10'),('unrecognized','')]:
   r=prepare_supplied_backup(R,[{'state':'ok','message_id':10}],synthetic=True,chat=chat)
   self.assertEqual(r['mapped_fixture_records'][0]['telegram_url'],link)
 def test_failures_continue_no_refs(self):
  for state in ('http_error','exception','json_error'):
   r=prepare_supplied_backup(R,[{'state':state,'message_id':10}],synthetic=True)
   self.assertEqual(r['mapped_fixture_records'][0]['telegram_url'],'');self.assertEqual(r['coarse_error_count'],1)
 def test_unconfigured_original_fallback(self):
  r=prepare_supplied_backup(R,[],synthetic=True,configured=False);self.assertEqual(r['fixture_send_trace'],[]);self.assertIsNone(r['mapped_fixture_records'][0]['telegram_message_id'])
 def test_explicit_synthetic_required(self):
  with self.assertRaises(BackupRefused):prepare_supplied_backup(R,[])
 def test_missing_outcome_refused(self):
  with self.assertRaises(BackupRefused):prepare_supplied_backup(R,[],synthetic=True)
 def test_original_oversize_bug_not_hidden(self):
  r=prepare_supplied_backup([dict(R[0],summary='x'*5000)],[{'state':'ok','message_id':10}],synthetic=True)
  self.assertEqual(r['oversize_fixture_batches'],1);self.assertFalse(r['production_ready'])
if __name__=='__main__':unittest.main()
