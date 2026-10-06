import unittest,copy
from unittest.mock import patch
from datetime import datetime,timezone,timedelta
from integration.supplied_collector_pipeline import *
D=datetime(2026,1,2,12,tzinfo=timezone.utc);SPEC=('Fixture','https://example.invalid/feed','HIGH');URL='https://example.invalid/story'
def row(**kw):return {'title':'Trade tariff new order','link':URL,'summary':'Tariff','published':D.isoformat()}|kw
def outcome(text='Trade tariff '+'x'*800):return {'download':'text','extract':'text','text':text}
class Tests(unittest.TestCase):
 def run_case(self,rows=None,o=None,**kw):return prepare_supplied_pipeline(SPEC,[row()] if rows is None else rows,{URL:outcome()} if o is None else o,cutoff=D-timedelta(days=1),fallback_clock=D,**kw)
 def test_composition_order_private_fields_aliases(self):
  rows=[row(),row()];o={URL:outcome()};before=copy.deepcopy((rows,o));r=self.run_case(rows,o)
  self.assertEqual(len(r['enrichment_trace']),4);self.assertEqual(r['prepared_count'],1);self.assertLessEqual(len(r['documents'][0]['summary']),300)
  r['enriched_candidates'][0]['summary']='changed';self.assertEqual(r['selected_candidates'][0]['summary'],'Tariff');self.assertNotEqual(r['documents'][0]['summary'],'changed');self.assertEqual((rows,o),before)
 def test_empty_modes_and_errors(self):
  r=self.run_case([],{});self.assertEqual(r['source_state'],'selected_empty')
  for kw in ({'enabled':False},{'available':False}):self.assertFalse(self.run_case(o={},**kw)['enrichment_trace'])
  for kw in ({'http_mode':'error'},{'parser_mode':'error'}):
   self.assertEqual(self.run_case(o={},**kw)['source_state'],'declared_error')
   with self.assertRaises(PipelineRefused):self.run_case(**kw)
 def test_missing_unused_selected_boundary_no_output(self):
  for rows,o in (([row()],{}),([],{URL:outcome()}),([row(link='x'*2001)],{'x'*2001:outcome()})):
   with self.assertRaises(PipelineRefused):self.run_case(rows,o)
 def test_malformed_config_before_stage(self):
  for kw in ({'categories':['x'*101]},{'max_chars':True},{'threshold':float('nan')},{'enabled':1}):
   with patch('integration.supplied_feed_fixture.prepare_supplied_feed',side_effect=AssertionError('stage ran')):
    with self.assertRaises(PipelineRefused):self.run_case(**kw)
  with patch('integration.supplied_feed_fixture.prepare_supplied_feed',side_effect=AssertionError('stage ran')):
   with self.assertRaises(PipelineRefused):self.run_case(o={URL:{'download':'text','extract':'bad','text':''}})
 def test_drift_before_stage(self):
  with patch.dict(PINS,{'integration/supplied_feed_fixture.py':'0'*64}),patch('integration.supplied_feed_fixture.prepare_supplied_feed',side_effect=AssertionError('stage ran')):
   with self.assertRaises(PipelineRefused):self.run_case()
 def test_combined_output_growth(self):
  with self.assertRaises(PipelineRefused):self.run_case([row() for i in range(100)],{URL:outcome('😀'*9000)},max_chars=9000)
 def test_independent_original_pipeline(self):
  # Independent original feed oracle already verifies selection; independently
  # assemble the original enrichment and doc functions with distinct mocks.
  import ast,re
  from dateutil import parser
  from intelligence.geo.processing.classifier import classify
  from intelligence.geo.processing.dedupe import dedupe_articles
  rows=[row(),row(summary='y'*200)];text=outcome()['text'];defs=[]
  class Response:
   content=b'inert'
   def raise_for_status(self):pass
  class Requests:
   def get(self,*a,**kw):return Response()
  class Feed:
   def parse(self,*a):return type('Parsed',(),{'entries':copy.deepcopy(rows)})()
  class DP:
   def parse(self,v):return parser.parse(v,default=D.replace(tzinfo=None))
  class Clock:
   @staticmethod
   def now(tz):return D
  class Provider:
   def fetch_url(self,u):return 'handle'
   def extract(self,*a,**kw):return text
  class Executor:
   def __init__(self,**kw):pass
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def map(self,fn,rows):return map(fn,rows)
  scope={'requests':Requests(),'feedparser':Feed(),'REQUEST_TIMEOUT':20,'MAX_ITEMS_PER_FEED':50,'dateparser':DP(),'datetime':Clock,'timezone':timezone,'re':re,'HAS_TRAFILATURA':True,'ENABLE_FULL_TEXT':True,'FULL_TEXT_MAX_CHARS':700,'FULL_TEXT_WORKERS':1,'trafilatura':Provider(),'ThreadPoolExecutor':Executor,'classify':classify,'dedupe_articles':dedupe_articles,'DEDUPE_THRESHOLD':.85,'ACTIVE_CATEGORIES':['TRADE']}
  for p,names in [('intelligence/geo/collectors/rss.py',('_fetch_feed','_enrich_with_full_text')),('intelligence/geo/processing/classifier.py',('strip_html','parse_date')),('intelligence/geo/processing/extract.py',('extract_full_text',))]:
   tree=ast.parse((ROOT/p).read_bytes());defs.extend(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names)
   for n in tree.body:
    if isinstance(n,ast.Assign):
     for t in n.targets:
      if isinstance(t,ast.Name) and t.id in ('_HEADERS','_ENTITY_MAP'):scope[t.id]=ast.literal_eval(n.value)
      if isinstance(t,ast.Name) and t.id=='_TAG_RE':scope[t.id]=re.compile(ast.literal_eval(n.value.args[0]))
  exec(compile(ast.Module(body=defs,type_ignores=[]),'independent-original-pipeline','exec'),scope)
  selected=scope['_fetch_feed'](SPEC,D-timedelta(days=1));enriched=scope['_enrich_with_full_text'](copy.deepcopy(selected));expected_enriched=copy.deepcopy(enriched);scope['candidates']=enriched
  tree=ast.parse((ROOT/'intelligence/geo/collectors/rss.py').read_bytes());collect=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='collect');exec(compile(ast.Module(body=collect.body[5:9],type_ignores=[]),'independent-original-docs','exec'),scope)
  r=self.run_case(rows);self.assertEqual(r['selected_candidates'],selected);self.assertEqual(r['enriched_candidates'],expected_enriched);self.assertEqual(r['documents'],scope['docs'])

 def test_whitespace_outcome_before_stage(self):
  with patch('integration.supplied_feed_fixture.prepare_supplied_feed',side_effect=AssertionError('stage ran')):
   with self.assertRaises(PipelineRefused):self.run_case(o={'   ':outcome()})
