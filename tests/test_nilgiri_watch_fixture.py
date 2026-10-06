import unittest,datetime as dt,threading,copy
from integration.nilgiri_watch_fixture.core import *
T=dt.datetime(2026,10,6,12,tzinfo=UTC)
HTML=b'<main><p>This is sufficient original visible page content for a valid fixture baseline.</p></main>'
def R(s=200,b=HTML,**headers):return {'status':s,'headers':{'Content-Type':'text/html',**headers},'body':b}
class Tests(unittest.TestCase):
 def calls(self,robot=None,page=None):
  calls=[]
  def f(u,h):calls.append((u,h));return (robot or R(404,b''))if u==ROBOTS else(page or R(ETag='opaque'))
  return f,calls
 def runit(self,s,f,t=T,**kw):return cycle(s,f,t,enabled=True,fixture_wired=True,**kw)
 def test_off_unwired(self):
  def no(*a):raise AssertionError('calls')
  self.assertEqual(cycle(MemoryFixtureStore(),no,T)['state'],'disabled');self.assertEqual(cycle(MemoryFixtureStore(),no,T,enabled=True)['state'],'requested-on-not-running')
 def test_fixed_first_and_cadence(self):
  s=MemoryFixtureStore();f,c=self.calls();r=self.runit(s,f);self.assertEqual(r['outcome'],'first_baseline');self.assertIsNone(r['alert']);self.assertEqual([x[0]for x in c],[ROBOTS,HOME]);self.runit(s,f,T+dt.timedelta(seconds=3599));self.assertEqual(len(c),2);self.assertEqual(self.runit(s,f,T+dt.timedelta(hours=1))['outcome'],'unchanged')
 def test_slower_clock_rollback(self):
  s=MemoryFixtureStore();f,c=self.calls();self.runit(s,f,interval=7200);self.runit(s,f,T+dt.timedelta(hours=1),interval=3600);self.assertEqual(len(c),2);self.assertEqual(self.runit(s,f,T-dt.timedelta(seconds=1))['reason'],'store_or_clock_uncertain')
 def test_robots_statuses(self):
  for status in [200,201,301,304,400,401,403,429,500,503]:
   s=MemoryFixtureStore();f,c=self.calls(R(status,b''));r=self.runit(s,f);self.assertEqual(len(c),1);self.assertIn(r['state'],('paused','stopped'));self.assertIsNone(s.content);self.runit(s,f,T+dt.timedelta(hours=2));self.assertEqual(len(c),1)
 def test_page_stop(self):
  for p in [R(403),R(429),R(b=b'<p>verify you are human captcha</p>')]:
   s=MemoryFixtureStore();f,c=self.calls(page=p);self.assertEqual(self.runit(s,f)['state'],'stopped');self.runit(s,f,T+dt.timedelta(hours=2));self.assertEqual(len(c),2)
 def test_schema(self):
  for p in [R(b=b'\xff'),R(**{'Content-Encoding':'gzip'}),R(**{'X-X':'bad\n'}),R(**{'Content-Length':'999'}),{'status':True,'headers':{},'body':b''},R(b=b'x'*131073),R(**{'ETag':'x'*1025}),R(**{'ETag':'a','etag':'b'})]:
   s=MemoryFixtureStore();f,c=self.calls(page=p);self.assertEqual(self.runit(s,f)['outcome'],'refusal');self.assertIsNone(s.content)
 def test_unconditional304(self):
  s=MemoryFixtureStore();f,c=self.calls(page=R(304,b''));self.assertEqual(self.runit(s,f)['outcome'],'refusal')
 def test_conditional304(self):
  s=MemoryFixtureStore();f,c=self.calls();self.runit(s,f);old=copy.deepcopy(s.content);f,c=self.calls(page=R(304,b'',ETag='opaque'));r=self.runit(s,f,T+dt.timedelta(hours=1));self.assertEqual(r['outcome'],'checked_unchanged');self.assertEqual(c[-1][1],{'If-None-Match':'opaque'});self.assertEqual(s.content['snapshot'],old['snapshot']);self.assertGreater(s.content['checked_at'],old['checked_at'])
 def test_stale_and_identity304(self):
  s=MemoryFixtureStore();f,c=self.calls();self.runit(s,f);f,c=self.calls(page=R(304,b''));self.assertEqual(self.runit(s,f,T+dt.timedelta(days=2))['outcome'],'refusal');self.assertEqual(c[-1][1],{})
  for k,v in [('policy','wrong'),('source','https://evil.example/'),('revision',0),('checked_at',T+dt.timedelta(days=1))]:
   s=MemoryFixtureStore();f,c=self.calls();self.runit(s,f);s.content[k]=v;f,c=self.calls();self.assertEqual(self.runit(s,f,T+dt.timedelta(hours=1))['outcome'],'refusal');self.assertEqual(c,[])
 def test_changed_preserves_errors(self):
  s=MemoryFixtureStore();f,c=self.calls();self.runit(s,f);f,c=self.calls(page=R(b=HTML.replace(b'original',b'changed')));self.assertEqual(self.runit(s,f,T+dt.timedelta(hours=1))['outcome'],'changed');good=copy.deepcopy(s.content);f,c=self.calls(page=R(500));self.runit(s,f,T+dt.timedelta(hours=2));self.assertEqual(s.content,good)
 def test_active_concurrent(self):
  s=MemoryFixtureStore();started=threading.Event();release=threading.Event();calls=[];out=[]
  def f(u,h):calls.append(u);started.set();release.wait(3);return R(404,b'')if u==ROBOTS else R()
  th=threading.Thread(target=lambda:out.append(self.runit(s,f)));th.start();self.assertTrue(started.wait(1));self.assertEqual(self.runit(s,f)['reason'],'active_attempt');release.set();th.join(4);self.assertFalse(th.is_alive());self.assertEqual(len(calls),2)
 def test_conflict_and_commitfail(self):
  class Conflict(MemoryFixtureStore):
   def finish(self,*a):return False
  s=Conflict();f,c=self.calls();r=self.runit(s,f);self.assertEqual(r['outcome'],'commit-conflict');self.assertIsNone(r['alert']);self.assertIsNotNone(s.active)
  class Fail(MemoryFixtureStore):
   def finish(self,*a):raise RuntimeError('failure')
  s=Fail();f,c=self.calls();self.assertEqual(self.runit(s,f)['reason'],'store_commit_uncertain');self.runit(s,f,T+dt.timedelta(hours=2));self.assertEqual(len(c),2)
 def test_parser_bounds(self):
  s=MemoryFixtureStore();f,c=self.calls(page=R(b=b'<p>'+b'a'*5000+b'</p>'));self.assertEqual(self.runit(s,f)['outcome'],'refusal')
 def test_future_baseline(self):
  s=MemoryFixtureStore();f,c=self.calls();self.runit(s,f);s.content['snapshot']=snapshot(HOME,HTML.decode(),(T+dt.timedelta(hours=5)).isoformat());f,c=self.calls();self.assertEqual(self.runit(s,f,T+dt.timedelta(hours=1))['outcome'],'refusal');self.assertEqual(c,[])
