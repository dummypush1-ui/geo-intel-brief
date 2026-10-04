import unittest
from datetime import datetime,timezone
from copy import deepcopy
from integration.country_signals import country_signals

NOW=datetime(2026,10,5,tzinfo=timezone.utc)
def row(key,day,country='India',project='geo',level='HIGH'):
 return dict(article_key=key,collected_at=day,published_at=day,original_country=country,project=project,risk_level=level,telegram_url='private',emailed=True)
class CountrySignalsTests(unittest.TestCase):
 def test_exact_label_geo_only_and_no_private_fields(self):
  d=country_signals([row('a','2026-10-04T00:00:00Z'),row('b','2026-10-04T00:00:00Z','india'),row('c','2026-10-04T00:00:00Z',project='brics')],'India',NOW)
  self.assertEqual(d['collected_28d_count'],1);self.assertNotIn('private',str(d));self.assertIsNone(d['risk_index']);self.assertFalse(d['coverage_verified'])
 def test_boundary_missing_future_and_publication_independent(self):
  a=row('a','2026-09-07T00:00:00Z');b=row('b','2026-09-06T23:59:59Z');c=row('c',None);c['published_at']='2026-10-04T00:00:00Z';d=row('d','2026-10-06T00:00:00Z')
  s=country_signals([a,b,c,d],'India',NOW);self.assertEqual(s['collected_28d_count'],1);self.assertEqual(s['published_28d_count'],2);self.assertEqual(s['missing_collection_time_count'],1);self.assertEqual(s['future_collection_time_count'],1)
 def test_history_span_does_not_invent_baseline(self):
  s=country_signals([row('a','2026-09-01T00:00:00Z')],'India',NOW);self.assertEqual(s['history_state'],'observed_span_only');self.assertIsNone(s['baseline']);self.assertIsNone(s['risk_index']);self.assertEqual(s['observed_active_date_labels_in_window'],0)
 def test_empty_and_recent_insufficient(self):
  for rows in [[],[row('a','2026-09-09T00:00:00Z')]]:
   self.assertEqual(country_signals(rows,'India',NOW)['risk_index_state'],'insufficient_history')
 def test_dedupe_and_no_mutation(self):
  rows=[row('a','2026-10-04T00:00:00Z'),row('a','2026-10-03T00:00:00Z')];before=deepcopy(rows);s=country_signals(rows,'India',NOW);self.assertEqual(s['loaded_distinct_article_keys'],1);self.assertEqual(rows,before)
 def test_invalid_time_and_unrecognized_risk(self):
  rows=[row('a','bad',level='CRITICAL'),row('b','2026-10-04T00:00:00',level='LOW'),row('c','2026-10-04T00:00:00Z',level='invented')];s=country_signals(rows,'India',NOW);self.assertEqual(s['missing_collection_time_count'],2);self.assertEqual(s['missing_risk_level_28d_count'],1);self.assertEqual(sum(s['stored_risk_level_counts'].values()),0)
 def test_validation_and_offset(self):
  for country,now in [('',NOW),(' India',NOW),('a'*101,NOW),('India',datetime(2026,10,5)),('India','bad')]:
   with self.assertRaises(ValueError):country_signals([],country,now)
  s=country_signals([row('a','2026-10-05T05:30:00+05:30')],'India',NOW);self.assertEqual(s['collected_28d_count'],1)

 def test_scan_cap_and_shapes(self):
  for rows in [None,1,iter([]),[None],[1],[[]],[{}]*10001]:
   with self.assertRaises(ValueError):country_signals(rows,'India',NOW)
  self.assertEqual(country_signals([{}]*10000,'India',NOW)['loaded_distinct_article_keys'],0)
 def test_field_limits_and_types(self):
  for field,size in [('original_country',101),('project',6),('article_key',129),('collected_at',101),('published_at',101),('risk_level',17)]:
   r=row('a','2026-10-04T00:00:00Z');r[field]='x'*size
   with self.assertRaises(ValueError):country_signals([r],'India',NOW)
  r=row('a','2026-10-04T00:00:00Z');r['article_key']=1
  with self.assertRaises(ValueError):country_signals([r],'India',NOW)
 def test_underflow(self):
  with self.assertRaises(ValueError):country_signals([],'India',datetime.min.replace(tzinfo=timezone.utc))
 def test_future_publication(self):
  r=row('a','2026-10-04T00:00:00Z');r['published_at']='2026-10-06T00:00:00Z'
  s=country_signals([r],'India',NOW);self.assertEqual(s['future_publication_time_count'],1);self.assertEqual(s['published_28d_count'],0)
 def test_closed_interval_has_29_possible_date_labels(self):
  from datetime import timedelta
  rows=[row(str(i),(NOW-timedelta(days=i)).isoformat()) for i in range(29)]
  s=country_signals(rows,'India',NOW);self.assertEqual(s['observed_active_date_labels_in_window'],29);self.assertEqual(s['window_interval'],'closed_28_day_elapsed_interval')
 def test_rounding_never_shows_28_when_insufficient(self):
  from datetime import timedelta
  s=country_signals([row('a',(NOW-timedelta(days=28)+timedelta(seconds=1)).isoformat())],'India',NOW)
  self.assertEqual(s['history_state'],'insufficient_history');self.assertLess(s['observed_history_days'],28)

 def test_subclasses_and_custom_timezone_no_hooks(self):
  from datetime import tzinfo
  calls=[]
  class Text(str):
   def strip(self,*a):calls.append('strip');raise RuntimeError('hook')
   def replace(self,*a):calls.append('replace');raise RuntimeError('hook')
  class Zone(tzinfo):
   def utcoffset(self,d):calls.append('utcoffset');raise RuntimeError('hook')
  for country,now in [(Text('India'),NOW),('India',Text('2026-10-05T00:00:00Z')),('India',datetime(2026,10,5,tzinfo=Zone()))]:
   with self.assertRaises(ValueError):country_signals([],country,now)
  r=row('a',datetime(2026,10,4,tzinfo=Zone()))
  with self.assertRaises(ValueError):country_signals([r],'India',NOW)
  r=row('a',Text('2026-10-04T00:00:00Z'))
  with self.assertRaises(ValueError):country_signals([r],'India',NOW)
  self.assertEqual(calls,[])

 def test_custom_key_rejected_before_lookup(self):
  calls=[]
  class Key:
   def __hash__(self):return hash('original_country')
   def __eq__(self,other):calls.append('eq');raise RuntimeError('hook')
  bad={Key():'India'}
  with self.assertRaises(ValueError):country_signals([bad],'India',NOW)
  self.assertEqual(calls,[])
  with self.assertRaises(ValueError):country_signals([{str(i):'' for i in range(101)}],'India',NOW)
