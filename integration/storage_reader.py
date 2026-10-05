"""Injected read-only stores. No credentials, client creation or index changes.

The caller must supply verified Geo/BRICS article stores separately. Never infer
that two stores named articles share a schema or represent the same project.
"""
from collections.abc import Mapping
from integration.public_news import READ_STORE_FIELDS
class ReadOnlyNewsReader:
 def __init__(self,stores,verified=False,limit=100,query_timeout_ms=None):
  if not verified:raise ValueError('Verified store mapping required')
  if not isinstance(stores,Mapping) or not stores or any(k not in ('geo','brics') for k in stores):raise ValueError('Explicit project stores required')
  if len(stores)==2 and stores['geo'] is stores['brics']:raise ValueError('Shared store requires reviewed project discriminator; unsupported here')
  if not isinstance(limit,int) or isinstance(limit,bool) or not 1<=limit<=1000:raise ValueError('Invalid read limit')
  if query_timeout_ms is not None and (type(query_timeout_ms) is not int or not 1<=query_timeout_ms<=5000):raise ValueError("Invalid query timeout")
  self.stores=dict(stores);self.limit=limit;self.query_timeout_ms=query_timeout_ms
 def __call__(self):
  result={}
  for project,store in self.stores.items():
   projection={key:1 for key in READ_STORE_FIELDS}
   cursor=None
   try:
    cursor=store.find({},projection)
    cursor.sort('created_at' if project=='geo' else 'collected_at',-1);cursor.limit(self.limit)
    if self.query_timeout_ms is not None:cursor.max_time_ms(self.query_timeout_ms)
    result[project]=[dict(row) for row in cursor]
   finally:
    if cursor is not None:
     try:cursor.close()
     except Exception:pass
  return result