class BoundaryTests(Tests):
 def test_custom_timezone_no_hooks(self):
  class Evil(dt.tzinfo):
   def utcoffset(self,x):raise AssertionError('hook called')
   def dst(self,x):raise AssertionError('hook called')
  bad=dt.datetime(2026,10,6,tzinfo=Evil())
  with self.assertRaises(Refusal):clock(bad)
  for where in ['last','checked_at']:
   s=MemoryFixtureStore();f,c=self.calls();self.runit(s,f)
   if where=='last':s.last=bad
   else:s.content[where]=bad
   f,c=self.calls();self.assertEqual(self.runit(s,f,T+dt.timedelta(hours=1))['outcome'],'refusal');self.assertEqual(c,[])
  self.assertEqual(clock(T),T)
  with self.assertRaises(Refusal):clock(T.replace(tzinfo=dt.timezone(dt.timedelta(hours=1))))
 def test_oversized_aggregate_hash_zero_fetch(self):
  for text,kind in [('x'*131073,'oversized'),('க'*44000,'multibyte'),('x'*130900,'aggregate')]:
   s=MemoryFixtureStore();f,c=self.calls();self.runit(s,f)
   import hashlib
   sn=s.content['snapshot'];sn['text']=text;sn['sha256']=hashlib.sha256(text.encode()).hexdigest();s.content['validators']={'etag':'x'*1024,'last-modified':'y'*1024}
   f,c=self.calls();self.assertEqual(self.runit(s,f,T+dt.timedelta(hours=1))['outcome'],'refusal',kind);self.assertEqual(c,[])
  s=MemoryFixtureStore();f,c=self.calls();self.runit(s,f);s.content['snapshot']['sha256']='0'*64;f,c=self.calls();self.assertEqual(self.runit(s,f,T+dt.timedelta(hours=1))['outcome'],'refusal');self.assertEqual(c,[])
class AdditiveInventoryTests(unittest.TestCase):
 def test_exact_additive92_paths_hashes_and_ast(self):
  import json,hashlib,ast
  from pathlib import Path
  root=Path(__file__).resolve().parents[1];d=json.loads((root/'integration/nilgiri_watch_fixture/inventory92.json').read_text());expected={'integration/nilgiri_watch_fixture/__init__.py','integration/nilgiri_watch_fixture/core.py','tests/test_nilgiri_watch_fixture.py'}
  self.assertEqual(set(d['files']),expected);self.assertEqual(d['kind'],'additive92_not_replacement87');imports={}
  for name,row in d['files'].items():
   b=(root/name).read_bytes();self.assertEqual(hashlib.sha256(b).hexdigest(),row['sha256'])
   found=[]
   for n in ast.walk(ast.parse(b)):
    if isinstance(n,ast.Import):found.extend(x.name for x in n.names)
    elif isinstance(n,ast.ImportFrom):found.append('.'*n.level+(n.module or ''))
   self.assertEqual(sorted(found),row['imports'])
  actual={str(p.relative_to(root))for p in(root/'integration/nilgiri_watch_fixture').glob('*.py')};self.assertEqual(actual,expected-{'tests/test_nilgiri_watch_fixture.py'})
if __name__=='__main__':unittest.main(verbosity=2)
