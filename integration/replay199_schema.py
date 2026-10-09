"""New unselected schemas only. No migration/provisioning or capacity release."""
import hashlib,json,copy
from bson import BSON
from collector108_prep.durable_ledger import _valid_document
from integration.finder198_receipts import _v2
from integration.collector197_archive import _bounded,pack as checkpoint_pack
class ReplayRefused(ValueError):pass
LIMIT_BYTES=8*1024*1024
MAX_EPOCHS=1024
MAX_RECORDS=4096
FAMILIES={'collector':('collector_jobs197','collector_replay199','geo108',2),'broker':('finder_budget198','finder_replay199','shared-finder-v1',3)}
EXTRA={'archive_epoch','archived_count','chain_head'}

def canonical(value):return json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8')
def digest(value):return hashlib.sha256(canonical(value)).hexdigest()
def ishash(v):return type(v)is str and len(v)==64 and all(c in '0123456789abcdef'for c in v)
def bounded(v):
 _bounded(v)
 if len(BSON.encode(v))>LIMIT_BYTES:raise ReplayRefused('Archive workload byte cap')
 return v

def source(family,d,fingerprint=None):
 try:
  if family not in FAMILIES or type(d)is not dict:raise ValueError()
  bounded(d);base={k:v for k,v in d.items()if k not in EXTRA|({'schema'}if family=='collector'else set())}
  if family=='collector':
   if type(d.get('schema'))is not int or d['schema']!=2 or not ishash(fingerprint):raise ValueError()
   _valid_document(base,'geo108',fingerprint)
  else:
   if type(d.get('schema'))is not int or d['schema']!=3:raise ValueError()
   base['schema']=2;_v2(base)
  if set(d)!=(set(base)|EXTRA|{'schema'}):raise ValueError()
  if any(type(d[k])is not int or d[k]<0 for k in ('archive_epoch','archived_count'))or d['archive_epoch']>MAX_EPOCHS or d['archived_count']>MAX_RECORDS or not ishash(d['chain_head']):raise ValueError()
  if (d['archive_epoch']==0)!=(d['archived_count']==0)or not d['archive_epoch']<=d['archived_count']<=d['fence'] or not 0<=d['revision']<2**53:raise ValueError()
  rows=d['history']if family=='collector'else d['receipts']
  if [r['fence']for r in rows]!=sorted(r['fence']for r in rows):raise ValueError()
  return d
 except Exception:raise ReplayRefused('Exact new source schema required')from None

def manifest(family,epoch,previous,records):
 if family not in FAMILIES or type(epoch)is not int or not 0<=epoch<=MAX_EPOCHS or not ishash(previous)or type(records)is not list or len(records)>64 or (epoch==0 and records)or (epoch>0 and not records):raise ReplayRefused('Bounded manifest required')
 body={'_id':'batch:'+str(epoch),'kind':'manifest','family':family,'epoch':epoch,'previous':previous,'records':records}
 bounded(body);return {**body,'sha256':digest(body)}

def validate_manifest(family,m):
 if type(m)is not dict or set(m)!={'_id','kind','family','epoch','previous','records','sha256'}:raise ReplayRefused('Exact manifest fields')
 expected=manifest(family,m['epoch'],m['previous'],m['records'])
 if expected!=m:raise ReplayRefused('Manifest hash mismatch')
 seen=set()
 for ref in m['records']:
  if type(ref)is not dict or set(ref)!={'id','sha256'}or not ishash(ref['id'])or not ishash(ref['sha256'])or ref['id']in seen:raise ReplayRefused('Manifest identities invalid')
  seen.add(ref['id'])
 return m

def record(family,row,*,epoch,source_revision,fingerprint=None,checkpoint=None):
 if family not in FAMILIES or type(epoch)is not int or not 1<=epoch<=MAX_EPOCHS or type(source_revision)is not int or not 0<=source_revision<2**53:raise ReplayRefused('Exact archive provenance')
 identity=row.get('key')if family=='collector'else row.get('nonce_hash')
 body={'_id':identity,'kind':'record','family':family,'epoch':epoch,'source_revision':source_revision,'fingerprint':fingerprint if family=='collector'else None,'row':row,'checkpoint':checkpoint}
 bounded(body);validate_record({**body,'sha256':digest(body)});return {**body,'sha256':digest(body)}

def validate_record(r):
 try:
  bounded(r)
  if type(r)is not dict or set(r)!={'_id','kind','family','epoch','source_revision','fingerprint','row','checkpoint','sha256'}or r['kind']!='record'or not ishash(r['_id'])or not ishash(r['sha256']):raise ValueError()
  if type(r['epoch'])is not int or not 1<=r['epoch']<=MAX_EPOCHS or type(r['source_revision'])is not int or not 0<=r['source_revision']<2**53:raise ValueError()
  if digest({k:v for k,v in r.items()if k!='sha256'})!=r['sha256']:raise ValueError()
  j=r['row']
  if r['family']=='collector':
   if type(j)is not dict or j.get('phase')not in ('completed','failed_before_write')or r['_id']!=j.get('key'):raise ValueError()
   fp=r['fingerprint']
   if not ishash(fp):raise ValueError()
   d={'_id':'geo108','revision':r['source_revision'],'fingerprint':fp,'fence':j['fence'],'active':None,'history':[j]}
   checkpoint_pack(d,[{'job':j['key'],'fence':j['fence'],'record':r['checkpoint']}],profile='geo108',fingerprint=fp)
  elif r['family']=='broker':
   if r['fingerprint']is not None or r['checkpoint']is not None or type(j)is not dict or j.get('phase')!='complete'or r['_id']!=j.get('nonce_hash'):raise ValueError()
   d={'_id':'shared-finder-v1','schema':2,'revision':r['source_revision'],'window_start':j['started_at'],'calls':1,'fence':j['fence'],'active':None,'last_clock':j['deadline'],'receipts':[j]};_v2(d)
  else:raise ValueError()
  return r
 except Exception:raise ReplayRefused('Immutable archive record refused')from None
