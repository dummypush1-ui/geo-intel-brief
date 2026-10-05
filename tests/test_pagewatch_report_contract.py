import copy,unittest
from integration.pagewatch_report import build_pagewatch_report
from integration.page_watch import snapshot,compare
class ContractTests(unittest.TestCase):
 def result(self,**kw):return {'state':'changed','items':[{'id':'hash','url':'https://nilgiried.com/','title':'Page changed','summary':'-Old\n+New',**kw}]}
 def test_golden_html_and_no_mutation(self):
  a=self.result();before=copy.deepcopy(a);r=build_pagewatch_report(a)
  self.assertEqual(r['html'],'<section><h2>Page changed </h2><p><a href="https://nilgiried.com/">Review source page</a></p><p>Observed page-text change, not independently verified event information.</p><pre style="white-space:pre-wrap;overflow-wrap:anywhere">-Old\n+New</pre></section>')
  self.assertEqual(a,before);self.assertFalse(r['mail']);self.assertFalse(r['marking'])
 def test_real_compare_accepted(self):
  a=snapshot('https://nilgiried.com/','<p>Sample visible event detail enough text for baseline</p>','2026-10-05T10:00:00Z')
  b=snapshot('https://nilgiried.com/','<p>Sample visible event detail changed text for baseline</p>','2026-10-05T10:00:01Z')
  self.assertIn('-Sample',build_pagewatch_report(compare(a,b))['html']);self.assertEqual(build_pagewatch_report(compare(None,a))['html'],'')
 def test_all_text_fields_escaped(self):
  r=build_pagewatch_report(self.result(title='<script>alert(1)</script>',summary='<script>alert(2)</script>'))
  self.assertNotIn('<script>',r['html']);self.assertIn('&lt;script&gt;',r['html'])
 def test_no_custom_hooks_or_scalar_coercion(self):
  class Evil:
   def __str__(self):raise AssertionError('hook')
  class Str(str):pass
  for key in ['id','url','title','summary']:
   for value in [True,123,None,Evil(),Str('text')]:
    with self.assertRaises(ValueError):build_pagewatch_report(self.result(**{key:value}))
 def test_bounds_closed_shape_flags_and_rows(self):
  for key,n in [('id',129),('title',201),('summary',12101),('url',2049)]:
   with self.assertRaises(ValueError):build_pagewatch_report(self.result(**{key:'x'*n}))
  for a in [{'state':'changed','items':[None]},{'state':'changed','items':[{},{}]},{'state':'baseline','items':[{}]},{'state':'baseline','extra':'x'},dict(self.result(),diff_omitted='yes'),self.result(summary='x\ud800'),self.result(title='\x00')]:
   with self.assertRaises(ValueError):build_pagewatch_report(a)
 def test_control_snapshot_falls_back_and_report_rejects_direct_controls(self):
  a=snapshot('https://nilgiried.com/','<p>Sample visible event detail enough text for baseline</p>','2026-10-05T10:00:00Z')
  b=snapshot('https://nilgiried.com/','<p>Sample visible event detail \x00 changed baseline</p>','2026-10-05T10:00:01Z')
  result=compare(a,b);self.assertTrue(result['diff_omitted']);self.assertIn('diff omitted',build_pagewatch_report(result)['html'])
  for text in ['\x00','\x85','\u202e','\u2028']:
   with self.assertRaises(ValueError):build_pagewatch_report(self.result(summary=text))
