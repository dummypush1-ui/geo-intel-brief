"""Fixed v2 same-document proxy-call receipts. Source-only injected adapter.
Explicit owner migration required. V1 untouched. No upsert/TTL/recovery/answer.
"""
import copy,hashlib
from integration.finder198_budget import ProxyCallBudget,BudgetRefused,ID,_state
FIELDS={'_id','schema','revision','window_start','calls','fence','active','last_clock','receipts'}
RECEIPT={'nonce_hash','body_hash','identity_hash','fence','phase','started_at','deadline','status','response_hash','response_bytes'}
def _hash(v):return type(v)is str and len(v)==64 and all(c in '0123456789abcdef'for c in v)
def _v2(d):
 if type(d)is not dict or set(d)!=FIELDS or type(d['schema'])is not int or d['schema']!=2 or type(d['receipts'])is not list or len(d['receipts'])>64:raise BudgetRefused('Preprovisioned v2 state required')
 base={k:v for k,v in d.items()if k not in ('schema','receipts')};_state(base)
 keys=set();fences=set()
 for r in d['receipts']:
  if type(r)is not dict or set(r)!=RECEIPT or not all(_hash(r[k])for k in ('nonce_hash','body_hash','identity_hash')):raise BudgetRefused('Closed receipt hashes required')
  if any(type(r[k])is not int for k in ('fence','started_at','deadline','response_bytes'))or not 0<r['fence']<=d['fence']or not 0<=r['started_at']<r['deadline']<=r['started_at']+25 or not 0<=r['response_bytes']<=1048576:raise BudgetRefused('Receipt counts refused')
  if r['nonce_hash']in keys or r['fence']in fences or r['phase']not in ('reserved','send_started','complete','unknown_held'):raise BudgetRefused('Receipt identity refused')
  keys.add(r['nonce_hash']);fences.add(r['fence'])
  if r['phase']=='complete':
   if type(r['status'])is not int or not 200<=r['status']<=599 or not _hash(r['response_hash']):raise BudgetRefused('Complete receipt refused')
  elif r['status']is not None or r['response_hash']is not None or r['response_bytes']!=0:raise BudgetRefused('No unverified result metadata')
 active=d['active'];open_rows=[r for r in d['receipts']if r['phase']!='complete']
 if active is None:
  if open_rows:raise BudgetRefused('Orphan in-flight receipt')
 else:
  if len(open_rows)!=1:raise BudgetRefused('Exact active receipt required')
  r=open_rows[0]
  if (r['nonce_hash'],r['fence'],r['started_at'],r['deadline'])!=(active['key'],active['fence'],active['started_at'],active['deadline'])or (r['phase']=='unknown_held')!=(active['phase']=='unknown_held'):raise BudgetRefused('Active receipt mismatch')
 return d

class ProxyReceiptBudget(ProxyCallBudget):
 def _change(self,now,mutate):
  if type(now)is not int or not 0<=now<2**53:raise BudgetRefused('Exact clock required')
  for _ in range(4):
   try:
    before=_v2(self.c.find_one({'_id':ID},max_time_ms=2000))
    if now<before['last_clock']:raise BudgetRefused('Clock rollback held')
    after=copy.deepcopy(before);out=mutate(after);after['last_clock']=now;after['revision']+=1;_v2(after)
    receipt=self.c.replace_one({'_id':ID,'schema':2,'revision':before['revision']},after,upsert=False)
    if receipt.acknowledged is not True:raise ValueError()
    if receipt.matched_count==1:return out
   except BudgetRefused:raise
   except Exception:raise BudgetRefused('Receipt CAS uncertain; no transport/retry')from None
  raise BudgetRefused('Receipt contention held')
 def claim(self,nonce,body_hash,identity_hash,now):
  if type(nonce)is not str or not 20<=len(nonce)<=80 or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'for c in nonce)or not _hash(body_hash)or not _hash(identity_hash):raise BudgetRefused('Exact request hashes required')
  key=hashlib.sha256(nonce.encode('ascii')).hexdigest()
  def mutate(d):
   found=[r for r in d['receipts']if r['nonce_hash']==key]
   if found:
    r=found[0]
    if (r['body_hash'],r['identity_hash'])!=(body_hash,identity_hash):raise BudgetRefused('Nonce request mismatch')
    return {'state':'replay_status_only','receipt':copy.deepcopy(r)}
   if d['active']is not None or len(d['receipts'])>=64:raise BudgetRefused('Busy or receipts full')
   if now-d['window_start']>=600:d['window_start']=now;d['calls']=0
   if d['calls']>=60:raise BudgetRefused('Proxy call budget full')
   d['calls']+=1;d['fence']+=1
   r={'nonce_hash':key,'body_hash':body_hash,'identity_hash':identity_hash,'fence':d['fence'],'phase':'reserved','started_at':now,'deadline':now+25,'status':None,'response_hash':None,'response_bytes':0}
   d['receipts'].append(r);d['active']={'key':key,'fence':r['fence'],'started_at':now,'deadline':now+25,'phase':'inflight'}
   return {'state':'claimed','receipt':copy.deepcopy(r)}
  return self._change(now,mutate)
 def _transition(self,ticket,now,phase,status=None,response_hash=None,response_bytes=0):
  if type(ticket)is not dict:raise BudgetRefused('Exact receipt ticket required')
  ticket=copy.deepcopy(ticket)
  def mutate(d):
   found=[r for r in d['receipts']if r==ticket]
   if len(found)!=1 or d['active']is None:raise BudgetRefused('Exact active receipt required')
   r=found[0]
   if phase=='send_started':
    if r['phase']!='reserved'or now>=r['deadline']:raise BudgetRefused('Send claim refused')
   elif phase in ('complete','unknown_held'):
    if r['phase']!='send_started':raise BudgetRefused('Transport already held or settled')
    if phase=='complete'and now>=r['deadline']:phase_local='unknown_held'
    else:phase_local=phase
    r['phase']=phase_local
    if phase_local=='complete':
     r.update(status=status,response_hash=response_hash,response_bytes=response_bytes);d['active']=None
    else:d['active']['phase']='unknown_held'
    return copy.deepcopy(r)
   else:raise BudgetRefused('Closed receipt phase')
   r['phase']=phase;return copy.deepcopy(r)
  return self._change(now,mutate)
 def start(self,ticket,now):return self._transition(ticket,now,'send_started')
 def finish(self,ticket,now,*,status,response_hash,response_bytes):return self._transition(ticket,now,'complete',status,response_hash,response_bytes)
 def hold(self,ticket,now):return self._transition(ticket,now,'unknown_held')
 def reserve(self,*a,**kw):raise BudgetRefused('V2 claim protocol only')
 def settle(self,*a,**kw):raise BudgetRefused('V2 receipt protocol only')
 def status(self):
  try:
   d=_v2(self.c.find_one({'_id':ID},max_time_ms=2000));return {'unit':'proxy_calls','calls':d['calls'],'active':copy.deepcopy(d['active']),'receipts':copy.deepcopy(d['receipts'])}
  except Exception:raise BudgetRefused('V2 status unavailable')from None
