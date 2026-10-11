import unittest
from unittest.mock import patch
from integration.news_pages import WholeGeoPages
from integration.public_live_builder import sanitize_public_geo_rows
from integration.code_news_links import Links
from integration.code_news_parent_prep import ResolveQuota
from integration.code_news_coverage_broker_prep import CoverageBroker
from tests.test_news_pages185 import Store,rows,F
T=dict(system='HS',edition='2022',code='8517',description='Phones');P={k:T[k]for k in ('system','edition','code')}
class Tests(unittest.TestCase):
 def make(self,n=60):
  self.now=0;data=rows(n)
  for row in data:row['title']='HS8517;';row['summary']=''
  self.store=Store(data);self.p=WholeGeoPages(self.store,sanitize_public_geo_rows,verified=True,clock=lambda:self.now,start_cleaner=False);self.addCleanup(self.p.close);self.m=Links([T],[]);self.quota=ResolveQuota();self.b=CoverageBroker(self.p,self.m,'a'*64,'v1',resolve_quota=self.quota);return self.b
 def next(self,r):return self.b.page(scope=r['next_cursor'],manifest='a'*64,matcher_version='v1')
 def test_firstEOF60carry25_25_10oneparent(self):
  b=self.make();a,_=b.page(P);b1,_=self.next(a);c,_=self.next(b1)
  self.assertEqual([len(x['items'])for x in(a,b1,c)],[25,25,10]);self.assertFalse(a['scan_complete']);self.assertTrue(c['scan_complete']);self.assertEqual(len(self.store.calls),1);self.assertIsNotNone(a['next_cursor']);self.assertNotEqual(a['next_cursor'],b1['next_cursor']);self.assertEqual(b.ledger.total(),1)
 def test_EOFwithtoken_carry_rotation(self):
  b=self.make(160);r,_=b.page(P);pages=[r]
  while r['next_cursor']:r,_=self.next(r);pages.append(r)
  self.assertEqual(len(self.store.calls),1);self.assertEqual(sum(len(x['items'])for x in pages),160);self.assertEqual(r['parent_pages'],2);self.assertTrue(r['scan_complete']);self.assertEqual(len({x['next_cursor']for x in pages[:-1]}),len(pages)-1)
 def test_refused_unreadable_count_once_replay(self):
  b=self.make();parent={'items':[dict(article_key=str(i),title='HS8517',summary='')for i in range(60)]+[dict(article_key='r',title='HS8517; '*33),dict(article_key='u',title=5)],'exhausted':True}
  with patch.object(self.p,'_page_locked',return_value=parent):
   a,_=b.page(P);r,_=self.next(a);replay,_=self.next(a);self.assertEqual(r,replay);c,_=self.next(r);replay2,_=self.next(r)
  self.assertEqual(c,replay2);self.assertEqual(c['articles_refused_mentions_limit'],1);self.assertEqual(c['articles_unreadable'],1);self.assertEqual(c['articles_unreadable_this_page'],1);self.assertEqual(c['articles_refused_this_page'],1);self.assertTrue(c['coverage_gap']);self.assertFalse(c['evidence_complete'])
 def test_empty_missing_null_checked_newadapter_Cunchanged(self):
  b=self.make();parent={'items':[dict(article_key='a',title=None,summary=None),dict(article_key='b'),dict(article_key='c',title='',summary='HS8517')],'exhausted':True}
  with patch.object(self.p,'_page_locked',return_value=parent):r,status=b.page(P)
  self.assertEqual(status,200);self.assertEqual(r['articles_checked'],3);self.assertEqual(len(r['items']),1);self.assertEqual(r['articles_unreadable'],0)
  from integration.code_news_links import Refused
  with self.assertRaises(Refused):self.m.for_news(dict(article_key='c',title='',summary='HS8517'))
 def test_wrong_type_oversize_unreadable_not503(self):
  b=self.make();parent={'items':[dict(article_key='a',title=1),dict(article_key='b',summary=[]),dict(article_key='c',title='x'*2001),dict(article_key='d',summary='x'*16001)],'exhausted':True}
  with patch.object(self.p,'_page_locked',return_value=parent):r,status=b.page(P)
  self.assertEqual(status,200);self.assertEqual(r['articles_unreadable'],4);self.assertTrue(r['coverage_gap'])
 def test_parent_page_caps_malformed503(self):
  for reply in [dict(items=[{}]*101,exhausted=True),dict(items=[{'x':'z'*2097152}],exhausted=True),dict(items=[],exhausted='true')]:
   b=self.make()
   with patch.object(self.p,'_page_locked',return_value=reply):self.assertEqual(b.page(P)[1],503)
   self.assertEqual(b.ledger.total(),0)
 def test_retained_parent_carry_requests_touch_idle(self):
  b=self.make(160);a,_=b.page(P)
  self.now=100;r,_=self.next(a);self.now=200;r,status=self.next(r);self.assertEqual(status,200);self.assertTrue(self.p.streams);self.assertEqual(next(iter(self.p.streams.values()))['used'],200)
  self.now=1800;self.assertEqual(self.next(r)[1],410)
 def test_quota_global_invalid_raised_lookup(self):
  b=self.make();calls=[]
  def bad(*a):calls.append(1);raise RuntimeError('private')
  self.m.resolve=bad
  for _ in range(10):self.assertEqual(b.page(P)[1],400)
  r,status=b.page(P);self.assertEqual(status,429);self.assertIn('New code scans are busy',r['message']);self.assertEqual(len(calls),10)
  self.now=60;self.assertEqual(b.page(P)[1],400);self.assertEqual(len(calls),11)
 def test_resolve_lock_released_before_lookup_HEADzero(self):
  b=self.make();held=[];original=self.m.resolve
  def resolve(*a):held.append((self.quota.lock.locked(),self.p.lock.locked()));return original(*a)
  self.m.resolve=resolve;self.assertEqual(b.head()[1],200);self.assertEqual(self.quota.attempts,0);b.page(P);self.assertEqual(held[0],(False,False))
 def test_carry_replay_no_parent_match_IO(self):
  b=self.make();a,_=b.page(P);r,_=self.next(a);counts=dict(b.contexts[next(iter(b.contexts))])
  with patch.object(self.p,'_page_locked',side_effect=AssertionError('parent')),patch.object(b,'_article',side_effect=AssertionError('matcher')):replay,status=self.next(a)
  self.assertEqual(status,200);self.assertEqual(replay,r);self.assertEqual(counts,b.contexts[next(iter(b.contexts))])
 def test_reply_cap_before_cache_503(self):
  b=self.make()
  with patch.object(b,'_article',return_value=('checked',[{'evidence':'x'*524288}])):self.assertEqual(b.page(P)[1],503)
  self.assertEqual(b.ledger.total(),0);self.assertEqual(b.replies,{})
 def test_budget20pages_aftercarry_incomplete(self):
  b=self.make(2500)
  for row in self.store.rows:row['title']='plain'
  r,_=b.page(P)
  for _ in range(19):r,status=self.next(r);self.assertEqual(status,200)
  self.assertEqual(r['parent_pages'],20);self.assertFalse(r['scan_complete']);self.assertFalse(r['evidence_complete']);self.assertEqual(r['state'],'budget_stopped_incomplete');self.assertIsNone(r['next_cursor'])
 def test_max100_unreadable_rows_perhold(self):
  b=self.make();reply={'items':[dict(article_key=str(i),title=5)for i in range(100)],'exhausted':False}
  with patch.object(self.p,'_page_locked',return_value=reply) as parent:r,_=b.page(P)
  self.assertEqual(parent.call_count,1);self.assertEqual(r['rows_consumed_this_page'],100);self.assertEqual(r['articles_unreadable'],100)

 def test_context_close_clear_and_four_complete_replay_slots(self):
  b=self.make(1)
  for _ in range(4):self.assertEqual(b.page(P)[1],200)
  self.assertEqual(b.page(P)[1],429);self.assertEqual(len(b.contexts),4)
  self.p.close();self.assertEqual(b.page(P)[1],503)
  # stopped-path finally pruning clears both replay and context.
  self.assertEqual(b.contexts,{});self.assertEqual(b.replies,{})
 def test_default_resolve_quota_shared(self):
  from integration.code_news_parent_prep import RESOLVE_QUOTA
  b=self.make();other=WholeGeoPages(Store(rows(1)),sanitize_public_geo_rows,verified=True,start_cleaner=False);self.addCleanup(other.close)
  c=CoverageBroker(other,self.m,'a'*64,'v1');self.assertIs(c.resolve_quota,RESOLVE_QUOTA)
  other2=WholeGeoPages(Store(rows(1)),sanitize_public_geo_rows,verified=True,start_cleaner=False);self.addCleanup(other2.close)
  d=CoverageBroker(other2,self.m,'a'*64,'v1');self.assertIs(d.resolve_quota,c.resolve_quota)
 def test_exact_target_all32_projection(self):
  b=self.make();parent={'items':[dict(article_key='a',title='HS8517; '*32,summary='',db_id='PRIVATE',provider='PRIVATE',url='PRIVATE')],'exhausted':True}
  with patch.object(self.p,'_page_locked',return_value=parent):r,status=b.page(P)
  self.assertEqual(status,200);self.assertEqual(len(r['items'][0]['relationships']),32)
  import json
  self.assertNotIn('PRIVATE',json.dumps(r));self.assertTrue(all(x['legal_classification_verified']is False for x in r['items'][0]['relationships']))
  self.assertEqual(r['items'][0]['relationships'][0]['target']['description'],'Phones')
 def test_concurrent_news_denied_during_match_under_lock(self):
  b=self.make();original=b._article;seen=[]
  def article(*a):seen.append(self.p.lock.locked());self.assertEqual(self.p.lock.acquire(False),False);return original(*a)
  b._article=article;b.page(P);self.assertTrue(all(seen))
 def test_unreadable_fault_clears_context(self):
  b=self.make()
  with patch.object(self.p,'_page_locked',return_value={'items':[],'exhausted':1}):self.assertEqual(b.page(P)[1],503)
  self.assertEqual(b.contexts,{});self.assertEqual(b.replies,{})
 def test_D_absolute_TTL_independent_parent(self):
  b=self.make(1);r,_=b.page(P);active=next(iter(b.ledger.rows));b.ledger.rows[active]['used']=1799;self.now=1800
  self.assertEqual(b.page(scope='A'*43,manifest='a'*64,matcher_version='v1')[1],410);self.assertEqual(b.ledger.rows,{})
 def test_preappend_payload_cap_independent_finalcap(self):
  from integration.code_news_parent_prep import Refused
  b=self.make();active='A'*43;b.ledger.reserve(active,{'target':T},0);b._initialize_locked(active)
  with patch.object(b,'_article',return_value=('checked',[{'evidence':'x'*510000}])):
   with self.assertRaises(Refused):b._finish_locked(active,{'items':[{'article_key':'a'}],'exhausted':True})
 def test_matching_delegates_C_empty_boundary(self):
  b=self.make();original=self.m.for_news
  with patch.object(self.m,'for_news',wraps=original) as matcher:
   state,links=b._article({'article_key':'a','title':'','summary':'HS8517'},T)
  self.assertEqual(state,'checked');self.assertEqual(len(links),1);matcher.assert_called_once_with({'article_key':'a','title':'\n','summary':'HS8517'})
 def test_nonempty_vocabulary_refused(self):
  from integration.code_news_parent_prep import Refused
  b=self.make();self.m.rules=[{}]
  with self.assertRaises(Refused):b._article({'article_key':'a','title':'HS8517'},T)
 def test_unresolved_heading_C_and_no_ambiguous_relationship(self):
  b=self.make();self.m=Links([T,dict(T,edition='2023')],[]);b.model=self.m
  self.assertEqual(self.m.for_news({'article_key':'a','title':'HS8517','summary':''})['items'],[])
  state,out=b._article({'article_key':'a','title':'HS8517'},T);self.assertEqual(state,'checked');self.assertEqual(out,[])
  with patch.object(self.m,'for_news',wraps=self.m.for_news) as matcher:b._article({'article_key':'a','title':'HS8517'},T)
  self.assertEqual(matcher.call_count,1)
 def test_target_exact_system_edition_code_not_codeonly(self):
  b=self.make();article={'article_key':'a','title':'HS8517'}
  for target in [dict(T,system='IN'),dict(T,edition='2023'),dict(T,code='9999')]:self.assertEqual(b._article(article,target),('checked',[]))
 def test_article_key_cap_and_controls_CRLF_normalized(self):
  b=self.make()
  for key in ['',None,'x'*101]:self.assertEqual(b._article({'article_key':key,'title':'HS8517'},T),('unreadable',[]))
  for field in ['title','summary']:
   row=dict(article_key='a',title='HS8517',summary='');row[field]='HS8517\x00';self.assertEqual(b._article(row,T),('unreadable',[]))
  for text in ['HS8517 phones\r\nmore','HS8517 phones\rmore']:
   self.assertEqual(len(b._article({'article_key':'x'*100,'title':text},T)[1]),1)
 def test_cached_body_headroom_cap_direct(self):
  from integration.code_news_parent_prep import Refused
  b=self.make();active='A'*43;b.ledger.reserve(active,{'target':T},0);b._initialize_locked(active)
  with patch('integration.code_news_coverage_broker_prep.json.dumps',return_value='x'*520001):
   with self.assertRaises(Refused):b._finish_locked(active,{'items':[],'exhausted':True})
 def test_budget_stop_closes_owned_cursor_not_other(self):
  b=self.make(2500)
  for row in self.store.rows:row['title']='plain'
  other=self.p.page(F);other_key=next(iter(self.p.streams));r,_=b.page(P);active=next(iter(b.ledger.rows));parent=b.ledger.rows[active]['parent'];cursor=self.p.streams[parent]['cursor'];other_cursor=self.p.streams[other_key]['cursor']
  for _ in range(19):r,_=self.next(r)
  self.assertEqual(cursor.closed,1);self.assertEqual(other_cursor.closed,0);self.assertEqual(r['state'],'budget_stopped_incomplete')
 def test_messages_singular_plural_and_initialize_replaces(self):
  b=self.make();active='A'*43;b.ledger.reserve(active,{'target':T},0);b._initialize_locked(active);b.contexts[active]['checked']=99;b._initialize_locked(active);self.assertEqual(b.contexts[active]['checked'],0)
  for n in [1,2]:
   b._initialize_locked(active);r,_=b._finish_locked(active,{'items':[{'article_key':str(i),'title':5}for i in range(n)]+[{'article_key':'r'+str(i),'title':'HS8517; '*33}for i in range(n)],'exhausted':True})
   noun='article'if n==1 else'articles';self.assertEqual(r['coverage_message'],f'{n} {noun} refused for too many code mentions; {n} {noun} unreadable. These are coverage gaps.')
