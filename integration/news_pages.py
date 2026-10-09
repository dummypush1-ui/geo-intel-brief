"""Bounded whole-store cursor browse. Mutable read, not a stable snapshot.
No client creation/writes; injected Geo store must already be reviewed.
Opaque tokens hold no source keys. Worker-local, expiry/restarts require refresh.
"""
import secrets,re,time
from threading import Lock,Event,Thread
from copy import deepcopy
from integration.public_news import READ_STORE_FIELDS,public_news_row
from integration.news_view import normalize_row
from integration.loaded_news import selection
class PageExpired(ValueError):pass
class PageBusy(Exception):pass
class PageUnavailable(Exception):pass

def validate(filters,limit,cursor):
 if type(filters)is not dict or set(filters)!={'project','query','category','country','sort'}:raise ValueError()
 caps={'project':5,'query':200,'category':100,'country':100,'sort':20}
 if any(type(v)is not str or len(v)>caps[k] for k,v in filters.items()):raise ValueError()
 if filters['project']!='geo' or filters['sort'] not in ('newest','title','country','score'):raise ValueError()
 if type(limit)is not int or not 1<=limit<=100:raise ValueError()
 if type(cursor)is not str or (cursor and not re.fullmatch('[A-Za-z0-9_-]{43}',cursor)):raise ValueError()

class WholeGeoPages:
 def __init__(self,store,sanitize,*,verified=False,clock=time.monotonic,start_cleaner=True):
  if verified is not True or not callable(sanitize):raise ValueError('Reviewed store and sanitizer required')
  self.store=store;self.sanitize=sanitize;self.clock=clock;self.lock=Lock();self.streams={};self.stopped=Event()
  if start_cleaner:
   self.cleaner=Thread(target=self._clean,daemon=True,name='news-page-expiry');self.cleaner.start()
 def _drop(self,key):
  state=self.streams.pop(key,None)
  if state:
   try:state['cursor'].close()
   except Exception:pass
 def _expire(self):
  now=self.clock()
  for key,state in list(self.streams.items()):
   if now-state['used']>=120 or now-state['born']>=1800:self._drop(key)
 def _clean(self):
  while not self.stopped.wait(15):
   if self.lock.acquire(blocking=False):
    try:self._expire()
    finally:self.lock.release()
 def close(self):
  self.stopped.set()
  with self.lock:
   for key in list(self.streams):self._drop(key)
 def page(self,filters,limit=25,token=''):
  validate(filters,limit,token)
  if not self.lock.acquire(blocking=False):raise PageBusy()
  key=None
  try:
   if self.stopped.is_set():raise PageUnavailable()
   self._expire()
   if token:
    key=next((k for k,s in self.streams.items() if token in (s['next'],s['last'])),None)
    if key is None:raise PageExpired()
    state=self.streams[key]
    if state['filters']!=filters or state['limit']!=limit:raise PageExpired()
    state['used']=self.clock()
    if token==state['last']:return deepcopy(state['reply'])
   else:
    if len(self.streams)>=16:raise PageBusy()
    cursor=None
    try:
     cursor=self.store.find({},{k:1 for k in READ_STORE_FIELDS})
     order={'newest':[('created_at',-1),('_id',-1)],'title':[('title',1),('_id',1)],'country':[('country',1),('_id',1)],'score':[('score',-1),('_id',-1)]}[filters['sort']]
     cursor.sort(order);cursor.batch_size(100);cursor.max_time_ms(2000)
    except Exception:
     if cursor is not None:
      try:cursor.close()
      except Exception:pass
     raise PageUnavailable()from None
    key=secrets.token_urlsafe(32);now=self.clock()
    state={'cursor':cursor,'filters':dict(filters),'limit':limit,'born':now,'used':now,'next':None,'last':None,'reply':None,'offset':0,'eof':False}
    self.streams[key]=state
   items=[];scanned=0;eof=state['eof']
   try:
    while not eof and len(items)<limit and scanned<1000:
     try:raw=next(state['cursor'])
     except StopIteration:eof=True;break
     scanned+=1
     clean=self.sanitize([raw])
     if not clean:continue
     row=normalize_row(clean[0],'geo')
     if row is None:continue
     chosen=selection([row],**filters)['items']
     if chosen:items.append(public_news_row(chosen[0]))
   except BaseException as error:
    self._drop(key)
    if not isinstance(error,Exception):raise
    raise PageUnavailable()from None
   if eof:
    try:state['cursor'].close()
    except Exception:pass
   next_token=None if eof else secrets.token_urlsafe(32)
   reply={'items':items,'scope':'whole_geo_store_cursor','consistency':'mutable_read_not_snapshot','sort_semantics':'raw_mongo_source_fields_with_id_tiebreak','limit':limit,'offset':state['offset'],'next_cursor':next_token,'exhausted':eof,'scanned_this_page':scanned,'total_count':None}
   state.update(next=next_token,last=token or None,reply=deepcopy(reply),eof=eof,offset=state['offset']+len(items),used=self.clock())
   # Retain the final reply briefly for a lost-response retry; cursor is closed.
   if eof and not token:self._drop(key)
   return reply
  finally:self.lock.release()
