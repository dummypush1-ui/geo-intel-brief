import unittest
from integration.code_news_matcher_prep import for_article
from integration.code_news_coverage_prep import Scan,SharedBudget
from integration.code_news_links import Links
TARGET=dict(system='HS',edition='2022',code='8517',description='Phones')
class Parent:
 def __init__(self,rows):self.rows=rows;self.calls=0;self.closed=[];self.eof=True
 def page(self,*a):self.calls+=1;return dict(items=self.rows,next_cursor='parent',exhausted=self.eof)
 def close(self,x):self.closed.append(x)
class Tests(unittest.TestCase):
 def setUp(self):self.m=Links([TARGET],[])
 def row(self,s,k='a'):return dict(article_key=k,title='Trade',summary=s)
 def scan(self,rows):
  p=Parent(rows);b=SharedBudget();return Scan(p,lambda t,r:for_article(self.m,t,r),b),p,b
 def test_raw_cap_unknown_repeats(self):
  for source in ['HS8517; '*33,'HS9999; '*33]:
   r=for_article(self.m,TARGET,self.row(source));self.assertEqual(r['state'],'evidence_refused_mentions_limit');self.assertEqual(r['items'],[])
 def test_exact32_keeps_all(self):self.assertEqual(len(for_article(self.m,TARGET,self.row('HS8517; '*32))['items']),32)
 def test_refusal_no_resolve(self):
  self.m.resolve=lambda *a:(_ for _ in ()).throw(AssertionError('resolve'))
  self.assertEqual(for_article(self.m,TARGET,self.row('HS8517; '*33))['coverage'],'article_refused')
 def test_nation_no_guess(self):self.assertEqual(for_article(self.m,TARGET,self.row('HSN8517;'))['items'],[])
 def test_whitespace_linear(self):
  import time
  start=time.process_time();for_article(self.m,TARGET,self.row('HS'+' '*15997+'x'));self.assertLess((time.process_time()-start)*1000,50)
 def test_eof_refusal_gap(self):
  s,p,b=self.scan([self.row('HS8517; '*33)]);r,status=s.page(target=TARGET)
  self.assertEqual(status,200);self.assertTrue(r['scan_complete']);self.assertFalse(r['evidence_complete']);self.assertTrue(r['coverage_gap']);self.assertEqual(r['articles_refused_mentions_limit'],1);self.assertEqual(r['items'],[]);self.assertIn('1 article refused',r['coverage_message']);self.assertEqual(b.code,0)
 def test_eof_checked_not_allnews(self):
  s,p,b=self.scan([self.row('Plain story')]);r,_=s.page(target=TARGET);self.assertTrue(r['scan_complete']);self.assertFalse(r['evidence_complete']);self.assertFalse(r['coverage_gap']);self.assertEqual(r['articles_checked'],1)
 def test_carry_preserves_article_and_refusals(self):
  rows=[self.row('HS8517; '*32,str(i))for i in range(60)]+[self.row('HS9999; '*33,'refused')]
  s,p,b=self.scan(rows);a,_=s.page(target=TARGET);b1,_=s.page(a['next_cursor']);c,_=s.page(b1['next_cursor'])
  self.assertEqual([len(x['items'])for x in(a,b1,c)],[25,25,10]);self.assertEqual(p.calls,1);self.assertEqual(c['articles_checked'],60);self.assertEqual(c['articles_refused_mentions_limit'],1);self.assertEqual(len(a['items'][0]['relationships']),32)
  calls=p.calls;replay,_=s.page(b1['next_cursor']);self.assertEqual(replay,c);self.assertEqual(p.calls,calls)
 def test_refusal_contract_malformed_closes(self):
  s,p,b=self.scan([self.row('x')]);s.match=lambda *a:dict(state='evidence_refused_mentions_limit',items=[{}],coverage='article_refused',not_exhaustive=True)
  self.assertEqual(s.page(target=TARGET)[1],503);self.assertEqual(b.code,0)
 def test_head_zero(self):
  s,p,b=self.scan([]);self.assertEqual(s.head()[1],200);self.assertEqual(p.calls,0)
