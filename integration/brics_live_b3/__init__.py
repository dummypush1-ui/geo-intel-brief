"""Reviewed separate BRICS read-only source bridge. All activation gates OFF.
Proof references are operator evidence to verify, not self-authenticating grants.
"""
import hashlib,json,re,sqlite3,threading,time
from dataclasses import dataclass
from datetime import datetime,timezone,timedelta
from pathlib import Path
from copy import deepcopy
from flask import Response,request
from integration.brics_news_boundary import project,FIELDS
from integration.geo_read_factory import ReadClient
ROOT=Path(__file__).resolve().parents[2]
FLAG='PUBLIC_BRICS_LIVE_READ_ENABLED';MAX_ROWS=100;MAX_BYTES=250000
PINS={'integration/brics_news_boundary.py': 'c206b85a9896b908a4fe0543417f86a6ebea4e14b99eb2d078e66da98a2ec700', 'integration/geo_read_factory.py': '8cd150bfa168e0d831afe77e542f6422372ff923eb7ad8fc44a730f3e804a0da', 'integration/brics_live_b3/page.html': '2066e6e92d98cfbe9cba4ac75e55bd22791c66c3c6dcd1251e39eb0de3dc3fe0', 'integration/brics_live_b3/page.js': '08c70d9df607315088d432c00aa96d531cd7a135a39e23d26d4ff91573f607ee'}
class Held(ValueError):pass
@dataclass(frozen=True)
class Review:
 identity:tuple
 mapping_ref:str
 disclosure_ref:str
 readonly_ref:str
 def validate(self):
  if type(self.identity)is not tuple or not self.identity or any(type(v)is not str or not v or len(v)>4096 for v in self.identity):raise Held('Separate source identity required')
  if any(type(v)is not str or not v.strip()or len(v)>512 for v in (self.mapping_ref,self.disclosure_ref,self.readonly_ref)):raise Held('Operator review evidence references required')

class SQLiteReader:
 def __init__(self,path):
  self.path=Path(path).absolute();self.identity=('sqlite',str(self.path));self.closed=False
 def read(self):
  if self.closed or self.path.is_symlink()or not self.path.is_file():raise Held('Read-only BRICS file unavailable')
  # mode=ro never creates a missing file; immutable is deliberately NOT used,
  # because the original collector uses WAL. No schema/index/WAL pragma writes.
  try:
   conn=sqlite3.connect(self.path.as_uri()+'?mode=ro',uri=True,timeout=1)
   try:
    conn.execute('PRAGMA query_only=ON');deadline=time.monotonic()+2
    conn.set_progress_handler(lambda:int(time.monotonic()>deadline),1000)
    columns='title,url,source,country,category,summary,published,collected_at'
    cursor=conn.execute('SELECT '+columns+' FROM articles ORDER BY collected_at DESC,id DESC LIMIT 101')
    try:rows=cursor.fetchmany(101)
    finally:cursor.close()
    if len(rows)>MAX_ROWS:rows=rows[:MAX_ROWS]
    return [dict(zip(columns.split(','),row))for row in rows]
   finally:conn.close()
  except Exception:raise Held('Read-only BRICS query unavailable')from None
 def close(self):self.closed=True

class MongoReader:
 def __init__(self,client,*,deployment,database,collection='articles'):
  if type(client)is not ReadClient or type(deployment)is not str or not re.fullmatch('[a-zA-Z0-9_-]{1,80}',deployment)or type(database)is not str or not re.fullmatch('[a-zA-Z0-9_-]{1,80}',database)or database=='geo_intel'or collection!='articles':raise Held('Separate reviewed BRICS Mongo mapping required')
  self.client=client;self.database=database;self.collection=collection;self.identity=('mongo',deployment,database,collection);self.closed=False
 def read(self):
  if self.closed:raise Held('BRICS reader closed')
  cursor=None
  try:
   projection={k:1 for k in FIELDS};projection['_id']=0
   cursor=self.client[self.database][self.collection].find({},projection).sort([('collected_at',-1),('id',-1)]).limit(100).batch_size(100).max_time_ms(2000)
   rows=[]
   for row in cursor:
    if len(rows)>=100:raise Held('BRICS cursor overflow')
    rows.append(row)
   return rows
  except Exception:raise Held('Read-only BRICS query unavailable')from None
  finally:
   if cursor is not None:
    try:cursor.close()
    except Exception:pass
 def close(self):
  if not self.closed:self.closed=True;self.client.close()

@dataclass(frozen=True)
class Binding:
 reader:object
 review:Review
 critical_keywords:tuple
 def validate(self):
  if type(self.reader)not in (SQLiteReader,MongoReader)or type(self.review)is not Review:raise Held('Exact separate BRICS binding required')
  self.review.validate()
  if self.reader.identity!=self.review.identity or self.reader.closed:raise Held('BRICS source identity changed')
  if type(self.critical_keywords)is not tuple or not 1<=len(self.critical_keywords)<=30 or any(type(k)is not str or not k.strip()or len(k)>80 for k in self.critical_keywords):raise Held('Reviewed BRICS critical keywords required')

