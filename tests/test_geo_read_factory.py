import unittest,importlib,sys,os
from unittest.mock import patch
from tests.test_geo_only_runtime import env,Client,Store
from integration.geo_read_factory import create_geo_read_client
class FactoryTests(unittest.TestCase):
 def test_lazy_options_narrow_surface(self):
  raw=Client()
  with patch('pymongo.MongoClient',return_value=raw) as ctor:
   client=create_geo_read_client('mongodb://fixture-secret')
  self.assertEqual(ctor.call_args.kwargs,dict(connect=False,tls=True,serverSelectionTimeoutMS=5000,connectTimeoutMS=5000,socketTimeoutMS=5000,maxPoolSize=4,minPoolSize=0,waitQueueTimeoutMS=2000,tlsAllowInvalidCertificates=False,tlsAllowInvalidHostnames=False))
  db=client['geo_intel'];col=db['articles'];cur=col.find({},{});cur.sort('created_at',-1).limit(100).max_time_ms(2000);self.assertIs(iter(cur),cur);cur.close()
  for obj in [client,db,col,cur]:
   for name in ['aggregate','command','with_options','insert_one','update_one','delete_many','create_index','bulk_write']:
    self.assertFalse(hasattr(obj,name))
 def test_sanitized_constructor(self):
  with patch('pymongo.MongoClient',side_effect=RuntimeError('fixture-secret')):
   with self.assertRaisesRegex(ValueError,'^Read-only client unavailable$') as e:create_geo_read_client('mongodb://fixture-secret')
  self.assertNotIn('fixture-secret',str(e.exception))
 def test_actual_router_read_gates_and_one_client(self):
  e=env();e['PREVIEW_GEO_ONLY_ENABLED']='true';raw=Client()
  sys.modules.pop('integration.private_router',None)
  try:
   with patch.dict(os.environ,e,clear=True),patch('pymongo.MongoClient',return_value=raw) as ctor:
    m=importlib.import_module('integration.private_router');self.assertEqual(ctor.call_count,1);self.assertEqual(raw.paths,['geo_intel','articles'])
  finally:sys.modules.pop('integration.private_router',None)
  for key in ['PREVIEW_ACCESS_ENABLED','NEWS_STORE_MAPPING_VERIFIED']:
   bad=dict(e);bad[key]='false'
   with patch.dict(os.environ,bad,clear=True),patch('pymongo.MongoClient',side_effect=AssertionError('should not construct')) as ctor:
    with self.assertRaises(ValueError):importlib.import_module('integration.private_router')
    ctor.assert_not_called()
   sys.modules.pop('integration.private_router',None)
 def test_cursor_close_all_setup_iteration_paths(self):
  from integration.storage_reader import ReadOnlyNewsReader
  for stage in ['sort','limit','max_time_ms','iterate','ok']:
   class Cursor:
    closed=False
    def sort(self,*a):
     if stage=='sort':raise RuntimeError()
     return self
    def limit(self,*a):
     if stage=='limit':raise RuntimeError()
     return self
    def max_time_ms(self,*a):
     if stage=='max_time_ms':raise RuntimeError()
     return self
    def __iter__(self):
     if stage=='iterate':raise RuntimeError()
     return iter([])
    def close(self):self.closed=True
   cur=Cursor()
   class Collection:
    def find(self,*a):return cur
   reader=ReadOnlyNewsReader({'geo':Collection()},verified=True,query_timeout_ms=2000)
   if stage=='ok':reader()
   else:
    with self.assertRaises(RuntimeError):reader()
   self.assertTrue(cur.closed)

 def test_iterator_never_exposes_raw_cursor_collection(self):
  from integration.geo_read_factory import ReadCursor
  class Raw:
   collection=object()
   def __iter__(self):return self
   def __next__(self):raise StopIteration
  cursor=ReadCursor(Raw());iterator=iter(cursor)
  self.assertIs(iterator,cursor);self.assertEqual(list(cursor),[])
  for name in ['collection','aggregate','command','with_options','insert_one','update_one','create_index']:
   self.assertFalse(hasattr(iterator,name))
