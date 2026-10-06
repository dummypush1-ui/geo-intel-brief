import unittest,threading,copy,hashlib
from pathlib import Path
from unittest.mock import patch
from integration.accounts.shared_service_fixture import *
from integration.accounts.shared_ledger_fixture import Ticket,RECEIPT_CAP
class Tests(unittest.TestCase):
 def setUp(self):self.h=create_shared_service_fixture();self.a,self.b=self.h.handles
 def login(self,handle=None,user='user001',password='wrong',client='client'):
  a=handle or self.a;p=a.preauth();return a.login(user,password,client,p['csrf'],p['nonce'])
 def counts(self):return [r['fails'] for r in self.h.ledger._state['keys'].values()]
 def test_builder_bound_dummy_and_closed(self):
  self.assertEqual(self.h.hasher.hash_calls,3)
  self.assertIs(self.a._service.store,self.b._service.store)
  self.assertIs(self.a._service.limiter.ledger,self.b._service.limiter.ledger)
  self.assertEqual(self.a.closed_signup()['error'],'forbidden') # CSRF precedes closed-mode exit.
  s=self.a._service;p=s.issue_preauth();self.assertEqual(s.signup('user001',PASSWORD,'none',p['csrf'],p['nonce'],'client',ORIGIN)['error'],'signup_failed')
  self.assertEqual(self.h.hasher.verify_calls,0);self.assertFalse(self.h.ledger._state['receipts'])
 def test_two_services_known_unknown_denial(self):
  for i in range(5):self.assertEqual(self.login(self.a if i%2 else self.b)['error'],'invalid_credentials')
  self.assertEqual(self.login()['error'],'too_many_attempts');self.assertEqual(self.h.hasher.verify_calls,5)
  self.assertEqual(self.login(user='unknown')['error'],'invalid_credentials')
  self.assertTrue(all(r['status']=='fail' for r in self.h.ledger._state['receipts'].values()))
 def test_busy_refund_success_finally_noop(self):
  self.h.hasher.configure('busy');self.assertEqual(self.login()['error'],'busy');self.assertEqual(self.counts(),[0,0])
  out=self.login(password=PASSWORD);self.assertTrue(out['ok']);self.assertEqual(len(self.h.store.sessions),1)
  self.assertEqual(self.h.ledger._state['receipts'][next(reversed(self.h.ledger._state['receipts']))]['status'],'success')
 def test_verify_error_fail_retains(self):
  self.h.hasher.configure('error')
  with self.assertRaisesRegex(FixtureRefused,'verify error'):self.login()
  self.assertEqual(self.counts(),[1,1]);self.assertEqual(next(iter(self.h.ledger._state['receipts'].values()))['status'],'fail')
 def test_verify_expiry_and_rollback_no_success_but_session_gap(self):
  for mode in ('expire','rollback'):
   self.setUp();self.h.hasher.configure(mode)
   with self.assertRaisesRegex(FixtureRefused,'settlement'):self.login(password=PASSWORD)
   self.assertEqual(len(self.h.store.sessions),1);self.assertEqual(self.counts(),[1,1])
   self.assertEqual(next(iter(self.h.ledger._state['receipts'].values()))['status'],'pending')
 def test_begin_capacity_no_verify(self):
  with patch('integration.accounts.shared_ledger_fixture.RECEIPT_CAP',0):
   with self.assertRaisesRegex(FixtureRefused,'admission'):self.login()
  self.assertEqual(self.h.hasher.verify_calls,0);self.assertFalse(self.h.store.sessions)
 def test_begin_rollback_no_verify(self):
  self.login();calls=self.h.hasher.verify_calls;self.h.clock.move(-1)
  with self.assertRaisesRegex(FixtureRefused,'admission'):self.login()
  self.assertEqual(self.h.hasher.verify_calls,calls)
 def test_finally_can_mask_verify_error(self):
  def bad(*args):self.h.clock.move(-1);raise RuntimeError('first verify error')
  with patch.object(FixtureHasher,'verify',side_effect=bad):
   with self.assertRaisesRegex(FixtureRefused,'settlement') as caught:self.login()
  self.assertIsInstance(caught.exception.__context__,Exception);self.assertFalse(self.h.store.sessions)
 def test_finally_failure_after_success_keeps_session(self):
  original=Adapter.success
  def shifted(a,t):r=original(a,t);a.clock.move(-1);return r
  with patch.object(Adapter,'success',shifted):
   with self.assertRaisesRegex(FixtureRefused,'settlement'):self.login(password=PASSWORD)
  self.assertEqual(len(self.h.store.sessions),1);self.assertEqual(next(iter(self.h.ledger._state['receipts'].values()))['status'],'success')
 def test_reauth_bad_good_busy_missing(self):
  self.assertEqual(self.a.synthetic_reauth('user001','bad','client')[0],'invalid_credentials')
  self.h.hasher.configure('busy');self.assertEqual(self.b.synthetic_reauth('user001',PASSWORD,'client')[0],'busy')
  self.assertIsNone(self.a.synthetic_reauth('user001',PASSWORD,'client')[0])
  self.assertEqual(self.b.synthetic_reauth('user002',PASSWORD,'client')[0],'unauthenticated')
 def test_exact_boundary_no_hooks(self):
  class Text(str):
   def __len__(self):raise AssertionError('hook')
  for v in (Text('client'),None,[],129*'x',200*'x'):
   with self.assertRaises(FixtureRefused):self.login(client=v)
  for v in (True,0,9,Text('1')):
   with self.assertRaises(FixtureRefused):create_shared_service_fixture(user_count=v)
  for cls in (FixtureClock,FixtureHasher,Adapter,ServiceHandle,Harness):
   with self.assertRaises(TypeError):type('Bad',(cls,),{})
 def test_concurrency_admission_counts_errors_surfaced(self):
  entered=threading.Barrier(5);release=threading.Event();out=[];errors=[];orig=FixtureHasher.verify
  def paused(h,p,s):entered.wait(2);self.assertTrue(release.wait(2));return orig(h,p,s)
  def run(i):
   try:out.append(self.login(self.h.handles[i%2],client=str(i)))
   except BaseException as e:errors.append(e)
  with patch.object(FixtureHasher,'verify',paused):
   ts=[threading.Thread(target=run,args=(i,)) for i in range(4)]
   for t in ts:t.start()
   try:
    entered.wait(2);self.assertEqual(self.h.ledger._state['keys'][self.h.ledger._key('u-login','user001')]['fails'],4)
    self.assertEqual(sum(r['status']=='pending' for r in self.h.ledger._state['receipts'].values()),4)
   finally:release.set()
   for t in ts:t.join(3);self.assertFalse(t.is_alive())
  self.assertFalse(errors,errors);self.assertEqual(len(out),4)

 def test_original_source_pins(self):
  expected={'integration/accounts/service.py': '7571c387db4ee7acc93e79c4290513569cbed57c4e8f62af1468143a30f1ea84', 'integration/accounts/limiter.py': '816112e2b31c0864ca9493b9ccece1096b93d6c25918631250e238b12ec2a565', 'integration/accounts/store.py': 'afd9d5c972aa38236b55d0cb90a7e68ce593046f442c685f3001699ce012cf0f', 'integration/accounts/mongo_store.py': 'a2205dd7141bd0c7a07685602f538e14b899d199c8366bebd2fcbf88d9d1f52c', 'integration/accounts/shared_ledger_fixture.py': '4ab0adeddef8e82ca9653547f214e4d1514c7f1a2821a35877f522354f737439'}
  root=Path(__file__).resolve().parents[1]
  for p,h in expected.items():self.assertEqual(hashlib.sha256((root/p).read_bytes()).hexdigest(),h,p)
