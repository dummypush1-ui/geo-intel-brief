"""198b-a fixed injected durable PROXY CALL budget, not provider attempt budget.
Preprovisioned state only. No client/index/upsert/TTL/purge/recovery/authority.
Unknown transport, expiry or CAS receipt never releases global in-flight hold.
"""
import copy,hashlib
class BudgetRefused(ValueError):pass
ID='shared-finder-v1'
MAX_CALLS=60
WINDOW=600
FIELDS={'_id','revision','window_start','calls','fence','active','last_clock'}

def _state(d):
 if type(d)is not dict or set(d)!=FIELDS or d['_id']!=ID:raise BudgetRefused('Closed budget document required')
 for k in ('revision','window_start','calls','fence','last_clock'):
  if type(d[k])is not int or not 0<=d[k]<2**53:raise BudgetRefused('Exact budget counters required')
 if d['calls']>MAX_CALLS or d['last_clock']<d['window_start']:raise BudgetRefused('Budget counters refused')
 a=d['active']
 if a is not None:
  if type(a)is not dict or set(a)!={'key','fence','started_at','deadline','phase'}:raise BudgetRefused('Closed in-flight ticket required')
  if type(a['key'])is not str or len(a['key'])!=64 or any(c not in '0123456789abcdef'for c in a['key']):raise BudgetRefused('Exact budget key required')
  if any(type(a[k])is not int for k in ('fence','started_at','deadline'))or not 0<a['fence']<=d['fence']or not 0<=a['started_at']<a['deadline']<=a['started_at']+25 or a['started_at']>d['last_clock'] or a['phase']not in ('inflight','unknown_held'):raise BudgetRefused('Budget ticket refused')
 return d

class ProxyCallBudget:
 def __init__(self,collection,*,review):
  expected={'mapping':('geo_intel','finder_budget198'),'preprovisioned_state_verified':True,'no_ttl_verified':True,'role_verified':True,'write_permission':True}
  if type(review)is not dict or review!=expected or any(type(review[k])is not bool for k in expected if k!='mapping'):raise BudgetRefused('Exact reviewed budget mapping required')
  try:
   if collection.name!='finder_budget198'or collection.database.name!='geo_intel':raise ValueError()
   w=collection.write_concern.document;r=collection.read_concern.document
   if w.get('w')!='majority'or w.get('j')is not True or type(w.get('wtimeout'))is not int or not 1<=w['wtimeout']<=5000 or r.get('level')!='majority':raise ValueError()
  except Exception:raise BudgetRefused('Durable budget concerns required')from None
  self.c=collection
 def _change(self,now,mutate):
  if type(now)is not int or not 0<=now<2**53:raise BudgetRefused('Exact clock required')
  for _ in range(4):
   try:
    before=_state(self.c.find_one({'_id':ID},max_time_ms=2000))
    if now<before['last_clock']:raise BudgetRefused('Budget clock rollback held')
    after=copy.deepcopy(before);result=mutate(after);after['last_clock']=now;after['revision']+=1;_state(after)
    receipt=self.c.replace_one({'_id':ID,'revision':before['revision']},after,upsert=False)
    if receipt.acknowledged is not True:raise ValueError()
    if receipt.matched_count==1:return result
   except BudgetRefused:raise
   except Exception:raise BudgetRefused('Budget state uncertain; no transport or retry')from None
  raise BudgetRefused('Budget contention held')
 def reserve(self,nonce,now):
  if type(nonce)is not str or not 20<=len(nonce)<=80 or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'for c in nonce):raise BudgetRefused('Exact request nonce required')
  key=hashlib.sha256(nonce.encode('ascii')).hexdigest()
  def mutate(d):
   if d['active']is not None:raise BudgetRefused('Global in-flight held; no lease takeover')
   if now-d['window_start']>=WINDOW:d['window_start']=now;d['calls']=0
   if d['calls']>=MAX_CALLS:raise BudgetRefused('Shared proxy call limit reached')
   d['calls']+=1;d['fence']+=1;d['active']={'key':key,'fence':d['fence'],'started_at':now,'deadline':now+25,'phase':'inflight'}
   return copy.deepcopy(d['active'])
  return self._change(now,mutate)
 def settle(self,ticket,now,*,known_complete):
  if type(known_complete)is not bool or type(ticket)is not dict:raise BudgetRefused('Exact transport outcome required')
  # Snapshot: only the original exact ticket can settle, not an arbitrary key.
  ticket=copy.deepcopy(ticket)
  def mutate(d):
   a=d['active']
   if a is None or a!=ticket or a['phase']!='inflight':raise BudgetRefused('Exact live ticket required')
   if known_complete and now<a['deadline']:
    d['active']=None;return {'state':'complete','unit':'proxy_calls','refund':False}
   d['active']['phase']='unknown_held';return {'state':'unknown_held','unit':'proxy_calls','refund':False}
  return self._change(now,mutate)
 def status(self):
  try:
   d=_state(self.c.find_one({'_id':ID},max_time_ms=2000));return {'calls':d['calls'],'window_start':d['window_start'],'active':copy.deepcopy(d['active']),'unit':'proxy_calls','cap':MAX_CALLS,'window_seconds':WINDOW}
  except Exception:raise BudgetRefused('Budget status unavailable')from None

def inspect_budget(client):
 """Read-only exact dedicated role/mapping/state preflight. No provisioning.
  This observes capabilities, not owner permission. No client creation here.
 """
 try:
  from pymongo.write_concern import WriteConcern
  from pymongo.read_concern import ReadConcern
  info=client.admin.command({'connectionStatus':1,'showPrivileges':True});hello=client.admin.command({'hello':1})
  if info.get('ok')!=1 or hello.get('ok')!=1 or not hello.get('setName')or hello.get('isWritablePrimary')is not True:raise ValueError()
  auth=info['authInfo']
  if type(auth['authenticatedUsers'])is not list or len(auth['authenticatedUsers'])!=1:raise ValueError()
  grants=auth['authenticatedUserPrivileges'];got=set()
  if type(grants)is not list or not 1<=len(grants)<=4:raise ValueError()
  for g in grants:
   if type(g)is not dict or set(g)!={'resource','actions'}or g['resource']!={'db':'geo_intel','collection':'finder_budget198'}or type(g['actions'])is not list or any(type(a)is not str for a in g['actions']):raise ValueError()
   got.update(g['actions'])
  if got!={'find','listIndexes','update'}:raise ValueError()
  c=client['geo_intel'].get_collection('finder_budget198',write_concern=WriteConcern(w='majority',j=True,wtimeout=5000),read_concern=ReadConcern('majority'))
  rows=c.list_indexes(maxTimeMS=2000)
  try:
   indexes=list(rows)
   if not 1<=len(indexes)<=16 or any('expireAfterSeconds'in r for r in indexes)or not any(dict(r.get('key',{}))=={'_id':1}and 'partialFilterExpression'not in r for r in indexes):raise ValueError()
  finally:rows.close()
  _state(c.find_one({'_id':ID},max_time_ms=2000))
  return c
 except Exception:raise BudgetRefused('Dedicated budget preflight unavailable; no writes')from None
