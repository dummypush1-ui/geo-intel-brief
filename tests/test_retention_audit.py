import unittest,json
from datetime import datetime,timezone,timedelta
from integration.retention_audit import audit,_functions
NOW=datetime(2026,10,5,tzinfo=timezone.utc)
def row(**kw):return {'title':'fixture','summary':'fulltext','created_at':'2026-08-01T00:00:00+00:00',**kw}
class RetentionAuditTests(unittest.TestCase):
 def test_original_fidelity_value_accounting_not_losslessness(self):
  rows=[row(title='x'*130,summary='full private summary')];r=audit(rows,NOW);i=r['counts']
  self.assertEqual(i['summary_title_chars_omitted'],10);self.assertEqual(i['summary_text_chars_not_found'],20)
  self.assertEqual(i['inputs'],1);self.assertFalse(r['selection_is_eligibility'])
  self.assertEqual(r['deletion_safety'],'not_established');self.assertEqual(r['backup_losslessness'],'not_established')
 def test_separator_overflow_and_oversized_single(self):
  fn=_functions('backup')['_format_full_record'];base=row(summary='');length=len(fn(base))
  rows=[row(summary='x'*(1748-length)) for _ in range(2)]
  r=audit(rows,NOW);b=r['backup_batches'][0]
  self.assertEqual(b['estimator_chars'],3500);self.assertTrue(b['over3500']);self.assertEqual(b['actual_chars'],3504)
  r=audit([row(summary='x'*4000)],NOW);self.assertTrue(r['counts']['single_record_over3500'])
 def test_unclassifiable_exact_cutoff_and_offsets(self):
  cutoff=NOW-timedelta(days=60)
  rows=[row(created_at=v) for v in ('','bad','2026-08-01T00:00:00',cutoff.isoformat(),(cutoff-timedelta(seconds=1)).isoformat(),(cutoff+timedelta(minutes=1)).astimezone(timezone(timedelta(hours=-5))).isoformat())]
  r=audit(rows,NOW);counts=r['counts']
  self.assertEqual(counts['unclassifiable'],3);self.assertEqual(counts['at_or_after_cutoff'],2);self.assertEqual(counts['before_cutoff'],1)
  self.assertGreaterEqual(counts['unclassifiable_source_would_select'],1);self.assertEqual(counts['lexical_time_discrepancy'],1)
 def test_no_ids_diagnostics_and_no_delivery_counts(self):
  with self.assertRaisesRegex(ValueError,'Closed inert fixture fields'):audit([row(_id='private-id')],NOW)
  r=audit([row(telegram_url=''),row(telegram_url='https://t.me/hint/1')],NOW)
  self.assertEqual(r['counts']['missing_backup_hint'],1);self.assertFalse(r['selection_is_eligibility'])
  self.assertIsNone(r['failed_input_count']);self.assertIsNone(r['partial_input_count']);self.assertEqual(r['dropped_input_count'],0)
 def test_same_day_name_collision_and_apps_script_omission(self):
  a=audit([],NOW);b=audit([],NOW+timedelta(hours=2))
  self.assertEqual(a['html_archive_name'],b['html_archive_name']);self.assertIn('does_not_call_archive',a['apps_script_archive'])
 def test_bounds_null_and_invalid(self):
  r=audit([row(created_at=None)],NOW);self.assertEqual(r['counts']['unclassifiable'],1)
  for bad in ([row(title='x'*16001)],[row(score=True)],[row(title=object())]):
   with self.assertRaises(ValueError):audit(bad,NOW)

 def test_unclassifiable_lexical_and_coincident_summary(self):
  r=audit([row(created_at='',summary='fixture'),row(created_at='2020-01-01T00:00:00'),row(created_at='bad')],NOW)
  self.assertEqual(r['counts']['source_would_select'],2)
  self.assertEqual(r['counts']['unclassifiable_source_would_select'],2)
  self.assertNotIn('items',r);self.assertEqual(r['value_checks'],'structural_substring_only_not_fidelity_proof')
  self.assertEqual(audit([row(summary='fixture')],NOW)['counts']['summary_text_chars_not_found'],0)

 def test_missing_null_not_mongo_lexical_selected(self):
  missing=row();missing.pop('created_at')
  r=audit([missing,row(created_at=None),row(created_at='')],NOW)
  self.assertEqual(r['counts']['unclassifiable_missing_or_null'],2)
  self.assertEqual(r['counts']['source_would_select'],1)
  self.assertEqual(r['counts']['unclassifiable_source_would_select'],1)
  for value in ('1',None):
   with self.assertRaises(ValueError):audit([row(score=value)],NOW)
