"""Injected bounded read-only Geo events reader, never constructs a DB client.

Original upcoming_events query semantics: inclusive UTC today..today+days,
ascending event_date. Projection and bounds are added here. Existing verified
DashboardSnapshots applies host/label/URL policy before any display.
"""
from datetime import datetime,date,timezone,timedelta
import json
FIELDS=('name','event_date','source_url','category','confidence','description')
class EventReadUnavailable(Exception):pass
class ReadOnlyEventsReader:
 def __init__(self,collection,clock,*,verified=False,days=90,limit=1000,max_bytes=2*1024*1024):
  if verified is not True or not callable(clock):raise ValueError('Explicit verified event reader and clock required')
  if type(days) is not int or not 0<=days<=366 or type(limit) is not int or not 1<=limit<=1000 or type(max_bytes) is not int or not 1024<=max_bytes<=2*1024*1024:raise ValueError('bounds')
  self.collection=collection;self.clock=clock;self.days=days;self.limit=limit;self.max_bytes=max_bytes
 def __call__(self):
  cursor=None
  try:
   now=self.clock()
   if type(now) is not datetime or type(now.tzinfo) is not timezone:raise ValueError('Fixed aware datetime required')
   now=now.astimezone(timezone.utc);today=now.date();end=today+timedelta(days=self.days)
   # _id explicitly excluded; all other non-contract fields absent at DB boundary.
   projection={k:1 for k in FIELDS};projection['_id']=0
   cursor=self.collection.find({'event_date':{'$gte':today.isoformat(),'$lte':end.isoformat()}},projection)
   cursor.sort('event_date',1)
   cursor.limit(self.limit+1)
   cursor.max_time_ms(2000)
   items=[]
   empty={'observed_at':now.isoformat(),'items':[]}
   size=len(json.dumps(empty,ensure_ascii=False,separators=(',',':')).encode('utf-8'))
   for row in cursor:
    if len(items)>=self.limit:raise ValueError('Input limit exceeded')
    if type(row) is not dict or len(row)>100 or any(type(k) is not str for k in row):raise ValueError('Plain bounded event row')
    item={k:row.get(k,'') for k in FIELDS}
    if any(type(v) is not str or len(v)>16000 for v in item.values()):raise ValueError('Bounded scalar fields')
    size+=len(json.dumps(item,ensure_ascii=False,separators=(',',':')).encode('utf-8'))+(1 if items else 0)
    if size>self.max_bytes:raise ValueError('Byte budget exceeded')
    # Defend against a broken fixture/provider ignoring the date query.
    day=date.fromisoformat(item['event_date'])
    if item['event_date']!=day.isoformat() or not today<=day<=end:raise ValueError('Event outside query')
    if items and item['event_date']<items[-1]['event_date']:raise ValueError('Event order')
    items.append(item)
   return {'observed_at':now.isoformat(),'items':items}
  except Exception:raise EventReadUnavailable('Events snapshot unavailable') from None
  finally:
   if cursor is not None:
    try:cursor.close()
    except Exception:pass
