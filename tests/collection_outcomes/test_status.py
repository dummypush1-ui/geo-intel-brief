import importlib,unittest
from unittest.mock import patch
class StatusTests(unittest.TestCase):
 def setUp(self):self.w=importlib.import_module('intelligence.geo.web')
 def run_job(self,rss,gnews=0):
  with patch.object(self.w,'collect_rss',return_value=rss),patch.object(self.w,'collect_gnews',return_value=gnews),patch.object(self.w,'ENABLE_GNEWS',True),patch.object(self.w,'seed_events',return_value=1):self.w._run_collect_job()
  return self.w._collect_status['last_result']
 def test_confirmed_counts(self):
  r=self.run_job(2);self.assertEqual(r['state'],'confirmed');self.assertEqual(r['rss']['inserted_count'],2)
 def test_partial_explicit(self):
  p=dict(state='partial',attempted=3,inserted_count=1,duplicate_count=1,failed_count=1,uncertain_count=0,retry_safe=False)
  r=self.run_job(p);self.assertEqual(r['state'],'partial');self.assertEqual(r['rss'],p)
 def test_unknown_explicit(self):
  p=dict(state='uncertain',attempted=3,inserted_count=None,duplicate_count=None,failed_count=None,uncertain_count=3,retry_safe=False)
  self.assertEqual(self.run_job(0,p)['state'],'uncertain')
 def test_invalid_outcome_redacted(self):
  for x in ({'secret':'private-uri'},-1,True):
   r=self.run_job(x);self.assertEqual(r['state'],'failed');self.assertNotIn('private',str(r))
 def test_raw_exception_not_status(self):
  with patch.object(self.w,'collect_rss',side_effect=RuntimeError('private-uri')):self.w._run_collect_job()
  self.assertEqual(self.w._collect_status['last_result']['error'],'collection_failed')
 def test_dashboard_no_false_backup_claim(self):
  from pathlib import Path
  s=(Path(__file__).parents[2]/'intelligence/geo/reports/dashboard.py').read_text()
  self.assertIn('backup is paused',s);self.assertNotIn('backup copy of every record',s);self.assertNotIn('full record shown for each',s)
