import unittest
from integration.code_news_cursor_prep import SharedBudget,Scan,Refused,PageBusy,PageExpired,PageUnavailable
class Parent:
 def __init__(self):self.calls=0;self.filters=None;self.closed=[];self.rows=[{'title':'fixture'}];self.error=None;self.exhausted=False
 def page(self,t,filters,n):
  self.calls+=1
  if self.error:raise self.error
  self.filters=filters;return {'items':self.rows,'next_cursor':'parent-token','exhausted':self.exhausted}
 def close(self,t):self.closed.append(t)
class Tests(unittest.TestCase):
 def setUp(self):self.now=0;self.p=Parent();self.b=SharedBudget();self.s=Scan(self.p,lambda t,r:None,self.b,lambda:self.now)
 def test_independent_token(self):
  r,status=self.s.page(target='HS8517');self.assertEqual(status,200);self.assertNotEqual(r['next_cursor'],'parent-token');self.assertEqual(self.s.page('parent-token')[1],410)
 def test_idle(self):
  r,_=self.s.page(target='x');self.now=120;self.assertEqual(self.s.page(r['next_cursor'])[1],410);self.assertEqual(self.b.code,0);self.assertEqual(len(self.p.closed),1)
 def test_combined_cap(self):self.b.news=16;self.assertEqual(self.s.page(target='x')[1],429);self.assertEqual(self.p.calls,0)
 def test_subset_cap(self):
  for n in range(4):self.s.page(target='x')
  self.assertEqual(self.s.page(target='x')[1],429)
 def test_quota_noadvance(self):
  self.s.calls=20;self.s.minute=0;self.assertEqual(self.s.page(target='x')[1],429);self.assertEqual(self.p.calls,0)
 def test_budget_stop(self):
  r,_=self.s.page(target='x')
  for n in range(19):r,_=self.s.page(r['next_cursor'])
  self.assertEqual(r['state'],'budget_stopped_incomplete');self.assertFalse(r['complete']);self.assertEqual(self.b.code,0)
 def test_fixed_filters(self):self.s.page(target='x');self.assertEqual(self.p.filters,{'project':'geo','query':'','category':'','country':'','sort':'newest'})
 def test_shared_lock(self):
  self.b.lock.acquire()
  try:self.assertEqual(self.s.page(target='x')[1],429);self.assertEqual(self.p.calls,0)
  finally:self.b.lock.release()
 def test_replay(self):
  a,_=self.s.page(target='x');t=a['next_cursor'];b,_=self.s.page(t);calls=self.p.calls;c,_=self.s.page(t);self.assertEqual(b,c);self.assertEqual(calls,self.p.calls)
  d,_=self.s.page(b['next_cursor']);self.assertEqual(self.s.page(t)[1],410)
 def test_carry_sixty(self):
  self.p.rows=[{'n':i} for i in range(60)];self.s.match=lambda t,r:r
  a,_=self.s.page(target='x');b,_=self.s.page(a['next_cursor']);c,_=self.s.page(b['next_cursor'])
  self.assertEqual([len(r['items']) for r in (a,b,c)],[25,25,10]);self.assertEqual(self.p.calls,1);self.assertEqual([r['n'] for p in (a,b,c) for r in p['items']],list(range(60)))
 def test_parent_busy(self):
  a,_=self.s.page(target='x');self.p.error=PageBusy();self.assertEqual(self.s.page(a['next_cursor'])[1],429);self.assertEqual(self.b.code,1);self.assertFalse(self.p.closed)
 def test_source_error_close_once(self):
  a,_=self.s.page(target='x');self.p.error=PageUnavailable();self.assertEqual(self.s.page(a['next_cursor'])[1],503);self.assertEqual(self.b.code,0);self.assertEqual(len(self.p.closed),1);self.s.page(a['next_cursor']);self.assertEqual(len(self.p.closed),1)
 def test_parent_expired(self):
  a,_=self.s.page(target='x');self.p.error=PageExpired();self.assertEqual(self.s.page(a['next_cursor'])[1],410);self.assertEqual(self.b.code,0)
 def test_first_call_failure(self):
  for e in (PageBusy(),PageExpired(),PageUnavailable()):
   self.p.error=e;self.s.page(target='x');self.assertEqual(self.b.code,0);self.assertFalse(self.s.states)
 def test_target_mismatch(self):
  a,_=self.s.page(target='x');calls=self.p.calls;self.assertEqual(self.s.page(a['next_cursor'],target='y')[1],410);self.assertEqual(self.p.calls,calls)
 def test_oversize(self):self.p.rows=[{'s':'x'*2097152}];self.assertEqual(self.s.page(target='x')[1],503);self.assertEqual(self.b.code,0);self.assertEqual(len(self.p.closed),1)
 def test_stale_before_quota(self):self.s.minute=0;self.s.calls=20;self.assertEqual(self.s.page('stale')[1],410);self.assertEqual(self.s.calls,20)
 def test_head(self):self.assertEqual(self.s.head()[1],200);self.assertEqual(self.p.calls,0);self.assertEqual(self.b.code,0)
 def test_expiry_sweep_admission(self):
  for i in range(4):self.s.page(target='x')
  self.now=120;self.assertEqual(self.s.page(target='x')[1],200);self.assertEqual(self.b.code,1)

 def test_eof_complete_replay(self):
  a,_=self.s.page(target='x');t=a['next_cursor'];self.p.exhausted=True;b,status=self.s.page(t)
  self.assertEqual(status,200);self.assertEqual(b['state'],'complete_mutable_read');self.assertTrue(b['complete']);self.assertIsNone(b['next_cursor']);self.assertEqual(len(self.p.closed),1);self.assertEqual(self.b.code,0)
  calls=self.p.calls;c,status=self.s.page(t);self.assertEqual(c,b);self.assertEqual(status,200);self.assertEqual(self.p.calls,calls);self.assertEqual(len(self.p.closed),1);self.assertEqual(self.b.code,0)
 def test_reply_byte_cap(self):
  self.p.rows=[{'n':i} for i in range(25)];self.s.match=lambda t,r:{'evidence':'x'*22000}
  b,status=self.s.page(target='x');self.assertEqual(status,503);self.assertEqual(b['state'],'page_refused');self.assertEqual(self.b.code,0);self.assertEqual(len(self.p.closed),1)
