import copy
import threading
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch
from collector109_prep.fixture_support import CASCollection
from collector108_prep.durable_ledger import DurableLedger, LedgerRefused
from collector110_prep.durable_checkpoint import DurableCheckpoints
from integration.collector197_config import configure, GATES, ConfigRefused, CollectorConfig
from integration.collector197_orchestrator import run_cycle, CycleRefused
from integration.geo_article_writer import GeoArticleWriter

class Checkpoints:
    def __init__(self):
        self.rows = {}
        self.write_concern = SimpleNamespace(document={'w':'majority','j':True,'wtimeout':5000})
        self.read_concern = SimpleNamespace(document={'level':'majority'})
    def update_one(self, q, u, upsert=False):
        self.rows.setdefault(q['_id'], copy.deepcopy(u['$setOnInsert']))
        return SimpleNamespace(acknowledged=True)
    def find_one(self, q):
        return copy.deepcopy(self.rows.get(q['_id']))

def candidates():
    return [{'title':'Trade tariff order', 'url':'https://example.com/news',
             'source':'Fixture', 'summary':'Supply chain tariff '+'x'*400,
             'published':datetime(2026,1,1,tzinfo=timezone.utc), 'credibility':'HIGH'}]

class Tests(unittest.TestCase):
    def setUp(self):
        self.c = CASCollection()
        self.c.write_concern = SimpleNamespace(document={'w':'majority','j':True,'wtimeout':5000})
        self.c.read_concern = SimpleNamespace(document={'level':'majority'})
        self.ledger = DurableLedger(self.c, 'geo108', 'a'*64)
        self.ledger.initialize()
        self.pc = Checkpoints()
        self.cp = DurableCheckpoints(self.pc)
        self.writer = GeoArticleWriter({}, review={'mapping':('geo_intel','articles'),
            'write_permission':True, 'unique_url_index_verified':True, 'source_contract_verified':True})
        self.calls = 0
        self.tick = 100
        self.elapsed = 0
    def fetch(self, **kw):
        self.calls += 1
        self.assertEqual(self.c.doc['active']['phase'], 'running')
        self.assertEqual(kw, {'deadline':90, 'per_feed_seconds':25})
        return candidates()
    def call(self, **kw):
        args = dict(ledger=self.ledger, checkpoints=self.cp, nonce='n'*24,
            fetch=self.fetch, categories=['TRADE'], threshold=.85,
            clock=lambda:self.tick, monotonic=lambda:self.elapsed)
        args.update(kw)
        return run_cycle(CollectorConfig(True), **args)
    def test_disabled_no_adapters_accessed(self):
        self.assertEqual(run_cycle(CollectorConfig(False), ledger=None, checkpoints=None,
            nonce=None, fetch=None, categories=None, threshold=None, clock=None)['state'], 'disabled')
        self.assertEqual(self.c.doc['revision'], 0)
    def test_defaults_off(self):
        self.assertFalse(configure({}, {}).enabled)
    def test_strict_boolean_switch(self):
        for value in (True, False, 'TRUE', '', '0', None):
            with self.assertRaises(ConfigRefused): configure({'COLLECTION_ENABLED':value}, {})
    def test_unsupported_features_even_off(self):
        for flag in ('ENABLE_FULL_TEXT','ENABLE_GNEWS','ENABLE_TELEGRAM_BACKUP'):
            with self.assertRaises(ConfigRefused):configure({flag:'true'}, {})
    def test_writer_never_fallback(self):
        p = dict.fromkeys(GATES, True)
        with self.assertRaises(ConfigRefused):configure({'COLLECTION_ENABLED':'true','GEO_MONGODB_URI':'reader'}, p)
    def test_alias_refused(self):
        for name in ('GEO_MONGODB_URI','MONGODB_URI'):
            with self.assertRaises(ConfigRefused):configure({'COLLECTION_ENABLED':'true','GEO_WRITER_MONGODB_URI':'same',name:'same'}, dict.fromkeys(GATES, True))
    def test_all_proofs_exact(self):
        v={'COLLECTION_ENABLED':'true','GEO_WRITER_MONGODB_URI':'private-not-retained'}
        for name in GATES:
            p=dict.fromkeys(GATES, True);p[name]=1
            with self.assertRaises(ConfigRefused):configure(v,p)
        self.assertEqual(configure(v,dict.fromkeys(GATES,True)), CollectorConfig(True))
        self.assertNotIn('private-not-retained',repr(configure(v,dict.fromkeys(GATES,True))))
    def test_concerns_before_submit_fetch(self):
        before=self.c.calls;self.c.write_concern.document['j']=False
        with self.assertRaises(CycleRefused):self.call()
        self.assertEqual(self.c.calls,before);self.assertEqual(self.calls,0)
    def test_claim_before_fetch_checkpoint_immutable(self):
        out=self.call();self.assertEqual(out['state'],'held_before_write')
        self.assertEqual(self.cp.get(out['job'],1)['candidates'], candidates())
        self.assertEqual(self.c.doc['active']['phase'],'prepare_complete')
    def test_replay_no_fetch_after_prepare(self):
        self.call();out=self.call();self.assertEqual(out['state'],'replay_held');self.assertEqual(self.calls,1)
    def test_parallel_same_id_one_fetch(self):
        entered=threading.Event();release=threading.Event();out=[]
        def fetch(**kw):self.calls+=1;entered.set();release.wait(2);return candidates()
        def first():out.append(self.call(fetch=fetch))
        t=threading.Thread(target=first);t.start();self.assertTrue(entered.wait(2))
        second=self.call(fetch=fetch);release.set();t.join(3)
        self.assertEqual(self.calls,1);self.assertEqual(second['state'],'replay_held');self.assertEqual(len(out),1)
    def test_fetch_failure_before_write(self):
        with self.assertRaises(CycleRefused):self.call(fetch=lambda **kw:(_ for _ in ()).throw(RuntimeError()))
        self.assertEqual(self.c.doc['history'][0]['phase'],'failed_before_write')
    def test_fetch_overrun_guards_not_preemption(self):
        def fetch(**kw):self.elapsed=90;return candidates()
        with self.assertRaises(CycleRefused):self.call(fetch=fetch)
        self.assertEqual(self.c.doc['history'][0]['phase'],'failed_before_write')
        self.assertFalse(self.pc.rows)
    def test_capture_budget_before_checkpoint(self):
        with self.assertRaises(CycleRefused):self.call(fetch=lambda **kw:[{'summary':'x'*10001}])
        self.assertFalse(self.pc.rows)
    def test_checkpoint_unacknowledged_stops(self):
        self.pc.update_one=lambda *a,**kw:SimpleNamespace(acknowledged=False)
        with self.assertRaises(CycleRefused):self.call()
        self.assertEqual(self.c.doc['history'][0]['phase'],'failed_before_write')
    def test_complete_write_once_and_terminal_replay(self):
        def write(w, docs, stamp):
            self.assertEqual(self.c.doc['active']['phase'],'write_started')
            return {'state':'inserted','attempted':len(docs),'inserted_count':len(docs),
                'duplicate_count':0,'failed_count':0,'uncertain_count':0,'retry_safe':False}
        with patch.object(GeoArticleWriter,'write',write):out=self.call(writer=self.writer)
        self.assertEqual(out['state'],'completed');self.assertEqual(self.call()['state'],'replay_held')
    def test_partial_locks_profile(self):
        with patch.object(GeoArticleWriter,'write',return_value={'state':'partial','attempted':1,
             'inserted_count':0,'duplicate_count':0,'failed_count':1,'uncertain_count':0,'retry_safe':False}):
            with self.assertRaises(CycleRefused):self.call(writer=self.writer)
        self.assertEqual(self.c.doc['active']['phase'],'uncertain_after_write')
        with self.assertRaises(LedgerRefused):self.ledger.submit('q'*24,101)
    def test_unknown_write_never_retries(self):
        with patch.object(GeoArticleWriter,'write',side_effect=RuntimeError()):
            with self.assertRaises(CycleRefused):self.call(writer=self.writer)
        self.assertEqual(self.call(writer=self.writer)['state'],'replay_held');self.assertEqual(self.calls,1)
    def test_expiry_never_takeover(self):
        self.ledger.submit('n'*24,100);self.tick=220
        with self.assertRaises(CycleRefused):self.call()
        self.assertEqual(self.calls,0);self.assertEqual(self.c.doc['active']['phase'],'accepted')
    def test_no_timeout_contract_override(self):
        with self.assertRaises(CycleRefused):run_cycle(CollectorConfig(True,whole_cycle_seconds=500),
            ledger=self.ledger,checkpoints=self.cp,nonce='n'*24,fetch=self.fetch,
            categories=['TRADE'],threshold=.85,clock=lambda:100)
    def test_history_full_closed_before_fetch(self):
        for i in range(64):
            j=self.ledger.submit(str(i).zfill(24),100)
            for p in ('running','failed_before_write'):self.ledger.advance(j['key'],j['fence'],p,101,{})
        with self.assertRaises(LedgerRefused):self.call()
        self.assertEqual(self.calls,0)

if __name__=='__main__':unittest.main()
