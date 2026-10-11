import unittest
from integration.code_news_scope_prep import *
from integration.code_news_links import Links
def token(s):return str(s).ljust(43,'_')
T=dict(system='HS',edition='2022',code='8517',description='Phones')
class Tests(unittest.TestCase):
 def setUp(self):self.m=Links([T],[]);self.p={k:T[k]for k in ('system','edition','code')};self.man='a'*64
 def test_resolve_before_parent_no_guess(self):
  calls=[]
  for code in ['9999','85','851700']:
   r=begin(self.m,dict(self.p,code=code),self.man,'v1',lambda r:calls.append(r));self.assertIsNone(r['target'])
  self.assertEqual(calls,[])
  r=begin(self.m,self.p,self.man,'v1',lambda r:calls.append(r)or'owned');self.assertEqual(r['parent'],'owned');self.assertEqual(len(calls),1)
 def test_ambiguity_omission_held(self):
  for state in ['ambiguous','conflicting_source_rows','not_in_link_model','unusable_description','unknown_code']:
   self.m.resolve=lambda *a:dict(state=state,items=[T]);r=begin(self.m,self.p,self.man,'v1',lambda r:(_ for _ in ()).throw(AssertionError('parent')));self.assertEqual(r['resolution'],state)
 def test_exact_target_fields_no_description_input(self):
  for p in [dict(self.p,description='guess'),dict(self.p,code='8517x'),dict(self.p,system='0'),dict(self.p,edition='x'*101)]:
   with self.assertRaises(Refused):target(self.m,p,self.man,'v1')
  self.m.resolve=lambda *a:dict(state='resolved',items=[dict(T,edition='wrong')])
  with self.assertRaises(Refused):target(self.m,self.p,self.man,'v1')
 def test_target_deepcopy_version_binding(self):
  row=dict(T);self.m.resolve=lambda *a:dict(state='resolved',items=[row]);r=target(self.m,self.p,self.man,'v1');row['description']='changed';self.assertEqual(r['target']['description'],'Phones');self.assertEqual(r['manifest'],self.man)
 def test_shared_12_news_4_D(self):
  l=Ledger()
  for i in range(12):l.admit(token(i),None,0)
  for i in range(4):l.admit(token('D'+str(i)),token('scope'+str(i)),0)
  with self.assertRaises(Busy):l.admit(token('extra'),None,0)
  with self.assertRaises(Busy):l.admit(token('extraD'),token('scope'),0)
 def test_D_replay_keeps_reservation(self):
  l=Ledger()
  for i in range(4):l.admit(token(i),token('scope'+str(i)),0);l.finish(token(i),token('scope'+str(i)),1)
  self.assertEqual(len(l.rows),4)
  with self.assertRaises(Busy):l.admit(token('fifth'),token('scope'),2)
  l.expire(121);l.admit(token('fifth'),token('scope'),121);self.assertEqual(len(l.rows),1)
 def test_scope_both_directions_noadvance_or_touch(self):
  l=Ledger();l.admit(token('News'),None,0);l.admit(token('D'),token('scope'),0);calls=[]
  for key,scope in [(token('News'),token('scope')),(token('D'),None),(token('D'),token('other'))]:
   with self.assertRaises(Expired):scoped_parent(l,key,scope,10,lambda:calls.append(1))
  self.assertEqual(calls,[]);self.assertEqual(l.rows[token('News')]['used'],0);self.assertEqual(l.rows[token('D')]['used'],0)
  self.assertEqual(scoped_parent(l,token('D'),token('scope'),10,lambda:'ok'),'ok')
 def test_expire_drop_direct_once(self):
  l=Ledger();l.admit(token('D'),token('scope'),0);r=l.rows[token('D')];l.expire(120);self.assertEqual(r['release_count'],1);self.assertIsNone(l.drop(token('D')));self.assertEqual(r['release_count'],1)
 def test_born1800_even_touched(self):
  l=Ledger();l.admit(token('n'),None,0)
  for n in range(100,1800,100):l.touch(token('n'),None,n)
  with self.assertRaises(Expired):l.own(token('n'),None,1800)
 def test_recursive_pagebusy_not_hang(self):
  from threading import Lock
  lock=Lock()
  def public_page():
   if not lock.acquire(False):raise Busy()
   try:return'public'
   finally:lock.release()
  calls=[]
  def internal_page_locked():
   if not lock.locked():raise Refused('Owner lock required')
   calls.append(1);return 'internal'
  with self.assertRaises(Refused):internal_page_locked()
  with lock:
   self.assertEqual(internal_page_locked(),'internal');self.assertEqual(calls,[1])
   with self.assertRaises(Busy):public_page()
