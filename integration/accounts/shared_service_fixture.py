"""Test-only closed service control flow. No HTTP, runtime config or real credentials."""
import hashlib, threading
from .service import AccountService
from .store import MemoryStore
from .passwords import Busy
from .shared_ledger_fixture import Ledger, LedgerRefused, TTL, epoch
ORIGIN='https://shared-fixture.invalid'
PASSWORD='synthetic-Fixture-123!'
SECRET=b'private-synthetic-shared-fixture-secret-000'
class FixtureRefused(ValueError):pass
class Sealed:
 def __init_subclass__(cls,**kw):
  if cls.__module__!=__name__:raise TypeError('fixture sealed')
class FixtureClock(Sealed):
 def __init__(self):self._now=100;self._lock=threading.RLock()
 def __call__(self):
  with self._lock:return self._now
 def move(self,delta):
  if type(delta) is not int or delta not in (-1,0,TTL,TTL+1):raise FixtureRefused('fixture clock control')
  with self._lock:self._now=epoch(self._now+delta)
class FixtureHasher(Sealed):
 def __init__(self,clock):
  if type(clock) is not FixtureClock:raise FixtureRefused('fixture hasher clock')
  self.clock=clock;self.hash_calls=0;self.verify_calls=0;self._mode='normal';self._lock=threading.RLock()
 def configure(self,mode):
  if type(mode) is not str or mode not in ('normal','busy','error','expire','rollback'):raise FixtureRefused('fixture verify control')
  with self._lock:self._mode=mode
 def hash(self,password):
  if type(password) is not str or not 1<=len(password)<=128:raise FixtureRefused('fixture synthetic hash input')
  with self._lock:self.hash_calls+=1
  return 'synthetic-sha256:'+hashlib.sha256(password.encode()).hexdigest()
 def verify(self,password,stored):
  with self._lock:self.verify_calls+=1;mode=self._mode;self._mode='normal'
  if mode=='busy':raise Busy()
  if mode=='error':raise FixtureRefused('fixture verify error')
  if mode=='expire':self.clock.move(TTL)
  if mode=='rollback':self.clock.move(-1)
  return type(password) is str and stored=='synthetic-sha256:'+hashlib.sha256(password.encode()).hexdigest()
 def needs_rehash(self,stored):return False
class Adapter(Sealed):
 def __init__(self,ledger,clock):
  if type(ledger) is not Ledger or type(clock) is not FixtureClock:raise FixtureRefused('fixture adapter types')
  self.ledger=ledger;self.clock=clock
 def begin(self,op,user,client):
  try:r=self.ledger.admit(op,user,client,self.clock())
  except LedgerRefused:raise FixtureRefused('fixture admission refused') from None
  if r['state']=='denied':return None,r['wait']
  return r['ticket'],0
 def _finish(self,ticket,action):
  try:return self.ledger.settle(ticket,action,self.clock())
  except LedgerRefused:raise FixtureRefused('fixture settlement refused') from None
 def fail(self,ticket):return self._finish(ticket,'fail')
 def refund(self,ticket):return self._finish(ticket,'refund')
 def success(self,ticket):return self._finish(ticket,'success')
def _text(value,cap):
 if type(value) is not str or len(value)>cap:raise FixtureRefused('fixture exact bounded text required')
class ServiceHandle(Sealed):
 def __init__(self,service):self._service=service
 def preauth(self):return self._service.issue_preauth()
 def login(self,username,password,client,csrf,nonce):
  for v,c in ((username,64),(password,128),(client,128),(csrf,200),(nonce,100)):_text(v,c)
  return self._service.login(username,password,csrf,nonce,client,ORIGIN)
 def closed_signup(self):return self._service.signup('user001',PASSWORD,None,None,None,'client',ORIGIN)
 def synthetic_reauth(self,username,password,client):
  for v,c in ((username,32),(password,128),(client,128)):_text(v,c)
  # Artificial session row solely for _reauth control-flow research, not authorization.
  if username not in ('user%03d'%i for i in range(1,9)):raise FixtureRefused('fixture synthetic username required')
  return self._service._reauth({'username':username,'uid':'synthetic-'+username},password,client)
class Harness(Sealed):
 def __init__(self,count):
  if type(count) is not int or not 1<=count<=8:raise FixtureRefused('fixture user count')
  self.clock=FixtureClock();self.hasher=FixtureHasher(self.clock);self.store=MemoryStore();self.ledger=Ledger()
  for i in range(1,count+1):
   u='user%03d'%i
   assert self.store.create_account(u,{'uid':'synthetic-'+u,'password':self.hasher.hash(PASSWORD),'pwv':0,'created':self.clock()},None,8)=='ok'
  services=[AccountService(self.store,SECRET,self.clock,hasher=self.hasher,signup_mode='closed',allowed_origins=(ORIGIN,)) for _ in range(2)]
  for s in services:s.limiter=Adapter(self.ledger,self.clock)
  self.handles=tuple(ServiceHandle(s) for s in services)
def create_shared_service_fixture(*,user_count=1):return Harness(user_count)
