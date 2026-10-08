import importlib, unittest
from types import SimpleNamespace
from unittest.mock import patch
from pymongo.errors import BulkWriteError

class LegacyBulkOutcome(unittest.TestCase):
    def setUp(self):
        self.db=importlib.import_module('intelligence.geo.database')
    def call(self, error=None, result=None, rows=None):
        docs=[{'title':'fixture'}] if rows is None else rows
        def insert(given,**kw):
            self.assertEqual(kw,{'ordered':False})
            given[0]['title']='driver-mutated'
            if error: raise error
            return result or SimpleNamespace(acknowledged=True,inserted_ids=list(range(len(given))))
        with patch.object(self.db,'connect',return_value=SimpleNamespace(articles=SimpleNamespace(insert_many=insert))):
            return self.db.save_articles_bulk(docs)
    def test_success_and_copy(self):
        rows=[{'title':'fixture'}];self.assertEqual(self.call(rows=rows),1)
        self.assertEqual(rows,[{'title':'fixture'}])
    def test_empty_no_connection(self):
        with patch.object(self.db,'connect',side_effect=AssertionError):self.assertEqual(self.db.save_articles_bulk([]),0)
    def test_confirmed_duplicate_uses_driver_ninserted(self):
        e=BulkWriteError({'nInserted':1,'writeErrors':[{'index':1,'code':11000,'keyPattern':{'url':1}}],'writeConcernErrors':[]})
        self.assertEqual(self.call(e,rows=[{},{}]),1)
    def test_mixed_failure_is_not_success_count(self):
        e=BulkWriteError({'nInserted':1,'writeErrors':[{'index':1,'code':11000,'keyPattern':{'url':1}},{'index':2,'code':121}],'writeConcernErrors':[]})
        with self.assertRaises(self.db.ArticleWriteOutcomeError) as c:self.call(e,rows=[{},{},{}])
        self.assertEqual((c.exception.outcome['inserted_count'],c.exception.outcome['duplicate_count'],c.exception.outcome['failed_count']),(1,1,1))
        self.assertFalse(c.exception.outcome['retry_safe'])
    def test_unknown_concern_malformed_and_network_redacted(self):
        errors=[RuntimeError('secret-uri'),BulkWriteError({'nInserted':1,'writeErrors':[],'writeConcernErrors':[{'errmsg':'secret-uri'}]}),BulkWriteError({'nInserted':999,'writeErrors':[],'writeConcernErrors':[]})]
        for error in errors:
            with self.assertRaises(self.db.ArticleWriteOutcomeError) as c:self.call(error)
            self.assertEqual(c.exception.outcome['state'],'uncertain');self.assertIsNone(c.exception.outcome['inserted_count'])
            self.assertNotIn('secret-uri',str(c.exception));self.assertIsNone(c.exception.__cause__)
    def test_unacknowledged_receipt_unknown(self):
        with self.assertRaises(self.db.ArticleWriteOutcomeError):self.call(result=SimpleNamespace(acknowledged=False,inserted_ids=[1]))
    def test_connection_failure_unknown_no_retry(self):
        with patch.object(self.db,'connect',side_effect=RuntimeError('secret-uri')) as p:
            with self.assertRaises(self.db.ArticleWriteOutcomeError) as c:self.db.save_articles_bulk([{}])
            self.assertEqual(p.call_count,1);self.assertNotIn('secret-uri',str(c.exception))
    def test_wrong_duplicate_key_is_partial(self):
        e=BulkWriteError({'nInserted':0,'writeErrors':[{'index':0,'code':11000,'keyPattern':{'_id':1}}],'writeConcernErrors':[]})
        with self.assertRaises(self.db.ArticleWriteOutcomeError) as c:self.call(e)
        self.assertEqual(c.exception.outcome['failed_count'],1)

    def test_all_duplicate_zero_inserts(self):
        e=BulkWriteError({'nInserted':0,'writeErrors':[{'index':0,'code':11000,'keyPattern':{'url':1}}],'writeConcernErrors':[]})
        self.assertEqual(self.call(e),0)
    def test_writeconcern_with_duplicates_stays_unknown(self):
        e=BulkWriteError({'nInserted':0,'writeErrors':[{'index':0,'code':11000,'keyPattern':{'url':1}}],'writeConcernErrors':[{'code':64}]})
        with self.assertRaises(self.db.ArticleWriteOutcomeError) as c:self.call(e)
        self.assertEqual(c.exception.outcome['state'],'uncertain')
        self.assertIsNone(c.exception.outcome['duplicate_count'])