class Boundaries(unittest.TestCase):
 def setUp(self):self.m=Links([T],[]);self.p={k:T[k]for k in ('system','edition','code')}
 def test_lowercase_system_and_one_digit_refused(self):
  for p in [dict(self.p,system='hs'),dict(self.p,code='8')]:
   with self.assertRaises(Refused):target(self.m,p,'a'*64,'v1')
 def test_version_regex(self):
  for version in ['', 'x'*41,'v/1','v 1',None,True]:
   with self.assertRaises(Refused):target(self.m,self.p,'a'*64,version)
 def test_two_resolved_rows_refused(self):
  self.m.resolve=lambda *a:dict(state='resolved',items=[T,T])
  with self.assertRaises(Refused):target(self.m,self.p,'a'*64,'v1')
 def test_duplicate_capability_refused(self):
  l=Ledger();l.admit(token('a'),None,0)
  with self.assertRaises(Refused):l.admit(token('a'),None,1)
 def test_idle120_exact(self):
  l=Ledger();l.admit(token('a'),None,0);l.own(token('a'),None,119)
  with self.assertRaises(Expired):l.own(token('a'),None,120)
 def test_begin_parent_mutation_cannot_change_result(self):
  def parent(r):r['target']['description']='mutated';r['manifest']='changed';return 'parent'
  out=begin(self.m,self.p,'a'*64,'v1',parent);self.assertEqual(out['target']['description'],'Phones');self.assertEqual(out['manifest'],'a'*64)
 def test_strict_ledger_inputs(self):
  for key,scope,now in [('a',None,0),(True,None,0),(token('a'),'scope',0),(token('a'),False,0),(token('a'),None,True),(token('a'),None,float('nan')),(token('a'),None,-1)]:
   with self.assertRaises(Refused):Ledger().admit(key,scope,now)
 def test_admit_sweeps_before_capacity(self):
  l=Ledger()
  for n in range(16):l.admit(token(n),None,0)
  l.admit(token('new'),None,120);self.assertEqual(l.total(),1)
 def test_expired_between_own_and_advance(self):
  l=Ledger();l.admit(token('a'),token('s'),0);l.own(token('a'),token('s'),119);calls=[]
  with self.assertRaises(Expired):scoped_parent(l,token('a'),token('s'),120,lambda:calls.append(1))
  self.assertEqual(calls,[])
 def test_first_pageEOF_Dreservation_no_doublecount(self):
  l=Ledger();l.admit(token('D'),token('s'),0);self.assertEqual(l.total(),1);l.finish(token('D'),token('s'),1,first_page=True)
  self.assertNotIn(token('D'),l.streams);self.assertIn(token('D'),l.rows);self.assertEqual(l.total(),1)
 def test_EOFwithtoken_counts_once(self):
  l=Ledger();l.admit(token('D'),token('s'),0);l.finish(token('D'),token('s'),1)
  self.assertIn(token('D'),l.streams);self.assertEqual(l.total(),1)
 def test_parentexpiry_Dcarry410_release_once(self):
  l=Ledger();l.admit(token('D'),token('s'),0);r=l.rows[token('D')];l.parent_expired(token('D'))
  with self.assertRaises(Expired):l.own(token('D'),token('s'),1)
  l.parent_expired(token('D'));self.assertEqual(r['release_count'],1);self.assertEqual(l.total(),0)
 def test_close_clears_ledger_streams(self):
  l=Ledger();l.admit(token('n'),None,0);l.admit(token('D'),token('s'),0);l.finish(token('D'),token('s'),1,first_page=True);rows=list(l.rows.values());l.close();l.close()
  self.assertEqual(l.rows,{});self.assertEqual(l.streams,{});self.assertEqual(l.total(),0);self.assertTrue(all(r['release_count']==1 for r in rows))
 def test_Dreplays_do_not_avoid_borncap(self):
  l=Ledger();l.admit(token('D'),token('s'),0);l.finish(token('D'),token('s'),1)
  for now in range(100,1800,100):l.touch(token('D'),token('s'),now)
  with self.assertRaises(Expired):l.touch(token('D'),token('s'),1800)
  self.assertEqual(l.total(),0)
 def test_HEAD_no_model_parent(self):
  from unittest.mock import patch
  with patch('integration.code_news_scope_prep.target',side_effect=AssertionError('resolve')):self.assertEqual(head()[1],200)
 def test_resume_versions_refuse_before_advance(self):
  l=Ledger();l.admit(token('D'),token('s'),0);calls=[]
  binding={'manifest':'a'*64,'matcher_version':'v1'}
  for current in [dict(binding,manifest='b'*64),dict(binding,matcher_version='v2')]:
   l=Ledger();l.admit(token('D'),token('s'),0)
   with self.assertRaises(Expired):bound_resume(l,token('D'),token('s'),1,binding,current,lambda:calls.append(1))
  self.assertEqual(calls,[]);self.assertNotIn(token('D'),l.rows);self.assertEqual(l.total(),0)
class FinalBoundaries(unittest.TestCase):
 def test_news_first_page_EOF_drops_immediately(self):
  l=Ledger();l.admit(token('news'),None,0);r=l.rows[token('news')];l.finish(token('news'),None,1,first_page=True)
  self.assertNotIn(token('news'),l.rows);self.assertNotIn(token('news'),l.streams);self.assertEqual(l.total(),0);self.assertEqual(r['release_count'],1)
 def test_invalid_clock_all_entrypoints(self):
  for now in [float('nan'),float('inf'),-1,True,'now']:
   for method in ['admit','own','touch']:
    l=Ledger()
    if method!='admit':l.admit(token('a'),None,0)
    with self.assertRaises(Refused):getattr(l,method)(token('a'),None,now)
 def test_drift_releases_owned_only_once(self):
  for current in [{'manifest':'b','matcher_version':'v1'},{'manifest':'a','matcher_version':'v2'}]:
   l=Ledger();l.admit(token('D'),token('s'),0);r=l.rows[token('D')];calls=[]
   with self.assertRaises(Expired):bound_resume(l,token('D'),token('s'),1,{'manifest':'a','matcher_version':'v1'},current,lambda:calls.append(1))
   self.assertEqual(calls,[]);self.assertEqual(l.total(),0);self.assertEqual(r['release_count'],1)
   with self.assertRaises(Expired):bound_resume(l,token('D'),token('s'),2,{},current,lambda:calls.append(1))
   self.assertEqual(r['release_count'],1)
 def test_unowned_drift_cannot_drop_other_slot(self):
  l=Ledger();l.admit(token('D'),token('s'),0)
  with self.assertRaises(Expired):bound_resume(l,token('D'),None,1,{}, {'manifest':'wrong'},lambda:None)
  self.assertEqual(l.total(),1)
