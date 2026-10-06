"""Injected transaction-backed bounded account-state store. No activation.

One pre-provisioned state document in geo_intel/accounts_state. Each public
AccountStore operation runs inside an explicit Mongo transaction with no retry.
MemoryStore semantics are reused within that transaction, not shared in memory.
Dedicated source/schema/role/transaction capability review and owner permission
are required before live use. No clients, indexes, credentials or timers created.
"""
import json,math,threading,time
from copy import deepcopy
from .store import AccountStore,MemoryStore,invite_value

TABLES=('users','by_uid','sessions','attempts','invites','settings')
METHODS=('create_account','get_user','delete_account','replace_password','rehash_password','create_session','touch_session','delete_session','update_attempts','get_attempts','delete_attempts','add_invite','get_settings','put_settings','purge')
class MongoStoreUnavailable(ValueError):pass
class MongoStoreInvalid(ValueError):pass

def _copy(value,depth=0,budget=None):
 if budget is None:budget=[0]
 budget[0]+=1
 if depth>16 or budget[0]>100000:raise ValueError()
 if value is None or type(value) in (str,bool,int,float):
  if type(value) is str and len(value)>16000:raise ValueError()
  if type(value) is float and not math.isfinite(value):raise ValueError()
  if type(value) is int and not -2**53<=value<=2**53:raise ValueError()
  return value
 if type(value) is list and len(value)<=10000:return [_copy(x,depth+1,budget) for x in list(value)]
 if type(value) is dict and len(value)<=10000:
  items=list(value.items())
  if any(type(k) is not str or len(k)>512 for k,v in items):raise ValueError()
  return {k:_copy(v,depth+1,budget) for k,v in items}
 raise ValueError()

def _state(value):
 state=_copy(value)
 if type(state) is not dict or set(state)!=set(TABLES) or any(type(state[k]) is not dict for k in TABLES):raise ValueError()
 if len(state['users'])>50 or len(state['by_uid'])!=len(state['users']) or len(state['sessions'])>500 or len(state['attempts'])>10000 or len(state['invites'])>1000 or len(state['settings'])>50:raise ValueError()
 for value in state['invites'].values():invite_value(value)
 for name,user in state['users'].items():
  if type(user) is not dict or user.get('username')!=name or type(user.get('uid')) is not str or state['by_uid'].get(user['uid'])!=name:raise ValueError()
 for uid,setting in state['settings'].items():
  if uid not in state['by_uid'] or type(setting) is not dict:raise ValueError()
 for session in state['sessions'].values():
  if type(session) is not dict or session.get('uid') not in state['by_uid']:raise ValueError()
 if len(json.dumps(state,allow_nan=False,ensure_ascii=False,separators=(',',':')).encode('utf-8'))>2*1024*1024:raise ValueError()
 return state

