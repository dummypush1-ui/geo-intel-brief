"""New unselected archive-aware adapters. Old exact-types/runtime unchanged.
All source mutations use same snapshot tx/complete archive view as rollover.
Native provider unavailable; synthetic tests only. No automatic retry/recovery.
"""
import copy,hashlib
from integration.replay199_core import ArchiveCore
from integration.replay199_schema import ReplayRefused,source,ishash,bounded
from collector108_prep.durable_ledger import NEXT,ACTIVE

def _nonce(nonce):
 if type(nonce)is not str or not 20<=len(nonce)<=80 or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'for c in nonce):raise ReplayRefused('Exact nonce required')
 return nonce

def _clock(now):
 if type(now)is not int or not 0<=now<2**53:raise ReplayRefused('Exact monotonic source clock')
 return now

class _Adapter:
 def __init__(self,core,family):
  if type(core)is not ArchiveCore or core.family!=family or core.enabled is not True:raise ReplayRefused('Exact enabled family core required')
  self.core=core
 def _change(self,mutate):
  core=self.core
  def work(session,deadline):
   before,archive,_=core.verified_view(session,deadline);after=copy.deepcopy(before);out=mutate(after,archive)
   # Replays and status-only branches return without source write.
   if after==before:return out
   after['revision']=before['revision']+1;source(core.family,after,core.fp);deadline()
   query={k:before[k]for k in ('_id','schema','revision','archive_epoch','chain_head')}
   ack=core.s.replace_one(query,after,upsert=False,session=session)
   if ack.acknowledged is not True or ack.matched_count!=1:raise ReplayRefused('Archive-aware CAS held')
   if core.s.find_one({'_id':after['_id']},session=session,max_time_ms=2000)!=after:raise ReplayRefused('Source readback held')
   return out
  return core._session(True,work)

class ArchivedCollectorLedger(_Adapter):
 def __init__(self,core):super().__init__(core,'collector');self.profile='geo108';self.fp=core.fp
 def submit(self,nonce,now):
  key=hashlib.sha256(('geo108\n'+_nonce(nonce)).encode()).hexdigest();_clock(now)
  def mutate(d,archive):
   rows=([d['active']]if d['active']is not None else[])+d['history']
   found=next((j for j in rows if j['key']==key),None)
   if found is not None:return copy.deepcopy(found)
   if key in archive:return copy.deepcopy(archive[key]['row'])
   if d['active']is not None or len(d['history'])>=64:raise ReplayRefused('Active/history capacity held')
   # No source clock rollback through old retained jobs either.
   times=[j['updated_at']for j in rows]+[r['row']['updated_at']for r in archive.values()]
   if times and now<max(times):raise ReplayRefused('Collector clock rollback held')
   d['fence']+=1;d['active']={'key':key,'fence':d['fence'],'phase':'accepted','lease_until':now+120,'counts':{},'updated_at':now}
   return copy.deepcopy(d['active'])
  return self._change(mutate)
 def advance(self,key,fence,phase,now,counts):
  if not ishash(key)or type(fence)is not int or fence<1 or type(phase)is not str or type(counts)is not dict:raise ReplayRefused('Exact collector transition')
  _clock(now)
  if len(counts)>8 or any(k not in ('fetched','prepared','attempted','inserted','duplicate','failed','uncertain')or type(v)is not int or not 0<=v<=1000 for k,v in counts.items()):raise ReplayRefused('Bounded collector counts')
  def mutate(d,archive):
   j=d['active']
   if key in archive or not j or j['key']!=key or j['fence']!=fence or now<j['updated_at']or now>=j['lease_until']or phase not in NEXT.get(j['phase'],set()):raise ReplayRefused('Collector transition held')
   j.update(phase=phase,counts=copy.deepcopy(counts),updated_at=now,lease_until=now+120);out=copy.deepcopy(j)
   if phase not in ACTIVE and phase!='uncertain_after_write':
    if len(d['history'])>=64:raise ReplayRefused('History full, no silent drop')
    d['history'].append(copy.deepcopy(j));d['active']=None
   return out
  return self._change(mutate)
 def heartbeat(self,key,fence,now):
  if not ishash(key)or type(fence)is not int or fence<1:raise ReplayRefused('Exact heartbeat')
  _clock(now)
  def mutate(d,archive):
   j=d['active']
   if key in archive or not j or j['key']!=key or j['fence']!=fence or now<j['updated_at']or now>=j['lease_until']:raise ReplayRefused('Heartbeat held')
   j.update(updated_at=now,lease_until=now+120);return copy.deepcopy(j)
  return self._change(mutate)
 def status(self,key):
  result=self.core.lookup(key)
  if result['state']!='status_only':raise ReplayRefused('Job not found, verified view only')
  j=result['row'];return {'job':key,'phase':j['phase'],'counts':copy.deepcopy(j['counts']),'archived':result['archived']}

