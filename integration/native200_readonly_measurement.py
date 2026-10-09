"""Default-off, explicit-client bounded observation. No mutation or transactions."""
import copy,hashlib,time
from types import SimpleNamespace
from bson import BSON,Int64
from bson.json_util import dumps,CANONICAL_JSON_OPTIONS
from pymongo.synchronous.mongo_client import MongoClient
from pymongo.read_preferences import ReadPreference
from integration.native200_transactions import NativeRefused,verify_native_pins
from integration.native200_store import NAMES,CAP
from integration.native200_admission_preflight import VALIDATORS
from integration.replay199_schema import FAMILIES,ishash,digest
from integration.replay199_core import ArchiveCore
from integration.collector197_archive import pack

MAX_ROWS=16385
TOTAL_BYTES=32*1024*1024

def _canonical(v):return dumps(v,json_options=CANONICAL_JSON_OPTIONS,sort_keys=True)
def _plain(v):
 # App validators use exact Python int. Preserve BSON typing separately before
 # this lossless Int64->int adapter. NEVER accept/convert a double into int.
 if type(v)is Int64:return int(v)
 if type(v)is dict:return {k:_plain(x)for k,x in v.items()}
 if type(v)is list:return [_plain(x)for x in v]
 return v

def _read(client,cmd):
 allowed={'hello','buildInfo','listCollections','listIndexes','find','count'}
 if type(cmd)is not dict or next(iter(cmd),None)not in allowed or cmd.get('maxTimeMS')!=2000:raise NativeRefused('Read-only bounded command required')
 action=next(iter(cmd))
 if action in ('hello','buildInfo'):
  if cmd!={action:1,'maxTimeMS':2000}:raise NativeRefused('Exact observation command')
 elif action=='listCollections':
  if set(cmd)!={'listCollections','filter','cursor','maxTimeMS'}or cmd[action]!=1 or type(cmd['filter'])is not dict or set(cmd['filter'])!={'name'}or cmd['filter']['name']not in NAMES or cmd['cursor']!={'batchSize':2}:raise NativeRefused('Exact collection inspection')
 elif cmd[action]not in NAMES:raise NativeRefused('Fixed geo_intel mapping')
 elif action=='listIndexes':
  if cmd!={action:cmd[action],'cursor':{'batchSize':17},'maxTimeMS':2000}:raise NativeRefused('Exact index inspection')
 elif action=='find':
  if cmd!={action:cmd[action],'filter':{},'limit':MAX_ROWS,'batchSize':MAX_ROWS,'singleBatch':True,'readConcern':{'level':'majority'},'maxTimeMS':2000}:raise NativeRefused('Exact bounded full observation')
 elif action=='count':
  if cmd!={action:cmd[action],'query':{},'readConcern':{'level':'majority'},'maxTimeMS':2000}:raise NativeRefused('Exact count observation')
 if len(BSON.encode(cmd))>CAP:raise NativeRefused('Read command cap')
 with client._conn_for_writes(None,next(iter(cmd)))as conn:
  if conn.is_mongos or conn.service_id is not None:raise NativeRefused('Replica-set connection only')
  out=conn.command('geo_intel',copy.deepcopy(cmd),read_preference=ReadPreference.PRIMARY,session=None,client=client,no_reauth=True)
 if type(out)is not dict or out.get('ok')!=1 or out.get('errorLabels')or out.get('writeConcernError')or len(BSON.encode(out))>CAP:raise NativeRefused('Read reply held')
 return out

def _rows(out,ns,limit):
 c=out.get('cursor')
 if type(c)is not dict or c.get('id')!=0 or c.get('ns')!=ns or type(c.get('firstBatch'))is not list or len(c['firstBatch'])>limit or any(type(r)is not dict for r in c['firstBatch']):raise NativeRefused('Exhausted bounded cursor required; no getMore')
 return c['firstBatch']

