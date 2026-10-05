"""In-process contract conformance only; pass proves exercised sequences."""
import unittest,copy,pickle,threading
from integration.accounts.limiter import Limiter,Reservation
from integration.accounts.store import MemoryStore
from tests.accounts.test_store_conformance import race
class ReservationTests(unittest.TestCase):
 def setUp(self):self.s=MemoryStore();self.now=[1000];self.l=Limiter(self.s,b'fixture-only'*4,lambda:self.now[0])
 def begin(self):return self.l.begin('login','alice','client')[0]
 def test_original_repeated_refund_regression(self):
  a=self.begin();b=self.begin();key=self.l.user_key('login','alice');self.l.refund(a);self.assertEqual(self.s.get_attempts(key)['fails'],1)
  self.l.refund(a);self.assertEqual(self.s.get_attempts(key)['fails'],1)
 def test_concurrent_same_refund_once(self):
  a=self.begin();self.begin();key=self.l.user_key('login','alice');race([lambda:self.l.refund(a) for _ in range(8)])
  self.assertEqual(self.s.get_attempts(key)['fails'],1)
 def test_success_refund_orders(self):
  for first,second in (('success','refund'),('refund','success')):
   a=self.begin();getattr(self.l,first)(a);before=copy.deepcopy(self.s.attempts);getattr(self.l,second)(a);self.assertEqual(before,self.s.attempts)
 def test_copy_serialize_handbuilt_foreign_rejected(self):
  a=self.begin()
  for fn in (copy.copy,copy.deepcopy,pickle.dumps):
   with self.assertRaises(TypeError):fn(a)
  before=copy.deepcopy(self.s.attempts)
  with self.assertRaises(TypeError):self.l.refund({'user':('fake','fake'),'client':('fake','fake')})
  forged=Reservation(a.owner,a.token)
  with self.assertRaises(TypeError):self.l.refund(forged)
  other=Limiter(self.s,b'fixture-only'*4,lambda:self.now[0])
  with self.assertRaises(TypeError):other.refund(a)
  self.assertEqual(before,self.s.attempts)
  with self.assertRaises(Exception):a.token='changed'
 def test_stale_generation_consumed_and_pruned(self):
  old=self.begin();self.now[0]+=5000;new=self.begin();before=copy.deepcopy(self.s.attempts)
  self.l.refund(old);self.assertEqual(before,self.s.attempts);self.assertNotIn(old.token,self.l._outstanding)
  self.l.success(new);self.assertEqual(self.l._outstanding,{})
 def test_outstanding_cap_and_rollover_pruning(self):
  self.l._reservation_cap=2;a=self.begin();b=self.begin();self.assertIsNone(self.begin());self.assertEqual(len(self.l._outstanding),2)
  self.now[0]+=5000;self.assertIsNotNone(self.begin());self.assertEqual(len(self.l._outstanding),1)
 def test_store_failure_consumes_token_no_retry(self):
  a=self.begin();old=self.s.update_attempts
  def fail(*args):raise RuntimeError('synthetic store failure')
  self.s.update_attempts=fail
  with self.assertRaises(RuntimeError):self.l.refund(a)
  self.assertNotIn(a.token,self.l._outstanding)
  self.s.update_attempts=old;before=copy.deepcopy(self.s.attempts);self.l.refund(a);self.assertEqual(before,self.s.attempts)

 def test_reentrant_callback_same_token_noop(self):
  a=self.begin();old=self.s.update_attempts;calls=[]
  def callback(key,fn):
   calls.append(key);self.l.refund(a);return old(key,fn)
  self.s.update_attempts=callback;self.l.refund(a)
  self.assertEqual(len(calls),2);self.assertEqual(len(self.l._outstanding),0)
 def test_second_store_callback_failure_no_retry(self):
  for finish in ('success','refund'):
   a=self.begin();old=self.s.update_attempts;calls=[]
   def callback(key,fn):
    calls.append(key)
    if len(calls)==2:raise RuntimeError('second operation failure')
    return old(key,fn)
   self.s.update_attempts=callback
   with self.assertRaises(RuntimeError):getattr(self.l,finish)(a)
   self.s.update_attempts=old;before=copy.deepcopy(self.s.attempts);getattr(self.l,finish)(a)
   self.assertEqual(before,self.s.attempts);self.assertNotIn(a.token,self.l._outstanding)
 def test_foreign_keeps_issuer_and_subclass_rejected(self):
  a=self.begin();other=Limiter(self.s,b'fixture-only'*4,lambda:self.now[0])
  with self.assertRaises(TypeError):other.refund(a)
  self.assertIn(a.token,self.l._outstanding)
  with self.assertRaises(TypeError):
   class Bad(Reservation):pass
 def test_eight_workers_success_refund_legal_counts(self):
  a=self.begin();b=self.begin();userkey=self.l.user_key('login','alice');clientkey=self.l.client_key('client')
  race([lambda i=i:self.l.success(a) if i%2 else self.l.refund(a) for i in range(8)])
  # Either success cleared user or refund left other reservation. Client once.
  record=self.s.get_attempts(userkey)
  self.assertTrue(record is None or record['fails']==1)
  self.assertEqual(self.s.get_attempts(clientkey)['fails'],1)
  self.assertNotIn(a.token,self.l._outstanding)
 def test_clear_then_refund_consumed(self):
  a=self.begin();self.l._clear(*self.l._outstanding[a.token][1]);before=copy.deepcopy(self.s.attempts)
  self.l.refund(a);self.assertEqual(self.s.get_attempts(self.l.client_key("client"))["fails"],0);self.assertEqual(self.l._outstanding,{})

 def test_real_service_failures_no_global_reservation_exhaustion(self):
  from tests.accounts.test_hardening import make,pre,ORIGIN,PW,signup
  svc,store,clock,hasher=make()
  for n in range(1030):
   token,nonce=pre(svc)
   result=svc.login('unknown'+str(n),'wrong password',token,nonce,'client'+str(n),ORIGIN)
   self.assertEqual(result['error'],'invalid_credentials')
   self.assertEqual(len(svc.limiter._outstanding),0)
  store.add_invite('unused',0)
  for name,invite in (('bad!','invite-code-1'),('alice','short'),('alice','wrong-code-123')):
   token,nonce=pre(svc);svc.signup(name,PW,invite,token,nonce,'signup-client',ORIGIN)
   self.assertEqual(len(svc.limiter._outstanding),0)
 def test_real_reauth_failure_terminal(self):
  from tests.accounts.test_hardening import make,signup,ORIGIN
  from integration.accounts.service import hash_invite
  svc,store,clock,hasher=make();store.add_invite(hash_invite(svc.secret,'invite-code-1'),1)
  account=signup(svc);self.assertTrue(account['ok'])
  result=svc.delete_account(account['session_token'],account['csrf'],'wrong password','client',ORIGIN)
  self.assertEqual(result['error'],'invalid_credentials');self.assertEqual(len(svc.limiter._outstanding),0)
 def test_fail_keeps_count_and_terminal_noop(self):
  a=self.begin();before=copy.deepcopy(self.s.attempts);self.l.fail(a);self.assertEqual(before,self.s.attempts)
  self.assertEqual(self.l._outstanding,{});self.l.refund(a);self.assertEqual(before,self.s.attempts)
 def test_bounded_prune_store_reads(self):
  # Unique keys avoid counter locks; outstanding simulate in-flight operations.
  for n in range(100):self.l.begin('login','user'+str(n),'client'+str(n))
  calls=[];old=self.s.get_attempts
  def get(key):calls.append(key);return old(key)
  self.s.get_attempts=get
  self.l.begin('login','fresh','fresh-client')
  self.assertLessEqual(len(calls),16)
  self.assertLessEqual(len(self.l._prune_queue),self.l._reservation_cap)

 def test_distinct_siblings_settle_current_client_once(self):
  for last in ('success','refund'):
   self.setUp()
   a=self.l.begin('login','alice','a')[0];b=self.l.begin('login','alice','b')[0]
   self.l.success(a);getattr(self.l,last)(b)
   self.assertEqual(self.s.get_attempts(self.l.client_key('b'))['fails'],0)
   self.assertEqual(self.l._outstanding,{})
   before=copy.deepcopy(self.s.attempts);self.l.refund(b);self.assertEqual(before,self.s.attempts)
 def test_twenty_siblings_no_false_client_lock(self):
  self.l.max_user=30
  a=self.l.begin('login','alice','a')[0]
  siblings=[self.l.begin('login','alice','b')[0] for _ in range(19)]
  self.l.success(a)
  for b in siblings:self.l.success(b)
  self.assertEqual(self.s.get_attempts(self.l.client_key('b'))['fails'],0)
  self.assertIsNotNone(self.l.begin('login','other','b')[0])
 def test_nested_begin_prohibited_cap_one(self):
  self.l._reservation_cap=1;old=self.s.update_attempts;seen=[]
  def callback(key,fn):
   with self.assertRaisesRegex(RuntimeError,'nested'):self.l.begin('login','nested','nested')
   seen.append(key);return old(key,fn)
  self.s.update_attempts=callback;self.assertIsNotNone(self.begin())
  self.assertEqual(len(seen),2);self.assertEqual(len(self.l._outstanding),1)
 def test_post_begin_exception_injection(self):
  from tests.accounts.test_hardening import make,signup,pre,ORIGIN,PW
  from integration.accounts.service import hash_invite
  for op,target,method in [('signup','hasher','hash'),('signup','store','create_account'),('signup','store','create_session'),('login','store','get_user'),('login','hasher','verify'),('login','hasher','needs_rehash'),('login','hasher','hash'),('login','store','rehash_password'),('login','store','create_session'),('reauth','store','get_user'),('reauth','hasher','verify')]:
   with self.subTest(op=op,method=method):
    svc,store,clock,hasher=make();store.add_invite(hash_invite(svc.secret,'invite-code-1'),3);signup(svc)
    hasher.needs_rehash=lambda value:True
    error=RuntimeError('injected '+method)
    def explode(*args,**kwargs):raise error
    setattr(store if target=='store' else hasher,method,explode)
    token,nonce=pre(svc)
    with self.assertRaises(RuntimeError) as caught:
     if op=='signup':svc.signup('bob',PW,'invite-code-1',token,nonce,'exception-client',ORIGIN)
     elif op=='login':svc.login('alice',PW,token,nonce,'exception-client',ORIGIN)
     else:svc._reauth({'username':'alice','uid':store.users['alice']['uid']},PW,'exception-client')
    self.assertIs(caught.exception,error);self.assertEqual(svc.limiter._outstanding,{})
 def test_1024_exceptions_then_unrelated_login_recovers(self):
  from tests.accounts.test_hardening import make,signup,login,pre,ORIGIN,PW
  from integration.accounts.service import hash_invite
  svc,store,clock,hasher=make();store.add_invite(hash_invite(svc.secret,'invite-code-1'),1);signup(svc)
  old=store.get_user
  def explode(*args):raise RuntimeError('store injection')
  store.get_user=explode
  for n in range(1025):
   token,nonce=pre(svc)
   with self.assertRaises(RuntimeError):svc.login('unknown'+str(n),PW,token,nonce,'client'+str(n),ORIGIN)
  self.assertEqual(svc.limiter._outstanding,{})
  store.get_user=old;self.assertTrue(login(svc,client='recovered')['ok'])

 def test_second_count_failure_compensates_user(self):
  old=self.s.update_attempts;client=self.l.client_key('client')
  def fail(key,fn):
   if key==client:raise RuntimeError('second count')
   return old(key,fn)
  self.s.update_attempts=fail
  for _ in range(7):
   with self.assertRaises(RuntimeError):self.begin()
  self.s.update_attempts=old
  self.assertEqual(self.s.get_attempts(self.l.user_key('login','alice'))['fails'],0)
  self.assertIsNotNone(self.begin())
 def test_denial_refund_exception_idempotent_compensation(self):
  for after_commit in (False,True):
   self.setUp();self.l.max_client=0;old=self.s.update_attempts;user=self.l.user_key('login','alice')
   state={'fail':True}
   def fail(key,fn):
    if key==user:
     # User count then denial compensating callback.
     before=self.s.get_attempts(key)
     if before and before['fails'] and state['fail']:
      state['fail']=False
      if after_commit:old(key,fn)
      raise RuntimeError('denial refund')
    return old(key,fn)
   self.s.update_attempts=fail
   with self.assertRaises(RuntimeError):self.begin()
   self.s.update_attempts=old
   self.assertEqual(self.s.get_attempts(user)['fails'],0)
   self.l.max_client=20;self.now[0]+=1000
   for _ in range(7):
    a=self.begin();self.assertIsNotNone(a);self.l.refund(a)
 def test_finish_callback_nested_begin_rejected(self):
  a=self.begin();old=self.s.update_attempts
  def cb(key,fn):
   with self.assertRaisesRegex(RuntimeError,'nested'):self.l.begin('login','nested','nested')
   return old(key,fn)
  self.s.update_attempts=cb;self.l.success(a);self.assertEqual(self.l._outstanding,{})

 @unittest.expectedFailure
 def test_UNSUPPORTED_two_limiter_compensation_marker_interleaving(self):
  # Pinned missing shared-instance idempotency. This is intentionally xfail.
  other=Limiter(self.s,b'fixture-only'*4,lambda:self.now[0])
  user=self.l.user_key('login','alice');client=self.l.client_key('client')
  old=self.s.update_attempts;state={'interleave':True}
  # Unrelated failure that must not be erased by A retry.
  prior=self.l.begin('login','alice','prior-client')[0];self.l.fail(prior)
  self.l.max_client=0;other.max_client=0
  def callback(key,fn):
   before=copy.deepcopy(self.s.get_attempts(key))
   result=old(key,fn);after=self.s.get_attempts(key)
   if key==user and before and after and after['fails']<before['fails'] and state['interleave']:
    state['interleave']=False
    # B counts then fails second key and compensates the same user record.
    try:other.begin('login','alice','other-client')
    except RuntimeError:pass
    raise RuntimeError('A compensation committed then raised')
   return result
  self.s.update_attempts=callback
  with self.assertRaises(RuntimeError):self.begin()
  self.s.update_attempts=old
  self.assertEqual(self.s.get_attempts(user)['fails'],1)
