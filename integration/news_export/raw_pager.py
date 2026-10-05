"""Injected Mongo-plan executor seam. No client, environment, route or network.

The callable adapter owns query execution, cursor cleanup and a stable snapshot.
Only an offline fixture adapter is provided in tests; no production adapter exists.
"""
import json
from asyncio import CancelledError
from bson import ObjectId
from .keyset_plan import query_plan,page_resume,KeysetPlanError

class RawPagerError(ValueError):pass
class RawPagerControlError(BaseException):pass

class RawPager:
 """Single-pass original-order raw pages, never a public cursor endpoint.

 verify_scope(project, order) must return exactly True after checking complete
 format-aware coverage, matching binary collation/index and stable snapshot.
 This callback is an adapter obligation, NOT proof supplied by this class.
 execute(plan) must return a fully materialized bounded list and close its cursor
 even on failure. Neither callback is retried; failure permanently closes pager.
 """
 def __init__(self,project,execute,verify_scope,*,page_size=500,max_page_bytes=2*1024*1024):
  plan=query_plan(project,limit=page_size)
  if not callable(execute) or not callable(verify_scope):raise RawPagerError('adapter callbacks required')
  if type(max_page_bytes) is not int or not 128<=max_page_bytes<=2*1024*1024:raise RawPagerError('page budget')
  self._project=project;self._execute=execute;self._verify=verify_scope
  self._size=page_size;self._budget=max_page_bytes;self._last=None
  self._verified=False;self._closed=False;self._eof=False
 def __init_subclass__(cls,**kwargs):
  raise TypeError("RawPager cannot be subclassed")
 def _shutdown(self):
  self._closed=True;self._execute=None;self._verify=None
 def close(self):
  RawPager._shutdown(self)
 def fetch_page(self):
  if self._closed:raise RawPagerError('pager closed')
  if self._eof:return []
  try:
   plan=query_plan(self._project,self._last,self._size)
   if not self._verified:
    if self._verify(self._project,tuple(plan['sort'])) is not True:raise RawPagerError('scope not verified')
    self._verified=True
   # The executor must not mutate the plan; validation uses independent contract.
   rows=self._execute(plan)
   if type(rows) is not list or len(rows)>self._size:raise RawPagerError('bounded materialized page required')
   fields=set(query_plan(self._project,limit=self._size)['projection'])
   total=2
   for row in rows:
    if type(row) is not dict or not set(row)<=fields:raise RawPagerError('closed projected row required')
    # Scalars and one bounded original corroboration-list shape only.
    for field,value in row.items():
     if field=='_id' and type(value) is ObjectId:continue
     if field=='corroborated_by' and type(value) is list:
      if len(value)>100 or any(type(x) is not str or len(x)>8000 for x in value):raise RawPagerError('bounded corroboration')
     elif value is not None and type(value) not in (str,int,float,bool):raise RawPagerError('scalar row required')
     elif type(value) is str and len(value)>32000:raise RawPagerError('bounded field required')
    encoded=json.dumps(row,ensure_ascii=False,allow_nan=False,separators=(',',':'),default=lambda x:str(x) if type(x) is ObjectId else None).encode('utf-8')
    total+=len(encoded)+1
    if total>self._budget:raise RawPagerError('page byte budget')
   last=page_resume(self._project,rows,self._last,limit=self._size)
   self._last=last
   if len(rows)<self._size:self._eof=True
   return rows
  except BaseException as exc:
   RawPager._shutdown(self)
   if not isinstance(exc,Exception):
    try:
     if type(exc) is SystemExit:
      code=exc.code if type(exc.code) is int or exc.code is None else 1
      replacement=SystemExit(code)
     elif type(exc) in (KeyboardInterrupt,GeneratorExit,CancelledError):replacement=type(exc)()
     else:replacement=RawPagerControlError('raw page interrupted')
    except BaseException:
     replacement=RawPagerControlError('raw page interrupted')
    raise replacement from None
   raise RawPagerError('raw page unavailable or invalid') from None