def _inventory(client,deadline):
 data={};evidence={};total=0
 for n in sorted(NAMES):
  deadline()
  rows=_rows(_read(client,{'listCollections':1,'filter':{'name':n},'cursor':{'batchSize':2},'maxTimeMS':2000}),'geo_intel.$cmd.listCollections',1)
  if len(rows)!=1 or rows[0].get('name')!=n or rows[0].get('type')!='collection':raise NativeRefused('Exact existing collection required')
  opts=rows[0].get('options',{})
  if type(opts)is not dict or set(opts)!={'validator','validationLevel','validationAction'}or opts['validationLevel']!='strict'or opts['validationAction']!='error'or _canonical(opts['validator'])!=_canonical(VALIDATORS[n]):raise NativeRefused('Exact typed strict/error validator required')
  idx=_rows(_read(client,{'listIndexes':n,'cursor':{'batchSize':17},'maxTimeMS':2000}),'geo_intel.'+n,16)
  if not idx or any('expireAfterSeconds'in r for r in idx)or not any(r.get('name')=='_id_'and r.get('key')=={'_id':1}and r.get('unique',True)is True and not r.get('sparse')and 'partialFilterExpression'not in r for r in idx):raise NativeRefused('Ordinary unique id/no TTL required')
  rows=_rows(_read(client,{'find':n,'filter':{},'limit':MAX_ROWS,'batchSize':MAX_ROWS,'singleBatch':True,'readConcern':{'level':'majority'},'maxTimeMS':2000}),'geo_intel.'+n,MAX_ROWS-1)
  count=_read(client,{'count':n,'query':{},'readConcern':{'level':'majority'},'maxTimeMS':2000}).get('n')
  if type(count)not in (int,Int64)or count!=len(rows):raise NativeRefused('Complete collection count mismatch; singleBatch may truncate')
  total+=sum(len(BSON.encode(r))for r in rows)
  if total>TOTAL_BYTES:raise NativeRefused('Total observation byte cap')
  byid={}
  for r in rows:
   k=r.get('_id')
   if type(k)is not str or k in byid:raise NativeRefused('Exact unique string identity')
   byid[k]=r
  data[n]=byid
  evidence[n]={'rows':len(rows),'validator_sha256':hashlib.sha256(_canonical(opts['validator']).encode()).hexdigest(),'indexes_sha256':hashlib.sha256(_canonical(idx).encode()).hexdigest(),'data_sha256':hashlib.sha256(_canonical([byid[k]for k in sorted(byid)]).encode()).hexdigest()}
 return data,evidence,total

class _Lookup:
 def __init__(self,rows):self.rows=rows
 def find_one(self,q,**kwargs):return copy.deepcopy(self.rows.get(q['_id']))

def _chains(data,fp,deadline):
 out={};sources={}
 for family,(sn,an,identity,_)in FAMILIES.items():
  if set(data[sn])!={identity}:raise NativeRefused('Unexpected source identity')
  view=SimpleNamespace(s=_Lookup(data[sn]),a=_Lookup(data[an]),family=family,fp=fp if family=='collector'else None)
  view._state=lambda session,v=view:ArchiveCore._state(v,session)
  d,records,size=ArchiveCore.verified_view(view,None,deadline)
  expected={'batch:'+str(e)for e in range(d['archive_epoch']+1)}|set(records)
  if set(data[an])!=expected:raise NativeRefused('Archive orphan/missing rows')
  sources[family]=d;out[family]={'archive_epochs':d['archive_epoch'],'archive_records':len(records),'chain_bytes':size,'source_revision':d['revision']}
  if family=='collector':
   jobs=([d['active']]if d['active']is not None else[])+d['history'];cp=data['collector_checkpoints197'];known={j['key']for j in jobs}|set(records)
   if not set(cp)<=known:raise NativeRefused('Unknown retained checkpoint')
   base={k:v for k,v in d.items()if k not in ('schema','archive_epoch','archived_count','chain_head')}
   pack(base,[{'job':j['key'],'fence':j['fence'],'record':cp.get(j['key'])}for j in jobs],profile='geo108',fingerprint=fp)
   for key,r in records.items():
    if key in cp and cp[key]!=r['checkpoint']:raise NativeRefused('Archived checkpoint mismatch')
 return out,sources

