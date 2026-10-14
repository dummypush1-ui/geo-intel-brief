import unittest,hashlib,dataclasses,json,ast
from unittest.mock import Mock,patch
from pathlib import Path
from integration import commodity_candidate_eval as c
SNAP=c.HeadingSnapshot('SYN','fixture-only','9999','Synthetic fixture: imaginary grain')
HASH=hashlib.sha256(SNAP.description.encode()).hexdigest()
def rule(**kw):return c.DraftRule(**dict(dict(id='synthetic-rule',system='SYN',edition='fixture-only',code='9999',description_sha256=HASH,phrases=('fixturegrain',),trade_cues=('export',),exclude_phrases=('video game',)),**kw))
def row(title='Fixturegrain export',summary=''):return dict(article_key='synthetic',title=title,summary=summary)
def run(rr=None,aa=None,resolve=None):return c.evaluate((rule(),)if rr is None else rr,(row(),)if aa is None else aa,resolve or(lambda *a:SNAP))
class Tests(unittest.TestCase):
 def test_candidate_determinism_fields(self):
  x=run();self.assertEqual(x,run());self.assertEqual(x['state'],'candidate_not_enabled');self.assertEqual(x['review_refs_state'],'supplied_unverified');self.assertIs(x['legal_classification_verified'],False);self.assertEqual(x['items'][0]['candidates'][0]['matched_phrases'],[dict(phrase='fixturegrain',source_field='title')]);self.assertIn('not legal',x['warning']);self.assertNotIn('score',str(x))
 def test_ref_inert(self):self.assertEqual(run((rule(review_refs=('trusted approved urgent',)),)),run((rule(review_refs=('unreviewed rejected',)),)))
 def test_cue_exclusion_boundary(self):
  for title in ['fixturegrain harvest','fixturegrain export video game','fakefixturegrain export','fixturegrains export']:
   self.assertEqual(run(aa=(row(title),))['items'][0]['candidates'],[])
  self.assertEqual(len(run(aa=(row('fixturegrain; export!'),))['items'][0]['candidates']),1)
 def test_casefold_unicode(self):
  r=rule(phrases=('STRASSE',));self.assertEqual(len(run((r,),(row('Straße export'),))['items'][0]['candidates']),1)
  for terms in [('a','A'),('ss','ß'),('',),('---',),(' trim ',)]:self.assertEqual(run((rule(phrases=terms),)),{'state':'unavailable'})
 def test_synthetic_only(self):
  for kw in [dict(system='HS'),dict(edition='2022'),dict(code='1006'),dict(code='999999')]:self.assertEqual(run((rule(**kw),)),{'state':'unavailable'})
  self.assertEqual(run(resolve=lambda *a:c.HeadingSnapshot('SYN','fixture-only','9999','Actual rice heading')),{'state':'unavailable'})
 def test_closed_callback_and_hash(self):
  for value in [dict(system='SYN',edition='fixture-only',code='9999',description=SNAP.description,sha256=HASH),c.HeadingSnapshot('SYN','fixture-only','9999','Synthetic fixture: changed'),object()]:self.assertEqual(run(resolve=lambda *a:value),{'state':'unavailable'})
  class Sub(c.HeadingSnapshot):pass
  self.assertEqual(run(resolve=lambda *a:Sub(*dataclasses.astuple(SNAP))),{'state':'unavailable'})
 def test_failure_no_text(self):
  for ex in [RuntimeError('SECRET'),TimeoutError('SECRET')]:self.assertEqual(run(resolve=Mock(side_effect=ex)),{'state':'unavailable'})
 def test_upfront_validation_before_callback(self):
  cases=[((rule(),)*21,(row(),)),((rule(),rule(id='other')),(row(),)),((rule(phrases=('x',)*21),),(row(),)),((rule(),),(row(),)*101),((rule(),),(dict(row(),private='SECRET'),)),((rule(),),(row('x'*2001),))]
  for rr,aa in cases:
   cb=Mock(side_effect=AssertionError('callback'));self.assertEqual(run(rr,aa,cb),{'state':'unavailable'});cb.assert_not_called()
 def test_text_and_surrogates(self):
  for bad in ['\x00','\u202e','\ud800','\u2028','\u2029','\n']:
   self.assertEqual(run((rule(phrases=('a'+bad,),),)),{'state':'unavailable'});self.assertEqual(run(aa=(row('x'+bad),)),{'state':'unavailable'})
 def test_bytes_and_work_caps(self):
  cb=Mock(return_value=SNAP);aa=tuple(dict(article_key=str(i),title='😀'*2000,summary='😀'*8000)for i in range(10));self.assertEqual(run(aa=aa,resolve=cb),{'state':'unavailable'});cb.assert_not_called()
  with patch.object(c,'MAX_WORK',1):self.assertEqual(run(),{'state':'unavailable'})
  with patch.object(c,'MAX_BYTES',150):self.assertEqual(run(),{'state':'unavailable'})
 def test_no_io_and_import_scan(self):
  source=Path(c.__file__).read_text();tree=ast.parse(source);imports=[]
  for n in ast.walk(tree):
   if isinstance(n,ast.Import):imports.extend(a.name for a in n.names)
   if isinstance(n,ast.ImportFrom):imports.append(n.module)
  self.assertEqual(set(imports),{'dataclasses','hashlib','json','unicodedata','integration.code_news_links'})
  with patch('builtins.open',side_effect=AssertionError('IO')),patch('socket.socket',side_effect=AssertionError('network')):self.assertEqual(run()['state'],'candidate_not_enabled')
 def test_production_unchanged(self):
  from integration.code_news_links import Links
  from integration.code_news_matcher_prep import for_article,Refused
  from integration.code_news_disk import DiskLinks
  self.assertIn('self.rules=[]',Path(__import__('integration.code_news_disk',fromlist=['']).__file__).read_text())
  self.assertIn("if self.model.rules:raise Refused('Explicit-only vocabulary required')",Path(__import__('integration.code_news_coverage_broker_prep',fromlist=['']).__file__).read_text())
  model=Links([dict(system='HS',edition='fixture-only',code='9999',description='Synthetic fixture heading')],[]);model.rules=[object()]
  with self.assertRaises(Refused):for_article(model,{},row())

 def test_ambiguity_all_not_first(self):
  rules=(rule(id='z',system='SYA'),rule(id='a',system='SYB'))
  cb=lambda system,edition,code:c.HeadingSnapshot(system,edition,code,SNAP.description)
  x=run(rules,resolve=cb);self.assertEqual(x['items'][0]['state'],'ambiguous_candidates');self.assertEqual([v['rule_id']for v in x['items'][0]['candidates']],['a','z']);self.assertEqual(run(tuple(reversed(rules)),resolve=cb),x)
 def test_mutants(self):
  source=Path(c.__file__).read_text()
  cases=[('not matched or not cues or excluded','not matched or excluded','cue'),('not matched or not cues or excluded','not matched or not cues','exclude'),(' or actual!=r.description_sha256','','hash'),("(r.edition,r.code)!=('fixture-only','9999')","(r.edition,r.code)!=('fixture-only','999999')",'heading'),('candidates=candidates))','candidates=candidates[:1]))','first'),('legal_classification_verified=False','legal_classification_verified=True','legal'),('actual=heading(snap)','actual=r.description_sha256','trusthash'),('if identity in identities:raise ValueError()','if False:raise ValueError()','duplicate'),("except Exception:return {'state':'unavailable'}","except Exception as e:return {'state':'unavailable','error':str(e)}",'exception'),("review_refs_state='supplied_unverified'","review_refs_state=str(rules[0].review_refs)",'review')]
  for old,new,kind in cases:
   self.assertIn(old,source);ns={'__name__':'mutant_'+kind};import sys,types
   module=types.ModuleType(ns['__name__']);sys.modules[ns['__name__']]=module;exec(compile(source.replace(old,new),kind,'exec'),module.__dict__);m=module
   def mr(**kw):return m.DraftRule(**dict(dict(id='r',system='SYN',edition='fixture-only',code='9999',description_sha256=HASH,phrases=('fixturegrain',),trade_cues=('export',),exclude_phrases=('video game',)),**kw))
   snap=m.HeadingSnapshot('SYN','fixture-only','9999',SNAP.description);cb=lambda *a:snap
   if kind=='cue':self.assertTrue(m.evaluate((mr(),),(row('fixturegrain harvest'),),cb)['items'][0]['candidates'])
   elif kind=='exclude':self.assertTrue(m.evaluate((mr(),),(row('fixturegrain export video game'),),cb)['items'][0]['candidates'])
   elif kind in ('hash','trusthash'):self.assertNotEqual(m.evaluate((mr(description_sha256='0'*64),),(row(),),cb),{'state':'unavailable'})
   elif kind=='heading':
    # Both independent identity guards must be removed to admit a detailed target.
    widened=source.replace("('fixture-only','9999')","('fixture-only','999999')");exec(compile(widened,'heading-both','exec'),module.__dict__);snap=m.HeadingSnapshot('SYN','fixture-only','999999',SNAP.description);self.assertNotEqual(m.evaluate((mr(code='999999'),),(row(),),lambda *a:snap),{'state':'unavailable'})
   elif kind=='first':
    rr=(mr(id='a',system='SYA'),mr(id='z',system='SYB'));cb=lambda system,edition,code:m.HeadingSnapshot(system,edition,code,SNAP.description);self.assertEqual(len(m.evaluate(rr,(row(),),cb)['items'][0]['candidates']),1)
   elif kind=='legal':self.assertTrue(m.evaluate((mr(),),(row(),),cb)['legal_classification_verified'])
   elif kind=='duplicate':self.assertNotEqual(m.evaluate((mr(),mr(id='other')),(row(),),cb),{'state':'unavailable'})
   elif kind=='exception':self.assertIn('SECRET',str(m.evaluate((mr(),),(row(),),Mock(side_effect=ValueError('SECRET')))))
   elif kind=='review':self.assertNotEqual(m.evaluate((mr(review_refs=('A',)),),(row(),),cb),m.evaluate((mr(review_refs=('B',)),),(row(),),cb))
  # Boundary helper mutation allows substring matches; production refuses it.
  with patch.object(c,'phrase',side_effect=lambda t,s:t.casefold()in s.casefold()):self.assertTrue(run(aa=(row('fakefixturegrain export'),))['items'][0]['candidates'])

 def test_import_traps(self):
  source=Path(c.__file__).read_text();import types,sys
  m=types.ModuleType('c1_import_trap');sys.modules[m.__name__]=m
  with patch('builtins.open',side_effect=AssertionError('IO')),patch('socket.socket',side_effect=AssertionError('network')),patch('os.getenv',side_effect=AssertionError('env')):exec(compile(source,'c1','exec'),m.__dict__)
 def test_callback_once_and_sort(self):
  cb=Mock(return_value=SNAP);run(aa=(dict(row(),article_key='z'),dict(row(),article_key='a')),resolve=cb);cb.assert_called_once_with('SYN','fixture-only','9999')
 def test_closed_rules_and_cap(self):
  for bad in [dict(id='fake'),None]:self.assertEqual(run((bad,)),{'state':'unavailable'})
  self.assertEqual(run((rule(),rule())),{'state':'unavailable'})
  with patch.object(c,'MAX_BYTES',400):
   self.assertEqual(run(aa=tuple(dict(row(),article_key=str(i))for i in range(3))),{'state':'unavailable'})

 def test_direct_boundaries(self):
  cb=lambda system,edition,code:c.HeadingSnapshot(system,edition,code,SNAP.description)
  self.assertEqual(run((rule(id='same'),rule(id='same',system='SYA')),resolve=cb),{'state':'unavailable'})
  for kw in [dict(phrases=()),dict(trade_cues=())]:self.assertEqual(run((rule(**kw),)),{'state':'unavailable'})
  self.assertEqual(run((rule(exclude_phrases=()),))['state'],'candidate_not_enabled')
  self.assertEqual(run(aa=(row(),row())),{'state':'unavailable'})
  self.assertEqual(run(rr=[rule()]),{'state':'unavailable'});self.assertEqual(run(aa=[row()]),{'state':'unavailable'})
  snap=c.HeadingSnapshot('SYN','fixture-only','9999','Wrong prefix synthetic');r=rule(description_sha256=hashlib.sha256(snap.description.encode()).hexdigest());self.assertEqual(run((r,),resolve=lambda *a:snap),{'state':'unavailable'})
 def test_sort_fields_articles(self):
  r=rule(phrases=('zgrain','agrain'),trade_cues=('ztrade','atrade'),exclude_phrases=())
  aa=(dict(row('zgrain agrain ztrade atrade'),article_key='z'),dict(row('zgrain agrain ztrade atrade'),article_key='a'))
  x=run((r,),aa);self.assertEqual([i['article_key']for i in x['items']],['a','z']);v=x['items'][0]['candidates'][0];self.assertEqual([e['phrase']for e in v['matched_phrases']],['agrain','zgrain']);self.assertEqual([e['phrase']for e in v['trade_cues']],['atrade','ztrade'])
 def test_review_ref_bounds(self):
  for refs,ok in [(('x',)*10,True),(('x',)*11,False),(('x'*200,),True),(('x'*201,),False)]:self.assertEqual(run((rule(review_refs=refs),))['state'],'candidate_not_enabled'if ok else'unavailable')
 def test_unmatched_and_same_word(self):
  x=run(aa=(row('unmatched'),));self.assertEqual(x['items'][0],dict(article_key='synthetic',state='candidate_not_enabled',candidates=[]));self.assertEqual(x['review_refs_state'],'supplied_unverified')
  r=rule(phrases=('fixturegrain',),trade_cues=('fixturegrain',),exclude_phrases=());self.assertTrue(run((r,),(row('fixturegrain'),))['items'][0]['candidates'])
