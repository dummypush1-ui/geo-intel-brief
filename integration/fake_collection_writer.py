"""In-memory writer contract exercise, not a MongoDB adapter or runtime path.

Separate project maps model separate prospective collections in one database.
Collection names, ownership and indexes are deliberately not chosen here. No
client, callback, disk, migration, index, scheduler or delivery operations.
Geo identity is exact supplied URL; BRICS identity is sha256 of that exact URL.
Supplied zoned clock produces UTC created_at/collected_at; the latter intentionally
replaces original naive UTC with an explicit zone. Duplicate rows are not updated.
Unknown/provider fields, including _id/id/emailed/time overrides, are stripped.
Outcome failures are synthetic fixtures, never interpreted as duplicate storage.
"""
from copy import deepcopy
from datetime import datetime,timezone
from hashlib import sha256
import math

FIELDS={'geo':('title','url','source','summary','country','category','score','risk_level','credibility','corroboration','published'), 'brics':('title','url','source','summary','country','category','published','corroborated_by')}

def plain(value,depth=0):
 if depth>8:return False
 if value is None or type(value) is bool:return True
 if type(value) in (int,float):return not isinstance(value,float) or math.isfinite(value)
 if type(value) is str:return len(value)<=10000
 if type(value) is list:return len(value)<=1000 and all(plain(v,depth+1) for v in value)
 if type(value) is dict:return len(value)<=100 and all(type(k) is str and len(k)<=100 and plain(v,depth+1) for k,v in value.items())
 return False

class FakeCollectionWriter:
 __slots__=('_geo','_brics')
 def __init__(self):self._geo={};self._brics={}
 def snapshot(self,project):
  if project not in FIELDS:raise ValueError('Exact project required')
  return deepcopy(self._geo if project=='geo' else self._brics)
 def write(self,project,rows,clock,failed_urls=()):
  if project not in FIELDS or type(rows) is not list or len(rows)>1000 or not plain(rows):raise ValueError('Bounded plain JSON rows required')
  if type(clock) is not str:raise ValueError('Explicit zoned clock required')
  try:
   now=datetime.fromisoformat(clock.replace('Z','+00:00'))
   if now.tzinfo is None:raise ValueError()
   stamp=now.astimezone(timezone.utc).isoformat()
  except (ValueError,OverflowError):raise ValueError('Explicit zoned clock required') from None
  if type(failed_urls) not in (list,tuple) or len(failed_urls)>1000 or any(type(u) is not str or len(u)>10000 for u in failed_urls):raise ValueError('Explicit synthetic failure URLs required')
  # Validate the entire batch before changing even the fake store.
  for row in rows:
   if type(row) is not dict or any(type(row.get(k)) is not str or not row[k].strip() for k in ('title','url','source')):raise ValueError('Required candidate strings missing')
  store=self._geo if project=='geo' else self._brics;out=[]
  for row in rows:
   url=row['url'];identity=url if project=='geo' else sha256(url.encode()).hexdigest()
   if url in failed_urls:state='failed'
   elif identity in store:state='duplicate'
   else:
    doc={k:deepcopy(row[k]) for k in FIELDS[project] if k in row}
    doc['emailed']=False
    if project=='geo':doc['created_at']=stamp
    else:doc.update(id=identity,collected_at=stamp)
    store[identity]=doc;state='inserted'
   out.append({'identity':identity,'state':state})
  return {'project':project,'state':'fake_store_only','inserted_count':sum(r['state']=='inserted' for r in out),'duplicate_count':sum(r['state']=='duplicate' for r in out),'failed_count':sum(r['state']=='failed' for r in out),'results':out,'live_writes':False,'delivery':False}
