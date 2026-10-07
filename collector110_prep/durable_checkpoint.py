"""Inactive injected immutable checkpoint adapter. No Mongo client/index creation.
BSON projection replaces only exact datetime leaves with UTC-offset ISO strings
plus an independent typed digest. Application must use this adapter consistently;
this is not article-write fencing, lease recovery or production activation.
"""
from datetime import datetime
from collector109_prep.checkpoint import digest,run_inputs
if __package__:
 from .input_budget import capture,InputRefused
else:
 from input_budget import capture,InputRefused
class DurableCheckpointRefused(ValueError):pass

def _encode(v):
 t=type(v)
 if t is datetime:return ['date',v.isoformat(),v.fold]
 if t is dict:return ['dict',[[k,_encode(x)]for k,x in sorted(v.items())]]
 if t is list:return ['list',[_encode(x)for x in v]]
 if v is None:return ['null']
 if t is bool:return ['bool',v]
 if t is int:return ['int',str(v)]
 if t is float:return ['float',v]
 if t is str:return ['str',v]
 raise DurableCheckpointRefused('Unsupported encoding')

def _decode(v,depth=0):
 if depth>10 or type(v)is not list or not v or type(v[0])is not str:raise DurableCheckpointRefused('Invalid encoded shape')
 tag=v[0]
 if tag=='null' and len(v)==1:return None
 if tag=='int' and len(v)==2:
  raw=v[1]
  if type(raw)is not str or not 1<=len(raw)<=20:raise DurableCheckpointRefused('Integer encoding')
  try:n=int(raw)
  except ValueError:raise DurableCheckpointRefused('Integer encoding')from None
  if str(n)!=raw or not -(2**63)<=n<=2**63-1:raise DurableCheckpointRefused('Signed int64 encoding')
  return n
 if len(v)==2 and tag in ('bool','float','str'):
  if type(v[1])is not {'bool':bool,'int':int,'float':float,'str':str}[tag]:raise DurableCheckpointRefused('Encoded scalar type')
  return v[1]
 if tag=='date' and len(v)==3 and type(v[1])is str and type(v[2])is int and v[2]in (0,1):return datetime.fromisoformat(v[1]).replace(fold=v[2])
 if tag=='list' and len(v)==2 and type(v[1])is list:return [_decode(x,depth+1)for x in v[1]]
 if tag=='dict' and len(v)==2 and type(v[1])is list:
  out={}
  for pair in v[1]:
   if type(pair)is not list or len(pair)!=2 or type(pair[0])is not str or pair[0]in out:raise DurableCheckpointRefused('Encoded key invalid')
   out[pair[0]]=_decode(pair[1],depth+1)
  return out
 raise DurableCheckpointRefused('Invalid tag')

class DurableCheckpoints:
 def __init__(self,collection):
  # Validate configured concerns without changing a user's collection/client.
  try:
   wc=collection.write_concern.document;rc=collection.read_concern.document
   if type(wc)is not dict or wc.get('w')!='majority' or wc.get('j')is not True or type(wc.get('wtimeout'))is not int or not 1<=wc['wtimeout']<=30000 or type(rc)is not dict or rc.get('level')!='majority':raise ValueError()
  except Exception:raise DurableCheckpointRefused('Majority+journal/read concern required')from None
  self.c=collection
 def put(self,key,fence,inputs):
  if type(key)is not str or len(key)!=64 or any(x not in '0123456789abcdef'for x in key) or type(fence)is not int or fence<1:raise DurableCheckpointRefused('Exact identity required')
  try:
   b=capture(inputs)['captured']
   if type(b)is not dict or set(b)!={'candidates','active_categories','threshold'}:raise ValueError()
   b=run_inputs(b['candidates'],b['active_categories'],b['threshold']);h=digest(key,fence,b)
   row={'_id':key,'fence':str(fence),'hash':h,'version':1,'inputs':_encode(b)}
   # Existing identity is not overwritten. A concurrent winner is read back.
   result=self.c.update_one({'_id':key},{'$setOnInsert':row},upsert=True)
   if result.acknowledged is not True:raise ValueError()
   saved=self.get(key,fence)
   if digest(key,fence,saved)!=h:raise ValueError()
   return h
  except Exception:raise DurableCheckpointRefused('Checkpoint write unverifiable; do not drive')from None
 def get(self,key,fence):
  if type(key)is not str or len(key)!=64 or any(x not in '0123456789abcdef'for x in key) or type(fence)is not int or fence<1:raise DurableCheckpointRefused('Exact identity required')
  try:
   row=self.c.find_one({'_id':key})
   if type(row)is not dict or set(row)!={'_id','fence','hash','version','inputs'} or row['_id']!=key or type(row['fence'])is not str or row['fence']!=str(fence) or type(row['version'])is not int or row['version']!=1 or type(row['hash'])is not str:raise ValueError()
   # Bound encoded data BEFORE recursive decode; encoding doubles depth.
   # A separate encoded-specific budget is necessary, implemented below.
   _encoded_budget(row['inputs'])
   b=capture(_decode(row['inputs']))['captured']
   if type(b)is not dict or set(b)!={'candidates','active_categories','threshold'}:raise ValueError()
   run_inputs(b['candidates'],b['active_categories'],b['threshold'])
   if digest(key,fence,b)!=row['hash']:raise ValueError()
   return b
  except Exception:raise DurableCheckpointRefused('Checkpoint read unverifiable')from None

def _encoded_budget(v):
 nodes=0;size=0
 def walk(x,d):
  nonlocal nodes,size
  nodes+=1;size+=16
  if nodes>100000 or d>24 or size>8*1024*1024:raise ValueError()
  if type(x)is list:
   if len(x)>1000:raise ValueError()
   for y in x:walk(y,d+1)
  elif type(x)is str:
   if len(x)>10000:raise ValueError()
   size+=len(x.encode('utf-8'))
  elif x is not None and type(x)not in (bool,int,float):raise ValueError()
 walk(v,0)
 if size>8*1024*1024:raise ValueError()
