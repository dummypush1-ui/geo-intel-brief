"""Injected source-only mail capability. No DB/client/proof creation or send.
Validation checks structure, freshness and scope; it does not prove assertions
or establish authority. A separately reviewed owner-scoped provider must do that.
"""
from dataclasses import dataclass
class MailBindingRefused(ValueError):pass
@dataclass(frozen=True)
class MailBinding:
 store:object
 secret:str
 clock:object
 close:object
 observed_at:int
 expires_at:int
 owner_reference:str
 source_reference:str
 scope:tuple
 verified:tuple
 def validate(self,now):
  if type(now)is not int or type(self.observed_at)is not int or type(self.expires_at)is not int or not 0<=self.observed_at<=now<self.expires_at<=self.observed_at+120:raise MailBindingRefused('Fresh mail binding required')
  for r in (self.owner_reference,self.source_reference):
   if type(r)is not str or not 1<=len(r)<=200 or any(not 33<=ord(c)<=126 for c in r):raise MailBindingRefused('Bounded mail references required')
  if self.scope!=('geo_intel','articles','events','mail_control','mail_receipts','displayed','private_receipt_no_send'):raise MailBindingRefused('Exact mail scope required')
  if type(self.verified)is not tuple or len(self.verified)!=6 or any(v is not True for v in self.verified):raise MailBindingRefused('Independent mail facts required')
  if type(self.secret)is not str or not 48<=len(self.secret)<=256 or any(not 33<=ord(c)<=126 for c in self.secret) or not callable(self.clock) or not callable(self.close):raise MailBindingRefused('Reviewed capabilities required')
  return self

def resolve_binding(provider,clock):
 if not callable(provider) or not callable(clock):raise MailBindingRefused('Injected mail provider required')
 value=provider()
 if type(value)is not MailBinding:raise MailBindingRefused('Exact mail binding required')
 value.validate(clock())
 from feature_mail_mount.store import MongoMailStore
 if not isinstance(value.store,MongoMailStore) or value.store.policy!='displayed':raise MailBindingRefused('Reviewed durable store required')
 return value

class MailDispatcher:
 """Private-path only, renews binding validity; no public route broadening."""
 def __init__(self,public,private,binding,clock,provider):self.public=public;self.private=private;self.binding=binding;self.clock=clock;self.provider=provider
 def __call__(self,environ,start_response):
  path=environ.get('PATH_INFO','')
  if path.startswith('/internal/mail/v1/'):
   try:
    fresh=resolve_binding(self.provider,self.clock)
    if (fresh.store is not self.binding.store or fresh.secret!=self.binding.secret or fresh.clock is not self.binding.clock or fresh.close is not self.binding.close or fresh.owner_reference!=self.binding.owner_reference or fresh.source_reference!=self.binding.source_reference or fresh.scope!=self.binding.scope):raise MailBindingRefused('Startup capability binding must remain unchanged')
   except Exception:
    start_response('503 Service Unavailable',[('Content-Type','application/json'),('Cache-Control','no-store')]);return [b'{"error":"mail_binding_unavailable","retry_send":false}']
   return self.private(environ,start_response)
  return self.public(environ,start_response)
