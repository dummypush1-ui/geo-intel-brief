import unittest,copy,threading
from unittest.mock import patch
from integration.accounts.shared_ledger_fixture import Ledger,Facade,Ticket,LedgerRefused,TTL
class Tests(unittest.TestCase):
 def setUp(self):self.l=Ledger();self.a=Facade(self.l);self.b=Facade(self.l)
 def admit(self,u='user',c='client',now=10):return self.a.admit('login',u,c,now)
 def test_two_facades_refund_late_failure(self):
  x=self.admit()['ticket'];y=self.b.admit('login','user','client',10)['ticket'];self.b.settle(y,'fail',10);self.b.settle(x,'refund',11);self.assertEqual([r['fails'] for r in self.l._state['keys'].values()],[1,1]);self.assertEqual(self.a.settle(x,'success',12)['state'],'already_settled')
 def test_asymmetric_user_denial(self):
  for i in range(5):self.admit(c=str(i))
  r=self.admit(c='fresh');self.assertEqual(r['state'],'denied');self.assertEqual(r['wait'],901);self.assertNotIn(self.l._key('c','fresh'),self.l._state['keys']);before=copy.deepcopy(self.l._state['keys']);self.admit(c='fresh');self.assertEqual(self.l._state['keys'],before)
 def test_client_denial_and_both(self):
  for i in range(20):self.admit(u=str(i))
  self.assertEqual(self.admit(u='fresh')['state'],'denied');self.assertNotIn(self.l._key('u-login','fresh'),self.l._state['keys'])
  for i in range(5):self.admit('same','other'+str(i))
  self.assertEqual(self.admit('same','client')['state'],'denied')
 def test_clear_stale_refund_generation(self):
  x=self.admit()['ticket'];y=self.admit()['ticket'];self.a.settle(x,'success',10);z=self.admit()['ticket'];self.b.settle(y,'refund',10);key=self.l._key('u-login','user');self.assertEqual(self.l._state['keys'][key]['fails'],1);self.assertIsNotNone(z)
 def test_terminal_race_wrong_owner_copy_forge(self):
  x=self.admit()['ticket'];bar=threading.Barrier(2);out=[]
  def f(action):bar.wait(2);out.append(self.b.settle(x,action,10)['state'])
  ts=[threading.Thread(target=f,args=(a,)) for a in ('refund','fail')]
  for t in ts:t.start()
  for t in ts:t.join(2);self.assertFalse(t.is_alive())
  self.assertCountEqual(out,['settled','already_settled'])
  for bad in (Ticket(x.nonce),object()):
   with self.assertRaises(LedgerRefused):self.a.settle(bad,'refund',10)
  with self.assertRaises(LedgerRefused):Facade(Ledger()).settle(x,'refund',10)
  with self.assertRaises(TypeError):copy.deepcopy(x)
 def test_pending_expiry_purge_replay_and_fair_budget(self):
  tickets=[self.admit(str(i),str(i))['ticket'] for i in range(12)]
  with self.assertRaises(LedgerRefused):self.a.settle(tickets[0],'refund',10+TTL)
  for _ in range(3):self.assertLessEqual(self.a.prune(10+TTL)['inspected'],8)
  self.assertEqual(self.l._state['receipts'],{})
  with self.assertRaises(LedgerRefused):self.a.settle(tickets[0],'refund',10+TTL)
 def test_clock_bounds_rollback_all_ops(self):
  x=self.admit()['ticket'];self.a.settle(x,'fail',20)
  for f in (lambda:self.admit(now=19),lambda:self.a.settle(x,'fail',19),lambda:self.a.prune(19)):
   with self.assertRaises(LedgerRefused):f()
  for v in (True,float('nan'),float('inf'),10**1000,-1):
   with self.assertRaises(LedgerRefused):self.a.prune(v)
 def test_window_boundary_policy(self):
  x=self.admit()['ticket'];self.a.settle(x,'fail',10);g=self.l._state['keys'][self.l._key('u-login','user')]['gen'];self.admit(now=910);self.assertEqual(self.l._state['keys'][self.l._key('u-login','user')]['gen'],g);self.admit(now=1811);self.assertNotEqual(self.l._state['keys'][self.l._key('u-login','user')]['gen'],g)
 def test_capacity_fault_and_invalid_state_no_publish(self):
  for i in range(100):self.admit(str(i),str(i))
  before=copy.deepcopy(self.l._state)
  with self.assertRaises(LedgerRefused):self.admit('new','new',11)
  self.assertEqual(self.l._state,before)
  l=Ledger();a=Facade(l);before=copy.deepcopy(l._state)
  with patch.object(l,'_publish',side_effect=RuntimeError('fixture injected fault')):
   with self.assertRaises(RuntimeError):a.admit('login','u','c',10)
  self.assertEqual(l._state,before)
  l._state['keys']={'bad':{}}
  with self.assertRaises(LedgerRefused):a.prune(10)
 def test_receipt_cap_live_and_output_alias(self):
  x=self.admit()['ticket'];r=self.a.settle(x,'fail',10);r['state']='tamper';self.assertEqual(self.b.settle(x,'refund',10)['state'],'already_settled')
  with patch('integration.accounts.shared_ledger_fixture.RECEIPT_CAP',1):
   before=copy.deepcopy(self.l._state)
   with self.assertRaises(LedgerRefused):self.admit('other','other')
   self.assertEqual(self.l._state,before)
 def test_old_policy_differential_admission(self):
  from integration.accounts.limiter import Limiter
  from integration.accounts.store import MemoryStore
  old=Limiter(MemoryStore(),b'x'*48,lambda:10)
  for i in range(6):
   _,w=old.begin('login','u',str(i));r=self.admit('u',str(i));self.assertEqual(w,r.get('wait',0))
 def test_generation_collision_and_exhaustion_no_publish(self):
  x=self.admit()['ticket'];y=self.admit()['ticket'];old=self.l._state['receipts'][y.nonce]['pairs'][0][1];self.a.settle(x,'success',10);before=copy.deepcopy(self.l._state)
  with patch('integration.accounts.shared_ledger_fixture.secrets.token_hex',return_value=old):
   with self.assertRaises(LedgerRefused):self.admit()
  self.assertEqual(self.l._state,before)
  with patch('integration.accounts.shared_ledger_fixture.secrets.token_hex',side_effect=[old,'a'*64,'b'*64]):z=self.admit()['ticket']
  self.a.settle(y,'refund',10);self.assertEqual(self.l._state['keys'][self.l._key('u-login','user')]['fails'],1)
  for _ in range(4):self.admit(c='fresh'+str(_))
  before=copy.deepcopy(self.l._state)
  current=next(iter(before['keys'].values()))['gen']
  with patch('integration.accounts.shared_ledger_fixture.secrets.token_hex',return_value=current):
   with self.assertRaises(LedgerRefused):self.admit(c='lock-new')
  self.assertEqual(self.l._state,before)
 def test_forged_nonce_no_hooks(self):
  class Hook:
   def __hash__(self):raise AssertionError('hook ran')
  class Text(str):pass
  for n in [Hook(),Text('a'*64),None,1,[],{},'x'*64,'a'*65]:
   with self.assertRaises(LedgerRefused):self.a.settle(Ticket(n),'refund',10)
 def test_each_terminal_repeats_and_racing_admission_cap(self):
  for action in ['success','refund','fail']:
   l=Ledger();a=Facade(l);ticket=a.admit('login','u','c',10)['ticket'];a.settle(ticket,action,10);before=copy.deepcopy(l._state['keys']);self.assertEqual(a.settle(ticket,action,10)['state'],'already_settled');self.assertEqual(l._state['keys'],before)
  bar=threading.Barrier(8);out=[];errors=[]
  def work(i):
   try:bar.wait(2);out.append(self.b.admit('login','race',str(i),10)['state'])
   except BaseException as e:errors.append(e)
  ts=[threading.Thread(target=work,args=(i,)) for i in range(8)]
  for t in ts:t.start()
  for t in ts:t.join(2);self.assertFalse(t.is_alive())
  self.assertEqual(errors,[]);self.assertEqual(out.count('admitted'),5);self.assertEqual(out.count('denied'),3)
 def test_prune_rotates_past_live_entries(self):
  for i in range(6):self.admit(str(i),str(i),10)
  for i in range(6,12):self.admit(str(i),str(i),20)
  for _ in range(4):self.a.prune(TTL+10)
  self.assertEqual(len(self.l._state['receipts']),6);self.assertTrue(all(r['expires']==TTL+20 for r in self.l._state['receipts'].values()))
