"""Synthetic plan shapes and source contracts, NOT a real Mongo explain."""
import ast,unittest
from pathlib import Path
from unittest.mock import patch,MagicMock
from intelligence.geo import database as db
class Tests(unittest.TestCase):
 def test_no_connection_exact_four_source_orders(self):
  with patch.object(db,'connect',side_effect=AssertionError):p=db.browse_index_candidates()
  self.assertEqual(len(p),4);self.assertEqual(len({n for n,k in p}),4)
  node=next(n for n in ast.walk(ast.parse(Path('integration/news_pages.py').read_text())) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name)and t.id=='order' for t in n.targets))
  orders=ast.literal_eval(node.value.value)
  self.assertEqual([list(k) for n,k in p],list(orders.values()))
  self.assertIn(p[1],db.query_index_candidates())
  self.assertNotEqual(p[-1][1],db.query_index_candidates()[0][1][:2])
 def test_gate_defaults_legacy_and_dedup_both_flags(self):
  m=MagicMock()
  with patch.object(db,'connect',return_value=m):
   db.init_db();self.assertEqual(m.articles.create_index.call_count,2);self.assertEqual(m.events.create_index.call_count,2)
   m.reset_mock();db.init_db(provision_browse_indexes=True);self.assertEqual(m.articles.create_index.call_count,6);self.assertEqual(m.events.create_index.call_count,2)
   for n,k in db.browse_index_candidates():m.articles.create_index.assert_any_call(list(k),name=n)
   m.reset_mock();db.init_db(True,True);self.assertEqual(m.articles.create_index.call_count,11)
   self.assertEqual(sum(c.kwargs.get('name')=='geo_article_title_order_v181'for c in m.articles.create_index.call_args_list),1)
   self.assertNotIn('expireAfterSeconds',repr(m.mock_calls))
 def test_bad_browse_gate_before_connection(self):
  with patch.object(db,'connect',side_effect=AssertionError)as c:
   for v in (1,'true',None,{},[]):
    with self.assertRaises(ValueError):db.init_db(provision_browse_indexes=v)
   c.assert_not_called()
 def test_synthetic_explain_shapes_not_a_planner_or_performance_receipt(self):
  # Deliberately supplied fixture evidence checks the exact expected sort prefix.
  # No Mongo process or optimization occurs here, no actual planner guarantee.
  for name,keys in db.browse_index_candidates():
   synthetic={'stage':'FETCH','inputStage':{'stage':'IXSCAN','indexName':name,'keyPattern':dict(keys)}}
   self.assertEqual(tuple(synthetic['inputStage']['keyPattern'].items()),keys)
  legacy=dict(db.query_index_candidates()[0][1]);self.assertEqual(list(legacy)[:3],['score','published','_id'])
  self.assertNotEqual(list(legacy)[:2],['score','_id'])
