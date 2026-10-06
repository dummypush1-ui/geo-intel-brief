"""Atomic two-key admission experiment. Memory/same-process only; no service wiring."""
import copy,hashlib,hmac,secrets,threading,math,json
from dataclasses import dataclass
WINDOW=900
MAX_LOCK=3600
BASE_LOCK=900
USER_LIMIT=5
CLIENT_LIMIT=20
KEY_CAP=200
RECEIPT_CAP=200
TTL=4500
class LedgerRefused(ValueError):pass
@dataclass(frozen=True,slots=True,eq=False)
class Ticket:
 nonce:str
 def __init_subclass__(cls,**kwargs):raise TypeError('sealed')
 def __copy__(self):raise TypeError('not copyable')
 def __deepcopy__(self,memo):raise TypeError('not copyable')
 def __reduce__(self):raise TypeError('not serializable')

class Ledger:
 def __init__(self):
  self._lock=threading.RLock();self._secret=secrets.token_bytes(32);self._tickets={}
  self._state={'clock':0,'keys':{},'receipts':{},'key_queue':[],'receipt_queue':[]}
 def __init_subclass__(cls,**kwargs):raise TypeError('sealed')
 def _key(self,kind,value):return hmac.new(self._secret,(kind+':'+value).encode(),hashlib.sha256).hexdigest()
 def _validate(self):
  s=self._state
  if type(s) is not dict or len(s)!=5 or any(type(k) is not str for k in s) or set(s)!={'clock','keys','receipts','key_queue','receipt_queue'}:raise LedgerRefused('invalid fixture state')
  epoch(s['clock'])
  for name,cap in [('keys',KEY_CAP),('receipts',RECEIPT_CAP)]:
   rows=s[name];q=s['key_queue' if name=='keys' else 'receipt_queue']
   if type(rows) is not dict or len(rows)>cap or type(q) is not list or len(q)!=len(rows) or any(type(x) is not str for x in q) or len(set(q))!=len(q) or set(q)!=set(rows):raise LedgerRefused('invalid fixture state')
   for k,r in rows.items():
    if type(k) is not str or len(k)!=64 or any(c not in '0123456789abcdef' for c in k) or type(r) is not dict or len(r)>6 or any(type(x) is not str for x in r):raise LedgerRefused('invalid fixture state')
    if name=='keys':
     if set(r)!={'fails','locks','last','locked_until','gen','expires'} or type(r['fails']) is not int or not 0<=r['fails']<=20 or type(r['locks']) is not int or not 0<=r['locks']<=64 or type(r['gen']) is not str or len(r['gen'])!=64 or any(c not in '0123456789abcdef' for c in r['gen']):raise LedgerRefused('invalid fixture state')
     for x in ('last','locked_until','expires'):epoch(r[x])
    else:
     if set(r)!={'pairs','status','expires'} or r['status'] not in ('pending','fail','refund','success','expired') or type(r['status']) is not str or type(r['pairs']) is not list or len(r['pairs'])!=2:raise LedgerRefused('invalid fixture state')
     epoch(r['expires'])
     for pair in r['pairs']:
      if type(pair) is not list or len(pair)!=2 or any(type(x) is not str or len(x)!=64 or any(c not in '0123456789abcdef' for c in x) for x in pair):raise LedgerRefused('invalid fixture state')
  if len(json.dumps(s,separators=(',',':'),allow_nan=False).encode())>256000:raise LedgerRefused('invalid fixture state')
  if type(self._tickets) is not dict or set(self._tickets)!=set(s['receipts']) or any(type(v) is not Ticket or v.nonce!=k for k,v in self._tickets.items()):raise LedgerRefused('invalid fixture state')
  return copy.deepcopy(s),dict(self._tickets)
 def _prune(self,s,tickets,now):
  inspected=0
  for name,qname in [('keys','key_queue'),('receipts','receipt_queue')]:
   q=s[qname]
   for _ in range(min(4,len(q))):
    k=q.pop(0);r=s[name][k];inspected+=1
    if r['expires']<=now and (name=='receipts' or r['locked_until']<=now):
     s[name].pop(k)
     if name=='receipts':tickets.pop(k,None)
    else:q.append(k)
  return inspected
 def _publish(self,s,tickets):
  # Allocation completed before replacing authoritative references; no callbacks.
  self._state=s;self._tickets=tickets
 def _token(self,existing):
  for _ in range(4):
   n=secrets.token_hex(32)
   if n not in existing:return n
  raise LedgerRefused('fixture identity unavailable')
 def admit(self,operation,username,client,now):
  epoch(now)
  if now>4133980799-TTL-MAX_LOCK:raise LedgerRefused("fixture clock upper bound")
  for v in (operation,username,client):
   if type(v) is not str or not 1<=len(v)<=128 or not v.isascii() or any(ord(c)<33 or ord(c)>126 for c in v):raise LedgerRefused('invalid fixture input')
  if operation not in ('login','signup'):raise LedgerRefused('invalid fixture input')
  with self._lock:
   s,tickets=self._validate()
   if now<s['clock']:raise LedgerRefused('fixture clock rollback')
   inspected=self._prune(s,tickets,now)
   keys=[self._key('u-'+operation,username),self._key('c',client)]
   generations={r['gen'] for r in s['keys'].values()}|{g for r in s['receipts'].values() for k,g in r['pairs']}
   def generation():
    g=self._token(generations);generations.add(g);return g
   if len(s['receipts'])>=RECEIPT_CAP or len(set(s['keys'])|set(keys))>KEY_CAP:raise LedgerRefused('fixture capacity') # no prune/clock published
   proposed=[];waits=[]
   for key,limit in zip(keys,(USER_LIMIT,CLIENT_LIMIT)):
    r=copy.deepcopy(s['keys'].get(key))
    if r is None or r['locked_until']<=now and now-r['last']>WINDOW:
     r={'fails':0,'locks':r['locks'] if r else 0,'last':0,'locked_until':0,'gen':generation(),'expires':now+TTL}
    w=0
    if r['locked_until']>now:w=int(r['locked_until']-now)+1
    else:
     r['fails']+=1;r['last']=now
     if r['fails']>limit:
      r['locks']=min(64,r['locks']+1);r['locked_until']=now+min(MAX_LOCK,BASE_LOCK*2**min(2,r['locks']-1));r['fails']=0;r['gen']=generation();w=int(r['locked_until']-now)+1
     r['expires']=max(r['locked_until'],now+WINDOW)+MAX_LOCK
    proposed.append(r);waits.append(w)
   if max(waits):
    # Keep limiting-side lock transition; no counterpart phantom contribution.
    for key,r,w in zip(keys,proposed,waits):
     if w:
      if key not in s['keys']:s['key_queue'].append(key)
      s['keys'][key]=r
    s['clock']=now;self._publish(s,tickets)
    return result('denied',wait=max(waits),inspected=inspected)
   nonce=self._token(s['receipts']);ticket=Ticket(nonce)
   for key,r in zip(keys,proposed):
    if key not in s['keys']:s['key_queue'].append(key)
    s['keys'][key]=r
   s['receipts'][nonce]={'pairs':[[k,r['gen']] for k,r in zip(keys,proposed)],'status':'pending','expires':now+TTL};s['receipt_queue'].append(nonce);tickets[nonce]=ticket;s['clock']=now;self._publish(s,tickets)
   return result('admitted',ticket=ticket,inspected=inspected)
 def settle(self,ticket,action,now):
  epoch(now)
  if now>4133980799-TTL-MAX_LOCK:raise LedgerRefused("fixture clock upper bound")
  if type(ticket) is not Ticket or type(ticket.nonce) is not str or len(ticket.nonce)!=64 or any(c not in '0123456789abcdef' for c in ticket.nonce) or type(action) is not str or action not in ('fail','refund','success'):raise LedgerRefused('invalid fixture settlement')
  with self._lock:
   s,tickets=self._validate()
   if now<s['clock']:raise LedgerRefused('fixture clock rollback')
   if tickets.get(ticket.nonce) is not ticket:raise LedgerRefused('unknown fixture ticket')
   r=s['receipts'][ticket.nonce]
   if r['expires']<=now:raise LedgerRefused('expired fixture ticket') # no count refund
   if r['status']!='pending':
    s['clock']=now;self._publish(s,tickets);return result('already_settled')
   for i,(k,g) in enumerate(r['pairs']):
    a=s['keys'].get(k)
    if a is None or a['gen']!=g:continue
    if action=='success' and i==0:
     s['keys'].pop(k);s['key_queue'].remove(k) # clears unrelated same-user generation failures intentionally
    elif action=='refund' or action=='success' and i==1:a['fails']=max(0,a['fails']-1)
   r['status']=action;s['clock']=now;inspected=self._prune(s,tickets,now);self._publish(s,tickets)
   return result('settled',inspected=inspected)
 def prune(self,now):
  epoch(now)
  if now>4133980799-TTL-MAX_LOCK:raise LedgerRefused("fixture clock upper bound")
  with self._lock:
   s,tickets=self._validate()
   if now<s['clock']:raise LedgerRefused('fixture clock rollback')
   inspected=self._prune(s,tickets,now);s['clock']=now;self._publish(s,tickets);return result('pruned',inspected=inspected)

class Facade:
 def __init__(self,ledger):
  if type(ledger) is not Ledger:raise LedgerRefused('exact fixture ledger required')
  self.ledger=ledger
 def admit(self,operation,username,client,now):return Ledger.admit(self.ledger,operation,username,client,now)
 def settle(self,ticket,action,now):return Ledger.settle(self.ledger,ticket,action,now)
 def prune(self,now):return Ledger.prune(self.ledger,now)

def epoch(now):
 if type(now) not in (int,float) or not 0<=now<=4133980799 or not math.isfinite(now):raise LedgerRefused('invalid fixture clock')
 return now

def result(state,**values):return {'state':state,'scope':'same_process_memory_fixture','network':False,'writes':False,'production_limiter':False,**values}
