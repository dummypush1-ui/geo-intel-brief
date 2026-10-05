"""Lazy Geo read-only facade. No I/O/imported Mongo client until called.

Private mapping/read gates belong to launcher/composition before invocation.
Dedicated read-only credential must be verified externally. This facade prevents
accidental write calls, not hostile in-process introspection or privileged URI.
"""
class ReadCursor:
 __slots__=('_cursor',)
 def __init__(self,cursor):self._cursor=cursor
 def sort(self,*args):self._cursor.sort(*args);return self
 def limit(self,n):self._cursor.limit(n);return self
 def max_time_ms(self,n):self._cursor.max_time_ms(n);return self
 def __iter__(self):return self
 def __next__(self):return next(self._cursor)
 def close(self):self._cursor.close()

class ReadCollection:
 __slots__=('_collection',)
 def __init__(self,collection):self._collection=collection
 def find(self,query,projection):return ReadCursor(self._collection.find(query,projection))

class ReadDatabase:
 __slots__=('_database',)
 def __init__(self,database):self._database=database
 def __getitem__(self,name):return ReadCollection(self._database[name])

class ReadClient:
 __slots__=('_client',)
 def __init__(self,client):self._client=client
 def __getitem__(self,name):return ReadDatabase(self._client[name])
 def close(self):self._client.close()

def create_geo_read_client(uri,*,serverSelectionTimeoutMS=5000,connect=False):
 """Never log URI; sanitized errors only. No ping or initial read."""
 try:
  from pymongo import MongoClient
  client=MongoClient(uri,connect=False,tls=True,serverSelectionTimeoutMS=5000,
                     connectTimeoutMS=5000,socketTimeoutMS=5000,
                     maxPoolSize=4,minPoolSize=0,waitQueueTimeoutMS=2000,
                     tlsAllowInvalidCertificates=False,tlsAllowInvalidHostnames=False)
  return ReadClient(client)
 except Exception:raise ValueError('Read-only client unavailable') from None
