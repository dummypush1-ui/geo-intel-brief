import unittest
from datetime import datetime,timezone
from integration.dashboard_model import signals,loaded_stats
from integration.news_view import views
from integration.news_api import create_app
NOW=datetime(2026,10,2,12,tzinfo=timezone.utc)
class DashboardModelTests(unittest.TestCase):
 def test_geo_signals_do_not_default_unknown(self):
  self.assertEqual(signals({},'geo'),{'risk_level':None,'credibility':None,'score':None})
  self.assertIsNone(signals({'score':True,'risk_level':'unknown'},'geo')['score'])
  self.assertIsNone(signals({'score':float('inf')},'geo')['score'])
 def test_brics_counts_only_supplied(self):
  self.assertEqual(signals({'corroborated_by':['A','B']},'brics')['corroboration_count'],2)
  self.assertIsNone(signals({'corroborated_by':'AB'},'brics')['corroboration_count'])
 def test_loaded_critical_window(self):
  rows=[{'project':'geo','risk_level':'CRITICAL','collected_at':t} for t in ['2026-10-02T11:00:00+00:00','2026-10-01T11:59:59+00:00','2026-10-03T00:00:00+00:00',None]]
  r=loaded_stats(rows,'geo',NOW);self.assertEqual(r['critical_24h_loaded'],1);self.assertEqual(r['critical_missing_time_count'],1);self.assertTrue(r['not_total_database']);self.assertEqual(r['events_state'],'unavailable')
 def test_wrong_project_and_clock(self):
  with self.assertRaises(ValueError):loaded_stats([],'other',NOW)
  with self.assertRaises(ValueError):loaded_stats([],'geo',datetime(2026,10,2))
 def test_readview_carries_original_signals(self):
  raw={'geo':[{'url':'https://example.com/a','title':'x','risk_level':'HIGH','credibility':'MEDIUM','score':42}]}
  r=views(raw)[0];self.assertEqual(r['score'],42);self.assertEqual(r['risk_level'],'HIGH');self.assertNotIn('project',raw['geo'][0])
 def test_route_guards_and_scope(self):
  self.assertEqual(create_app().test_client().get('/api/dashboard-signals?project=geo').status_code,403)
  c=create_app(authorize=lambda r:True).test_client();self.assertEqual(c.get('/api/dashboard-signals').status_code,400)
  r=c.get('/api/dashboard-signals?project=brics').json;self.assertEqual(r['critical_state'],'unavailable_without_original_policy');self.assertEqual(r['loaded_count'],0)

 def test_naive_endpoint_time_not_invented(self):
  from unittest.mock import patch
  from integration.dashboard_model import loaded_stats as actual
  rows={'geo':[{'url':'https://example.com/a','title':'x','risk_level':'CRITICAL','created_at':'2026-10-02T11:00:00'}]}
  c=create_app(reader=lambda:rows,authorize=lambda r:True).test_client()
  with patch('integration.news_api.loaded_stats',side_effect=lambda rows,project:actual(rows,project,NOW)):
   d=c.get('/api/dashboard-signals?project=geo').json
  self.assertEqual(d['critical_24h_loaded'],0);self.assertEqual(d['critical_missing_time_count'],1)
 def test_extreme_values_missing_not_crash(self):
  from integration.news_view import date_view
  for value in ['0001-01-01T00:00:00+01:00','9999-12-31T23:59:59-01:00']:
   self.assertIsNone(date_view(value))
  self.assertIsNone(signals({'score':10**400},'geo')['score'])
 def test_internal_ids_absent_every_public_route(self):
  rows={'geo':[{'_id':'PRIVATE-MONGO-ID','url':'https://example.com/a','title':'HS 090121'}]}
  c=create_app(reader=lambda:rows,authorize=lambda r:True).test_client()
  for response in [c.get('/api/news'),c.get('/api/story-groups'),c.post('/api/related-news',headers={'Origin':'http://localhost'},json={'code':'090121'})]:
   self.assertNotIn('PRIVATE-MONGO-ID',response.text);self.assertNotIn('legacy_id',response.text)
  key=c.get('/api/news').json['items'][0]['article_key']
  self.assertEqual(c.post('/api/finder-context',headers={'Origin':'http://localhost'},json={'project':'geo','article_key':key}).status_code,200)