def _journals(data,sources):
 guards=data['native_guards200'];ops=data['native_operations200'];outcomes=data['native_outcomes200']
 keys={f+':'+FAMILIES[f][2]for f in FAMILIES}
 if set(guards)!=keys:raise NativeRefused('Exact two guards required')
 states={};seen=set()
 for family in FAMILIES:
  key=family+':'+FAMILIES[family][2];g=guards[key]
  if set(g)!={'_id','schema','family','serial','operation','phase'}or type(g['schema'])is not int or g['schema']!=1 or g['family']!=family or type(g['serial'])is not int or not 0<=g['serial']<=4096 or g['phase']not in ('idle','reserved','commit_attempt','acknowledged','admission_attempt')or(g['phase']=='idle')!=(g['operation']is None)or g['operation']is not None and not ishash(g['operation'])or (g['serial']==0)!=(g['phase']=='idle'):raise NativeRefused('Exact guard state')
  serials=set()
  for op in ops.values():
   if op.get('guard')!=key:continue
   if set(op)!={'_id','schema','guard','serial','plan'}or not ishash(op['_id'])or type(op['schema'])is not int or op['schema']!=1 or type(op['serial'])is not int or not 1<=op['serial']<=g['serial']or op['serial']in serials:raise NativeRefused('Exact operation serial')
   serials.add(op['serial']);seen.add(op['_id']);p=op['plan']
   if type(p)is not dict or set(p)!={'family','source','expected_revision','epoch','head','after_hash'}or p['family']!=family or p['source']!=FAMILIES[family][2]or type(p['expected_revision'])is not int or not 0<=p['expected_revision']<2**53 or type(p['epoch'])is not int or not 0<=p['epoch']<=1024 or not ishash(p['head'])or not ishash(p['after_hash']):raise NativeRefused('Exact operation plan')
   m=outcomes.get(op['_id'])
   if m is not None and _canonical(m)!=_canonical({'_id':op['_id'],'schema':1,'guard':key,'serial':op['serial'],'plan_hash':digest(p),'after_hash':p['after_hash']}):raise NativeRefused('Exact outcome marker')
  # Missing current intent can be an interrupted reservation, not permission.
  if g['operation']is not None:
   current=ops.get(g['operation'])
   if current is not None and(current['guard']!=key or current['serial']!=g['serial']):raise NativeRefused('Guard/current intent mismatch')
   if g['phase']=='acknowledged':
    if g['operation']not in outcomes or current is None:raise NativeRefused('Acknowledged marker missing')
    d=sources[family]
    if d['revision']!=current['plan']['expected_revision']+1 or digest(d)!=current['plan']['after_hash']:raise NativeRefused('Acknowledged source proof mismatch')
  expected_serials=set(range(1,g['serial']+1))
  if g['operation']is not None and g['operation']not in ops:expected_serials.discard(g['serial'])
  if serials!=expected_serials:raise NativeRefused('Retained operation serial gap')
  states[family]=g['phase']
 if seen!=set(ops):raise NativeRefused('Unbound operation')
 for op in ops.values():
  if op['_id']!=guards[op['guard']]['operation']:
   if op['_id']not in outcomes:raise NativeRefused('Prior outcome missing')
  if op['serial']>1 and 'admission:'+op['_id']not in outcomes:raise NativeRefused('Successor closure missing')
 for k,m in outcomes.items():
  if k in ops:continue
  if type(m)is not dict or set(m)!={'_id','kind','schema','guard','old_operation','old_serial','new_operation','new_serial','source_hash'}or m['kind']!='admission'or type(m['schema'])is not int or m['schema']!=1 or not ishash(m['new_operation'])or k!='admission:'+m['new_operation']or m['guard']not in keys or not ishash(m['old_operation'])or not ishash(m['source_hash'])or type(m['old_serial'])is not int or type(m['new_serial'])is not int or not 1<=m['old_serial']<4096 or m['new_serial']!=m['old_serial']+1:raise NativeRefused('Exact admission closure')
  old=ops.get(m['old_operation']);new=ops.get(m['new_operation'])
  if old is None or new is None or old['guard']!=m['guard']or new['guard']!=m['guard']or old['serial']!=m['old_serial']or new['serial']!=m['new_serial']or old['_id']not in outcomes or m['source_hash']!=old['plan']['after_hash']:raise NativeRefused('Admission linkage mismatch')
 return states

def measure(client=None,*,enabled=False,fingerprint=None,clock=time.monotonic):
 """Read-only observed evidence only. Does not construct/close clients or sessions."""
 if type(enabled)is not bool:raise NativeRefused('Exact read-only selection')
 if not enabled:return {'state':'disabled','ready':False,'database_effects':False}
 try:
  if type(client)is not MongoClient or not ishash(fingerprint)or not callable(clock):raise NativeRefused('Explicit pinned client/fingerprint required')
  version=verify_native_pins()
  opts=client.options
  if opts.retry_writes or opts.retry_reads or opts.load_balanced or opts.timeout is not None or client._encrypter is not None:raise NativeRefused('Exact nonretry replica-set client')
  credentials=opts.pool_options._credentials
  if credentials is not None and credentials.mechanism=='MONGODB-OIDC':raise NativeRefused('No reauthentication route')
  start=clock()
  def deadline():
   now=clock()
   if type(start)not in (int,float)or type(now)not in (int,float)or not 0<=start<=now<start+20:raise NativeRefused('Observation deadline')
  hello=_read(client,{'hello':1,'maxTimeMS':2000})
  if client.topology_description.topology_type_name!='ReplicaSetWithPrimary'or not hello.get('setName')or hello.get('isWritablePrimary')is not True or 'msg'in hello or 'serviceId'in hello or type(hello.get('maxWireVersion'))is not int or hello['maxWireVersion']<7 or type(hello.get('logicalSessionTimeoutMinutes'))is not int or hello['logicalSessionTimeoutMinutes']<1:raise NativeRefused('Observed replica-set primary required')
  build=_read(client,{'buildInfo':1,'maxTimeMS':2000})
  if type(build.get('version'))is not str or not 1<=len(build['version'])<=64 or any(c not in '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.-+'for c in build['version']):raise NativeRefused('Sanitized server version required')
  data,evidence,size=_inventory(client,deadline)
  plain=_plain(data);chains,sources=_chains(plain,fingerprint,deadline);states=_journals(plain,sources)
  _,after,_=_inventory(client,deadline);deadline()
  if evidence!=after:raise NativeRefused('Observed data/schema/index changed; no snapshot claim')
  return {'state':'readonly_observed','ready':False,'database_effects':False,'driver_version':version,'server_version':build['version'],'topology':'ReplicaSetWithPrimary','collections':evidence,'chains':chains,'guard_phases':states,'observed_bytes':size,'atomic_snapshot':False,'retry_safe':False,'holds_cleared':False,'capacity_released':False,'role_verified':False,'durability_proven':False}
 except Exception:raise NativeRefused('Read-only measurement held; no mutations/retry/recovery permission')from None
