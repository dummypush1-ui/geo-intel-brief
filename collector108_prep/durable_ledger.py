"""Inactive single-document Mongo CAS ledger adapter. No Mongo client creation.
Exact injected collection, majority+journal concern REQUIRED by deployment
review; no automatic index/TTL or lease steal/recovery. Run-specific writes
remain separately unwired: ledger fencing alone cannot fence article writes.
"""
import hashlib,copy
class LedgerRefused(ValueError):pass
ACTIVE={'accepted','running','fetch_complete','prepare_complete','write_started'}
NEXT={'accepted':{'running'},'running':{'fetch_complete','failed_before_write'},'fetch_complete':{'prepare_complete','failed_before_write'},'prepare_complete':{'write_started','failed_before_write'},'write_started':{'completed','uncertain_after_write'}}
def _valid_job(j):
 if type(j)is not dict or set(j)!={'key','fence','phase','lease_until','counts','updated_at'}:raise ValueError()
 if type(j['key'])is not str or len(j['key'])!=64 or any(x not in '0123456789abcdef'for x in j['key']):raise ValueError()
 if type(j['fence'])is not int or j['fence']<1 or type(j['lease_until'])is not int or type(j['updated_at'])is not int or not 0<=j['updated_at']<j['lease_until']:raise ValueError()
 if type(j['phase'])is not str or j['phase']not in ACTIVE|{'completed','failed_before_write','uncertain_after_write'}:raise ValueError()
 c=j['counts']
 if type(c)is not dict or len(c)>8 or any(k not in ('fetched','prepared','attempted','inserted','duplicate','failed','uncertain')or type(v)is not int or not 0<=v<=1000 for k,v in c.items()):raise ValueError()
def _valid_document(d,profile,fp):
 if type(d)is not dict or set(d)!={'_id','revision','fingerprint','fence','active','history'}or d['_id']!=profile or d['fingerprint']!=fp or type(d['revision'])is not int or d['revision']<0 or type(d['fence'])is not int or d['fence']<0 or type(d['history'])is not list or len(d['history'])>64:raise ValueError()
 rows=([d['active']]if d['active']is not None else[])+d['history'];keys=set();fences=set()
 for j in rows:
  _valid_job(j)
  if j['key']in keys or j['fence']in fences or j['fence']>d['fence']:raise ValueError()
  keys.add(j['key']);fences.add(j['fence'])
 if any(j['phase']not in ('completed','failed_before_write')for j in d['history']):raise ValueError()
class DurableLedger:
 def __init__(self,collection,profile,fingerprint):
  if type(profile)is not str or profile!='geo108' or type(fingerprint)is not str or len(fingerprint)!=64 or any(x not in '0123456789abcdef'for x in fingerprint):raise LedgerRefused('Profile review required')
  self.c=collection;self.profile=profile;self.fp=fingerprint
 def initialize(self):
  # Explicit separate non-live preparation only. Deployment needs reviewed store.
  try:
   result=self.c.update_one({'_id':self.profile},{'$setOnInsert':{'revision':0,'fingerprint':self.fp,'fence':0,'active':None,'history':[]}},upsert=True)
   if result.acknowledged is not True:raise ValueError()
  except Exception:raise LedgerRefused('Ledger initialization uncertain')from None
 def _change(self,mutate):
  for _ in range(8):
   try:
    before=self.c.find_one({'_id':self.profile})
    _valid_document(before,self.profile,self.fp)
    after=copy.deepcopy(before);out=mutate(after);after['revision']+=1;_valid_document(after,self.profile,self.fp)
    r=self.c.replace_one({'_id':self.profile,'revision':before['revision'],'fingerprint':self.fp},after)
    if r.acknowledged is not True:raise ValueError()
    if r.matched_count==1:return out
   except LedgerRefused:raise
   except Exception:raise LedgerRefused('Ledger operation uncertain')from None
  raise LedgerRefused('Ledger contention')
 def submit(self,nonce,now):
  if type(nonce)is not str or not 20<=len(nonce)<=80 or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'for c in nonce)or type(now)is not int or now<0:raise LedgerRefused('Exact nonce/clock required')
  key=hashlib.sha256((self.profile+'\n'+nonce).encode()).hexdigest()
  def mutate(d):
   if d['active']and d['active']['key']==key:return copy.deepcopy(d['active'])
   for j in d['history']:
    if j['key']==key:return copy.deepcopy(j)
   if d['active']is not None or len(d['history'])>=64:raise LedgerRefused('Busy or history full')
   d['fence']+=1;d['active']={'key':key,'fence':d['fence'],'phase':'accepted','lease_until':now+120,'counts':{},'updated_at':now}
   return copy.deepcopy(d['active'])
  return self._change(mutate)
 def advance(self,key,fence,phase,now,counts):
  if type(key)is not str or type(fence)is not int or type(now)is not int or now<0 or type(phase)is not str or type(counts)is not dict or len(counts)>8 or any(k not in ('fetched','prepared','attempted','inserted','duplicate','failed','uncertain')or type(v)is not int or not 0<=v<=1000 for k,v in counts.items()):raise LedgerRefused('Exact transition required')
  counts=copy.deepcopy(counts)
  def mutate(d):
   j=d['active']
   if not j or j['key']!=key or j['fence']!=fence or now<j['updated_at']or now>=j['lease_until']or phase not in NEXT.get(j['phase'],set()):raise LedgerRefused('Transition refused')
   j.update(phase=phase,counts=counts,lease_until=now+120,updated_at=now);out=copy.deepcopy(j)
   if phase not in ACTIVE and phase!='uncertain_after_write':d['history'].append(copy.deepcopy(j));d['active']=None
   return out
  return self._change(mutate)
 def heartbeat(self,key,fence,now):
  if type(key)is not str or type(fence)is not int or type(now)is not int or now<0:raise LedgerRefused('Exact heartbeat required')
  def mutate(d):
   j=d['active']
   if not j or j['key']!=key or j['fence']!=fence or now<j['updated_at']or now>=j['lease_until']:raise LedgerRefused('Heartbeat refused')
   j['lease_until']=now+120;j['updated_at']=now;return copy.deepcopy(j)
  return self._change(mutate)
 def status(self,key):
  if type(key)is not str or len(key)!=64 or any(c not in '0123456789abcdef'for c in key):raise LedgerRefused('Exact job key required')
  try:
   d=self.c.find_one({'_id':self.profile})
   _valid_document(d,self.profile,self.fp)
   rows=([d['active']]if d.get('active')else[])+d['history']
   for j in rows:
    if type(j)is not dict:raise ValueError()
    if j.get('key')!=key:continue
    phase=j.get('phase');counts=j.get('counts')
    if type(phase)is not str or phase not in ACTIVE|{'completed','failed_before_write','uncertain_after_write'}or type(counts)is not dict or len(counts)>8 or any(k not in ('fetched','prepared','attempted','inserted','duplicate','failed','uncertain')or type(v)is not int or not 0<=v<=1000 for k,v in counts.items()):raise ValueError()
    return {'job':key,'phase':phase,'counts':copy.deepcopy(counts)}
  except Exception:raise LedgerRefused('Ledger status uncertain')from None
  raise LedgerRefused('Job not found')
