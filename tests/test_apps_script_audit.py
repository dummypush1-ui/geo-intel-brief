import unittest,subprocess,json
from pathlib import Path
class AppsScriptAuditTests(unittest.TestCase):
 def test_child_hash_selftest_and_cases(self):
  r=subprocess.run(['node','integration/apps_script_audit/audit.js'],capture_output=True,text=True,timeout=10)
  self.assertEqual(r.returncode,0,r.stderr)
  result=json.loads(r.stdout);self.assertEqual(len(result['cases']),25)
  expected={'Gmail_quota_throw_no_mark', 'mark403_after_send_unknown_receipt_no_retry', 'truncated_JSON', 'trusted_harness_direct_globals_absent_but_host_escape_exists', 'invalid_UTF8_decoded_JSON', 'creation_cleanup_failure_is_visible', 'send_then_mark_UTF8_fixture', 'digest_non200_no_send', 'strict_time_edge_cases', 'interval_mode_ignores_unused_digest_times', 'staging_capacity_preserves_existing', 'two_cycles_mark_never200_duplicate_send', 'critical_only_sends_no_mark', 'doGet_dummy_secret_only', 'large_mark_body_no_original_bound', 'replacement_character_HTML_is_not_rejected_by_original', 'trigger_staging_preserves_unrelated_and_rolls_back_creation_failure', 'partial_old_deletion_failure_is_reported_no_false_rollback', 'trigger_success_preserves_unrelated_and_removes_managed', 'empty_digest_skipped', 'held403_all_jobs_visible_no_mail_no_retry', 'strict_int_rejects_partial_numeric', 'non200_critical_weekly_collect_health_visible', 'mark_transport_error_after_send_logged', 'all_schedule_validation_precedes_trigger_changes'}
  self.assertEqual({x['case'] for x in result['cases']},expected)
  self.assertEqual(len({x['case'] for x in result['cases']}),25)
  self.assertEqual(result['scope'],'offline_not_production_not_receipt_proof')
  import hashlib
  self.assertEqual(result['source_sha256'],hashlib.sha256(Path('intelligence/geo/apps_script/Code.gs').read_bytes()).hexdigest())
  self.assertEqual(r.stderr,'')
  for forbidden in ('https://','http://','fixture-1','DUMMY_NON_SECRET','@'):
   self.assertNotIn(forbidden,r.stdout+r.stderr)
  for case in result['cases']:
   self.assertEqual(case['scope'],'offline_not_production_not_receipt_proof');self.assertEqual(case['status'],'pass')
  self.assertNotIn('DUMMY_NON_SECRET',r.stdout);self.assertNotIn('@',r.stdout)
