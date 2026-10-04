import unittest
from integration.news_api import create_app
class CountrySignalRoutes(unittest.TestCase):
 def test_guard_no_write(self):
  c=create_app().test_client();self.assertEqual(c.get('/api/country-signals?country=India').status_code,403)
  c=create_app(authorize=lambda r:True).test_client();self.assertEqual(c.get('/api/country-signals?country=India').json['risk_index_state'],'insufficient_history');self.assertEqual(c.post('/api/country-signals',headers={'Origin':'http://localhost'}).status_code,405)
 def test_validation_and_private_rows(self):
  raw={'geo':[dict(url='https://example.com/a',title='Fixture',country='India',risk_level='HIGH',created_at='2026-10-04T00:00:00Z',telegram_url='private',emailed=True,_id='private')]}
  c=create_app(reader=lambda:raw,authorize=lambda r:True).test_client();d=c.get('/api/country-signals?country=India').json
  self.assertEqual(d['loaded_distinct_article_keys'],1);self.assertNotIn('private',str(d));self.assertEqual(c.get('/api/country-signals').status_code,400);self.assertEqual(c.get('/api/country-signals?country='+('x'*101)).status_code,400)
 def test_failure_distinct_from_zero(self):
  def fail():raise RuntimeError('private')
  c=create_app(reader=fail,authorize=lambda r:True).test_client();r=c.get('/api/country-signals?country=India');self.assertEqual(r.status_code,503);self.assertNotIn('private',r.get_data(as_text=True))

 def test_data_error503_other_country_isolated(self):
  raw={'geo':[dict(url='https://example.com/a',title='A',country='India'),dict(url='https://example.com/b',title='B',country='China',risk_level='HIGH',created_at='2026-10-04T00:00:00Z')]}
  raw['geo'][1]['country']='x'*101
  c=create_app(reader=lambda:raw,authorize=lambda r:True).test_client();r=c.get('/api/country-signals?country=India');self.assertEqual(r.status_code,200);self.assertEqual(r.json['supplied_read_view_rows'],2)
