"""D2b1 pure target/scope/ledger fixture, no News/store/route/IO wiring."""
from copy import deepcopy
import re,math
class Refused(ValueError):pass
class Expired(Exception):pass
class Busy(Exception):pass

def target(model,params,manifest,matcher_version):
 if type(params)is not dict or set(params)!={'system','edition','code'}:raise Refused('Exact target fields')
 caps={'system':3,'edition':100,'code':12}
 if any(type(v)is not str or not 1<=len(v)<=caps[k]for k,v in params.items()):raise Refused('Typed target')
 if not re.fullmatch('[A-Z]{2,3}',params['system'])or not re.fullmatch('[0-9]{2,12}',params['code']):raise Refused('Target identity')
 if type(manifest)is not str or not re.fullmatch('[a-f0-9]{64}',manifest)or type(matcher_version)is not str or not re.fullmatch('[A-Za-z0-9_.-]{1,40}',matcher_version):raise Refused('Version binding')
 resolved=model.resolve(params['code'],params['system'],params['edition'])
 if type(resolved)is not dict or resolved.get('state')!='resolved':return {'state':'target_unavailable','resolution':resolved.get('state')if type(resolved)is dict else'invalid','target':None}
 rows=resolved.get('items')
 if type(rows)is not list or len(rows)!=1 or type(rows[0])is not dict or any(rows[0].get(k)!=v for k,v in params.items()):raise Refused('Exact resolved identity')
 return {'state':'resolved','target':deepcopy(rows[0]),'manifest':manifest,'matcher_version':matcher_version}

class Ledger:
 """Pure central reservation/stream fixture, no actual News state or cleaner."""
 def __init__(self):self.rows={};self.streams={}
 def validate(self,key,scope,now):
  if type(key)is not str or not re.fullmatch('[A-Za-z0-9_-]{43}',key):raise Refused('Opaque capability required')
  if scope is not None and(type(scope)is not str or not re.fullmatch('[A-Za-z0-9_-]{43}',scope)):raise Refused('Private issued scope required')
  if type(now)not in(int,float)or not math.isfinite(now)or now<0:raise Refused('Finite clock required')
 def total(self):return len(self.streams)+sum(k not in self.streams for k,r in self.rows.items()if r['scope']is not None)
 def admit(self,key,scope,now):
  self.validate(key,scope,now);self.expire(now)
  if key in self.rows:raise Refused('Duplicate capability')
  if self.total()>=16 or scope is not None and sum(r['scope']is not None for r in self.rows.values())>=4:raise Busy()
  self.rows[key]={'scope':scope,'used':now,'born':now,'cursor_closed':False,'release_count':0}
  self.streams[key]=True
 def own(self,key,scope,now):
  self.validate(key,scope,now)
  r=self.rows.get(key)
  if r is None or r['scope']!=scope:raise Expired()
  if now-r['used']>=120 or now-r['born']>=1800:self.drop(key);raise Expired()
  return r
 def touch(self,key,scope,now):r=self.own(key,scope,now);r['used']=now
 def finish(self,key,scope,now,first_page=False):
  r=self.own(key,scope,now);r['cursor_closed']=True;r['used']=now
  if first_page:
   self.streams.pop(key,None)
   if scope is None:self.drop(key)
  # D reservation stays admitted even when first-page EOF drops parent entry.
 def parent_expired(self,key):return self.drop(key)
 def drop(self,key):
  self.streams.pop(key,None);r=self.rows.pop(key,None)
  if r is not None:r['release_count']+=1
  return r
 def expire(self,now):
  if type(now)not in(int,float)or not math.isfinite(now)or now<0:raise Refused('Finite clock required')
  for key,r in list(self.rows.items()):
   if now-r['used']>=120 or now-r['born']>=1800:self.drop(key)
 def close(self):
  for key in list(self.rows):self.drop(key)
  self.streams.clear()

def head():return {'state':'metadata_only'},200

def bound_resume(ledger,key,scope,now,binding,current,advance):
 ledger.own(key,scope,now)
 if binding!=current:
  ledger.drop(key);raise Expired()
 return scoped_parent(ledger,key,scope,now,advance)

def scoped_parent(ledger,key,scope,now,advance):
 ledger.own(key,scope,now) # Before source/cursor advance, never caller scope.
 return advance()

def begin(model,params,manifest,version,parent_open):
 result=target(model,params,manifest,version)
 if result['state']!='resolved':return result
 return dict(result,parent=parent_open(deepcopy(result)))