class ArchivedProxyReceiptBudget(_Adapter):
 def __init__(self,core):super().__init__(core,'broker')
 def claim(self,nonce,body_hash,identity_hash,now):
  key=hashlib.sha256(_nonce(nonce).encode('ascii')).hexdigest();_clock(now)
  if not ishash(body_hash)or not ishash(identity_hash):raise ReplayRefused('Exact request scope')
  def mutate(d,archive):
   if now<d['last_clock']:raise ReplayRefused('Clock rollback held')
   found=next((r for r in d['receipts']if r['nonce_hash']==key),None)
   if found is None and key in archive:found=archive[key]['row']
   if found is not None:
    if(found['body_hash'],found['identity_hash'])!=(body_hash,identity_hash):raise ReplayRefused('Nonce scope mismatch, no status disclosure')
    return {'state':'replay_status_only','receipt':copy.deepcopy(found)}
   if d['active']is not None or len(d['receipts'])>=64:raise ReplayRefused('Active/receipts capacity held')
   if now-d['window_start']>=600:d['window_start']=now;d['calls']=0
   if d['calls']>=60:raise ReplayRefused('Proxy call cap')
   d['calls']+=1;d['fence']+=1;d['last_clock']=now
   r={'nonce_hash':key,'body_hash':body_hash,'identity_hash':identity_hash,'fence':d['fence'],'phase':'reserved','started_at':now,'deadline':now+25,'status':None,'response_hash':None,'response_bytes':0}
   d['receipts'].append(r);d['active']={'key':key,'fence':r['fence'],'started_at':now,'deadline':now+25,'phase':'inflight'}
   return {'state':'claimed','receipt':copy.deepcopy(r)}
  return self._change(mutate)
 def _transition(self,ticket,now,phase,status=None,response_hash=None,response_bytes=0):
  if type(ticket)is not dict:raise ReplayRefused('Exact original receipt ticket')
  _clock(now);bounded(ticket);ticket=copy.deepcopy(ticket)
  def mutate(d,archive):
   if now<d['last_clock']:raise ReplayRefused('Clock rollback held')
   found=[r for r in d['receipts']if r==ticket]
   if len(found)!=1 or d['active']is None:raise ReplayRefused('Original active ticket held')
   r=found[0];d['last_clock']=now
   if phase=='send_started':
    if r['phase']!='reserved'or now>=r['deadline']:raise ReplayRefused('Send-start refused')
    r['phase']=phase
   elif phase in ('complete','unknown_held'):
    if r['phase']!='send_started':raise ReplayRefused('Already settled/held')
    actual='unknown_held'if now>=r['deadline']else phase;r['phase']=actual
    if actual=='complete':r.update(status=status,response_hash=response_hash,response_bytes=response_bytes);d['active']=None
    else:d['active']['phase']='unknown_held'
   else:raise ReplayRefused('Closed phase')
   return copy.deepcopy(r)
  return self._change(mutate)
 def start(self,ticket,now):return self._transition(ticket,now,'send_started')
 def finish(self,ticket,now,*,status,response_hash,response_bytes):return self._transition(ticket,now,'complete',status,response_hash,response_bytes)
 def hold(self,ticket,now):return self._transition(ticket,now,'unknown_held')
 def status(self,nonce,body_hash,identity_hash):
  key=hashlib.sha256(_nonce(nonce).encode('ascii')).hexdigest();out=self.core.lookup(key,body_hash=body_hash,identity_hash=identity_hash)
  if out['state']!='status_only':raise ReplayRefused('Receipt not found')
  return {'state':'replay_status_only','receipt':copy.deepcopy(out['row']),'archived':out['archived']}
