"""Private supplied supported-schema archive. No routes/writes/source query."""
import json,hashlib,math,base64,re
from datetime import datetime,timezone
from bson import ObjectId
FIELDS={'_id','title','url','source','credibility','corroboration','category','summary','telegram_message_id','telegram_url','published','score','risk_level','country','created_at','emailed'}
SCHEMA='synthetic_supported_geo_storage_fields_v1'
class ArchiveRefused(ValueError):pass

def encode(value,depth=0,budget=None):
 if budget is None:budget=[0]
 budget[0]+=1
 if depth>8 or budget[0]>20000:raise ValueError()
 t=type(value)
 if value is None:return ['null']
 if t is bool:return ['bool',value]
 if t is int and -2**63<=value<2**63:return ['int',str(value)]
 if t is float and math.isfinite(value):return ['float',value.hex()]
 if t is str and len(value)<=1000000 and not any(0xD800<=ord(c)<=0xDFFF for c in value):return ['str',value]
 if t is bytes and len(value)<=1000000:return ['bytes',base64.b64encode(value).decode()]
 if t is ObjectId:return ['oid',str(value)]
 if t is datetime:
  if value.tzinfo is not None and type(value.tzinfo) is not timezone:raise ValueError()
  if value.microsecond%1000:raise ValueError()
  d=value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
  if not 1970<=d.year<=2100:raise ValueError()
  return ['datetime_ms_utc',d.isoformat()]
 if t is list and len(value)<=100:return ['list',[encode(x,depth+1,budget) for x in value]]
 if t is dict and len(value)<=30 and all(type(k) is str and len(k)<=100 for k in value):return ['dict',[[k,encode(v,depth+1,budget)] for k,v in value.items()]]
 raise ValueError()

def decode(value,depth=0,budget=None):
 if budget is None:budget=[0]
 budget[0]+=1
 if depth>8 or budget[0]>20000 or type(value) is not list or not 1<=len(value)<=2 or type(value[0]) is not str:raise ValueError()
 tag=value[0]
 if tag=='null' and len(value)==1:return None
 if len(value)!=2:raise ValueError()
 v=value[1]
 if tag=='bool' and type(v) is bool:return v
 if tag=='int' and type(v) is str and re.fullmatch('-?(0|[1-9][0-9]{0,18})',v):
  n=int(v)
  if -2**63<=n<2**63:return n
 if tag=='float' and type(v) is str and len(v)<=100:
  n=float.fromhex(v)
  if math.isfinite(n) and n.hex()==v:return n
 if tag=='str' and type(v) is str and len(v)<=1000000 and not any(0xD800<=ord(c)<=0xDFFF for c in v):return v
 if tag=='bytes' and type(v) is str and len(v)<=1400000:
  b=base64.b64decode(v,validate=True)
  if len(b)<=1000000 and base64.b64encode(b).decode()==v:return b
 if tag=='oid' and type(v) is str and re.fullmatch('[0-9a-f]{24}',v):return ObjectId(v)
 if tag=='datetime_ms_utc' and type(v) is str:
  d=datetime.fromisoformat(v)
  if d.tzinfo is not None and d.utcoffset().total_seconds()==0 and encode(d)==value:return d
 if tag=='list' and type(v) is list and len(v)<=100:return [decode(x,depth+1,budget) for x in v]
 if tag=='dict' and type(v) is list and len(v)<=30:
  out={}
  for pair in v:
   if type(pair) is not list or len(pair)!=2 or type(pair[0]) is not str or len(pair[0])>100 or pair[0] in out:raise ValueError()
   out[pair[0]]=decode(pair[1],depth+1,budget)
  return out
 raise ValueError()

