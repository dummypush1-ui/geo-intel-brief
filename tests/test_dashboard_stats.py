import unittest
from integration.news_api import create_app
from test_bridges import ROWS
class DashboardStatsTests(unittest.TestCase):
 def setUp(self):self.c=create_app(lambda:ROWS,lambda r:True).test_client()
 def test_counts_explicit_scope(self):
  d=self.c.get('/api/news-stats?project=geo').json;self.assertEqual(d['count'],1);self.assertTrue(d['not_total_database']);self.assertEqual(d['scope'],'loaded_read_view')
 def test_invalid_project_and_private(self):
  self.assertEqual(self.c.get('/api/news-stats?project=other').status_code,400);self.assertEqual(create_app().test_client().get('/api/news-stats').status_code,403)
 def test_filters_and_empty(self):
  rows=self.c.get('/api/news?project=geo').json['items'];country=rows[0]['original_country'];category=rows[0]['category']
  from urllib.parse import urlencode
  self.assertEqual(len(self.c.get('/api/news?'+urlencode({'project':'geo','country':country,'category':category})).json['items']),1)
  self.assertEqual(self.c.get('/api/news?country=unknown').json['items'],[])

 def test_no_internal_mail_fields_in_view(self):
  row=self.c.get('/api/news').json['items'][0]
  for key in ['mongo_id','emailed','original_url']:self.assertNotIn(key,row)
