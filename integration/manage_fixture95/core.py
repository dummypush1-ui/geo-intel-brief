"""Partial supplied-data admin fixture. RAM only, no runtime effects."""
from copy import deepcopy
from threading import RLock
import json
class Refused(ValueError): pass
# Read-only source evidence: former .md paths resolve in root README sections. Values are authored fixture settings, not live config.
_CATALOG_ROWS=(
 {'id':'nilgiri_watch','evidence':['integration/FEATURE_STATUS.md','integration/nilgiri_watch_fixture/LIMITS.md'],'original_default':'off in isolated fixture92; no production default verified','requested':'unspecified','last_known_configured':'unknown','effective':'unwired_unknown','reason':'Production transport, persistence and activation unverified','settings':{'cadence_seconds':3600},'ranges':{'cadence_seconds':[3600,86400]},'units':{'cadence_seconds':'seconds'}},
 {'id':'tenders','evidence':['integration/FEATURE_STATUS.md'],'original_default':'Earlier references differ; final source absent','requested':'unspecified','last_known_configured':'unknown','effective':'unwired_unknown','reason':'Exact source baseline not selected; no collector integration','settings':{'max_items':20},'ranges':{'max_items':[1,100]},'units':{'max_items':'items per fixture batch'}},
 {'id':'finder','evidence':['integration/FEATURE_STATUS.md','integration/FINDER_NETWORK_LIMITS.md'],'original_default':'Network preview off; original Finder retained','requested':'unspecified','last_known_configured':'unknown','effective':'unwired_unknown','reason':'This fixture has no runtime control connection','settings':{'display_limit':20},'ranges':{'display_limit':[1,100]},'units':{'display_limit':'supplied display rows'}},
 {'id':'stored_news','evidence':['integration/FEATURE_STATUS.md','integration/GEO_ONLY_LIMITS.md'],'original_default':'Explicit read gates default off','requested':'unspecified','last_known_configured':'unknown','effective':'unwired_unknown','reason':'This fixture does not read or control stored news','settings':{'display_limit':100},'ranges':{'display_limit':[1,100]},'units':{'display_limit':'supplied display rows'}},
)
CATALOG=json.dumps(_CATALOG_ROWS,sort_keys=True).encode("utf-8")
del _CATALOG_ROWS
def integer(x):
 if type(x)is not int:raise Refused('exact integer required')
 return x
class Fixture:
 def __init__(self,authorize=None):
  if authorize is not None and not callable(authorize):raise Refused('supplied authorization required')
  self._authorize=authorize;self._lock=RLock();self._revision=0;self._history=[]
  self._rows={x['id']:deepcopy(dict(x,registered=False,activation_enabled=False))for x in json.loads(CATALOG)}
 def _auth(self,principal):
  # Principal is trusted caller context, never a mutation JSON admin flag.
  try:ok=self._authorize is not None and self._authorize(principal)is True
  except Exception:ok=False
  if not ok:raise Refused('authorization denied')
 def view(self,principal):
  with self._lock:
   self._auth(principal)
   return self._snapshot()
 def _snapshot(self):
  return deepcopy({'scope':'PARTIAL catalog; RAM-only fixture, no runtime effects','revision':self._revision,'rows':list(self._rows.values()),'history':self._history,'uninventoried':'Other capabilities not yet audited; unknown Add refused'})
 def mutate(self,principal,expected_revision,operations):
  with self._lock:
   self._auth(principal)
   if integer(expected_revision)!=self._revision:raise Refused('stale revision')
   if type(operations)is not list or not 1<=len(operations)<=16:raise Refused('closed batch')
   pending=deepcopy(self._rows);seen=set()
   for op in operations:
    if type(op)is not dict or any(type(k)is not str for k in op) or set(op)!={'id','action','value'}:raise Refused('closed operation')
    i=op['id'];a=op['action'];v=op['value']
    if type(i)is not str or i not in pending or type(a)is not str:raise Refused('unknown adapter or action')
    if i in seen:raise Refused('duplicate adapter')
    seen.add(i);row=pending[i]
    if a=='register':
     if v is not None:raise Refused('register value')
     row['registered']=True
    elif a=='request':
     if type(v)is not str or v not in ('on','off'):raise Refused('requested intent')
     row['requested']=v+'_not_applied'
    elif a=='tune':
     if type(v)is not dict or not v or any(type(k)is not str or k not in row['ranges']for k in v):raise Refused('closed tune fields')
     for k,n in v.items():
      lo,hi=row['ranges'][k]
      if not lo<=integer(n)<=hi:raise Refused('tuning range')
      row['settings'][k]=n
    else:raise Refused('activation unavailable')
   prior=deepcopy(self._rows);self._rows=pending;self._revision+=1
   self._history.append({'revision':self._revision,'kind':'edit','prior':prior});self._history=self._history[-8:]
   return self._snapshot()
 def undo(self,principal,expected_revision,target_revision):
  with self._lock:
   self._auth(principal)
   if integer(expected_revision)!=self._revision:raise Refused('stale revision')
   integer(target_revision)
   if target_revision!=self._revision:raise Refused('undo only current edit')
   if not self._history or self._history[-1]['revision']!=target_revision or self._history[-1]['kind']!='edit':raise Refused('no reversible current edit')
   prior=deepcopy(self._rows);restored=deepcopy(self._history[-1]['prior']);self._rows=restored;self._revision+=1
   self._history.append({'revision':self._revision,'kind':'undo','prior':prior});self._history=self._history[-8:]
   return self._snapshot()
