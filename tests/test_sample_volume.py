import unittest
from datetime import datetime,timezone
from integration.news_api import create_app
STAMP=datetime.now(timezone.utc).isoformat()
class SampleVolumeTests(unittest.TestCase):
 def test_selection_scope_duplicate_and_missing(self):
  rows={'geo':[{'url':'https://example.com/'+str(i),'title':str(i),'country':'India','created_at':STAMP} for i in range(101)]}
  c=create_app(reader=lambda:rows,authorize=lambda r:True).test_client();d=c.get('/api/sample-volume?project=geo').json
  self.assertEqual(d['sample_count'],100);self.assertTrue(d['truncated']);self.assertTrue(d['not_total_database']);self.assertEqual(sum(x['count'] for x in d['daily_volume']),100)
  rows['geo']=[{'url':'https://example.com/x','title':'one','country':'India'},{'url':'https://example.com/x','title':'one','country':'India'}]
  d=c.get('/api/sample-volume?project=geo&country=India').json;self.assertEqual(d['sample_count'],1);self.assertEqual(d['duplicates_omitted'],1);self.assertEqual(d['missing_time_count'],1)
  self.assertEqual(c.get('/api/sample-volume?project=geo&country=Brazil').json['sample_count'],0)
 def test_outside_window_counts_account_for_entire_sample(self):
  rows={'geo':[{'url':'https://example.com/'+str(i),'title':str(i),'created_at':t} for i,t in enumerate([STAMP,'2000-01-01T00:00:00Z','2099-01-01T00:00:00Z',None])]}
  d=create_app(reader=lambda:rows,authorize=lambda r:True).test_client().get('/api/sample-volume?project=geo').json
  self.assertEqual(d['outside_window_count'],1);self.assertEqual(d['sample_count'],sum(x['count'] for x in d['daily_volume'])+d['missing_time_count']+d['future_time_count']+d['outside_window_count'])
 def test_guards_errors_policy_off(self):
  self.assertEqual(create_app().test_client().get('/api/sample-volume?project=geo').status_code,403)
  c=create_app(reader=lambda:{'brics':[]},authorize=lambda r:True).test_client()
  for q in ['', 'project=bad','project=brics&sort=score']:self.assertEqual(c.get('/api/sample-volume?'+q).status_code,400)
  d=c.get('/api/sample-volume?project=brics').json;self.assertEqual(len(d['daily_volume']),14);self.assertEqual(d['critical_state'],'unavailable_without_original_policy')
  c=create_app(reader=lambda:1/0,authorize=lambda r:True).test_client();self.assertEqual(c.get('/api/sample-volume?project=geo').status_code,503)
