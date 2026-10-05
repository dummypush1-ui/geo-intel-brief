"""Separate injected Geo write adapter, never default runtime or read facade.

Developer review is a prerequisite, not owner authorization. Real use still
requires source-grounded user write permission. No URI/client/index creation,
route/environment selection, retry, Telegram, mail or scheduler.
"""
from copy import deepcopy
from datetime import datetime,timezone
from pymongo.errors import BulkWriteError
from integration.fake_collection_writer import plain

FIELDS={'title','url','source','credibility','corroboration','category','summary','telegram_message_id','telegram_url','published','score','risk_level','country'}
class WriterUnavailable(ValueError):pass
class GeoArticleWriter:
 def __init__(self,client,*,review):
  if type(review) is not dict or any(type(k) is not str for k in review) or type(review.get('mapping')) is not tuple or len(review['mapping'])!=2 or any(type(x) is not str for x in review['mapping']) or set(review)!={'mapping','write_permission','unique_url_index_verified','source_contract_verified'} or review.get('mapping')!=('geo_intel','articles') or review.get('write_permission') is not True or review.get('unique_url_index_verified') is not True or review.get('source_contract_verified') is not True:raise WriterUnavailable('Explicit Geo write source review required')
  self._client=client
 def __init_subclass__(cls,**kwargs):raise TypeError('Writer cannot be subclassed')
 def write(self,documents,clock):
  failed=False
  try:
   if type(documents) is not list or len(documents)>1000 or type(clock) is not datetime or type(clock.tzinfo) is not timezone:raise ValueError()
   # Copy exact built-in JSON values first; never validate caller objects then
   # submit a later copy. Concurrent mutation fails closed or validates the
   # actual captured snapshot, not a stale earlier view.
   nodes=[0]
   def snapshot(v,depth=0):
    nodes[0]+=1
    if nodes[0]>100000:raise ValueError()
    if depth>8:raise ValueError()
    if v is None or type(v) in (bool,int,float):return v
    if type(v) is str and len(v)<=10000:return v
    if type(v) is list and len(v)<=1000:return [snapshot(x,depth+1) for x in list(v)]
    if type(v) is dict and len(v)<=100:
     items=list(v.items())
     if any(type(k) is not str or len(k)>100 for k,x in items):raise ValueError()
     return {k:snapshot(x,depth+1) for k,x in items}
    raise ValueError()
   documents=snapshot(documents)
   stamp=clock.astimezone(timezone.utc).isoformat();docs=[];size=0
   import json,math
   for d in documents:
    if type(d) is not dict or set(d)!=FIELDS or not plain(d):raise ValueError()
    if any(type(d[k]) is not str or not d[k].strip() for k in ('title','url','source')):raise ValueError()
    if any(type(d[k]) is not str for k in ('credibility','category','summary','telegram_url','published','risk_level','country')) or len(d['summary'])>300 or d['telegram_message_id'] is not None or d['telegram_url']!='':raise ValueError()
    if d['credibility'] not in ('HIGH','MEDIUM','LOW') or d['risk_level'] not in ('CRITICAL','HIGH','MODERATE','LOW') or d['category'] not in ('GEOPOLITICS','CONFERENCE','TRADE','SANCTIONS','RISK','RESEARCH','GENERAL'):raise ValueError()
    if type(d['corroboration']) is not int or not 1<=d['corroboration']<=1000 or type(d['score']) not in (int,float) or not math.isfinite(d['score']) or not -2**53<=d['score']<=2**53:raise ValueError()
    day=datetime.fromisoformat(d['published'])
    if day.tzinfo is None:raise ValueError()
    size+=len(json.dumps(d,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8'))
    if size>2*1024*1024:raise ValueError()
    doc=deepcopy(d);doc['created_at']=stamp;docs.append(doc)
  except Exception:failed=True
  if failed:raise WriterUnavailable('Geo article batch invalid')
  if not docs:return {'state':'empty','attempted':0,'inserted_count':0,'duplicate_count':0,'failed_count':0,'uncertain_count':0,'retry_safe':True}
  attempted=len(docs);submitted=tuple(docs)
  # No source mapping or driver mutation before entire batch copied/validated.
  try:
   collection=self._client['geo_intel']['articles']
   insert=collection.insert_many
   driver_docs=[deepcopy(d) for d in submitted]
  except Exception:return self._uncertain(attempted)
  try:
   result=insert(driver_docs,ordered=False)
  except BulkWriteError as exc:
   try:return self._bulk_outcome(exc.details,attempted)
   except Exception:return self._uncertain(attempted)
  except Exception:return self._uncertain(attempted)
  # Receipt failures are not write-command errors. Never classify their
  # attached BulkWriteError as confirmed duplicates from insert_many.
  try:
   acknowledged=result.acknowledged
   ids=result.inserted_ids
   if acknowledged is not True or type(ids) is not list or len(ids)!=attempted:raise ValueError()
   return {'state':'inserted','attempted':attempted,'inserted_count':attempted,'duplicate_count':0,'failed_count':0,'uncertain_count':0,'retry_safe':False}
  except Exception:return self._uncertain(attempted)
 @staticmethod
 def _uncertain(n):return {'state':'uncertain','attempted':n,'inserted_count':None,'duplicate_count':None,'failed_count':None,'uncertain_count':n,'retry_safe':False}
 @staticmethod
 def _bulk_outcome(details,n):
  try:
   if type(details) is not dict or any(type(k) is not str for k in details):raise ValueError()
   concern=details.get('writeConcernErrors')
   if type(concern) is not list or len(concern)!=0:raise ValueError()
   errors=details.get('writeErrors');inserted=details.get('nInserted')
   if type(errors) is not list or len(errors)>n:raise ValueError()
   captured=[]
   for e in list(errors):
    if type(e) is not dict or len(e)>100 or any(type(k) is not str for k in e):raise ValueError()
    index=e.get('index');code=e.get('code');pattern=e.get('keyPattern')
    if type(index) is not int or type(code) is not int:raise ValueError()
    copied_pattern=None
    if pattern is not None:
     if type(pattern) is not dict or len(pattern)>100:raise ValueError()
     items=list(pattern.items())
     if any(type(k) is not str or type(v) is not int for k,v in items):raise ValueError()
     copied_pattern=dict(items)
    captured.append({'index':index,'code':code,'keyPattern':copied_pattern})
   errors=captured
   if type(errors) is not list or not 1<=len(errors)<=n or type(inserted) is not int or not 0<=inserted<=n or inserted+len(errors)!=n:raise ValueError()
   indices=set();duplicates=0;failed=0
   for e in errors:
    if type(e) is not dict or any(type(k) is not str for k in e) or type(e.get('index')) is not int or not 0<=e['index']<n or e['index'] in indices or type(e.get('code')) is not int:raise ValueError()
    indices.add(e['index'])
    # Code alone doesn't prove duplicate URL; don't infer a different key.
    if e['code']==11000 and type(e.get('keyPattern')) is dict and all(type(k) is str for k in e['keyPattern']) and set(e['keyPattern'])=={'url'} and type(e['keyPattern']['url']) is int and e['keyPattern']['url']==1:duplicates+=1
    else:failed+=1
   if inserted+duplicates+failed!=n:raise ValueError()
   return {'state':'partial' if failed else 'duplicates','attempted':n,'inserted_count':inserted,'duplicate_count':duplicates,'failed_count':failed,'uncertain_count':0,'retry_safe':False}
  except Exception:return GeoArticleWriter._uncertain(n)