def prepare(env,binding=None):
 if type(env)is not dict or any(type(k)is not str or type(v)is not str for k,v in env.items()):raise Held('Plain environment strings required')
 value=env.get(FLAG,'false')
 if value not in ('true','false'):raise Held('Exact BRICS live flag required')
 if value=='false':
  if binding is not None:raise Held('Binding supplied while BRICS live gate off')
  return None
 gates=('PREVIEW_PUBLIC_SAMPLE_ENABLED','PUBLIC_NEWS_READ_ENABLED','PUBLIC_BRICS_NEWS_ENABLED','BRICS_STORE_MAPPING_VERIFIED','BRICS_PUBLIC_DISCLOSURE_VERIFIED','BRICS_READONLY_CREDENTIAL_VERIFIED')
 if any(env.get(k)!='true'for k in gates)or type(binding)is not Binding:raise Held('Reviewed separate BRICS source and disclosure gates required')
 binding.validate()
 if any(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=h for n,h in PINS.items()):raise Held('BRICS live source pins changed')
 return binding

class Service:
 def __init__(self,binding,clock=time.monotonic,now=lambda:datetime.now(timezone.utc)):
  binding.validate();self.binding=binding;self.clock=clock;self.now=now;self.lock=threading.Lock();self.cached=None;self.skipped=0;self.until=0;self.failed=False;self.closed=False
 def close(self):
  if not self.closed:self.closed=True;self.cached=None;self.binding.reader.close()
 def run(self):
  if not self.lock.acquire(timeout=1):return {'state':'unavailable','message':'Separate BRICS source unavailable. No Geo fallback.'},503
  try:
   if self.closed or self.failed:raise Held('BRICS source closed or failed')
   self.binding.validate()
   if self.cached is None or self.clock()>=self.until:
    rows=self.binding.reader.read()
    if type(rows)is not list or len(rows)>MAX_ROWS:raise Held('BRICS read cap')
    items=[];skipped=0
    for row in rows:
     try:
      if type(row)is not dict:raise Held('Plain BRICS row required')
      items.append(project(dict(row,**{'published':None}if row.get('published')==''else{}),self.binding.critical_keywords))
     except (ValueError,TypeError,UnicodeError,OverflowError):skipped+=1
    self.skipped=skipped
    # Legacy empty publication strings mean unknown, not recent publication.
    self.cached=[r for r in items if r['brics_relevant']];self.until=self.clock()+60
   items=deepcopy(self.cached);now=self.now()
   if type(now)is not datetime or now.tzinfo is None:raise Held('UTC source clock required')
   critical=[];unknown=0
   for row in items:
    if row['critical_keyword_match']:
     if row['collected_at']is None:unknown+=1;continue
     age=now.astimezone(timezone.utc)-datetime.fromisoformat(row['collected_at'].replace('Z','+00:00'))
     if timedelta(0)<=age<timedelta(hours=24):critical.append(row['article_key'])
   result={'state':'reviewed_brics_read','message':'Separate read-only BRICS source; latest up to100 stored rows, not whole-store totals.','scope':'latest100_then_brics_filter_not_full_store','skipped_rows':self.skipped,'items':items,'critical_24h_keys':critical,'critical_time_unknown_count':unknown,'source_freshness':'stored dates only; upstream collection not verified','date_policy':'collected_at naive means UTC; published requires explicit timezone; unknown corroboration is not cleared'}
   if len(json.dumps(result,ensure_ascii=True,separators=(',',':')).encode())>MAX_BYTES:raise Held('BRICS response cap')
   return result,200
  except Exception:
   self.failed=True;self.cached=None
   try:self.binding.reader.close()
   except Exception:pass
   return {'state':'unavailable','message':'Separate BRICS source unavailable. No Geo fallback.'},503
  finally:self.lock.release()

def install(app,binding):
 from integration import public_brics_news as base
 if not base.mounted(app)or 'brics_live_b3'in app.extensions:raise Held('Existing BRICS boundary mount required')
 service=Service(binding)
 def listing():
  if request.method=='HEAD':return Response('',mimetype='application/json')
  result,status=service.run();return Response(json.dumps(result,ensure_ascii=True,separators=(',',':')),status=status,mimetype='application/json')
 def shell():return Response(''if request.method=='HEAD'else(ROOT/'integration/brics_live_b3/page.html').read_text(),mimetype='text/html')
 def asset():return Response(''if request.method=='HEAD'else(ROOT/'integration/brics_live_b3/page.js').read_text(),mimetype='application/javascript')
 app.view_functions['public_brics_news_get']=listing;app.view_functions['public_brics_news_page']=shell;app.view_functions['public_brics_news_asset']=asset
 app.extensions.update(brics_live_b3=service,brics_live_close=service.close,public_brics_news_view=shell)
 import atexit
 atexit.register(service.close)
