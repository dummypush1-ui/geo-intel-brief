"""In-memory specification tests ONLY. No DB, HTTP, imports of legacy or jobs.
Not a durable production ledger/queue/collector. Never runs supplied code.
"""
import hashlib,hmac,re
from threading import Lock

class Refused(ValueError):pass
class FixtureLedger:
 def __init__(self,token,profile):
  if type(token)is not str or len(token)<48 or type(profile)is not str or not re.fullmatch(r'[a-z0-9_-]{1,64}',profile):raise Refused('Fixture configuration invalid')
  self._token=token;self.profile=profile;self.jobs={};self.lock=Lock();self.fence=0;self.active=None
 def authenticate(self,header):
  if type(header)is not str or not hmac.compare_digest(header.encode(),('Bearer '+self._token).encode()):raise Refused('Unauthorized')
 def submit(self,header,body,now):
  self.authenticate(header)
  if type(now)is not int or now<0 or type(body)is not dict or set(body)!={'profile','nonce','created_at'} or body['profile']!=self.profile or type(body['nonce'])is not str or not re.fullmatch(r'[a-zA-Z0-9_-]{20,80}',body['nonce'])or type(body['created_at'])is not int or abs(now-body['created_at'])>300:raise Refused('Exact bounded request required')
  key=hashlib.sha256((self.profile+'\n'+body['nonce']).encode()).hexdigest()
  with self.lock:
   if key not in self.jobs:self.jobs[key]={'phase':'accepted','fence':None,'lease_until':None,'counts':{}}
   return key,dict(self.jobs[key])
 def claim(self,key,now):
  with self.lock:
   if type(now)is not int or now<0 or key not in self.jobs or self.jobs[key]['phase']!='accepted' or self.active is not None:raise Refused('No claim')
   self.fence+=1;self.active=key;j=self.jobs[key];j.update(phase='running',fence=self.fence,lease_until=now+120);return self.fence
 def transition(self,key,fence,phase,now,counts=None):
  successors={'running':{'fetch_complete','failed_before_write'},'fetch_complete':{'prepare_complete','failed_before_write'},'prepare_complete':{'write_started','failed_before_write'},'write_started':{'completed','uncertain_after_write'}}
  if type(counts)is not dict or len(counts)>8 or any(k not in ('fetched','prepared','attempted','inserted','duplicate','failed','uncertain')or type(v)is not int or not 0<=v<=1000 for k,v in counts.items()):raise Refused('Aggregate counts only')
  with self.lock:
   j=self.jobs.get(key)
   if not j or self.active!=key or type(fence)is not int or j['fence']!=fence or type(now)is not int or now>=j['lease_until']or phase not in successors.get(j['phase'],set()):raise Refused('Invalid fenced transition')
   j.update(phase=phase,counts=dict(counts))
   if phase in ('completed','failed_before_write'):self.active=None
 def reconcile_expired(self,key,now):
  # Expiry alone NEVER transfers the active claim. Operator/process-stop proof
  # belongs to durable implementation, not supplied here.
  with self.lock:
   j=self.jobs.get(key)
   if not j or type(now)is not int or j['lease_until']is None or now<j['lease_until']:raise Refused('Lease not expired')
   j['phase']='uncertain_after_write'if j['phase']=='write_started'else'interrupted'
   return dict(j)
