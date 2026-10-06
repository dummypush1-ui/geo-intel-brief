import unittest,copy,ast,sys
from datetime import datetime,timezone,timedelta
from unittest.mock import patch
from integration.supplied_fulltext_fixture import *
D=datetime(2026,1,1,tzinfo=timezone.utc)
def row(summary='Tariff trade update',url='https://example.invalid/news'):
 return {'title':'Trade tariff new order','url':url,'source':'Fixture','summary':summary,'published':D,'credibility':'HIGH'}
def outcome(text='More tariff trade extracted text',download='text',extract='text'):return {'download':download,'extract':extract,'text':text}
class Tests(unittest.TestCase):
 def run_case(self,a=None,o=None,**kw):return prepare_supplied_fulltext(a if a is not None else [row()],o if o is not None else {row()['url']:outcome()},**kw)
 def test_threshold_order_repeats_mutation(self):
  rows=[row('x'*199),row('x'*200),row('x'*201),row('short')];old=copy.deepcopy(rows);r=self.run_case(rows)
  self.assertEqual(rows,old);self.assertEqual([x['call'] for x in r['trace']],['download','extract','download','extract'])
  self.assertEqual(r['candidates'][1]['summary'],'x'*200);r['candidates'][0]['summary']='changed';self.assertEqual(rows,old)
 def test_disabled_unavailable_empty_calls(self):
  for kw in ({'enabled':False},{'available':False}):self.assertFalse(self.run_case(o={},**kw)['trace'])
  r=self.run_case(o={row()['url']:outcome('',download='empty',extract='empty')});self.assertEqual(len(r['trace']),1)
  self.assertEqual(r['candidates'][0]['summary'],row()['summary'])
 def test_errors_empty_whitespace_and_short_replace(self):
  for o in (outcome('',download='error',extract='empty'),outcome('',extract='error'),outcome('',extract='empty'),outcome('\u2003 \n ')):
   self.assertEqual(self.run_case(o={row()['url']:o})['candidates'][0]['summary'],row()['summary'])
  self.assertEqual(self.run_case(o={row()['url']:outcome(' x ')})['candidates'][0]['summary'],'x')
 def test_exact_limit_ellipsis_unicode(self):
  for t in ('a'*7,'a'*8,'\u2003'+'😀'*8+'\u2003'):
   s=t.strip();expected=s[:7]+'...' if len(s)>7 else s
   self.assertEqual(self.run_case(o={row()['url']:outcome(t)},max_chars=7)['candidates'][0]['summary'],expected)
 def test_missing_unused_before_execution(self):
  for o in ({},{'unused':outcome()}):
   with patch('integration.supplied_fulltext_fixture._definitions',side_effect=AssertionError('executed')):
    with self.assertRaises(FulltextRefused):self.run_case(o=o)
 def test_invalid_whole_batch_no_hooks(self):
  class Text(str):
   def __len__(self):raise AssertionError('hook')
  for a in ([dict(row(),summary=Text('x'))],[row(),dict(row(),published=datetime(1969,1,1,tzinfo=timezone.utc))],[dict(row(),emailed=True)],[dict(row(),summary='x'*10001)],[dict(row(),summary='\ud800')]):
   with patch('integration.supplied_fulltext_fixture._definitions',side_effect=AssertionError('executed')):
    with self.assertRaises(FulltextRefused):self.run_case(a=a)
  for v in (True,0,9998,10**1000):
   with self.assertRaises(FulltextRefused):self.run_case(max_chars=v)
 def test_aggregate_budget_and_fixed_date_boundary(self):
  rows=[row('😀'*10000,str(i)) for i in range(30)]
  with self.assertRaises(FulltextRefused):self.run_case(a=rows,o={})
  d=datetime(1970,1,1,tzinfo=timezone(timedelta(hours=1)))
  with self.assertRaises(FulltextRefused):self.run_case(a=[dict(row(),published=d)])
 def test_output_budget_no_publication(self):
  rows=[row('short') for i in range(100)];o={row()['url']:outcome('😀'*9000)}
  with self.assertRaises(FulltextRefused):self.run_case(a=rows,o=o,max_chars=9000)
 def test_source_drift_and_no_original_import_effects(self):
  with patch.dict(PINS,{'intelligence/geo/processing/extract.py':'0'*64}):
   with self.assertRaises(FulltextRefused):self.run_case()
  before=set(sys.modules);r=self.run_case()
  for m in ('trafilatura','intelligence.geo.collectors.rss','intelligence.geo.processing.extract','intelligence.geo.reports.telegram_backup'):self.assertNotIn(m,set(sys.modules)-before)
  self.assertFalse(r['network']);self.assertFalse(r['writes']);self.assertFalse(r['delivery'])
  for d in r['documents']:
   self.assertNotIn('_id',d);self.assertNotIn('emailed',d);self.assertEqual(d['telegram_url'],'');self.assertIsNone(d['telegram_message_id'])
 def test_independent_original_differential(self):
  # Independent mocks and unrestricted standard builtins only in test oracle.
  trace=[]
  class Provider:
   def fetch_url(self,u):trace.append(('download',u));return 'inert-content'
   def extract(self,c,**kw):trace.append(('extract',c));return ' \u2003Tariff '+'z'*800+' '
  class Executor:
   def __init__(self,**kw):pass
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def map(self,fn,a):return map(fn,a)
  definitions=[]
  for p,name in [('intelligence/geo/processing/extract.py','extract_full_text'),('intelligence/geo/collectors/rss.py','_enrich_with_full_text')]:definitions.append(next(n for n in ast.parse((ROOT/p).read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name==name))
  scope={'HAS_TRAFILATURA':True,'ENABLE_FULL_TEXT':True,'FULL_TEXT_MAX_CHARS':700,'FULL_TEXT_WORKERS':1,'trafilatura':Provider(),'ThreadPoolExecutor':Executor}
  exec(compile(ast.Module(body=definitions,type_ignores=[]),'independent-original-oracle','exec'),scope)
  rows=[row(),row('y'*200),row()];expected=scope['_enrich_with_full_text'](copy.deepcopy(rows));r=self.run_case(a=rows,o={row()['url']:outcome(' \u2003Tariff '+'z'*800+' ')})
  self.assertEqual(r['candidates'],expected);self.assertEqual(len(trace),len(r['trace']));self.assertLessEqual(len(r['documents'][0]['summary']),300)

 def test_category_before_any_execution(self):
  class Text(str):
   def __len__(self):raise AssertionError('hook')
  for categories in (['x'*101],[Text('TRADE')],['']):
   with patch('integration.supplied_fulltext_fixture._definitions',side_effect=AssertionError('executed')):
    with self.assertRaises(FulltextRefused):self.run_case(categories=categories)
