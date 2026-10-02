import unittest
from integration.loaded_charts import BricsKeywordPolicy,loaded_chart
STAMP='2026-10-02T12:00:00Z'
class LoadedChartTests(unittest.TestCase):
 def test_utc_chart_window_missing_future(self):
  rows=[{'project':'brics','collected_at':t} for t in ['2026-10-02T05:30:00+05:30','2026-10-01T12:00:00Z','2026-10-02T13:00:00Z','2026-09-01T00:00:00Z','2026-10-02T00:00:00']]
  d=loaded_chart(rows,'brics',STAMP);self.assertEqual(len(d['daily_volume']),14);self.assertEqual(sum(r['count'] for r in d['daily_volume']),2);self.assertEqual(d['missing_time_count'],1);self.assertEqual(d['future_time_count'],1);self.assertEqual(d['critical_state'],'unavailable_without_original_policy')
 def test_exact_supplied_policy_original_substring_not_proof(self):
  p=BricsKeywordPolicy([' Sanctions '],True);rows=[{'project':'brics','title':'SANCTIONS announced','collected_at':'2026-10-01T12:00:00Z'},{'project':'brics','title':'Sanctions later','collected_at':'2026-10-02T13:00:00Z'},{'project':'brics','title':'sanctions missing'}]
  d=loaded_chart(rows,'brics',STAMP,p);self.assertEqual(d['critical_24h_loaded'],1);self.assertEqual(d['critical_keyword_matches_missing_time'],1);self.assertTrue(d['not_total_database'])
 def test_policy_and_input_fail_closed(self):
  for keywords,verified in [([],True),([''],True),(['attack'],1),(['x'*201],True)]:
   with self.assertRaises(ValueError):BricsKeywordPolicy(keywords,verified)
  for rows,project,now in [([],'all',STAMP),([],'geo','2026-10-02'),([{}]*1001,'geo',STAMP)]:
   with self.assertRaises(ValueError):loaded_chart(rows,project,now)
  with self.assertRaises(ValueError):loaded_chart([],'brics',STAMP,lambda r:True)
 def test_geo_seven_days_empty_not_full_database(self):
  d=loaded_chart([],'geo',STAMP);self.assertEqual(len(d['daily_volume']),7);self.assertEqual(sum(r['count'] for r in d['daily_volume']),0);self.assertEqual(d['scope'],'loaded_read_view')
