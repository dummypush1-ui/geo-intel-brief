import importlib,unittest,time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch,MagicMock
from threading import Barrier
class Tests(unittest.TestCase):
 def setUp(self):
  self.db=importlib.import_module('intelligence.geo.database');self.old=(self.db._client,self.db._db);self.db._client=self.db._db=None
 def tearDown(self):self.db._client,self.db._db=self.old
 def test_concurrent_pair_single_client(self):
  marker=object();client=MagicMock();client.__getitem__.return_value=marker;barrier=Barrier(12)
  def construct(*a,**k):time.sleep(.015);return client
  def call():barrier.wait();return self.db.connect()
  with patch.object(self.db,'MongoClient',side_effect=construct)as ctor,ThreadPoolExecutor(max_workers=12)as pool:
   results=list(pool.map(lambda _:call(),range(12)))
  self.assertTrue(all(x is marker for x in results));ctor.assert_called_once();self.assertIs(self.db._client,client);client.__getitem__.assert_called_once();client.close.assert_not_called()
 def test_failed_db_selection_closes_and_never_publishes(self):
  failed=MagicMock();failed.__getitem__.side_effect=RuntimeError('fixture');good=MagicMock();marker=object();good.__getitem__.return_value=marker
  with patch.object(self.db,'MongoClient',side_effect=[failed,good]):
   with self.assertRaises(RuntimeError):self.db.connect()
   self.assertIsNone(self.db._client);self.assertIsNone(self.db._db);failed.close.assert_called_once();self.assertIs(self.db.connect(),marker);self.assertIs(self.db._client,good)
 def test_ctor_failure_leaves_pair_empty(self):
  with patch.object(self.db,'MongoClient',side_effect=RuntimeError('fixture')):
   with self.assertRaises(RuntimeError):self.db.connect()
  self.assertIsNone(self.db._client);self.assertIsNone(self.db._db)
 def test_candidate_no_client_no_ttl_and_default_off(self):
  with patch.object(self.db,'connect',return_value=MagicMock())as connect:
   candidates=self.db.query_index_candidates();connect.assert_not_called();self.assertEqual(len(candidates),6)
   self.db.init_db();db=connect.return_value;self.assertEqual(db.articles.create_index.call_count,2);self.assertEqual(db.events.create_index.call_count,2)
   db.reset_mock();self.db.init_db(provision_query_indexes=True);self.assertEqual(db.articles.create_index.call_count,8);self.assertEqual(db.events.create_index.call_count,2)
   for name,keys in candidates:db.articles.create_index.assert_any_call(list(keys),name=name)
   self.assertNotIn('expireAfterSeconds',repr(db.mock_calls))
 def test_closed_gate_before_connect(self):
  with patch.object(self.db,'connect',side_effect=AssertionError)as c:
   for v in ('true',1,None):
    with self.assertRaises(ValueError):self.db.init_db(v)
   c.assert_not_called()
