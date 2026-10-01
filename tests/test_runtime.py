import unittest
from werkzeug.security import generate_password_hash
from integration.runtime import compose
class Store:
 def find(self,query,projection=None):assert query=={};return self
 def sort(self,*a):return self
 def limit(self,n):return []
class Database:
 def __getitem__(self,key):return Store()
class Client:
 def __getitem__(self,key):return Database()
 def close(self):pass
class RuntimeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.hash=generate_password_hash('fixture')
 def config(self):return {'PREVIEW_ACCESS_ENABLED':'true','PREVIEW_ORIGIN':'https://preview.example','PREVIEW_PASSWORD_HASH':self.hash,'PREVIEW_SESSION_KEY':'k'*64,'NEWS_READ_ENABLED':'true','NEWS_STORE_MAPPING_VERIFIED':'true','GEO_MONGODB_URI':'mongodb://fixture-geo','BRICS_MONGODB_URI':'mongodb://fixture-brics'}
 def test_no_clients_by_default(self):
  def forbidden(*a,**kw):raise AssertionError('Client must not be created')
  app=compose({},forbidden);self.assertEqual(app.test_client().get('/health').status_code,200);self.assertEqual(app.extensions['read_only_news_clients'],[])
 def test_config_gates_before_clients(self):
  for field in ['PREVIEW_ACCESS_ENABLED','NEWS_STORE_MAPPING_VERIFIED','GEO_MONGODB_URI','PREVIEW_SESSION_KEY']:
   e=self.config();e.pop(field)
   def forbidden(*a,**kw):raise AssertionError('Client must not be created')
   with self.assertRaises(ValueError):compose(e,forbidden)
 def test_explicit_isolated_reads(self):
  calls=[]
  def factory(uri,**kw):calls.append((uri,kw));return Client()
  app=compose(self.config(),factory);self.assertEqual(len(calls),2)
  self.assertTrue(all(c[1]['connect'] is False for c in calls));self.assertEqual(app.test_client().get('/api/news').status_code,403)
 def test_same_store_rejected(self):
  e=self.config();e.update(BRICS_MONGODB_URI=e['GEO_MONGODB_URI'],BRICS_MONGODB_DB='geo_intel')
  with self.assertRaises(ValueError):compose(e,lambda *a,**k:Client())

 def test_storage_failure_is_redacted(self):
  from integration.news_api import create_app
  def broken():raise RuntimeError('mongodb://secret:password@private-host')
  c=create_app(broken,lambda r:True).test_client()
  for path in ['/api/news','/api/story-groups']:
   response=c.get(path);self.assertEqual(response.status_code,503);self.assertNotIn('password',response.text);self.assertNotIn('private-host',response.text)
