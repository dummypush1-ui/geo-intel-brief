import unittest
from werkzeug.security import generate_password_hash
from integration.single_db_plan import SingleDatabasePlan
from integration.single_db_runtime import compose_single_database
class Store:
 def find(self,*a,**kw):return self
 def sort(self,*a):return self
 def limit(self,n):return []
class Database:
 def __init__(self):self.geo=Store();self.other=Store();self.keys=[]
 def __getitem__(self,k):self.keys.append(k);return self.geo if k=='geo_rows' else self.other
class Client:
 def __init__(self):self.db=Database();self.keys=[];self.closed=False
 def __getitem__(self,k):self.keys.append(k);return self.db
 def close(self):self.closed=True
class SingleDBRuntimeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.hash=generate_password_hash('fixture')
 def config(self):return {'PREVIEW_ACCESS_ENABLED':'true','PREVIEW_ORIGIN':'https://preview.example','PREVIEW_PASSWORD_HASH':self.hash,'PREVIEW_SESSION_KEY':'k'*64,'NEWS_READ_ENABLED':'true','NEWS_STORE_MAPPING_VERIFIED':'true','GEO_MONGODB_URI':'mongodb://fixture'}
 def test_one_client_explicit_maps_private(self):
  calls=[];client=Client()
  def factory(uri,**kw):calls.append((uri,kw));return client
  app=compose_single_database(self.config(),SingleDatabasePlan('fixture_db','geo_rows','other_rows'),factory)
  self.assertEqual(len(calls),1);self.assertEqual(client.keys,['fixture_db']);self.assertEqual(client.db.keys,['geo_rows','other_rows']);self.assertFalse(calls[0][1]['connect']);self.assertEqual(app.test_client().get('/api/news').status_code,403)
 def test_gates_before_factory(self):
  def forbidden(*a,**k):raise AssertionError('Client forbidden')
  for key in ['PREVIEW_ACCESS_ENABLED','NEWS_STORE_MAPPING_VERIFIED','GEO_MONGODB_URI','PREVIEW_SESSION_KEY']:
   e=self.config();e.pop(key);self.assertRaises(ValueError,compose_single_database,e,SingleDatabasePlan('fixture_db','geo_rows','other_rows'),forbidden)
 def test_disabled_no_client(self):
  def forbidden(*a,**k):raise AssertionError('Client forbidden')
  app=compose_single_database({},SingleDatabasePlan('fixture_db','geo_rows','other_rows'),forbidden);self.assertEqual(app.extensions['read_only_news_clients'],[])
 def test_failed_mapping_closes_client(self):
  c=Client();c.db.other=c.db.geo
  self.assertRaises(ValueError,compose_single_database,self.config(),SingleDatabasePlan('fixture_db','geo_rows','other_rows'),lambda *a,**k:c);self.assertTrue(c.closed)

 def test_subclasses_and_raising_factory(self):
  class Env(dict):pass
  class Plan(SingleDatabasePlan):pass
  p=SingleDatabasePlan('fixture_db','geo_rows','other_rows')
  self.assertRaises(ValueError,compose_single_database,Env(self.config()),p,lambda *a,**k:Client())
  self.assertRaises(ValueError,compose_single_database,self.config(),Plan('fixture_db','geo_rows','other_rows'),lambda *a,**k:Client())
  def raising(*a,**k):raise RuntimeError('mongodb://secret-host')
  with self.assertRaises(ValueError) as error:compose_single_database(self.config(),p,raising)
  self.assertNotIn('secret-host',str(error.exception))
  self.assertRaises(ValueError,compose_single_database,self.config(),p,lambda *a,**k:None)
 def test_explicit_access_off_with_reads_on(self):
  e=self.config();e['PREVIEW_ACCESS_ENABLED']='false'
  def forbidden(*a,**k):raise AssertionError('must not run')
  self.assertRaises(ValueError,compose_single_database,e,SingleDatabasePlan('fixture_db','geo_rows','other_rows'),forbidden)
