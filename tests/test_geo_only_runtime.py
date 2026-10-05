import unittest
from werkzeug.security import generate_password_hash
from integration.geo_only_runtime import compose_geo_only
HASH=generate_password_hash('fixture-private-access-password')
def env():return {'PREVIEW_ACCESS_ENABLED':'true','PREVIEW_ORIGIN':'https://preview.example','PREVIEW_SESSION_KEY':'x'*64,'PREVIEW_PASSWORD_HASH':HASH,'NEWS_READ_ENABLED':'true','NEWS_STORE_MAPPING_VERIFIED':'true','GEO_MONGODB_URI':'mongodb://fixture-only','GEO_DATABASE':'geo_intel','GEO_ARTICLES_COLLECTION':'articles'}
def login(c):
 import re
 base='https://preview.example';r=c.get('/login',base_url=base);token=re.search(r'name="csrf" value="([^"]+)"',r.text)[1]
 assert c.post('/login',base_url=base,headers={'Origin':base},data={'csrf':token,'password':'fixture-private-access-password'}).status_code==303
class Store:
 def __init__(self):self.calls=[]
 def find(self,q,p):self.calls.append(('find',q,p));return self
 def sort(self,*a):self.calls.append(('sort',*a));return self
 def limit(self,n):self.calls.append(('limit',n));return self
 def max_time_ms(self,n):self.calls.append(('max_time_ms',n));return self
 def close(self):self.calls.append(('close',))
 def __iter__(self):return iter([{'title':'fixture','url':'https://example.com/a','country':'','created_at':'2026-09-09T17:07:50+00:00','emailed':True}])
class Client:
 def __init__(self):self.paths=[];self.closed=False;self.store=Store()
 def __getitem__(self,key):self.paths.append(key);return self.store if key=='articles' else self
 def close(self):self.closed=True
class GeoOnlyTests(unittest.TestCase):
 def test_default_off_no_factory(self):
  a=compose_geo_only({});self.assertEqual(a.extensions['read_only_news_clients'],[]);self.assertEqual(a.test_client().get('/api/news').status_code,403)
 def test_only_geo_labels_and_bounded_find(self):
  client=Client();a=compose_geo_only(env(),lambda *args,**kwargs:client);c=a.test_client()
  login(c)
  response=c.get('/api/news',base_url='https://preview.example');self.assertEqual(response.status_code,200);self.assertEqual([r['project'] for r in response.json['items']],['geo']);self.assertEqual(client.paths,['geo_intel','articles']);self.assertIn(('limit',100),client.store.calls);self.assertEqual(client.store.calls[-1],('close',));self.assertNotIn('emailed',response.json['items'][0]);self.assertEqual(response.json['items'][0]['original_country'],'')
 def test_no_client_without_gates(self):
  for key,value in [('NEWS_STORE_MAPPING_VERIFIED','false'),('PREVIEW_ACCESS_ENABLED','false'),('GEO_MONGODB_URI',''),('GEO_ARTICLES_COLLECTION','events'),('GEO_DATABASE','admin'),('GEO_DATABASE','newsbot'),('GEO_DATABASE','NewsBot'),('GEO_ARTICLES_COLLECTION','ADMIN'),('GEO_ARTICLES_COLLECTION','local'),('GEO_DATABASE','geo_other')]:
   e=env();e[key]=value;called=[]
   with self.assertRaises(ValueError):compose_geo_only(e,lambda *args,**kwargs:called.append(1))
   self.assertEqual(called,[])
 def test_creation_redacts_and_mapping_closes(self):
  def fail(*a,**kw):raise RuntimeError('secret-uri')
  with self.assertRaisesRegex(ValueError,'Read-only client unavailable'):compose_geo_only(env(),fail)
  class Broken(Client):
   def __getitem__(self,key):raise RuntimeError('secret-uri')
  c=Broken()
  with self.assertRaisesRegex(ValueError,'mapping unavailable'):compose_geo_only(env(),lambda *a,**kw:c)
  self.assertTrue(c.closed)
 def test_factory_connect_false_one_call(self):
  calls=[]
  def factory(*args,**kwargs):calls.append((args,kwargs));return Client()
  compose_geo_only(env(),factory);self.assertEqual(len(calls),1);self.assertFalse(calls[0][1]['connect']);self.assertEqual(calls[0][1]['serverSelectionTimeoutMS'],5000)
 def test_override_separate_grant_cannot_bypass_denials(self):
  for key,value in [('GEO_DATABASE','NewsBot'),('GEO_DATABASE','LOCAL'),('GEO_DATABASE','EVENTS'),('GEO_ARTICLES_COLLECTION','Admin'),('GEO_ARTICLES_COLLECTION','EVENTS')]:
   e=env();e.update(GEO_MAPPING_OVERRIDE_VERIFIED='true');e[key]=value
   with self.assertRaises(ValueError):compose_geo_only(e,lambda *a,**kw:Client())
 def test_request_errors_close_once_and_latch_503(self):
  for stage in ('find','sort','limit','cursor'):
   class BadStore(Store):
    def find(self,*args):
     if stage=='find':raise RuntimeError('private-find')
     return self
    def sort(self,*args):
     if stage=='sort':raise RuntimeError('private-sort')
     return self
    def limit(self,*args):
     if stage=='limit':raise RuntimeError('private-limit')
     return self
    def __iter__(self):raise RuntimeError('private-cursor')
   class BadClient(Client):
    def __init__(self):super().__init__();self.store=BadStore();self.closes=0
    def close(self):self.closes+=1;super().close()
   client=BadClient();a=compose_geo_only(env(),lambda *a,**kw:client);c=a.test_client()
   login(c)
   for _ in range(2):
    response=c.get('/api/news',base_url='https://preview.example');self.assertEqual(response.status_code,503);self.assertNotIn('private-',response.get_data(as_text=True))
   self.assertEqual(client.closes,1)
