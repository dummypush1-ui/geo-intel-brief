"""Unwired D2b3 actual News-map admission bridge. No app routes/client creation.
Internal broker scopes are server-issued; token opacity is not authentication.
All ledger operations use the existing News operational lock, one cleaner.
"""
import secrets,math,re
from copy import deepcopy
from integration.news_pages import PageBusy,PageExpired,PageUnavailable
from integration.code_news_scope_prep import target as resolve_target,Refused
F={'project':'geo','query':'','category':'','country':'','sort':'newest'}
class Restart(Exception):pass

def clock_value(now):
 if type(now)not in(int,float)or not math.isfinite(now)or now<0:raise Refused('Finite clock required')
 return now
class Admission:
 def __init__(self,pages):self.pages=pages;self.rows={}
 def total(self):return len(self.pages.streams)+sum(r['parent']not in self.pages.streams for r in self.rows.values())
 def can_open(self,scope):
  if scope is None:return self.total()<16
  row=self.rows.get(scope)
  return row is not None and row['parent'] is None and self.total()<=16
 def reserve(self,scope,binding,now):
  clock_value(now)
  if type(scope)is not str or not re.fullmatch('[A-Za-z0-9_-]{43}',scope)or scope in self.rows:raise Refused('Private unique scope required')
  if len(self.rows)>=4 or self.total()>=16:raise PageBusy()
  self.rows[scope]={'parent':None,'used':now,'born':now,'binding':deepcopy(binding),'done':False,'expired':False}
 def bind_parent(self,scope,key):
  row=self.rows.get(scope)
  if row is None or row['parent']is not None:raise Refused('Owned parent binding')
  row['parent']=key
 def parent_dropped(self,key,reason):
  for scope,row in list(self.rows.items()):
   if row['parent']==key:
    if reason=='first_eof':row['parent']=None;row['done']=True
    else:self.rows.pop(scope,None)
 def drop(self,scope):
  row=self.rows.pop(scope,None)
  if row and row['parent']in self.pages.streams:self.pages._drop(row['parent'])
 def expire(self,now):
  clock_value(now)
  for scope,row in list(self.rows.items()):
   if now-row['used']>=120 or now-row['born']>=1800:self.drop(scope)
 def close(self):
  for scope in list(self.rows):self.drop(scope)
class Broker:
 def __init__(self,pages,model,manifest,matcher_version,token_factory=lambda:secrets.token_urlsafe(32)):
  if pages.admission is not None:raise Refused('Admission bridge already attached')
  self.pages=pages;self.model=model;self.manifest=manifest;self.version=matcher_version;self.tokens=token_factory;self.replies={};self.calls=0;self.minute=None
  self.ledger=Admission(pages);pages.admission=self.ledger
 def head(self):return {'state':'metadata_only'},200
 def page(self,params=None,scope='',manifest=None,matcher_version=None):
  resolved=None
  if not scope:
   try:resolved=resolve_target(self.model,params,self.manifest,self.version)
   except Exception:return {'state':'target_unavailable'},400
   if resolved['state']!='resolved':return resolved,200
  # One non-blocking actual News lock. No route/client/DB injection here.
  p=self.pages
  if not p.lock.acquire(False):return {'state':'busy'},429
  active=None;new=False
  try:
   if p.stopped.is_set():return {'state':'source_unavailable'},503
   now=clock_value(p.clock());p._expire()
   # Replay payloads are dropped by observing central ledger expiry, not cleaner.
   for old in list(self.replies):
    if old not in self.ledger.rows:self.replies.pop(old,None)
   if scope:
    if type(scope)is not str or not re.fullmatch('[A-Za-z0-9_-]{43}',scope):return {'state':'expired_restart'},410
    active=next((key for key,r in self.replies.items()if scope in(r['next'],r['last'])),None)
    if active is None or active not in self.ledger.rows:return {'state':'expired_restart'},410
    row=self.ledger.rows[active]
    if manifest!=row['binding']['manifest']or matcher_version!=row['binding']['matcher_version']:
     self.ledger.drop(active);self.replies.pop(active,None);return {'state':'binding_changed_restart'},410
    if params is not None and params!=row['binding']['params']:
     self.ledger.drop(active);self.replies.pop(active,None);return {'state':'target_mismatch'},410
    if scope==self.replies[active]['last']:
     row['used']=now
     if row['parent']in p.streams:p.streams[row['parent']]['used']=now
     return deepcopy(self.replies[active]['body']),200
   else:
    active=self.tokens();new=True
    binding={'params':deepcopy(params),'target':resolved['target'],'manifest':self.manifest,'matcher_version':self.version}
    try:self.ledger.reserve(active,binding,now)
    except PageBusy:return {'state':'shared_capacity'},429
    row=self.ledger.rows[active]
   minute=int(now//60)
   if minute!=self.minute:self.minute=minute;self.calls=0
   if self.calls>=20:
    if new:self.ledger.drop(active)
    return {'state':'quota_wait'},429
   self.calls+=1
   parent=row['parent'];token='' if parent is None else p.streams[parent]['next']
   # Internal directly under held lock, never recursively invoke public page().
   reply=p._page_locked(F,100,token,owner_scope=active)
   row=self.ledger.rows.get(active)
   if row is None:raise PageExpired()
   row['used']=now;row['done']=reply['exhausted']
   next_token=None if reply['exhausted']else self.tokens()
   body={'scope':next_token,'next_cursor':next_token,'target':deepcopy(row['binding']['target']),'items':deepcopy(reply['items']),'scan_complete':reply['exhausted'],'evidence_complete':False,'manifest':self.manifest,'matcher_version':self.version,'state':'parent_fixture_only','parent_pages_not_relationship_results':True}
   self.replies[active]={'next':next_token,'last':scope or None,'body':deepcopy(body)}
   return body,200
  except PageExpired:
   if active:self.ledger.drop(active);self.replies.pop(active,None)
   return {'state':'expired_restart'},410
  except PageBusy:
   # Our own internal PageBusy implies admission invariant fault, not retry.
   if active:self.ledger.drop(active);self.replies.pop(active,None)
   return {'state':'admission_fault'},503
  except Exception:
   if active:self.ledger.drop(active);self.replies.pop(active,None)
   return {'state':'source_unavailable'},503
  finally:p.lock.release()
