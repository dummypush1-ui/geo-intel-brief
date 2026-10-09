"""Bounded source reads using an injected collection, no client or provisioning."""
import time
MAX_ROWS=2000
PAGE_ROWS=250
MAX_BYTES=16*1024*1024
MAX_SECONDS=30
MAX_TIME_MS=3000
EXPORT_FIELDS=('title','source','category','risk_level','score','credibility','country','corroboration','published','created_at','url','summary')
def bounded_limit(value,maximum=MAX_ROWS):
 if type(value) is not int or not 1<=value<=maximum:raise ValueError('Read limit outside reviewed bound')
 return value
def cursor_rows(cursor,limit,require_complete=False):
 bounded_limit(limit)
 cursor=cursor.limit(limit+1 if require_complete else limit).max_time_ms(MAX_TIME_MS).batch_size(min(limit,PAGE_ROWS))
 rows=[]
 try:
  for row in cursor:
   if len(rows)>=limit:raise ValueError("Cursor exceeded read bound")
   rows.append(row)
  return rows
 finally:cursor.close()
def article_pages(collection,category=None,max_rows=MAX_ROWS,clock=time.monotonic):
 """Stable _id keyset traversal with frozen lower ID, not a DB snapshot.
 Concurrent updates/deletes can alter results. Not a complete recovery backup.
 Exhaustion or any cap raises rather than presenting truncated success.
 """
 bounded_limit(max_rows)
 if category is not None and (type(category) is not str or not 1<=len(category)<=60 or any(ord(c)<32 for c in category)):raise ValueError('Invalid category')
 base={} if category is None else ({'$or':[{'category':'GENERAL'},{'category':None},{'category':{'$exists':False}}]} if category=='GENERAL' else {'category':category})
 top=collection.find(base,{'_id':1}).sort([('_id',1)]).limit(1).max_time_ms(MAX_TIME_MS)
 try:upper=next(iter(top),None)
 finally:top.close()
 if upper is None:return
 if '_id' not in upper:raise ValueError('Missing export boundary ID')
 start=clock();last=None;count=0;size=0
 while True:
  if clock()-start>MAX_SECONDS:raise TimeoutError('Export wall limit')
  query=dict(base);query['_id']={'$gte':upper['_id']}
  if last is not None:query['_id']['$lt']=last
  cur=collection.find(query,{k:1 for k in ('_id',)+EXPORT_FIELDS}).sort([('_id',-1)]).limit(PAGE_ROWS).max_time_ms(MAX_TIME_MS).batch_size(PAGE_ROWS)
  rows=[]
  try:
   for row in cur:
    if clock()-start>MAX_SECONDS:raise TimeoutError('Export wall limit')
    if type(row) is not dict or '_id' not in row:raise ValueError('Invalid export record')
    ident=row['_id']
    if (last is not None and ident>=last) or ident<upper['_id']:raise ValueError('Unstable export order')
    last=ident;count+=1
    if count>max_rows:raise ValueError('Export row limit; use a reviewed narrower selection')
    clean={k:row.get(k) for k in EXPORT_FIELDS}
    # Representation is bounded per cell before encoding, never serialize unknown fields.
    for k,v in clean.items():
     if v is not None and not isinstance(v,(str,int,float,bool)):raise ValueError('Unsupported export field')
     if isinstance(v,str) and len(v)>8000:raise ValueError('Export cell limit')
    size+=sum(len(str(v).encode('utf-8',errors='replace')) for v in clean.values())
    if size>MAX_BYTES:raise ValueError('Export byte limit')
    rows.append(clean)
  finally:cur.close()
  if not rows:return
  yield rows