class MongoAccountStore(AccountStore):
 def __init__(self,client,*,review,clock=time.time):
  keys={'mapping','state_schema_verified','transaction_supported','write_permission'}
  if type(review) is not dict or any(type(k) is not str for k in review) or set(review)!=keys or type(review.get('mapping')) is not tuple or len(review['mapping'])!=2 or any(type(x) is not str for x in review['mapping']) or review['mapping']!=('geo_intel','accounts_state') or any(review[k] is not True for k in keys-{'mapping'}):raise MongoStoreUnavailable('Explicit account source review required')
  if not callable(clock):raise MongoStoreInvalid('Account store invalid clock')
  self._client=client;self._local=threading.local();self._clock=clock
 def _operation(self,name,args):
  if getattr(self._local,'active',False):raise MongoStoreUnavailable('Nested account store operation refused')
  self._local.active=True;session=None;failed=False;committed=False;ended=False;result=None;invalid=False;control=None
  try:
   session=self._client.start_session(causal_consistency=False)
   if session is None:raise ValueError()
   from pymongo.read_concern import ReadConcern
   from pymongo.write_concern import WriteConcern
   session.start_transaction(read_concern=ReadConcern('snapshot'),write_concern=WriteConcern('majority'),max_commit_time_ms=2000)
   collection=self._client['geo_intel']['accounts_state']
   document=collection.find_one({'_id':'account-state-v1'},session=session,max_time_ms=2000)
   if type(document) is not dict or any(type(k) is not str for k in document) or set(document)!={'_id','schema','version','state'} or document['_id']!='account-state-v1' or type(document['schema']) is not int or document['schema']!=1 or type(document['version']) is not int or not 0<=document['version']<2**53:raise ValueError()
   try:before=_state(document['state'])
   except (ValueError,TypeError,OverflowError):raise MongoStoreInvalid('Account state limit or invalid input')
   memory=MemoryStore()
   for key in TABLES:setattr(memory,key,deepcopy(before[key]))
   now=self._clock()
   if type(now) not in (int,float) or not math.isfinite(now):raise MongoStoreInvalid('Account state limit or invalid input')
   # Reclaim expired limiter records before a new key reaches bounded capacity.
   if name not in ('get_user','get_attempts','get_settings'):
    for key,a in list(memory.attempts.items()):
     if type(a) is dict and type(a.get('expires',0)) in (int,float) and a.get('expires',0)<=now:memory.attempts.pop(key,None)
    # Exhausted invites cannot be used again; provisioning may replace a hash.
    for key,uses in list(memory.invites.items()):
     if type(uses) is int and uses<=0:memory.invites.pop(key,None)
   # Trusted service callback update_attempts executes once, never driver retry.
   result=getattr(memory,name)(*args)
   try:after=_state({key:getattr(memory,key) for key in TABLES})
   except (ValueError,TypeError,OverflowError):raise MongoStoreInvalid('Account state limit or invalid input')
   if after!=before:
    receipt=collection.replace_one({'_id':'account-state-v1','version':document['version']},{'_id':'account-state-v1','schema':1,'version':document['version']+1,'state':after},upsert=False,session=session)
    acknowledged=receipt.acknowledged;matched=receipt.matched_count
    if acknowledged is not True or type(matched) is not int or matched!=1:raise ValueError()
   session.commit_transaction();committed=True
  except BaseException as exc:
   failed=True
   invalid=type(exc) is MongoStoreInvalid
   if not isinstance(exc,Exception):control=exc
  finally:
   if session is not None:
    if not committed:
     try:session.abort_transaction()
     except BaseException as exc:
      if not isinstance(exc,Exception):control=exc
    try:session.end_session();ended=True
    except BaseException as exc:
     failed=True
     if not isinstance(exc,Exception):control=exc
   self._local.active=False
  if control is not None:raise control
  if invalid:raise MongoStoreInvalid('Account state limit or invalid input')
  if failed:raise MongoStoreUnavailable('Account store outcome unavailable; do not retry')
  return result
 def create_account(self,username,record,invite_hash,max_users,now=None):return self._operation('create_account',(username,record,invite_hash,max_users,now))
 def get_user(self,username):return self._operation('get_user',(username,))
 def delete_account(self,username,uid,pwv,session_hash,now):return self._operation('delete_account',(username,uid,pwv,session_hash,now))
 def replace_password(self,uid,pwv,new_hash,session_hash,now):return self._operation('replace_password',(uid,pwv,new_hash,session_hash,now))
 def rehash_password(self,uid,pwv,new_hash):return self._operation('rehash_password',(uid,pwv,new_hash))
 def create_session(self,token_hash,record,uid,pwv,max_sessions):return self._operation('create_session',(token_hash,record,uid,pwv,max_sessions))
 def touch_session(self,token_hash,now,idle_ttl):return self._operation('touch_session',(token_hash,now,idle_ttl))
 def delete_session(self,token_hash):return self._operation('delete_session',(token_hash,))
 def update_attempts(self,key,fn):return self._operation('update_attempts',(key,fn))
 def get_attempts(self,key):return self._operation('get_attempts',(key,))
 def delete_attempts(self,key):return self._operation('delete_attempts',(key,))
 def add_invite(self,code_hash,uses=1,expires_at=None):return self._operation('add_invite',(code_hash,uses,expires_at))
 def get_settings(self,uid):return self._operation('get_settings',(uid,))
 def put_settings(self,uid,doc,expected_version,session_hash,now):return self._operation('put_settings',(uid,doc,expected_version,session_hash,now))
 def purge(self,now):return self._operation('purge',(now,))
