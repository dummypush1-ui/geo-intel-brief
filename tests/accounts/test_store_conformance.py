"""Contract conformance on a single-process store.

Pass proves only exercised sequences, not shared production atomicity. Fake
clock, <=8 workers, bounded barriers/joins, no sleeps or real account secrets.
"""
import copy,threading,unittest
from integration.accounts.store import MemoryStore
from integration.accounts.passwords import normalize_username
from integration.accounts.limiter import Limiter
NOW=1000

def user(uid='fixture-uid'):return {'uid':uid,'pwv':0,'password':'fixture-hash'}
def session(uid='fixture-uid',expires=2000):return {'uid':uid,'created':NOW,'expires':expires,'idle_expires':expires}
def race(functions):
 if not 1<=len(functions)<=8:raise ValueError('worker cap')
 barrier=threading.Barrier(len(functions));results=[None]*len(functions);errors=[]
 def work(i,fn):
  try:barrier.wait(timeout=2);results[i]=fn()
  except BaseException as exc:errors.append(type(exc).__name__)
 threads=[threading.Thread(target=work,args=(i,f),daemon=True) for i,f in enumerate(functions)]
 for t in threads:t.start()
 for t in threads:t.join(timeout=3)
 if any(t.is_alive() for t in threads):raise AssertionError('worker timeout')
 if errors:raise AssertionError('worker errors '+','.join(errors))
 return results

class StoreConformanceTests(unittest.TestCase):
 def setUp(self):self.store=MemoryStore()
 def seed(self):
  self.assertEqual(self.store.create_account('alice',user(),None,10),'ok')
  self.assertTrue(self.store.create_session('caller',session(), 'fixture-uid',0,10))
 def test_username_normalization_service_boundary(self):
  self.assertEqual(normalize_username(' Alice '),normalize_username('ALICE'))
 def test_invite_cap_claims_and_failed_state(self):
  self.store.add_invite('fixture-invite',3)
  out=race([lambda i=i:self.store.create_account('fixture'+str(i),user('uid'+str(i)),'fixture-invite',10) for i in range(6)])
  self.assertEqual(out.count('ok'),3);self.assertEqual(out.count('invite'),3);self.assertEqual(self.store.invites['fixture-invite'],0)
  before=copy.deepcopy(self.store.invites)
  self.assertEqual(self.store.create_account('extra',user('extra'),'fixture-invite',0),'invite')
  self.assertEqual(before,self.store.invites)
 def test_same_username_and_user_cap(self):
  out=race([lambda i=i:self.store.create_account('alice',user('uid'+str(i)),None,1) for i in range(6)])
  self.assertEqual(out.count('ok'),1);self.assertEqual(out.count('taken'),5)
  before=copy.deepcopy(self.store.users);self.store.add_invite('available',1)
  self.assertEqual(self.store.create_account('bob',user('bob'),'available',1),'cap');self.assertEqual(self.store.invites['available'],1);self.assertEqual(before,self.store.users)
 def test_two_password_changes_and_caller_retention(self):
  self.seed();self.store.create_session('other',session(),'fixture-uid',0,10)
  out=race([lambda:self.store.replace_password('fixture-uid',0,'new-a','caller',NOW),lambda:self.store.replace_password('fixture-uid',0,'new-b','caller',NOW)])
  self.assertEqual(sorted(out),[False,True]);self.assertIn('caller',self.store.sessions);self.assertNotIn('other',self.store.sessions)
  self.assertEqual(self.store.get_user('alice')['pwv'],1)
 def test_settings_cas_and_expiry_boundary(self):
  self.seed();out=race([lambda:self.store.put_settings('fixture-uid',{'version':1,'label':'a'},0,'caller',NOW),lambda:self.store.put_settings('fixture-uid',{'version':1,'label':'b'},0,'caller',NOW)])
  self.assertEqual(sorted(out),[False,True])
  self.store.sessions['caller']['expires']=NOW
  before=copy.deepcopy(self.store.settings)
  self.assertFalse(self.store.put_settings('fixture-uid',{'version':2},1,'caller',NOW));self.assertEqual(before,self.store.settings)
  self.assertIsNone(self.store.touch_session('caller',NOW,100));self.assertNotIn('caller',self.store.sessions)
 def test_delete_settings_session_race_no_orphans(self):
  self.seed()
  out=race([lambda:self.store.delete_account('alice','fixture-uid',0,'caller',NOW),lambda:self.store.put_settings('fixture-uid',{'version':1},0,'caller',NOW),lambda:self.store.create_session('late',session(),'fixture-uid',0,10)])
  self.assertTrue(out[0]);self.assertEqual(self.store.users,{});self.assertEqual(self.store.sessions,{});self.assertEqual(self.store.settings,{})
  self.assertIsNone(self.store.touch_session('late',NOW,100))
  self.store.create_account('alice',user('new-uid'),None,10)
  self.assertFalse(self.store.create_session('stale',session(),'fixture-uid',0,10))
 def test_deterministic_pause_stale_session_after_change_and_delete(self):
  self.seed();captured=self.store.get_user('alice')
  entered=threading.Event();resume=threading.Event();result=[];errors=[]
  def pending():
   try:
    entered.set()
    if not resume.wait(2):raise AssertionError('pause timeout')
    result.append(self.store.create_session('stale',session(),captured['uid'],captured['pwv'],10))
   except BaseException as e:errors.append(type(e).__name__)
  t=threading.Thread(target=pending,daemon=True);t.start();self.assertTrue(entered.wait(2))
  self.assertTrue(self.store.replace_password('fixture-uid',0,'new','caller',NOW));resume.set();t.join(3)
  self.assertFalse(t.is_alive());self.assertEqual(errors,[]);self.assertEqual(result,[False])
  self.assertTrue(self.store.delete_account('alice','fixture-uid',1,'caller',NOW));self.assertFalse(self.store.create_session('late',session(),'fixture-uid',1,10))
 def test_limiter_reservation_cap_and_stale_refund(self):
  clock=[NOW];lim=Limiter(self.store,b'fixture-secret-bytes-not-real'*2,lambda:clock[0],max_user=3,max_client=20)
  out=race([lambda:lim.begin('login','alice','client') for _ in range(8)])
  self.assertEqual(sum(wait==0 for reservation,wait in out),3)
  allowed=[r for r,w in out if w==0];old=allowed[0]
  clock[0]+=5000;new,wait=lim.begin('login','alice','client');self.assertEqual(wait,0)
  before=copy.deepcopy(self.store.attempts);lim.refund(old);self.assertEqual(before,self.store.attempts)
 def test_negative_control_detects_non_atomic_invite(self):
  class Broken(MemoryStore):
   def create_account(self,name,record,invite,max_users):
    if self.invites.get(invite,0)<=0:return 'invite'
    # Deliberately omit invite consumption to demonstrate contract detection.
    return super().create_account(name,record,None,max_users)
  bad=Broken();bad.add_invite('invite',1)
  out=race([lambda i=i:bad.create_account(str(i),user(str(i)),'invite',10) for i in range(2)])
  with self.assertRaises(AssertionError):self.assertEqual(out.count('ok'),1)