class MatcherGuards(unittest.TestCase):
 def model(self):return Links([TARGET],[])
 def row(self,s='HS8517',**kw):return dict(article_key='a',title='Trade',summary=s,**kw)
 def test_nonempty_vocabulary_refused(self):
  m=self.model();m.rules=[{}]
  from integration.code_news_links import Refused
  with self.assertRaises(Refused):for_article(m,TARGET,self.row())
 def test_shape_summary_cap(self):
  from integration.code_news_links import Refused
  for row in [None,[],{},dict(title='Trade',summary='HS8517'),dict(article_key='a',title='',summary='HS8517'),self.row('x'*16001),self.row(None)]:
   with self.assertRaises(Refused):for_article(self.model(),TARGET,row)
  self.assertEqual(for_article(self.model(),TARGET,self.row('x'*16000))['state'],'checked')
 def test_unresolved_four_digit_skip(self):
  m=self.model();m.resolve=lambda *a:dict(state='ambiguous',items=[TARGET])
  self.assertEqual(for_article(m,TARGET,self.row())['items'],[])
 def test_exact_target_all_fields(self):
  m=self.model()
  for k,v in [('system','IN'),('edition','1999'),('code','8518')]:
   t=dict(TARGET);t[k]=v;self.assertEqual(for_article(m,t,self.row())['items'],[])
  self.assertEqual(len(for_article(m,TARGET,self.row())['items']),1)
 def test_not_legal_verification(self):self.assertIs(for_article(self.model(),TARGET,self.row())['items'][0]['legal_classification_verified'],False)

class CursorGuards(unittest.TestCase):
 def make(self,rows=None):
  self.now=0;self.p=Parent(rows or [dict(article_key='a',title='Trade',summary='HS8517')]);self.b=SharedBudget();m=Links([TARGET],[])
  self.s=Scan(self.p,lambda t,r:for_article(m,t,r),self.b,clock=lambda:self.now);return self.s
 def test_continue_and_budget_stop_not_scancomplete(self):
  s=self.make();self.p.eof=False;r,_=s.page(target=TARGET);self.assertFalse(r['scan_complete']);self.assertFalse(r['complete']);self.assertFalse(r['evidence_complete'])
  for _ in range(19):r,_=s.page(r['next_cursor'])
  self.assertEqual(r['state'],'budget_stopped_incomplete');self.assertEqual(r['parent_pages'],20);self.assertFalse(r['scan_complete']);self.assertFalse(r['evidence_complete']);self.assertIsNone(r['next_cursor']);self.assertEqual(self.b.code,0);self.assertEqual(self.p.closed,['parent'])
 def test_reply_bytecap(self):
  s=self.make([dict(article_key=str(i))for i in range(25)]);s.match=lambda t,r:dict(state='checked',items=[{'evidence':'x'*22000}],coverage='bounded_explicit_mentions_checked',not_exhaustive=True)
  r,status=s.page(target=TARGET);self.assertEqual(status,503);self.assertEqual(r['state'],'page_refused');self.assertEqual(self.b.code,0)
 def test_parent_bytes_rows(self):
  for rows in [[{'big':'x'*2097152}],[dict(article_key=str(i))for i in range(101)]]:
   s=self.make(rows);self.assertEqual(s.page(target=TARGET)[1],503);self.assertEqual(self.b.code,0);self.assertEqual(self.p.closed,['parent'])
 def test_report_item_cap32(self):
  s=self.make();s.match=lambda *a:dict(state='checked',items=[{}]*33,coverage='bounded_explicit_mentions_checked',not_exhaustive=True)
  self.assertEqual(s.page(target=TARGET)[1],503);self.assertEqual(self.b.code,0)
 def test_clock_minute_quota(self):
  s=self.make();s.calls=20;s.minute=0
  self.assertEqual(s.page(target=TARGET)[1],429);self.assertEqual(self.p.calls,0);self.assertEqual(self.b.code,0)
  self.now=60;self.assertEqual(s.page(target=TARGET)[1],200);self.assertEqual(self.p.calls,1)
 def test_idle_120_boundary(self):
  s=self.make();self.p.eof=False;r,_=s.page(target=TARGET);self.now=120
  self.assertEqual(s.page(r['next_cursor'])[1],410);self.assertEqual(self.b.code,0);self.assertEqual(self.p.closed,['parent'])
 def test_target_mismatch_410_noadvance(self):
  s=self.make();self.p.eof=False;r,_=s.page(target=TARGET);other=dict(TARGET,edition='wrong')
  self.assertEqual(s.page(r['next_cursor'],target=other)[1],410);self.assertEqual(self.p.calls,1);self.assertEqual(self.b.code,1)
 def test_shared_code_cap4(self):
  s=self.make();self.p.eof=False
  for _ in range(4):self.assertEqual(s.page(target=TARGET)[1],200)
  self.assertEqual(s.page(target=TARGET)[1],429);self.assertEqual(self.p.calls,4)
 def test_close_done(self):
  s=self.make();r,_=s.page(target=TARGET);self.assertTrue(r['scan_complete']);self.assertEqual(self.p.closed,['parent']);self.assertEqual(self.b.code,0)
 def test_exhausted_strict_bool(self):
  for value in [1,0,'true',None]:
   s=self.make();self.p.eof=value;self.assertEqual(s.page(target=TARGET)[1],503);self.assertEqual(self.b.code,0)
 def test_not_exhaustive_true(self):
  for value in [False,1,'true',None]:
   s=self.make();s.match=lambda *a:dict(state='checked',items=[],coverage='bounded_explicit_mentions_checked',not_exhaustive=value)
   self.assertEqual(s.page(target=TARGET)[1],503);self.assertEqual(self.b.code,0)
 def test_malformed_article_whole_scan_closed(self):
  s=self.make([dict(article_key='a',title='Trade')]);r,status=s.page(target=TARGET);self.assertEqual(status,503);self.assertEqual(r['state'],'page_refused');self.assertEqual(self.b.code,0);self.assertEqual(self.p.closed,['parent'])
 def test_plural_grammar(self):
  s=self.make([dict(article_key=str(i),title='Trade',summary='HS8517; '*33)for i in range(2)]);r,_=s.page(target=TARGET);self.assertIn('2 articles refused',r['coverage_message'])
