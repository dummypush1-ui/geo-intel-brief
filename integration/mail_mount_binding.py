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


def env_mail_binding_provider(environ,client_factory=None,clock=None):
 """Owner-scoped provider built from the deployment environment.
 Nothing is read or created until the first call, so a bad setting or an
 unreachable database never stops the web app. The six facts are measured
 against the live database on first use and again at most every 100 seconds;
 no environment flag can state them. One client and one MongoMailStore are
 kept for the process (the dispatcher requires the same objects). It never
 sends mail and never writes or provisions anything (reads only)."""
 import time
 from datetime import timedelta,datetime,timezone
 clock=clock or (lambda:int(time.time()))
 import threading
 lock=threading.Lock()
 state={'client':None,'store':None,'checked':0,'close':None}
 scope=('geo_intel','articles','events','mail_control','mail_receipts','displayed','private_receipt_no_send')
 def settings():
  for name in ('MAIL_MONGODB_URI','MAIL_V1_HEADER_SECRET','MAIL_V1_CHANNEL','MAIL_OWNER_REFERENCE','MAIL_SOURCE_REFERENCE'):
   if type(environ.get(name))is not str or not environ[name]:raise MailBindingRefused('Mail setting required: '+name)
 def measure(client,now):
  from feature_mail_mount.reports import FIELDS,_articles,_rows
  hello=client.admin.command('hello')
  if not (hello.get('setName') and hello.get('logicalSessionTimeoutMinutes')):raise MailBindingRefused('Transactions unavailable')
  db=client['geo_intel']
  status=client.admin.command({'connectionStatus':1,'showPrivileges':True})
  # Collections and actions the real flow uses: reads of articles/events/control,
  # receipt inserts and updates, control updates, article mark updates.
  need={('articles','find'),('articles','update'),('events','find'),('mail_control','find'),('mail_control','update'),
        ('mail_receipts','find'),('mail_receipts','insert'),('mail_receipts','update')}
  have=set()
  for p in status.get('authInfo',{}).get('authenticatedUserPrivileges',[]):
   res=p.get('resource',{})
   if res.get('db')in('geo_intel','') and res.get('collection','')in('articles','events','mail_control','mail_receipts',''):
    for a in p.get('actions',[]):have.add((res.get('collection') or '*',a))
  for c,a in need:
   if (c,a) not in have and ('*',a) not in have:raise MailBindingRefused('Mail privilege not proven: '+c+' '+a)
  control=db['mail_control'].find_one({'_id':'mail-v1'},max_time_ms=2000)
  if (type(control)is not dict or set(control)!={'_id','schema','revision','channel_id','policy','active'} or control['_id']!='mail-v1'
      or type(control['schema'])is not int or control['schema']!=1 or type(control['revision'])is not int or control['revision']<0
      or control['policy']!='displayed' or control['channel_id']!=environ['MAIL_V1_CHANNEL'] or type(control['active'])is not dict):
   raise MailBindingRefused('Mail control row not provisioned')
  # Run the renderer's own canonical schema and UTC-date validation on the most
  # recent rows. This samples recent rows only; it does not prove every row.
  cutoff=(datetime.fromtimestamp(now,timezone.utc)-timedelta(days=7)).isoformat()
  rows=_rows(db['articles'].find({'created_at':{'$gte':cutoff}},{k:1 for k in FIELDS}).sort([('created_at',-1),('_id',-1)]).limit(20).max_time_ms(2000),20)
  if not rows:raise MailBindingRefused('No recent articles to verify schema')
  try:_articles(rows)
  except ValueError:raise MailBindingRefused('Article schema or canonical UTC dates not verified') from None
 def provider():
  from feature_mail_mount.store import MongoMailStore
  settings()
  now=clock()
  with lock: # init only; the network measurement below runs outside the lock
   if state['client'] is None:
    factory=client_factory
    if factory is None:
     from integration.collector197_http import create_writer_client as factory
    c=factory(environ['MAIL_MONGODB_URI'])
    state['client']=c;state['close']=lambda:c.close()
   client=state['client'];first=state['store'] is None;due=now-state['checked']>=100
  if first or due:
   try:measure(client,now)
   except MailBindingRefused:raise
   except Exception:raise MailBindingRefused('Mail database checks unavailable') from None
   with lock:
    if state['store'] is None:
     state['store']=MongoMailStore(client,review={'mapping':('geo_intel','articles','events','mail_control','mail_receipts'),'transaction_supported':True,'source_schema_verified':True,'write_permission':True,'control_provisioned':True,'iso_article_dates_verified':True},channel_id=environ['MAIL_V1_CHANNEL'],marking_policy='displayed')
    state['checked']=max(state['checked'],now)
  with lock:
   store=state['store'];close=state['close']
  return MailBinding(store=store,secret=environ['MAIL_V1_HEADER_SECRET'],clock=clock,close=close,observed_at=now,expires_at=now+100,
   owner_reference=environ['MAIL_OWNER_REFERENCE'],source_reference=environ['MAIL_SOURCE_REFERENCE'],scope=scope,verified=(True,)*6)
 provider.close=lambda:state['client'].close() if state['client'] is not None else None
 return provider

class LazyMailDispatcher:
 """Mail routes come up on first successful request; the public app never waits
 on, or fails with, the mail database. Failures answer 503 and never resend."""
 def __init__(self,public,provider,clock):
  self.public=public;self.provider=provider;self.clock=clock;self.binding=None;self.private=None
 def close(self):
  close=getattr(self.provider,'close',None)
  if close:close()
 def __call__(self,environ,start_response):
  if not environ.get('PATH_INFO','').startswith('/internal/mail/v1/'):return self.public(environ,start_response)
  try:
   fresh=resolve_binding(self.provider,self.clock)
   if self.binding is None:
    from flask import Flask
    from feature_mail_mount.composition import compose_private_mail
    private=Flask('production_private_mail',static_folder=None);private.logger.disabled=True
    compose_private_mail(private,enabled=True,store=fresh.store,secret=fresh.secret,clock=fresh.clock)
    self.binding=fresh;self.private=private.wsgi_app
   elif (fresh.store is not self.binding.store or fresh.secret!=self.binding.secret or fresh.clock is not self.binding.clock or fresh.close is not self.binding.close or fresh.owner_reference!=self.binding.owner_reference or fresh.source_reference!=self.binding.source_reference or fresh.scope!=self.binding.scope):
    raise MailBindingRefused('Startup capability binding must remain unchanged')
  except Exception:
   start_response('503 Service Unavailable',[('Content-Type','application/json'),('Cache-Control','no-store')]);return [b'{"error":"mail_binding_unavailable","retry_send":false}']
  return self.private(environ,start_response)
