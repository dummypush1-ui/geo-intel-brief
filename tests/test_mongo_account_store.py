import unittest,threading
from copy import deepcopy
from types import SimpleNamespace
from integration.accounts.mongo_store import MongoAccountStore,MongoStoreUnavailable,MongoStoreInvalid,TABLES
R={'mapping':('geo_intel','accounts_state'),'state_schema_verified':True,'transaction_supported':True,'write_permission':True}
class Session:
 def __init__(self,c):self.c=c;self.backup=None;self.ended=0;self.aborted=0
 def start_transaction(self,**kw):self.kw=kw;self.c.lock.acquire();self.backup=deepcopy(self.c.doc)
 def commit_transaction(self):
  if self.c.fail_commit:raise ValueError('secret-commit')
  self.c.lock.release();self.backup=None
 def abort_transaction(self):
  self.aborted+=1
  if self.backup is not None:self.c.doc=self.backup;self.backup=None;self.c.lock.release()
 def end_session(self):self.ended+=1
class Client:
 def __init__(self):self.doc={'_id':'account-state-v1','schema':1,'version':0,'state':{k:{} for k in TABLES}};self.lock=threading.Lock();self.sessions=[];self.calls=[];self.fail_commit=False
 def start_session(self,**kw):s=Session(self);self.sessions.append(s);return s
 def __getitem__(self,k):self.calls.append(k);return self
 def find_one(self,q,**kw):return deepcopy(self.doc)
 def replace_one(self,q,d,**kw):
  self.calls.append((q,kw));matched=q['version']==self.doc['version']
  if matched:self.doc=deepcopy(d)
  return SimpleNamespace(acknowledged=True,matched_count=int(matched))
