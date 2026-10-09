"""Unselected read-only supplied collector snapshot. No DB client/file writes.
Does not free history capacity or authorize live reads, purge or reconciliation.
"""
import copy,json,hashlib,math
from collector108_prep.durable_ledger import DurableLedger,_valid_document
from collector110_prep.durable_checkpoint import DurableCheckpoints,_encoded_budget
from integration.collector197_coverage import CoverageCheckpoints
from integration.collector197_orchestrator import _concerns
class ArchiveRefused(ValueError):pass
MAX_BYTES=16*1024*1024
SCHEMA='collector197-complete-retained-snapshot-v1'

def _raw(value):return json.dumps(value,ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def _bounded(value):
 # Count before JSON/deepcopy; exact plain JSON types only, cycles refused.
 nodes=0;size=0;ancestors=set()
 def walk(v,depth):
  nonlocal nodes,size
  nodes+=1;size+=32
  if nodes>2000000 or depth>32 or size>MAX_BYTES:raise ValueError()
  t=type(v)
  if t is str:
   if len(v)>10000:raise ValueError()
   size+=len(v.encode('utf-8'))*6
  elif t is int:
   if not -(2**63)<=v<=2**63-1:raise ValueError()
  elif t is float:
   if not math.isfinite(v):raise ValueError()
  elif t is bool or v is None:pass
  elif t in (dict,list):
   if len(v)>1000 or id(v)in ancestors:raise ValueError()
   ancestors.add(id(v))
   if t is dict:
    for k,x in v.items():
     if type(k)is not str:raise ValueError()
     walk(k,depth+1);walk(x,depth+1)
   else:
    for x in v:walk(x,depth+1)
   ancestors.remove(id(v))
  else:raise ValueError()
  if size>MAX_BYTES:raise ValueError()
 walk(value,0)
 if len(_raw(value))>MAX_BYTES:raise ValueError()

class _CheckpointRead:
 def __init__(self,row):
  self.row=row
  class Concern:
   def __init__(self,d):self.document=d
  self.write_concern=Concern({'w':'majority','j':True,'wtimeout':5000});self.read_concern=Concern({'level':'majority'})
 def find_one(self,query):return copy.deepcopy(self.row)

def _validate(body):
 if type(body)is not dict or set(body)!={'schema','profile','fingerprint','ledger','checkpoints','scope'}or body['schema']!=SCHEMA or body['scope']!='all_retained_jobs_not_lifetime_history':raise ValueError()
 d=body['ledger'];_valid_document(d,body['profile'],body['fingerprint'])
 if body['profile']!='geo108' or type(body['fingerprint'])is not str or len(body['fingerprint'])!=64 or any(c not in '0123456789abcdef'for c in body['fingerprint']):raise ValueError()
 jobs=([d['active']]if d['active']is not None else[])+d['history'];cp=body['checkpoints']
 if type(cp)is not list or len(cp)!=len(jobs):raise ValueError()
 for j,r in zip(jobs,cp):
  if type(r)is not dict or set(r)!={'job','fence','record'}or r['job']!=j['key']or type(r['fence'])is not int or r['fence']!=j['fence']:raise ValueError()
  record=r['record']
  if record is None:
   if j['phase']not in ('accepted','running','failed_before_write'):raise ValueError()
  else:
   if type(record)is not dict:raise ValueError()
   version=record.get('version');adapter=DurableCheckpoints if type(version)is int and version==1 else CoverageCheckpoints if type(version)is int and version==2 else None
   if adapter is None:raise ValueError()
   # Bound raw encoded projections before adapter recursive decoding.
   _encoded_budget(record.get('inputs'))
   if version==2:_encoded_budget(record.get('coverage'))
   adapter(_CheckpointRead(record)).get(j['key'],j['fence'])
 return body

def pack(ledger_document,checkpoint_rows,*,profile,fingerprint):
 try:
  body={'schema':SCHEMA,'profile':profile,'fingerprint':fingerprint,'scope':'all_retained_jobs_not_lifetime_history','ledger':ledger_document,'checkpoints':checkpoint_rows}
  _bounded(body);_validate(body);raw=_raw(body)
  envelope=_raw({'body':body,'sha256':hashlib.sha256(raw).hexdigest()})
  if len(envelope)>MAX_BYTES:raise ValueError()
  unpack(envelope) # validate actual output/readback before returning bytes
  return envelope
 except Exception:raise ArchiveRefused('Complete collector snapshot refused; no capacity released')from None

def unpack(blob):
 try:
  if type(blob)is not bytes or not 0<len(blob)<=MAX_BYTES:raise ValueError()
  def pairs(items):
   out={}
   for k,v in items:
    if k in out:raise ValueError()
    out[k]=v
   return out
  e=json.loads(blob,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError()))
  if type(e)is not dict or set(e)!={'body','sha256'}or type(e['sha256'])is not str:raise ValueError()
  _bounded(e['body'])
  if hashlib.sha256(_raw(e['body'])).hexdigest()!=e['sha256']:raise ValueError()
  _validate(e['body']);return copy.deepcopy(e['body'])
 except Exception:raise ArchiveRefused('Collector snapshot readback refused')from None

def capture(ledger,checkpoints):
 """Source-injected bounded reads only. Two matching ledger reads detect races,
 not a transactional snapshot or proof of owner quiescence. Checkpoints immutable.
 """
 try:
  if type(ledger)is not DurableLedger or type(checkpoints)not in (DurableCheckpoints,CoverageCheckpoints):raise ValueError()
  _concerns(ledger.c);_concerns(checkpoints.c)
  before=ledger.c.find_one({'_id':ledger.profile},max_time_ms=2000);_bounded(before);_valid_document(before,ledger.profile,ledger.fp)
  jobs=([before['active']]if before['active']is not None else[])+before['history'];rows=[];total=0
  for j in jobs:
   record=checkpoints.c.find_one({'_id':j['key']},max_time_ms=2000)
   _bounded(record);total+=len(_raw(record))
   if total>MAX_BYTES:raise ValueError()
   rows.append({'job':j['key'],'fence':j['fence'],'record':record})
  after=ledger.c.find_one({'_id':ledger.profile},max_time_ms=2000);_bounded(after)
  if before!=after:raise ValueError()
  return pack(before,rows,profile=ledger.profile,fingerprint=ledger.fp)
 except Exception:raise ArchiveRefused('Read-only collector snapshot unavailable; no mutations/retry')from None

def status(blob,key):
 body=unpack(blob)
 if type(key)is not str or len(key)!=64 or any(c not in '0123456789abcdef'for c in key):raise ArchiveRefused('Exact retained job key required')
 d=body['ledger'];jobs=([d['active']]if d['active']is not None else[])+d['history']
 for j,r in zip(jobs,body['checkpoints']):
  if j['key']==key:return {'job':key,'fence':j['fence'],'phase':j['phase'],'counts':copy.deepcopy(j['counts']),'checkpoint_present':r['record']is not None,'classification':'terminal_recorded_not_delivery_proof'if j['phase']in ('completed','failed_before_write')else'held_owner_review_required','capacity_released':False,'snapshot_only':True}
 raise ArchiveRefused('Job not retained in snapshot; not proof it never existed')
