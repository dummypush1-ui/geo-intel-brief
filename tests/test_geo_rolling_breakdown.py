import unittest
from integration.geo_rolling_breakdown import geo_rolling_breakdown
NOW='2026-10-02T12:00:00Z'
def row(time,category='TRADE',country='India',project='geo'):
 return {'project':project,'collected_at':time,'category':category,'original_country':country}
class GeoRollingTests(unittest.TestCase):
 def test_exact_rolling_boundaries_and_accounting(self):
  rows=[row(t) for t in ['2026-09-25T12:00:00Z','2026-09-25T11:59:59Z','2026-10-02T12:00:01Z',None,'2026-10-02','2026-10-02T12:00:00']]+[row('2026-10-02T17:30:00+05:30')]
  d=geo_rolling_breakdown(rows,NOW);self.assertEqual(d['in_window_count'],2);self.assertEqual(d['outside_window_count'],1);self.assertEqual(d['future_time_count'],1);self.assertEqual(d['missing_time_count'],3)
  self.assertEqual(d['loaded_count'],sum(d[k] for k in ('in_window_count','outside_window_count','future_time_count','missing_time_count')));self.assertEqual(d['categories'],[{'category':'TRADE','count':2}]);self.assertTrue(d['not_total_database'])
 def test_country_cap_ties_missing_and_no_mutation(self):
  rows=[row(NOW,'C',str(i)) for i in range(10)]+[row(NOW,'',''),row(NOW,project='brics')];before=[dict(r) for r in rows]
  d=geo_rolling_breakdown(rows,NOW);self.assertEqual(len(d['top_countries']),8);self.assertEqual(d['other_country_story_count'],2);self.assertEqual(d['missing_country_count'],1);self.assertEqual(d['missing_category_count'],1);self.assertEqual(d['loaded_count'],11);self.assertEqual(rows,before)
  self.assertEqual(d,geo_rolling_breakdown(list(reversed(rows)),NOW))
 def test_empty_and_validation(self):
  d=geo_rolling_breakdown([],NOW);self.assertEqual(d['loaded_count'],0);self.assertEqual(d['categories'],[])
  for rows,now in [([],None),([],'2026-10-02'),([],'0001-01-01T00:00:00Z'),([{}],NOW),([row(NOW)]*1001,NOW),([row(NOW,category=None)],NOW),([row(NOW,project='wrong')],NOW)]:
   with self.assertRaises(ValueError):geo_rolling_breakdown(rows,now)
 def test_duplicates_caller_contract(self):
  d=geo_rolling_breakdown([row(NOW),row(NOW)],NOW);self.assertEqual(d['in_window_count'],2)
