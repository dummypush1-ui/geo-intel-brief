import unittest
from bson import ObjectId
from asyncio import CancelledError
from integration.news_export.raw_pager import RawPager,RawPagerError,RawPagerControlError
from integration.news_export.original_contract import original_snapshot

def row(n):return {'_id':ObjectId(f'{n:024x}'),'score':n//2,'published':'2026-10-05T00:00:00+00:00','title':str(n)}
def match(r,q):
 if not q:return True
 return any(all(r[k]<v['$lt'] if type(v) is dict else r[k]==v for k,v in term.items()) for term in q['$or'])
class RawPagerTests(unittest.TestCase):
 def test_fixture_multi_page_differential(self):
  rows=[row(n) for n in range(12,0,-1)];calls=[]
  def execute(plan):
   calls.append(plan)
   return [r.copy() for r in rows if match(r,plan['query'])][:plan['limit']]
  checks=[]
  pager=RawPager('geo',execute,lambda p,o:checks.append((p,o)) or True,page_size=3)
  out=[]
  while True:
   page=pager.fetch_page()
   if not page:break
   out+=page
  self.assertEqual(out,rows);self.assertEqual(len(calls),5);self.assertEqual(len(checks),1)
  self.assertEqual(original_snapshot(out,'geo')[0],original_snapshot(rows,'geo')[0])
  pager.fetch_page();self.assertEqual(len(calls),5)
 def test_scope_exact_bool_and_fail_before_executor(self):
  for grant in (False,None,1,'true'):
   calls=[];pager=RawPager('geo',lambda p:calls.append(p),lambda p,o:grant)
   with self.assertRaises(RawPagerError):pager.fetch_page()
   self.assertEqual(calls,[])
   with self.assertRaises(RawPagerError):pager.fetch_page()
 def test_duplicates_out_of_order_missing_and_over_limit(self):
  for rows in ([row(2),row(2)],[row(1),row(2)],[{'title':'missing'}],[row(3),row(2),row(1)]):
   pager=RawPager('geo',lambda p:rows,lambda p,o:True,page_size=2)
   with self.assertRaises(RawPagerError):pager.fetch_page()
 def test_nonadvancing_second_page(self):
  calls=[]
  def execute(p):calls.append(p);return [row(2)]
  pager=RawPager('geo',execute,lambda p,o:True,page_size=1)
  pager.fetch_page()
  with self.assertRaises(RawPagerError):pager.fetch_page()
  self.assertEqual(len(calls),2)
 def test_exceptions_redacted_and_no_retry(self):
  for phase in ('verify','execute'):
   def bad(*args):raise RuntimeError('secret database details')
   pager=RawPager('geo',bad if phase=='execute' else lambda p:[],bad if phase=='verify' else lambda p,o:True)
   with self.assertRaisesRegex(RawPagerError,'^raw page unavailable or invalid$'):pager.fetch_page()
   with self.assertRaisesRegex(RawPagerError,'^pager closed$'):pager.fetch_page()
 def test_brics_fixture_internal_fields_not_csv(self):
  rows=[{'_id':ObjectId(f'{n:024x}'),'collected_at':'2026-10-05T00:00:00.123456','summary':'PRIVATE','title':'fixture'} for n in (3,2)]
  pager=RawPager('brics',lambda p:rows,lambda p,o:True,page_size=3)
  data=original_snapshot(pager.fetch_page(),'brics')[0].decode()
  self.assertNotIn('_id',data);self.assertNotIn('PRIVATE',data);self.assertNotIn(str(rows[0]['_id']),data)
 def test_closed_projection_and_budget(self):
  for r,budget in (({**row(2),'password':'private'},2048),({**row(2),'title':'x'*3000},128),({**row(2),'title':'\ud800'},2048)):
   pager=RawPager('geo',lambda p:[r],lambda p,o:True,max_page_bytes=budget)
   with self.assertRaises(RawPagerError):pager.fetch_page()
 def test_manual_close(self):
  pager=RawPager('geo',lambda p:[],lambda p,o:True);pager.close();pager.close()
  with self.assertRaises(RawPagerError):pager.fetch_page()

 def test_control_flow_closes_and_discards_secret_args(self):
  for phase in ('verify','execute'):
   for kind in (KeyboardInterrupt,SystemExit):
    calls=[]
    def bad(*args):calls.append(1);raise kind('secret credential text')
    pager=RawPager('geo',bad if phase=='execute' else lambda p:[],bad if phase=='verify' else lambda p,o:True)
    with self.assertRaises(kind) as caught:pager.fetch_page()
    if kind is SystemExit:self.assertEqual(caught.exception.code,1)
    else:
     self.assertEqual(caught.exception.args,())
     self.assertEqual(str(caught.exception),'')
    self.assertNotIn('secret',str(caught.exception))
    self.assertTrue(pager._closed);self.assertIsNone(pager._execute);self.assertIsNone(pager._verify)
    with self.assertRaisesRegex(RawPagerError,'^pager closed$'):pager.fetch_page()
    self.assertEqual(calls,[1])

 def test_system_exit_codes_preserved(self):
  for code in (0,1,27,-1,None,'secret',True):
   def bad(p):raise SystemExit(code)
   pager=RawPager('geo',bad,lambda p,o:True)
   with self.assertRaises(SystemExit) as caught:pager.fetch_page()
   self.assertEqual(caught.exception.code,code if type(code) is int or code is None else 1)
   self.assertTrue(pager._closed)
 def test_known_and_unknown_base_exceptions(self):
  class CustomInterrupt(BaseException):
   def __init__(self,required):super().__init__(required)
  for kind,expected in ((GeneratorExit,GeneratorExit),(CancelledError,CancelledError),(CustomInterrupt,RawPagerControlError)):
   def bad(p):raise kind('secret')
   pager=RawPager('geo',bad,lambda p,o:True)
   with self.assertRaises(expected) as caught:pager.fetch_page()
   self.assertNotIn('secret',str(caught.exception));self.assertTrue(pager._closed)
   self.assertIsNone(pager._execute);self.assertIsNone(pager._verify)
 def test_close_override_cannot_intercept_failure(self):
  def bad(p):raise ValueError('secret')
  pager=RawPager('geo',bad,lambda p,o:True)
  pager.close=lambda:None
  with self.assertRaises(RawPagerError):pager.fetch_page()
  self.assertTrue(pager._closed);self.assertIsNone(pager._execute)
  with self.assertRaises(TypeError):
   class BadPager(RawPager):pass