def canonical(value):return json.dumps(value,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8')
def stamp(value):
 if type(value) is not str or len(value)>40:raise ValueError()
 d=datetime.fromisoformat(value.replace('Z','+00:00'))
 if d.tzinfo is None:raise ValueError()
 d=d.astimezone(timezone.utc)
 if not 1970<=d.year<=2100:raise ValueError()
 return d.isoformat()

def capture(rows):
 if type(rows) is not list or len(rows)>100:raise ValueError()
 records=[];identities=[];seen={};coverage=set();total=0;nodes=[0]
 for row in rows:
  if type(row) is not dict or len(row)>len(FIELDS) or any(type(k) is not str or k not in FIELDS for k in row) or '_id' not in row or type(row['_id']) not in (ObjectId,str):raise ValueError()
  for k,v in row.items():
   if k=='_id':
    if type(v) not in (ObjectId,str) or type(v) is str and not 1<=len(v)<=100:raise ValueError()
   elif k in ('score','corroboration'):
    if type(v) not in (int,float) or not math.isfinite(v) or not -2**53<=v<=2**53 or k=='corroboration' and type(v) is not int:raise ValueError()
   elif k=='emailed':
    if type(v) is not bool:raise ValueError()
   elif k=='telegram_message_id':
    if v is not None and (type(v) is not int or not -2**63<=v<2**63):raise ValueError()
   elif type(v) is not str or len(v)>1000000:raise ValueError()
   # Incremental conservative JSON/tag/identity envelope accounting.
   # No large UTF-8 temporary and no tagged copy before this check.
   total+=len(k)+192
   if total>2*1024*1024-4096:raise ValueError()
   if type(v) is str:
    for char in v:
     code=ord(char)
     if 0xD800<=code<=0xDFFF:raise ValueError()
     total+=max(6,1 if code<128 else 2 if code<2048 else 3 if code<65536 else 4)
     if total>2*1024*1024-4096:raise ValueError()
  typed=encode(row,budget=nodes);copy=decode(typed);identity=encode(copy['_id'])
  marker=canonical(identity)
  if marker in seen and seen[marker]!=canonical(typed):raise ValueError()
  seen[marker]=canonical(typed);identities.append(identity);records.append(typed);coverage.update(row)
 return records,identities,sorted(coverage)

def pack(rows,*,created_at,scope='supplied_subset'):
 failed=False;result=None
 try:
  if scope not in ('supplied_subset','supplied_truncated_subset') or type(scope) is not str:raise ValueError()
  records,identities,coverage=capture(rows)
  body={'version':1,'schema':SCHEMA,'created_at':stamp(created_at),'scope':scope,'count':len(records),'manifest':{'identities':identities,'supported_fields':coverage},'records':records}
  raw=canonical(body)
  if len(raw)>2*1024*1024:raise ValueError()
  result=canonical({'body':body,'sha256':hashlib.sha256(raw).hexdigest()})
  if len(result)>2*1024*1024:raise ValueError()
 except (ValueError,TypeError,OverflowError,RecursionError):failed=True
 if failed:raise ArchiveRefused('Supplied archive refused')
 return result

def unpack(data):
 failed=False;out=None
 try:
  if type(data) is not bytes or len(data)>2*1024*1024:raise ValueError()
  def pairs(items):
   d={}
   for k,v in items:
    if k in d:raise ValueError()
    d[k]=v
   return d
  obj=json.loads(data.decode('utf-8'),object_pairs_hook=pairs,parse_constant=lambda v:(_ for _ in ()).throw(ValueError()))
  if type(obj) is not dict or set(obj)!={'body','sha256'} or type(obj['sha256']) is not str or not re.fullmatch('[0-9a-f]{64}',obj['sha256']):raise ValueError()
  b=obj['body']
  if type(b) is not dict or set(b)!={'version','schema','created_at','scope','count','manifest','records'} or type(b['version']) is not int or b['version']!=1 or b['schema']!=SCHEMA or type(b['count']) is not int or not 0<=b['count']<=100 or type(b['records']) is not list or len(b['records'])!=b['count'] or type(b['manifest']) is not dict or set(b['manifest'])!={'identities','supported_fields'} or stamp(b['created_at'])!=b['created_at'] or b['scope'] not in ('supplied_subset','supplied_truncated_subset'):raise ValueError()
  if hashlib.sha256(canonical(b)).hexdigest()!=obj['sha256']:raise ValueError()
  rows=[decode(r) for r in b['records']];records,identities,coverage=capture(rows)
  if records!=b['records'] or b['manifest']!={'identities':identities,'supported_fields':coverage}:raise ValueError()
  out={'rows':rows,'receipt':{'scope':b['scope'],'schema':SCHEMA,'count':b['count'],'supported_fields':coverage,'integrity':'sha256_not_authentication','source_completeness':False,'durable_backup':False}}
 except (ValueError,TypeError,OverflowError,RecursionError,UnicodeError):failed=True
 if failed:raise ArchiveRefused('Supplied archive refused')
 return out

def retrieve(data,identity):
 failed=False;out=None
 try:
  if type(identity) not in (ObjectId,str):raise ValueError()
  target=encode(identity);archive=unpack(data);rows=[r for r in archive['rows'] if encode(r['_id'])==target]
  if len(rows)!=1:raise ValueError()
  out={'record':rows[0],'receipt':archive['receipt']}
 except (ValueError,TypeError,OverflowError):failed=True
 if failed:raise ArchiveRefused('Supplied archive retrieval refused')
 return out
