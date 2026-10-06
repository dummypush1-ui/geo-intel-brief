import unittest,threading,copy
from integration.accounts.store import MemoryStore,epoch
from integration.accounts.mongo_store import MongoAccountStore,MongoStoreInvalid,MongoStoreUnavailable,_state
from tests.test_mongo_account_store import Client,Session,R,user
class Tests(unittest.TestCase):
 def test_boundary_fraction_exhausted_legacy(self):
  s=MemoryStore();s.add_invite('x',2,100.5);self.assertEqual(s.create_account('one',user(),'x',10,100.499),'ok');before=copy.deepcopy((s.users,s.invites));self.assertEqual(s.create_account('two',user('v'),'x',10,100.5),'invite');self.assertEqual((s.users,s.invites),before)
  s.add_invite('old',1);self.assertEqual(s.create_account('three',user('z'),'old',10),'ok');self.assertEqual(s.invites['old'],0)
 def test_invalid_record_cap_clock_no_burn(self):
  s=MemoryStore();s.add_invite('x',1,100);before=copy.deepcopy(s.invites)
  for rec in [dict(user(),password=object()),dict(user(),pwv=True),dict(user(),extra='secret')]:
   with self.assertRaises(ValueError):s.create_account('one',rec,'x',10,50)
  for now in [None,True,float('nan'),10**500,-1,4133980800]:
   with self.assertRaises(ValueError):s.create_account('one',user(),'x',10,now)
  self.assertEqual(s.invites,before);self.assertEqual(s.users,{})
  self.assertEqual(s.create_account('one',user(),'x',0,50),'cap');self.assertEqual(s.invites,before)
 def test_provisioning_cap_replacement_and_purge(self):
  s=MemoryStore()
  for i in range(1000):s.add_invite(str(i),1,100)
  s.add_invite('0',2,200)
  with self.assertRaises(ValueError):s.add_invite('new',1,100)
  before=copy.deepcopy(s.invites)
  with self.assertRaises(ValueError):s.purge(float('nan'))
  self.assertEqual(s.invites,before);s.purge(100);self.assertEqual(s.invites,{'0':{'uses':2,'expires_at':200}})
 def test_snapshot_exact_shapes(self):
  c=Client()
  for v in [True,{'uses':1,'expires_at':100,'extra':0},{'uses':True,'expires_at':100},{'uses':1,'expires_at':float('nan')}]:
   c.doc['state']['invites']={'x':v}
   with self.assertRaises(ValueError):_state(c.doc['state'])
  c.doc['state']['invites']={'old':0,'timed':{'uses':0,'expires_at':100}};self.assertEqual(_state(c.doc['state'])['invites'],c.doc['state']['invites'])
 def test_multi_store_transaction_admission_time_not_commit(self):
  c=Client();a=MongoAccountStore(c,review=R,clock=lambda:150);b=MongoAccountStore(c,review=R,clock=lambda:150);a.add_invite('x',1,100)
  # Admitted at50, transaction runs at150. Deliberately admission-time semantics.
  self.assertEqual(b.create_account('one',user(),'x',10,50),'ok');self.assertEqual(a.get_user('one')['uid'],'u')
 def test_delayed_lock_uses_admission_clock(self):
  s=MemoryStore();s.add_invite('x',1,100);out=[];started=threading.Event()
  with s._l:
   def work():started.set();out.append(s.create_account('one',user(),'x',10,50))
   t=threading.Thread(target=work);t.start();self.assertTrue(started.wait(2))
  t.join(2);self.assertFalse(t.is_alive());self.assertEqual(out,['ok'])
 def test_racing_claims_no_overuse(self):
  s=MemoryStore();s.add_invite('x',2,100);bar=threading.Barrier(4);out=[]
  def work(i):bar.wait(2);out.append(s.create_account(str(i),user(str(i)),'x',10,50))
  ts=[threading.Thread(target=work,args=(i,)) for i in range(4)]
  for t in ts:t.start()
  for t in ts:t.join(2);self.assertFalse(t.is_alive())
  self.assertEqual(out.count('ok'),2);self.assertEqual(s.invites['x']['uses'],0)
 def test_abort_and_committed_response_lost_no_retry(self):
  c=Client();s=MongoAccountStore(c,review=R,clock=lambda:0);s.add_invite('x',1,100);c.fail_commit=True
  with self.assertRaises(MongoStoreUnavailable):s.create_account('one',user(),'x',10,50)
  self.assertEqual(c.doc['state']['invites']['x']['uses'],1);self.assertEqual(c.doc['state']['users'],{})
  class Lost(Session):
   def commit_transaction(self):super().commit_transaction();raise ValueError('lost')
  class Driver(Client):
   def start_session(self,**kw):r=Lost(self);self.sessions.append(r);return r
  d=Driver();d.doc['state']['invites']={'x':{'uses':1,'expires_at':100}};s=MongoAccountStore(d,review=R,clock=lambda:0)
  with self.assertRaises(MongoStoreUnavailable):s.create_account('one',user(),'x',10,50)
  self.assertEqual(len(d.sessions),1);self.assertEqual(d.doc['state']['invites']['x']['uses'],0);self.assertIn('one',d.doc['state']['users'])
 def test_service_post_hash_clock_closed_open_and_late_failure(self):
  from integration.accounts import AccountService,Hasher,hash_invite
  from unittest.mock import patch
  secret=b'x'*48;now=[50];origin='https://example.invalid';password='correct horse battery'
  def svc(store,mode='invite'):return AccountService(store,secret,lambda:now[0],hasher=Hasher(n=1024),signup_mode=mode,allowed_origins=[origin])
  def signup(v,name='alice'):
   p=v.issue_preauth();return v.signup(name,password,'invite-code-1',p['csrf'],p['nonce'],'client1',origin)
  s=MemoryStore();v=svc(s);key=hash_invite(secret,'invite-code-1');s.add_invite(key,1,100);original=v.hasher.hash
  def slow(p):r=original(p);now[0]=100;return r
  with patch.object(v.hasher,'hash',side_effect=slow):self.assertFalse(signup(v)['ok'])
  self.assertEqual(s.invites[key]['uses'],1);self.assertEqual(s.users,{})
  for mode in ('closed','open'):
   now[0]=100;s=MemoryStore();s.add_invite(key,1,50);v=svc(s,mode);result=signup(v);self.assertEqual(result['ok'],mode=='open');self.assertEqual(s.invites[key]['uses'],1)
  now[0]=50;s=MemoryStore();s.add_invite(key,1,100);v=svc(s)
  with patch.object(s,'create_session',return_value=False):self.assertFalse(signup(v)['ok'])
  self.assertIn('alice',s.users);self.assertEqual(s.invites[key]['uses'],0) # preexisting later-signup failure gap
 def test_endpoint_epoch_and_subclasses(self):
  for v in (0,4133980799.999999,100.25):self.assertEqual(epoch(v),v)
  class Evil(dict):pass
  s=MemoryStore();s.invites['x']=Evil(uses=1,expires_at=100)
  with self.assertRaises(ValueError):s.create_account('one',user(),'x',10,50)
