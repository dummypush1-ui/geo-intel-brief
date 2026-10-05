import unittest,subprocess,json
from pathlib import Path
class AppsScriptAuditTests(unittest.TestCase):
 def test_child_hash_selftest_and_cases(self):
  r=subprocess.run(['node','integration/apps_script_audit/audit.js'],capture_output=True,text=True,timeout=10)
  self.assertEqual(r.returncode,0,r.stderr)
  result=json.loads(r.stdout);self.assertEqual(len(result['cases']),17)
  expected={'trusted_harness_direct_globals_absent_but_host_escape_exists','empty_digest_skipped','critical_only_sends_no_mark','send_then_mark_UTF8_fixture','digest_non200_no_send','truncated_JSON','invalid_UTF8_decoded_JSON','replacement_character_HTML_is_not_rejected_by_original','Gmail_quota_throw_no_mark','two_cycles_mark_never200_duplicate_send','mark_transport_error_after_send_logged','large_mark_body_no_original_bound','trigger_rebuild_deletes_unrelated_and_partial_failure','partial_trigger_deletion_failure','parse_time_edge_cases','read_int_partial_numeric','doGet_dummy_secret_only'}
  self.assertEqual({x['case'] for x in result['cases']},expected)
  self.assertEqual(len({x['case'] for x in result['cases']}),17)
  self.assertEqual(result['scope'],'offline_not_production_not_receipt_proof')
  import hashlib
  self.assertEqual(result['source_sha256'],hashlib.sha256(Path('intelligence/geo/apps_script/Code.gs').read_bytes()).hexdigest())
  self.assertEqual(r.stderr,'')
  for forbidden in ('https://','http://','fixture-1','DUMMY_NON_SECRET','@'):
   self.assertNotIn(forbidden,r.stdout+r.stderr)
  for case in result['cases']:
   self.assertEqual(case['scope'],'offline_not_production_not_receipt_proof');self.assertEqual(case['status'],'pass')
  self.assertNotIn('DUMMY_NON_SECRET',r.stdout);self.assertNotIn('@',r.stdout)
