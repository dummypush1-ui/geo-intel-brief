import unittest,ast,copy
from datetime import datetime,timezone,timedelta
from unittest.mock import patch
from integration.telegram_format_audit import *
class Tests(unittest.TestCase):
 def run_case(self,r=None):return audit_synthetic_telegram_format([{}] if r is None else r,synthetic=True)
 def test_defaults_empty_raw_unicode(self):
  self.assertFalse(self.run_case([])['batches']);r=self.run_case([{'summary':'தமிழ்😀\n\x00'}]);t=r['records'][0]['original_text'];m=r['records'][0]['metrics']
  self.assertIn('தமிழ்😀\n\x00',t);self.assertGreater(m['utf16_code_units'],m['python_codepoints']);self.assertGreater(m['utf8_bytes'],m['python_codepoints']);self.assertIn('Country: —',t);self.assertIn('Credibility: MEDIUM',t)
 def test_estimate_gap_crossing_boundary(self):
  base=len(self.run_case([{}])['records'][0]['original_text']);lengths=[1748-base,1748-base]
  r=self.run_case([{'summary':'x'*n} for n in lengths]);b=r['batches'][0];self.assertEqual(b['source_packing_estimate'],3500);self.assertEqual(b['metrics']['python_codepoints'],3504);self.assertTrue(b['actual_over_source3500']);self.assertFalse(b['estimate_over_source3500']);self.assertEqual(b['actual_minus_estimate'],4)
 def test_single_equal_one_over_and_unsplit(self):
  base=len(self.run_case([{}])['records'][0]['original_text'])
  for n,flag in ((3500,False),(3501,True)):
   b=self.run_case([{'summary':'x'*(n-base)}])['batches'][0];self.assertEqual(b['metrics']['python_codepoints'],n);self.assertEqual(b['actual_minus_estimate'],-2);self.assertEqual(b['unsplit_single_oversized'],flag)
 def test_spans_repeats_order_no_mutation(self):
  rows=[{'summary':'x'*2000},{'summary':'y'*2000},{'summary':'y'*2000}];old=copy.deepcopy(rows);r=self.run_case(rows);self.assertEqual([b['span'] for b in r['batches']],[[0,1],[1,2],[2,3]]);r['batches'][0]['span'][0]=99;self.assertEqual(rows,old);self.assertFalse(r['ready_for_delivery'])
 def test_published_fixed_conversion(self):
  d=datetime(2026,1,1,tzinfo=timezone(timedelta(hours=5,minutes=30)));self.assertIn(d.isoformat(),self.run_case([{'published':d}])['records'][0]['original_text'])
  with self.assertRaises(FormatRefused):self.run_case([{'published':'not-date'}])
 def test_private_hooks_surrogates_before_execution(self):
  class Text(str):
   def __len__(self):raise AssertionError('hook')
  for row in ({'token':'x'},{'summary':Text('x')},{'summary':'\ud800'},{'score':True},{'corroboration':float('inf')}):
   with patch('integration.telegram_format_audit._functions',side_effect=AssertionError('executed')):
    with self.assertRaises(FormatRefused):self.run_case([row])
  with self.assertRaises(FormatRefused):audit_synthetic_telegram_format([{}])
 def test_drift_and_output_growth(self):
  with patch('integration.telegram_format_audit.PIN','0'*64):
   with self.assertRaises(FormatRefused):self.run_case()
  with self.assertRaises(FormatRefused):self.run_case([{'summary':'x'*6000} for i in range(100)])
 def test_independent_original_oracle(self):
  source=(ROOT/SOURCE).read_bytes();tree=ast.parse(source);defs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_format_full_record','_split_into_batches')];scope={'TELEGRAM_MSG_LIMIT':3500};exec(compile(ast.Module(body=defs,type_ignores=[]),'independent-original-format','exec'),scope)
  rows=[{'summary':'Tamil தமிழ் 😀\n'+str(i)*1500,'country':''} for i in range(4)];r=self.run_case(rows)
  self.assertEqual([x['original_text'] for x in r['records']],[scope['_format_full_record'](x) for x in rows]);self.assertEqual([(tuple(b['span']),b['original_text']) for b in r['batches']],scope['_split_into_batches'](rows))
