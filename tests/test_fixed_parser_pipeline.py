import unittest,copy,ast
from datetime import datetime,timezone,timedelta
from unittest.mock import patch
from integration.fixed_parser_pipeline import *
D=datetime(2026,1,2,12,tzinfo=timezone.utc)
def outcome(t='Trade tariff '+'x'*800):return {'download':'text','extract':'text','text':t}
class Tests(unittest.TestCase):
 def run_case(self,case='rss',o=None,**kw):return prepare_fixed_parser_pipeline(case,{'https://example.invalid/one':outcome()} if o is None else o,synthetic=True,cutoff=D.replace(day=1),fallback_clock=D,**kw)
 def test_rss_atom_bozo_empty_and_copies(self):
  for case,url in [('rss','one'),('atom','atom')]:
   o={'https://example.invalid/'+url:outcome()};old=copy.deepcopy(o);r=self.run_case(case,o);self.assertTrue(r['selected_candidates']);r['enriched_candidates'][0]['summary']='change';self.assertNotEqual(r['selected_candidates'][0]['summary'],'change');self.assertEqual(o,old)
  for case in ('empty','broken_empty','broken_entries','internal_entity','empty_dates'):self.assertEqual(self.run_case(case,{})['selection_state'],'selected_empty')
 def test_missing_unused_disabled_unavailable(self):
  for case,o in [('rss',{}),('empty',{'unused':outcome()})]:
   with self.assertRaises(FixedPipelineRefused):self.run_case(case,o)
  for kw in ({'enabled':False},{'available':False}):self.assertFalse(self.run_case(o={},**kw)['enrichment_trace'])
 def test_raw_invalid_allpins_before_child(self):
  with patch('integration.feedparser_audit.runner.run_fixed_parser',side_effect=AssertionError('child ran')):
   for kw in ({'categories':['x'*101]},{'max_chars':True}):
    with self.assertRaises(FixedPipelineRefused):self.run_case(**kw)
   with self.assertRaises(FixedPipelineRefused):self.run_case(o={'   ':outcome()})
   for p in PINS:
    with patch.dict(PINS,{p:'0'*64}):
     with self.assertRaises(FixedPipelineRefused):self.run_case()
 def test_non_utc_preserved_and_rawboundary(self):
  r=self.run_case('atom',{'https://example.invalid/atom':outcome()});d=r['selected_candidates'][0]['published'];self.assertEqual(d.utcoffset(),timedelta(0));self.assertEqual(d.astimezone(timezone.utc),D)
  bad=datetime(1970,1,1,tzinfo=timezone(timedelta(hours=1)))
  with self.assertRaises(FixedPipelineRefused):prepare_fixed_parser_pipeline('empty',{},synthetic=True,cutoff=bad,fallback_clock=D)
 def test_child_output_duplication_budget(self):
  # Trusted test fault only, no runtime caller XML/child extension.
  fake={'candidates':[{'title':'Trade tariff','url':'https://example.invalid/one','source':'Synthetic','credibility':'HIGH','summary':'x'*10000,'published':D.isoformat()}]*100,'corpus_hash':'fixed','feedparser_version':'6.0.11','backend':'fixed','bozo':False,'bozo_label':'flag','field_presence':[]}
  with patch('integration.feedparser_audit.runner.run_fixed_parser',return_value=fake):
   with self.assertRaises(FixedPipelineRefused):self.run_case(o={})
 def test_independent_enrichment_docs_oracle(self):
  from integration.feedparser_audit.runner import run_fixed_parser
  from intelligence.geo.processing.classifier import classify
  from intelligence.geo.processing.dedupe import dedupe_articles
  parsed=run_fixed_parser('rss',cutoff=D.replace(day=1),fallback_clock=D);selected=[dict(r,published=datetime.fromisoformat(r['published'])) for r in parsed['candidates']]
  class Provider:
   def fetch_url(self,u):return 'handle'
   def extract(self,*a,**k):return outcome()['text']
  class Executor:
   def __init__(self,**kw):pass
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def map(self,fn,rows):return map(fn,rows)
  defs=[];scope={'HAS_TRAFILATURA':True,'ENABLE_FULL_TEXT':True,'FULL_TEXT_MAX_CHARS':700,'FULL_TEXT_WORKERS':1,'trafilatura':Provider(),'ThreadPoolExecutor':Executor,'classify':classify,'dedupe_articles':dedupe_articles,'DEDUPE_THRESHOLD':.85,'ACTIVE_CATEGORIES':['TRADE']}
  for p,name in [('intelligence/geo/collectors/rss.py','_enrich_with_full_text'),('intelligence/geo/processing/extract.py','extract_full_text')]:defs.append(next(n for n in ast.parse((ROOT/p).read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name==name))
  exec(compile(ast.Module(body=defs,type_ignores=[]),'independent-fixedpipeline-enrichment','exec'),scope);enriched=scope['_enrich_with_full_text'](copy.deepcopy(selected));expected=copy.deepcopy(enriched);scope['candidates']=enriched;tree=ast.parse((ROOT/'intelligence/geo/collectors/rss.py').read_bytes());collect=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='collect');exec(compile(ast.Module(body=collect.body[5:9],type_ignores=[]),'independent-fixedpipeline-docs','exec'),scope)
  r=self.run_case();self.assertEqual(r['selected_candidates'],selected);self.assertEqual(r['enriched_candidates'],expected);self.assertEqual(r['documents'],scope['docs'])