def user(uid='u'):return {'uid':uid,'password':'hash','pwv':1,'created':0}
def session(uid='u'):return {'uid':uid,'username':'one','created':0,'expires':100,'idle_expires':50}
class Tests(unittest.TestCase):
 def setUp(self):self.c=Client();self.s=MongoAccountStore(self.c,review=R,clock=lambda:0)
 def test_review_no_effect(self):
  with self.assertRaises(MongoStoreUnavailable):MongoAccountStore(self.c,review={})
  self.assertEqual(self.c.sessions,[])
 def test_persistence_across_adapter_instances(self):
  self.assertEqual(self.s.create_account('one',user(),None,50),'ok');other=MongoAccountStore(self.c,review=R,clock=lambda:0);self.assertEqual(other.get_user('one')['uid'],'u');self.assertTrue(all(x.ended==1 for x in self.c.sessions))
 def test_invite_cap_and_no_burn(self):
  self.s.add_invite('invite',2);self.assertEqual(self.s.create_account('one',user(),'invite',1),'ok');self.assertEqual(self.s.create_account('two',user('v'),'invite',1),'cap');self.assertEqual(self.c.doc['state']['invites']['invite'],1)
 def test_password_and_session_fences_settings_delete(self):
  self.s.create_account('one',user(),None,50);self.assertTrue(self.s.create_session('a',session(),'u',1,10));self.s.create_session('b',session(),'u',1,10)
  self.assertTrue(self.s.put_settings('u',{'version':1},0,'a',1));self.assertFalse(self.s.put_settings('u',{'version':2},0,'a',1))
  self.assertTrue(self.s.replace_password('u',1,'new','a',1));self.assertIsNone(self.s.touch_session('b',1,20));self.assertFalse(self.s.create_session('c',session(),'u',1,10));self.assertFalse(self.s.delete_account('one','u',1,'a',1));self.assertTrue(self.s.delete_account('one','u',2,'a',1));self.assertIsNone(self.s.get_settings('u'))
 def test_commit_failure_rollback_no_retry_redacted(self):
  self.c.fail_commit=True
  with self.assertRaises(MongoStoreUnavailable) as e:self.s.create_account('one',user(),None,50)
  self.assertIsNone(e.exception.__context__);self.assertNotIn('secret',str(e.exception));self.assertEqual(self.c.doc['state']['users'],{});self.assertEqual(len(self.c.sessions),1);self.assertEqual(self.c.sessions[0].ended,1)
 def test_attempt_callback_atomic_once_and_nested_refused(self):
  calls=[]
  self.s.update_attempts('key',lambda old:calls.append(1) or {'n':1,'expires':100});self.assertEqual(calls,[1])
  with self.assertRaises(MongoStoreUnavailable):self.s.update_attempts('key',lambda old:self.s.get_attempts('key'))
  self.assertEqual(self.s.get_attempts('key')['n'],1)
 def test_concurrent_same_username_one_winner(self):
  out=[];errors=[];bar=threading.Barrier(4)
  def worker(i):
   try:bar.wait();out.append(self.s.create_account('one',user(str(i)),None,50))
   except BaseException as e:errors.append(e)
  workers=[threading.Thread(target=worker,args=(i,)) for i in range(4)]
  for t in workers:t.start()
  for t in workers:t.join(5);self.assertFalse(t.is_alive())
  self.assertEqual(errors,[]);self.assertEqual(out.count('ok'),1);self.assertEqual(out.count('taken'),3)
 def test_bad_state_fail_closed(self):
  self.c.doc['state']['users']={'bad':{'uid':'u','username':'bad'}}
  with self.assertRaises(MongoStoreInvalid):self.s.get_user('bad')
  self.assertEqual(self.c.sessions[-1].ended,1)

 def test_expired_attempt_capacity_reclaimed(self):
  self.c.doc['state']['attempts']={str(i):{'expires':0} for i in range(10000)}
  self.s.update_attempts('new',lambda old:{'expires':100,'n':1});self.assertEqual(len(self.c.doc['state']['attempts']),1)
 def test_deterministic_nonjson_and_user_limit_not_outage(self):
  with self.assertRaises(MongoStoreInvalid):self.s.update_attempts('new',lambda old:object())
  for i in range(50):self.s.create_account(str(i),user(str(i)),None,100)
  with self.assertRaises(MongoStoreInvalid):self.s.create_account('overflow',user('overflow'),None,100)
  self.assertEqual(len(self.c.doc['state']['users']),50)
 def test_control_exceptions_cleanup_and_reraise(self):
  for error in (KeyboardInterrupt(),SystemExit(2)):
   with self.assertRaises(type(error)):self.s.update_attempts('x',lambda old:(_ for _ in ()).throw(error))
   self.assertEqual(self.c.sessions[-1].ended,1);self.assertEqual(self.c.sessions[-1].aborted,1)
 def test_transaction_labels_no_retry_no_double_apply(self):
  from pymongo.errors import OperationFailure
  for label,code in (('TransientTransactionError',112),('UnknownTransactionCommitResult',91)):
   class Fail(Session):
    def commit_transaction(self):raise OperationFailure('secret',code,{'errorLabels':[label]})
   class Driver(Client):
    def start_session(self,**kw):s=Fail(self);self.sessions.append(s);return s
   c=Driver();s=MongoAccountStore(c,review=R,clock=lambda:0);calls=[]
   with self.assertRaises(MongoStoreUnavailable):s.update_attempts('x',lambda old:calls.append(1) or {'expires':100})
   self.assertEqual(calls,[1]);self.assertEqual(len(c.sessions),1);self.assertEqual(c.doc['state']['attempts'],{})
 def test_same_invite_four_threads_cap_race(self):
  self.s.add_invite('only',2);bar=threading.Barrier(4);out=[];errors=[]
  def work(i):
   try:bar.wait();out.append(self.s.create_account(str(i),user(str(i)),'only',2))
   except BaseException as e:errors.append(e)
  threads=[threading.Thread(target=work,args=(i,)) for i in range(4)]
  for t in threads:t.start()
  for t in threads:t.join(5);self.assertFalse(t.is_alive())
  self.assertEqual(errors,[]);self.assertEqual(out.count('ok'),2);self.assertEqual(len(self.c.doc['state']['users']),2)

 def test_pure_reads_do_not_persist_expiry_purge(self):
  self.c.doc['state']['attempts']={'old':{'expires':0},'missing':{'n':1}}
  before=deepcopy(self.c.doc);self.s.get_attempts('old');self.s.get_user('absent');self.s.get_settings('absent');self.assertEqual(self.c.doc,before)
  self.s.update_attempts('new',lambda old:{'expires':100});self.assertEqual(set(self.c.doc['state']['attempts']),{'new'})
 def test_all_control_baseexceptions_reraised(self):
  from asyncio import CancelledError
  for error in (CancelledError(),GeneratorExit()):
   with self.assertRaises(type(error)):self.s.update_attempts('x',lambda old:(_ for _ in ()).throw(error))
   self.assertEqual(self.c.sessions[-1].ended,1);self.assertEqual(self.c.sessions[-1].aborted,1)
