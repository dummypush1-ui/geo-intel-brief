"""Unwired D2b3 actual News-map admission bridge. No app routes/client creation.
Internal broker scopes are server-issued; token opacity is not authentication.
All ledger operations use the existing News operational lock, one cleaner.
"""
import secrets,math,re,json
from threading import Lock
from integration.code_news_coverage_contract_prep import serialize
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
class ResolveQuota:
 def __init__(self):self.lock=Lock();self.minute=None;self.attempts=0
 def admit(self,now):
  if not self.lock.acquire(False):return False
  try:
   minute=int(clock_value(now)//60)
   if minute!=self.minute:self.minute=minute;self.attempts=0
   if self.attempts>=10:return False
   self.attempts+=1;return True
  finally:self.lock.release()
# Shared across broker instances in this worker; no per-user fairness claim.
RESOLVE_QUOTA=ResolveQuota()
class Broker:
 def __init__(self,pages,model,manifest,matcher_version,token_factory=lambda:secrets.token_urlsafe(32),resolve_quota=None):
  if pages.admission is not None:raise Refused('Admission bridge already attached')
  self.pages=pages;self.model=model;self.manifest=manifest;self.version=matcher_version;self.tokens=token_factory;self.replies={};self.calls=0;self.minute=None
  self.resolve_quota=resolve_quota or RESOLVE_QUOTA
  self.ledger=Admission(pages);pages.admission=self.ledger
 def head(self):return {'state':'metadata_only'},200
 def page(self,params=None,scope='',manifest=None,matcher_version=None):
  resolved=None;prepared=None
  if not scope:
   if not self.resolve_quota.admit(self.pages.clock()):return {'state':'resolve_busy','message':'New code scans are busy. Wait before starting another scan.'},429
   try:resolved=resolve_target(self.model,params,self.manifest,self.version)
   except Exception:return {'state':'target_unavailable'},400
   if resolved['state']!='resolved':return resolved,200
   prepared=self._prepare_binding(resolved['target']) # Quota admitted, no slot/News lock yet.
  # One non-blocking actual News lock. No route/client/DB injection here.
  p=self.pages
  if not p.lock.acquire(False):return {'state':'busy'},429
  active=None;new=False
  try:
   if p.stopped.is_set():return {'state':'source_unavailable'},503
   now=clock_value(p.clock());p._expire()
   # Replay payloads are dropped by observing central ledger expiry, not cleaner.
   self._prune_locked()
   if scope:
    if type(scope)is not str or not re.fullmatch('[A-Za-z0-9_-]{43}',scope):return {'state':'expired_restart'},410
    active=next((key for key,r in self.replies.items()if scope in(r['next'],r['last'])),None)
    if active is None or active not in self.ledger.rows:return {'state':'expired_restart'},410
    row=self.ledger.rows[active]
    if manifest!=row['binding']['manifest']or matcher_version!=row['binding']['matcher_version']:
     self.ledger.drop(active);self.replies.pop(active,None);return {'state':'binding_changed_restart'},410
    if params is not None and params!=row['binding']['params']:
     self.ledger.drop(active);self.replies.pop(active,None);return {'state':'target_mismatch'},410
    row['used']=now
    if row['parent']in p.streams:p.streams[row['parent']]['used']=now
    if scope==self.replies[active]['last']:
     row['used']=now
     if row['parent']in p.streams:p.streams[row['parent']]['used']=now
     return self._reply_copy(active,deepcopy(self.replies[active]['body'])),200
   else:
    active=self.tokens();new=True
    binding={'params':deepcopy(params),'target':resolved['target'],'manifest':self.manifest,'matcher_version':self.version}
    if prepared is not None:binding['finder_evidence']=prepared
    try:self.ledger.reserve(active,binding,now)
    except PageBusy:return {'state':'shared_capacity'},429
    row=self.ledger.rows[active];self._initialize_locked(active)
   need_parent=self._need_parent_locked(active)
   minute=int(now//60)
   if minute!=self.minute:self.minute=minute;self.calls=0
   if need_parent and self.calls>=20:
    if new:self.ledger.drop(active)
    return {'state':'quota_wait'},429
   reply=None
   if need_parent:
    self.calls+=1
    parent=row['parent'];token='' if parent is None else p.streams[parent]['next']
    reply=p._page_locked(F,100,token,owner_scope=active)
   row=self.ledger.rows.get(active)
   if row is None:raise PageExpired()
   row['used']=now
   body,done=self._finish_locked(active,reply)
   row['done']=done
   next_token=None if done else self.tokens()
   body.update(scope=next_token,next_cursor=next_token,manifest=self.manifest,matcher_version=self.version)
   if len(serialize(body))>524288:raise Refused('Cached reply byte cap')
   self.replies[active]={'next':next_token,'last':scope or None,'body':deepcopy(body)}
   return self._reply_copy(active,body),200
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
  finally:
   self._prune_locked();p.lock.release()

 def _prune_locked(self):
  for old in list(self.replies):
   if old not in self.ledger.rows:self.replies.pop(old,None)
 def _reply_copy(self,active,body):return body
 def _prepare_binding(self,target):return None
 def _initialize_locked(self,active):pass
 def _need_parent_locked(self,active):return True
 def _finish_locked(self,active,reply):
  row=self.ledger.rows[active]
  body={'target':deepcopy(row['binding']['target']),'items':deepcopy(reply['items']),'scan_complete':reply['exhausted'],'evidence_complete':False,'state':'parent_fixture_only','parent_pages_not_relationship_results':True}
  return body,reply['exhausted']
