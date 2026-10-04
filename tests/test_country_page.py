import unittest
from integration.country_page import country_page
from integration.news_view import views
from integration.news_api import create_app

DATA={'geo':[{'url':'https://example.com/a','title':'India steel <img src=x>','country':'India','created_at':'2026-10-04T12:00:00Z','emailed':True,'_id':'secret'}, {'url':'https://example.com/b','title':'India mentioned only','country':'China'}, {'url':'https://example.com/c','title':'Lower-case label','country':'india'}], 'brics':[{'url':'https://example.com/d','title':'Trade brief','country':'India'}]}

class CountryPageTests(unittest.TestCase):
 def test_exact_labels_and_no_mentions_or_alias_union(self):
  d=country_page(views(DATA),'India');self.assertEqual(d['count'],2);self.assertEqual(d['project_counts'],{'geo':1,'brics':1});self.assertEqual(d['countries'],['China','India','india']);self.assertIsNone(d['risk_index']);self.assertFalse(d['delivery']);self.assertNotIn('_id',str(d));self.assertNotIn('emailed',str(d))
 def test_normalization_string_contract_and_padded_labels(self):
  raw={'geo':[{'url':'https://example.com/none','title':'A','country':None},{'url':'https://example.com/int','title':'B','country':42},{'url':'https://example.com/padded','title':'C','country':' India '}]}
  rows=views(raw);self.assertTrue(all(isinstance(r['original_country'],str) for r in rows))
  d=country_page(rows,'India');self.assertEqual(d['count'],0);self.assertNotIn(' India ',d['countries']);self.assertEqual(d['countries'],['42'])
 def test_project_isolation_empty_and_unknown(self):
  self.assertEqual(country_page(views(DATA),'India','geo')['count'],1)
  self.assertEqual(country_page(views(DATA),'USA')['count'],0)
  self.assertEqual(country_page(views(DATA))['count'],0)
 def test_limit_not_total_and_no_input_mutation(self):
  rows=views(DATA);d=country_page(rows*101,'India');self.assertTrue(d['truncated']);self.assertEqual(len(d['items']),100);self.assertEqual(d['count'],202);self.assertEqual(len(rows),4);self.assertTrue(d['not_total_database'])
 def test_validation(self):
  for c,p in [('a'*101,''),('India','wrong'),('India\n','')]:
   with self.assertRaises(ValueError):country_page([],c,p)
 def test_routes_guard_errors_and_no_new_write_route(self):
  denied=create_app().test_client()
  for path in ['/workspace/countries','/api/country-page','/workspace/assets/countries.js']:self.assertEqual(denied.get(path).status_code,403)
  client=create_app(reader=lambda:DATA,authorize=lambda req:True).test_client()
  self.assertEqual(client.get('/api/country-page?country=India').json['count'],2)
  self.assertEqual(client.get('/api/country-page?project=wrong').status_code,400)
  self.assertEqual(client.post('/api/country-page',headers={'Origin':'http://localhost'}).status_code,405)
  response=client.get('/workspace/countries');self.assertEqual(response.headers['Cache-Control'],'no-store');response.close()
 def test_reader_failure_is_not_empty(self):
  def fail():raise RuntimeError('private detail')
  r=create_app(reader=fail,authorize=lambda req:True).test_client().get('/api/country-page?country=India');self.assertEqual(r.status_code,503);self.assertNotIn('private detail',r.get_data(as_text=True))
 def test_atlas_sample_shape_read_only_empty_country(self):
  raw={'geo':[{'_id':'fixture-private','title':'Atlas-shape fixture','url':'https://example.com/a?at_medium=RSS&at_campaign=rss','source':'BBC World','category':'TRADE','summary':'Fixture only','published':'2026-09-09T10:20:40+00:00','score':16,'risk_level':'MODERATE','country':'','created_at':'2026-09-09T17:07:50.869488+00:00','emailed':True}]}
  normalized=views(raw);self.assertEqual(normalized[0]['original_country'],'');self.assertTrue(normalized[0]['collected_at'].endswith('+00:00'));self.assertIn('at_medium=RSS',normalized[0]['url']);self.assertEqual(country_page(normalized,'India')['count'],0)
  d=create_app(reader=lambda:raw,authorize=lambda req:True).test_client().get('/api/news?project=geo').json['items'][0];self.assertNotIn('emailed',d);self.assertNotIn('mongo_id',d);self.assertTrue(raw['geo'][0]['emailed'])
