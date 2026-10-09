import unittest
from integration.news_api import create_app
from integration.query_validation import SHAPES
class Validation(unittest.TestCase):
 def test_rejects_before_reader(self):
  calls=[];c=create_app(reader=lambda:calls.append(1)or{'geo':[]},authorize=lambda _:True).test_client()
  for path,shape in SHAPES.items():
   self.assertEqual(c.get(path+'?unapproved=x').status_code,400,path)
   for k,cap in shape.items():
    for q in [k+'=a&'+k+'=b',k+'='+'a'*(cap+1),k+'=a%00b',k+'=a%0Ab']:
     self.assertEqual(c.get(path+'?'+q).status_code,400,(path,q))
  self.assertEqual(calls,[])
 def test_auth_precedes_validation(self):
  self.assertEqual(create_app().test_client().get('/api/news?q='+'a'*201).status_code,403)
 def test_valid_at_caps_and_legacy_v1_match(self):
  c=create_app(reader=lambda:{'geo':[]},authorize=lambda _:True).test_client()
  for q in ['project=geo&q='+'a'*200+'&category='+'b'*100+'&country='+'c'*100+'&sort=newest','project=geo','']:
   a=c.get('/api/news?'+q);b=c.get('/api/v1/news?'+q);self.assertEqual(a.status_code,200);self.assertEqual(a.json,b.json)
 def test_noquery_routes_and_domain_checks_still_hold(self):
  c=create_app(authorize=lambda _:True).test_client();self.assertEqual(c.get('/api/news?project=invalid').status_code,400);self.assertEqual(c.get('/api/news?q=a%7Fb').status_code,400);self.assertEqual(c.get('/api/news?q=%FF').status_code,400);self.assertEqual(c.get('/api/news-stats?project=geo&project=geo').status_code,400)
