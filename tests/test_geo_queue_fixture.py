import unittest,ast
from pathlib import Path
from datetime import datetime,timezone
from bson import ObjectId
from integration.geo_queue_fixture import build_supplied_queue,query_plan,MARKING_POLICY
from integration.report_adapters import geo_report_builder
NOW=datetime(2026,10,5,tzinfo=timezone.utc)
def row(n,**kw):return {'_id':ObjectId(f'{n:024x}'),'title':'fixture','summary':'summary','url':'https://example.com/news','source':'fixture','category':'TRADE','country':'India','risk_level':'LOW','score':n,'credibility':'HIGH','corroboration':1,'published':'2026-10-05T00:00:00+00:00','created_at':'2026-10-05T00:00:00+00:00',**kw}
class GeoQueueFixtureTests(unittest.TestCase):
 def test_query_projection_and_limit_label(self):
  p=query_plan();self.assertEqual(p['query'],{'emailed':{'$ne':True}});self.assertEqual(p['limit'],60);self.assertEqual(p['sort'][-1],('_id',-1));self.assertEqual(query_plan(limit=2)['limit_scope'],'fixture_only')
 def test_original_differential_low_score_critical_scope(self):
  rows=[row(5),row(2,risk_level='CRITICAL')]
  r=build_supplied_queue(rows,NOW);original=geo_report_builder(lambda:rows,lambda days:[],now=NOW)()
  self.assertEqual(r['html'],original['html']);self.assertEqual(r['critical_count'],1);self.assertEqual(r['displayed_critical_count'],0)
  self.assertEqual(r['fetched_ids'],tuple(x['_id'] for x in rows));self.assertEqual(r['displayed_ids'],tuple(original['ids']));self.assertEqual(r['displayed_ids'],(rows[0]['_id'],));self.assertEqual(original['critical_count'],0)
  self.assertEqual(r['marking_policy'],MARKING_POLICY);self.assertFalse(r['unsent_queue_verified']);self.assertNotIn('ids_to_mark',r);self.assertNotIn('emailed_ids',r)
 def test_missing_null_false_true_and_array_whole_snapshot(self):
  rows=[row(8),row(7,emailed=None),row(6,emailed=False),row(5,emailed=True)]
  r=build_supplied_queue(rows,NOW);self.assertEqual(r['fetched_count'],3)
  for value in ([True],[],1,'false'):
   with self.assertRaisesRegex(ValueError,'emailed scalar schema'):build_supplied_queue(rows+[row(1,emailed=value)],NOW)
 def test_limit_before_displayfilter_and_tie_deviation(self):
  rows=[row(2),row(3)]
  r=build_supplied_queue(rows,NOW,limit=1);self.assertEqual(r['fetched_count'],1);self.assertEqual(r['displayed_count'],0)
  a=row(6,score=5);b=row(7,score=5);r=build_supplied_queue([a,b],NOW)
  self.assertEqual(r['fetched_ids'],(b['_id'],a['_id']));self.assertIn('addition',r['tie_order'])
 def test_no_ids_in_rendered_output(self):
  rows=[row(5)];r=build_supplied_queue(rows,NOW)
  self.assertNotIn(str(rows[0]['_id']),r['html']);self.assertEqual(r['snapshot_source'],'supplied_fixture')
  with self.assertRaisesRegex(ValueError,'identity in rendered'):build_supplied_queue([row(5,title=str(rows[0]['_id']))],NOW)
 def test_bad_shapes_bounds(self):
  for rows in ([row(5),row(5)],[row(5,score=True)],[row(5,score=float('nan'))],[row(5,published='naive')],[row(5,password='private')],[row(5,title='x'*16001)]):
   with self.assertRaises(ValueError):build_supplied_queue(rows,NOW)
 def test_static_import_guard(self):
  source=Path('integration/geo_queue_fixture.py').read_text();tree=ast.parse(source)
  modules=[x.module for x in ast.walk(tree) if isinstance(x,ast.ImportFrom)]
  self.assertFalse(any('pymongo' in x or 'mail_bridge' in x or 'delivery' in x for x in modules if x))
  self.assertNotIn('ReceiptBridge',source);self.assertNotIn('MongoClient',source)

 def test_original_get_defaults_differential(self):
  r=row(5);r.pop('credibility');r.pop('corroboration')
  result=build_supplied_queue([r],NOW)
  original=geo_report_builder(lambda:[r],lambda days:[],now=NOW)()
  self.assertEqual(result['html'],original['html']);self.assertIn('MEDIUM credibility',result['html'])
  self.assertEqual(result['events_scope'],'omitted_fixture_events_not_verified_zero')
 def test_renderer_min_score_and_get_defaults_drift(self):
  tree=ast.parse(Path('intelligence/geo/reports/email_report.py').read_text())
  constants={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='MIN_SCORE'}
  self.assertEqual(constants['MIN_SCORE'],4)
  gets=[]
  for n in ast.walk(tree):
   if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='get' and n.args and isinstance(n.args[0],ast.Constant):
    try:gets.append(tuple(ast.literal_eval(a) for a in n.args))
    except ValueError:pass
  self.assertEqual(sorted(set(gets),key=str),sorted([('credibility','MEDIUM'),('corroboration',1)],key=str))
 def test_identity_uppercase_and_encoded_html_guard(self):
  from urllib.parse import quote
  r=row(5);identity=str(r['_id'])
  for text in (identity.upper(),''.join('&#'+str(ord(c))+';' for c in identity),''.join('%'+format(ord(c),'02X') for c in identity)):
   with self.assertRaises(ValueError):build_supplied_queue([row(5,title=text)],NOW)
 def test_snapshot_id_bound_to_limit_and_none_strictness(self):
  rows=[row(5)]
  self.assertNotEqual(build_supplied_queue(rows,NOW)['snapshot_id'],build_supplied_queue(rows,NOW,limit=1)['snapshot_id'])
  for field in ('summary','source','credibility','score'):
   with self.assertRaises(ValueError):build_supplied_queue([row(5,**{field:None})],NOW)
