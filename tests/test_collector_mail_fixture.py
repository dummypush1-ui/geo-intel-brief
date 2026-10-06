import unittest,copy,ast
from unittest.mock import patch
from datetime import datetime,timezone
from bson import ObjectId
from integration.collector_mail_fixture import prepare_fixture,FixtureRefused,PINS,ROOT
NOW=datetime(2026,10,6,tzinfo=timezone.utc)
def candidate():return {'title':'Trade tariff order','url':'https://example.com/new','source':'Fixture','summary':'trade tariff','published':NOW}
def row(n=5):return {'_id':ObjectId(f'{n:024x}'),'title':'Stored story','url':'https://example.com/stored','source':'Fixture','summary':'summary','score':n,'category':'TRADE','risk_level':'LOW','published':NOW.isoformat()}
def run(a=None,b=None):return prepare_fixture([candidate()] if a is None else a,[row()] if b is None else b,['TRADE'],.85,NOW)
class Tests(unittest.TestCase):
 def test_differential_separate_inputs(self):
  from integration.geo_collector_contract import prepare_geo_documents
  from integration.geo_queue_fixture import build_supplied_queue
  r=run();self.assertEqual(r['prepared'],prepare_geo_documents([candidate()],['TRADE'],.85));self.assertEqual(r['queue_diagnostic'],build_supplied_queue([row()],NOW));self.assertNotIn('Trade tariff order',r['mail_preview']['html']);self.assertNotIn('_id',r['prepared']['documents'][0]);self.assertFalse(r['delivery'])
 def test_whole_invalid_queue_before_any_seam(self):
  with patch('integration.geo_collector_contract.prepare_geo_documents',side_effect=AssertionError('must not call')):
   for q in [dict(row(),password='secret'),dict(row(),emailed=True,score=[]),dict(row(),published='naive'),{k:v for k,v in row().items() if k!='score'}]:
    with self.assertRaises(FixtureRefused):run(b=[q])
  with patch('integration.geo_collector_contract.prepare_geo_documents',side_effect=AssertionError('must not call')):
   with self.assertRaises(FixtureRefused):run(b=[row(),row()])
 def test_private_candidate_extras_before_seams(self):
  with patch('integration.geo_queue_fixture.build_supplied_queue',side_effect=AssertionError('must not call')):
   for k in ['_id','emailed','telegram_url','password']:
    with self.assertRaises(FixtureRefused):run(a=[dict(candidate(),**{k:'secret'})])
 def test_overflow_multibyte_and_hooks(self):
  class Evil(str):
   def __str__(self):raise AssertionError('hook')
  for a in [[dict(candidate(),title=Evil('x'))],[dict(candidate(),summary='界'*16001)],[dict(candidate(),summary='界'*16000) for _ in range(30)],[dict(candidate(),summary=['x'])]]:
   with self.assertRaises(FixtureRefused):run(a=a)
 def test_copy_isolation(self):
  a=[candidate()];b=[row()];r=run(a,b);a[0]['title']='changed';b[0]['title']='changed';self.assertEqual(r['prepared']['documents'][0]['title'],'Trade tariff order');r['queue_diagnostic']['html']='tamper';self.assertIn('Stored story',r['mail_preview']['html']);self.assertIn('Stored story',run()['mail_preview']['html'])
 def test_scope_empty_low_score_critical(self):
  b=[dict(row(2),risk_level='CRITICAL')];r=run(b=b);p=r['mail_preview'];self.assertEqual(p['fetched_fixture_critical_count'],1);self.assertEqual(p['displayed_fixture_critical_count'],0);self.assertIn('Events omitted, not verified zero',p['html']);self.assertFalse(p['unsent_queue_verified']);self.assertEqual(run(a=[],b=[])['prepared']['prepared_count'],0)
 def test_pin_drift_before_seams(self):
  with patch.dict(PINS,{'intelligence/geo/processing/classifier.py':'0'*64}),patch('integration.geo_collector_contract.prepare_geo_documents',side_effect=AssertionError('must not call')):
   with self.assertRaises(FixtureRefused):run()
 def test_id_encoded_leak_and_hostile_html(self):
  identity=str(row()['_id'])
  with self.assertRaises(FixtureRefused):run(b=[dict(row(),title=''.join('&#'+str(ord(c))+';' for c in identity))])
  p=run(b=[dict(row(),title='<script>evil</script>',url='javascript:evil')])['mail_preview'];self.assertNotIn('<script>',p['html']);self.assertNotIn('href="javascript:',p['html']);self.assertNotIn(identity,p['html'])
 def test_no_effectful_imports_or_runtime_reference(self):
  source=(ROOT/'integration/collector_mail_fixture.py').read_text();tree=ast.parse(source)
  self.assertFalse(any(isinstance(n,ast.ImportFrom) and n.module and any(s in n.module for s in ('mail_bridge','database','collectors','apps_script')) for n in ast.walk(tree)))
  for p in ['integration/runtime.py','integration/private_router.py','integration/preview_launcher.py']:
   self.assertNotIn('collector_mail_fixture',(ROOT/p).read_text())
  for forbidden in ['article_ids','ids_to_mark','recipient','subject','ReceiptBridge']:self.assertNotIn(forbidden,run()['mail_preview'])
 def test_clock_after_utc_bounds_and_caps(self):
  from datetime import timedelta
  for d in [datetime(1970,1,1,tzinfo=timezone(timedelta(hours=1))),datetime(2100,12,31,23,30,tzinfo=timezone(timedelta(hours=-1)))]:
   with self.assertRaises(FixtureRefused):prepare_fixture([],[],['TRADE'],.85,d)
  with self.assertRaises(FixtureRefused):run(a=[candidate()]*101)

 def test_large_unknown_row_cheap_refusal(self):
  class Evil(str):
   def __hash__(self):return 1
  huge={str(i):'x' for i in range(10000)}
  with patch('integration.geo_collector_contract.prepare_geo_documents',side_effect=AssertionError('must not call')):
   with self.assertRaises(FixtureRefused):run(a=[huge])
