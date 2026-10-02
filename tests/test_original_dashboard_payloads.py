import unittest
from integration.original_dashboard_payloads import geo_events,brics_sources
from integration.dashboard_snapshots import DashboardSnapshots
STAMP='2026-10-02T00:00:00Z'
class OriginalPayloadTests(unittest.TestCase):
 def test_events_preserve_original_metadata_no_private_keys(self):
  raw=[{'name':'Summit','event_date':'2026-10-03','source_url':'https://example.com/a','description':'meeting','category':'CONFERENCE','confidence':'CONFIRMED','_id':'private'}]
  snapshot=geo_events(raw,STAMP);d=DashboardSnapshots({'geo_events':lambda:snapshot},True,{'geo_events':['example.com']})('geo')['panels']['geo_events']['items'][0]
  self.assertEqual(d['category'],'CONFERENCE');self.assertEqual(d['confidence'],'CONFIRMED');self.assertNotIn('_id',d);self.assertIn('_id',raw[0])
 def test_naive_time_requires_explicit_original_utc_contract(self):
  rows=[{'name':'A','url':'https://example.com/a','country':'India'}];status={'A':{'status':'ok','count':3,'checked_at':'2026-10-02T00:00:00','message':'password secret'}}
  self.assertIsNone(brics_sources(rows,status,STAMP)['items'][0]['last_checked'])
  result=brics_sources(rows,status,STAMP,'UTC')['items'][0];self.assertEqual(result['last_checked'],'2026-10-02T00:00:00+00:00');self.assertNotIn('message',result)
 def test_missing_status_not_empty_cycle(self):
  with self.assertRaises(ValueError):brics_sources([],None,STAMP)
  result=brics_sources([{'name':'A'}],{},STAMP);self.assertNotIn('last_count',result['items'][0])
 def test_capture_time_and_bounds(self):
  for rows,stamp in [([],None),([],'2026-10-02'),([{}]*1001,STAMP)]:
   with self.assertRaises(ValueError):geo_events(rows,stamp)
  with self.assertRaises(ValueError):brics_sources([],{},STAMP,'Asia/Calcutta')
 def test_zoned_checked_time_preserved_and_bad_time_missing(self):
  for time,want in [('2026-10-02T05:30:00+05:30','2026-10-02T00:00:00+00:00'),('invalid',None),(True,None)]:
   self.assertEqual(brics_sources([{'name':'A'}],{'A':{'checked_at':time}},STAMP,'UTC')['items'][0]['last_checked'],want)

 def test_malformed_names_no_crash_and_no_input_mutation(self):
  rows=[{'name':[],'url':'https://example.com/x'},{'name':'A','url':'https://example.com/a','secret':'private'}];statuses={'A':{'status':'ok','checked_at':'2026-10-02T00:00:00','count':2}}
  result=brics_sources(rows,statuses,STAMP,'UTC');self.assertEqual(result['items'][1]['last_count'],2);self.assertNotIn('secret',result['items'][1]);self.assertNotIn('last_count',rows[1]);self.assertEqual(statuses['A']['checked_at'],'2026-10-02T00:00:00')