class IsolatedBoundaryTests(unittest.TestCase):
 def test_unresolved_4digit_never_inspects_candidates(self):
  class Candidates:
   def __iter__(self):raise AssertionError('Unresolved four-digit candidates must not be inspected')
  m=Links([TARGET],[]);m.resolve=lambda *a:dict(state='ambiguous',items=Candidates())
  self.assertEqual(for_article(m,TARGET,dict(article_key='a',title='Trade',summary='HS8517'))['items'],[])
 def scan(self,rows):
  self.p=Parent(rows);self.b=SharedBudget()
  return Scan(self.p,lambda *a:dict(state='checked',items=[],coverage='bounded_explicit_mentions_checked',not_exhaustive=True),self.b)
 def test_parent_2MiB_cap_isolated_valid_match(self):
  rows=[dict(article_key='a',padding='x'*2097152)];s=self.scan(rows)
  r,status=s.page(target=TARGET);self.assertEqual(status,503);self.assertEqual(r['state'],'page_refused');self.assertEqual(self.b.code,0);self.assertEqual(self.p.closed,['parent'])
 def test_parent_101_rows_isolated_valid_match(self):
  s=self.scan([dict(article_key=str(i))for i in range(101)])
  r,status=s.page(target=TARGET);self.assertEqual(status,503);self.assertEqual(r['state'],'page_refused');self.assertEqual(self.b.code,0);self.assertEqual(self.p.closed,['parent'])
 def test_checked_coverage_exact(self):
  s=self.scan([dict(article_key='a')]);s.match=lambda *a:dict(state='checked',items=[],coverage='article_refused',not_exhaustive=True)
  r,status=s.page(target=TARGET);self.assertEqual(status,503);self.assertEqual(r['state'],'page_refused');self.assertEqual(self.b.code,0)
