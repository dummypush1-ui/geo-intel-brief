import unittest,copy,ast,re
from datetime import datetime,timezone,timedelta
from unittest.mock import patch
from integration.supplied_multi_feed import *
D=datetime(2026,1,2,12,tzinfo=timezone.utc);U='https://example.invalid/story'
def entry(**kw):return {'title':'Trade tariff new order','link':U,'summary':'Tariff','published':D.isoformat()}|kw
def batch(name='Fixture',rows=None,mode='ok'):return {'feed':(name,'https://example.invalid/feed','HIGH'),'entries':[entry()] if rows is None else rows,'http_mode':mode,'parser_mode':'ok'}
def outcome(text='Trade tariff '+'x'*800):return {'download':'text','extract':'text','text':text}
class Tests(unittest.TestCase):
 def run_case(self,b=None,o=None,**kw):return prepare_supplied_multi_feed([batch()] if b is None else b,{U:outcome()} if o is None else o,cutoff=D-timedelta(days=1),fallback_clock=D,**kw)
 def test_duplicates_order_global_dedupe_corrob_alias(self):
  b=[batch('One'),batch('Two'),batch('Two')];old=copy.deepcopy(b);r=self.run_case(b)
  self.assertEqual([x['source'] for x in r['selected_candidates']],['One','Two','Two']);self.assertEqual(len(r['enrichment_trace']),6);self.assertEqual(r['prepared_count'],1);self.assertEqual(r['documents'][0]['corroboration'],3)
  r['enriched_candidates'][0]['summary']='changed';self.assertEqual(r['selected_candidates'][0]['summary'],'Tariff');self.assertEqual(b,old);self.assertFalse(r['coverage_verified'])
 def test_errors_empty_zero_mixed_same_url(self):
  self.assertEqual(self.run_case([],{})['state'],'all_empty');self.assertEqual(self.run_case([batch(rows=[])],{})['state'],'all_empty')
  self.assertEqual(self.run_case([batch(mode='error')],{})['state'],'all_failed')
  r=self.run_case([batch(mode='error'),batch('Other')]);self.assertEqual(r['state'],'partially_failed');self.assertEqual(r['selected_count'],1)
  with self.assertRaises(MultiFeedRefused):self.run_case([batch(mode='error')])
 def test_disabled_unavailable_unused_filtered(self):
  for kw in ({'enabled':False},{'available':False}):self.assertFalse(self.run_case(o={},**kw)['enrichment_trace'])
  with self.assertRaises(MultiFeedRefused):self.run_case([batch(rows=[entry(title='')])])
 def test_whole_later_malformed_before_stage(self):
  for b in ([batch(),dict(batch(),extra='x')],[batch(),batch(rows=[entry(summary='\ud800')])],[batch(rows=[entry()]*51),batch(rows=[entry()]*50)]):
   with patch('integration.supplied_feed_fixture.prepare_supplied_feed',side_effect=AssertionError('stage ran')):
    with self.assertRaises(MultiFeedRefused):self.run_case(b)
 def test_drift_config_boundary_before_stage(self):
  with patch.dict(PINS,{'integration/supplied_collector_pipeline.py':'0'*64}),patch('integration.supplied_feed_fixture.prepare_supplied_feed',side_effect=AssertionError('stage ran')):
   with self.assertRaises(MultiFeedRefused):self.run_case()
  for kw in ({'categories':['x'*101]},{'max_chars':True}):
   with self.assertRaises(MultiFeedRefused):self.run_case(**kw)
  with self.assertRaises(MultiFeedRefused):self.run_case([batch(rows=[entry(link='x'*2001)])],{'x'*2001:outcome()})
 def test_per_feed_slice_missing_and_global_growth(self):
  r=self.run_case([batch(rows=[entry(title=''),entry()]),batch('Other')],max_items=1);self.assertEqual(r['selected_count'],1)
  with self.assertRaises(MultiFeedRefused):self.run_case([batch(rows=[entry()]*100)],{U:outcome('😀'*9000)},max_chars=9000)
 def test_independent_original_global_oracle(self):
  from dateutil import parser
  from intelligence.geo.processing.classifier import classify
  from intelligence.geo.processing.dedupe import dedupe_articles
  batches=[batch('One'),batch('Two',rows=[entry(summary='Trade tariff sanctions export ban '*10)])];defs=[];byurl={str(i):b for i,b in enumerate(batches)}
  class Response:
   def __init__(self,u):self.content=u
   def raise_for_status(self):pass
  class Requests:
   def get(self,u,**kw):return Response(u)
  class Feed:
   def parse(self,u):return type('Parsed',(),{'entries':copy.deepcopy(byurl[u]['entries'])})()
  class DP:
   def parse(self,v):return parser.parse(v,default=D.replace(tzinfo=None))
  class Clock:
   @staticmethod
   def now(tz):return D
  class Provider:
   def fetch_url(self,u):return 'inert'
   def extract(self,*a,**k):return outcome()['text']
  class Executor:
   def __init__(self,**k):pass
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def map(self,fn,rows):return map(fn,rows)
  scope={'requests':Requests(),'feedparser':Feed(),'REQUEST_TIMEOUT':20,'MAX_ITEMS_PER_FEED':50,'dateparser':DP(),'datetime':Clock,'timezone':timezone,'re':re,'HAS_TRAFILATURA':True,'ENABLE_FULL_TEXT':True,'FULL_TEXT_MAX_CHARS':700,'FULL_TEXT_WORKERS':1,'trafilatura':Provider(),'ThreadPoolExecutor':Executor,'classify':classify,'dedupe_articles':dedupe_articles,'DEDUPE_THRESHOLD':.85,'ACTIVE_CATEGORIES':['TRADE'],'feeds':[(b['feed'][0],str(i),b['feed'][2]) for i,b in enumerate(batches)],'cutoff':D-timedelta(days=1),'candidates':[]}
  for p,names in [('intelligence/geo/collectors/rss.py',('_fetch_feed','_enrich_with_full_text')),('intelligence/geo/processing/classifier.py',('strip_html','parse_date')),('intelligence/geo/processing/extract.py',('extract_full_text',))]:
   tree=ast.parse((ROOT/p).read_bytes());defs.extend(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names)
   for n in tree.body:
    if isinstance(n,ast.Assign):
     for t in n.targets:
      if isinstance(t,ast.Name) and t.id in ('_HEADERS','_ENTITY_MAP'):scope[t.id]=ast.literal_eval(n.value)
      if isinstance(t,ast.Name) and t.id=='_TAG_RE':scope[t.id]=re.compile(ast.literal_eval(n.value.args[0]))
  exec(compile(ast.Module(body=defs,type_ignores=[]),'independent-original-multifeed','exec'),scope)
  tree=ast.parse((ROOT/'intelligence/geo/collectors/rss.py').read_bytes());collect=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='collect')
  # Only reviewed pure flatten/enrichment/classify/dedupe/filter/doc statements.
  exec(compile(ast.Module(body=collect.body[3:9],type_ignores=[]),'independent-global-pure-stages','exec'),scope)
  r=self.run_case(batches);self.assertEqual(r['documents'],scope['docs']);self.assertLessEqual(len(r['documents'][0]['summary']),300)
