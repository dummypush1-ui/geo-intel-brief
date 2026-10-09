# Copyright (c) 2026 Push. All rights reserved.
import copy
import unittest
from unittest.mock import patch
from datetime import datetime, timezone
from types import SimpleNamespace
from flask import Flask
from bson import ObjectId
from feature_mail_mount.store import MongoMailStore, MailUnavailable
from feature_mail_mount.http import blueprint
from feature_mail_mount.reports import _articles, _rows, build

NOW = datetime(2026, 10, 8, 5, 0, tzinfo=timezone.utc)
CHANNEL = 'c' * 64
ID = str(ObjectId())
REVIEW = {'mapping': ('geo_intel', 'articles', 'events', 'mail_control', 'mail_receipts'),
          'transaction_supported': True, 'source_schema_verified': True, 'write_permission': True,
          'control_provisioned': True, 'iso_article_dates_verified': True}


def payload(policy='displayed', kind='digest', skip=False):
    return {'kind': kind, 'subject': 'Fixture', 'html': '<html><body>Fixture</body></html>',
            'fetched_ids': [ID], 'displayed_ids': [ID], 'mark_ids': [] if skip or kind == 'weekly' else [ID],
            'critical_count': 0, 'skip': skip, 'policy': policy,
            'source_scope': 'transaction_snapshot', 'clock_scope': 'UTC',
            'events_scope': 'queried_90day' if kind == 'digest' else 'not_in_original_report'}


class Collection:
    def __init__(self, client, name): self.client, self.name = client, name
    @property
    def rows(self): return self.client.rows[self.name]
    def find_one(self, q, **kw): return copy.deepcopy(self.rows.get(q['_id']))
    def count_documents(self, q, **kw): return len(self.rows)
    def insert_one(self, r, **kw):
        if r['_id'] in self.rows: raise ValueError()
        self.rows[r['_id']] = copy.deepcopy(r)
        return SimpleNamespace(acknowledged=True)
    def replace_one(self, q, r, **kw):
        if self.client.fail == 'replace': raise ValueError()
        old = self.rows.get(q['_id'])
        matched = old is not None and all(old.get(k) == v for k, v in q.items())
        if matched: self.rows[q['_id']] = copy.deepcopy(r)
        return SimpleNamespace(acknowledged=True, matched_count=int(matched))
    def update_many(self, q, value, **kw):
        if self.client.fail == 'mark': raise ValueError()
        ids = q['_id']['$in']
        matched = 0
        for identity in ids:
            if identity in self.rows:
                self.rows[identity].update(value['$set']);matched += 1
        return SimpleNamespace(acknowledged=True, matched_count=matched)


class Database:
    def __init__(self, client): self.client = client
    def __getitem__(self, name): return Collection(self.client, name)


class Session:
    def __init__(self, client): self.client = client
    def start_transaction(self, **kw): self.before = copy.deepcopy(self.client.rows)
    def commit_transaction(self):
        if self.client.fail == 'commit': raise ValueError()
    def abort_transaction(self): self.client.rows = self.before
    def end_session(self): pass


class Client:
    def __init__(self, policy='displayed'):
        self.rows = {'mail_control': {'mail-v1': {'_id': 'mail-v1', 'schema': 1, 'revision': 0,
          'channel_id': CHANNEL, 'policy': policy, 'active': {}}}, 'mail_receipts': {},
          'articles': {ObjectId(ID): {'_id': ObjectId(ID), 'emailed': False}}, 'events': {}}
        self.fail = None
    def __getitem__(self, name):
        if name != 'geo_intel': raise ValueError()
        return Database(self)
    def start_session(self, **kw): return Session(self)


class Tests(unittest.TestCase):
    def setUp(self):
        self.client = Client(); self.store = MongoMailStore(self.client, review=REVIEW, channel_id=CHANNEL, marking_policy='displayed')
        self.mock = patch('feature_mail_mount.store.build', side_effect=lambda c,s,k,n,p: payload(p,k));self.mock.start();self.addCleanup(self.mock.stop)
    def prepared(self, kind='digest', nonce='n'*24): return self.store.prepare(kind, nonce, NOW)
    def started(self, kind='digest'):
        r=self.prepared(kind); self.store.claim(r['_id'], r['hash'], 'a'*24);return r
    def test_prepare_archives_without_mark(self):
        r=self.prepared();self.assertEqual(r['state'],'prepared');self.assertFalse(self.client.rows['articles'][ObjectId(ID)]['emailed'])
        self.assertEqual(self.prepared(),r)
    def test_claim_is_one_shot(self):
        r=self.prepared();self.assertTrue(self.store.claim(r['_id'],r['hash'],'a'*24)['permit']);self.assertFalse(self.store.claim(r['_id'],r['hash'],'a'*24)['permit'])
    def test_active_prevents_duplicate_digest(self):
        self.started()
        with self.assertRaises(MailUnavailable):self.prepared(nonce='z'*24)
    def test_ack_atomic_idempotent(self):
        r=self.started();args=(r['_id'],r['hash'],'a'*24,NOW)
        first=self.store.acknowledge(*args);self.assertEqual(first,self.store.acknowledge(*args));self.assertEqual(first['scope'],'bridge_send_returned_not_delivery')
        self.assertTrue(self.client.rows['articles'][ObjectId(ID)]['emailed']);self.assertEqual(self.client.rows['mail_control']['mail-v1']['active'],{})
    def test_mark_failure_rolls_back_receipt(self):
        r=self.started();self.client.fail='mark'
        with self.assertRaises(MailUnavailable):self.store.acknowledge(r['_id'],r['hash'],'a'*24,NOW)
        self.client.fail=None;self.assertEqual(self.store.status(r['_id'])['state'],'started');self.assertFalse(self.client.rows['articles'][ObjectId(ID)]['emailed'])
    def test_commit_failure_no_send_permit(self):
        r=self.prepared();self.client.fail='commit'
        with self.assertRaises(MailUnavailable):self.store.claim(r['_id'],r['hash'],'a'*24)
        self.client.fail=None;self.assertEqual(self.store.status(r['_id'])['state'],'prepared')
    def test_missing_article_ack_held(self):
        r=self.started();self.client.rows['articles'].clear()
        with self.assertRaises(MailUnavailable):self.store.acknowledge(r['_id'],r['hash'],'a'*24,NOW)
        self.assertEqual(self.store.status(r['_id'])['state'],'started')
    def test_wrong_binding_and_premature_ack(self):
        r=self.prepared()
        for h,a in [(r['hash'],'a'*24),('0'*64,'a'*24)]:
            with self.assertRaises(MailUnavailable):self.store.acknowledge(r['_id'],h,a,NOW)
    def test_critical_separate_flag(self):
        r=self.started('critical');self.store.acknowledge(r['_id'],r['hash'],'a'*24,NOW)
        article=self.client.rows['articles'][ObjectId(ID)];self.assertTrue(article['mail_critical_sent']);self.assertFalse(article['emailed'])
    def test_weekly_no_mark(self):
        r=self.started('weekly');self.store.acknowledge(r['_id'],r['hash'],'a'*24,NOW);self.assertFalse(self.client.rows['articles'][ObjectId(ID)]['emailed'])
    def test_archive_capacity_fails_closed(self):
        self.client.rows['mail_receipts']={str(i):{} for i in range(128)}
        with self.assertRaises(MailUnavailable):self.prepared()
    def test_constructor_review_and_policy(self):
        for field in REVIEW:
            bad=dict(REVIEW);bad[field]=False
            with self.assertRaises(MailUnavailable):MongoMailStore(self.client,review=bad,channel_id=CHANNEL,marking_policy='displayed')
        with self.assertRaises(MailUnavailable):MongoMailStore(self.client,review=REVIEW,channel_id=CHANNEL,marking_policy=None)
    def test_corrupt_archive_refused(self):
        r=self.prepared();self.client.rows['mail_receipts'][r['_id']]['payload']['html']='Changed'
        with self.assertRaises(MailUnavailable):self.store.status(r['_id'])
    def test_http_auth_and_duplicate_json(self):
        app=Flask(__name__);app.register_blueprint(blueprint(self.store,secret='s'*48,clock=lambda:NOW));c=app.test_client();headers={'Authorization':'Bearer '+'s'*48}
        self.assertEqual(c.post('/internal/mail/v1/prepare',json={'kind':'digest','nonce':'n'*24}).status_code,401)
        self.assertEqual(c.post('/internal/mail/v1/prepare?key=x',headers=headers,json={'kind':'digest','nonce':'n'*24}).status_code,401)
        self.assertEqual(c.post('/internal/mail/v1/prepare',headers=headers,data='{"kind":"digest","kind":"weekly"}',content_type='application/json').status_code,400)
        self.assertEqual(c.post('/internal/mail/v1/prepare',headers=headers,json={'kind':'digest','nonce':'n'*24}).status_code,200)
    def test_row_identity_and_date_schema(self):
        for row in ({'_id':'fake'},{'_id':ObjectId(), 'created_at':NOW, 'published':NOW}):
            with self.assertRaises(ValueError):_articles([row])
    def test_cursor_cap_closes(self):
        class Cursor:
            closed=False
            def __iter__(self):return iter([1,2])
            def close(self):self.closed=True
        c=Cursor()
        with self.assertRaises(ValueError):_rows(c,1)
        self.assertTrue(c.closed)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.ids=[ObjectId(),ObjectId()]
        self.docs=[{'_id':identity,'title':'Fixture coffee news','summary':'Fixture description','url':'https://example.org/article',
                    'source':'Fixture','category':'TRADE','country':'India','risk_level':'HIGH','score':score,'credibility':'MEDIUM',
                    'corroboration':1,'published':NOW.isoformat(),'created_at':NOW.isoformat(),'emailed':False}
                   for identity,score in zip(self.ids,[8,2])]
    def sources(self, events=None, aggregates=None):
        class Cursor:
            def __init__(self,rows):self.rows=copy.deepcopy(rows);self.closed=False
            def sort(self,*a):return self
            def limit(self,n):self.rows=self.rows[:n];return self
            def max_time_ms(self,n):return self
            def __iter__(self):return iter(self.rows)
            def close(self):self.closed=True
        class Articles:
            def find(_,q,p,**kw):return Cursor(self.docs)
            def aggregate(_,pipeline,**kw):
                return Cursor([{'_id':'TRADE' if pipeline[1]['$group']['_id']=='$category' else 'India','cnt':203}])
        class Events:
            def find(_,q,p,**kw):return Cursor(events or [])
        return {'articles':Articles(),'events':Events()}
    def test_original_digest_actual_renderer(self):
        displayed=build(self.sources(),None,'digest',NOW,'displayed')
        fetched=build(self.sources(),None,'digest',NOW,'fetched')
        self.assertEqual(displayed['mark_ids'],[str(self.ids[0])]);self.assertEqual(fetched['mark_ids'],[str(i) for i in self.ids])
        self.assertIn('Daily Brief',displayed['html']);self.assertIn('Fixture coffee news',displayed['html'])
        self.assertNotIn('Supplied sample only',displayed['html'])
        for i in self.ids:self.assertNotIn(str(i),displayed['html'])
    def test_original_weekly_aggregates_not_bounded_sample(self):
        result=build(self.sources(),None,'weekly',NOW,'displayed')
        self.assertIn('203',result['html']);self.assertEqual(result['mark_ids'],[])
    def test_original_critical(self):
        self.docs=[dict(self.docs[0],risk_level='CRITICAL')]
        result=build(self.sources(),None,'critical',NOW,'displayed')
        self.assertFalse(result['skip']);self.assertEqual(result['mark_ids'],[str(self.ids[0])])
    def test_events_only_and_hidden_critical_skip(self):
        event={'name':'Fixture','event_date':'2026-10-09','source_url':'https://example.org/event','category':'CONFERENCE','confidence':'HIGH','description':'Fixture'}
        self.docs=[]
        r=build(self.sources(events=[event]),None,'digest',NOW,'displayed')
        self.assertFalse(r['skip']);self.assertEqual(r['mark_ids'],[]);self.assertIn('Fixture',r['html'])
        self.setUp();self.docs=[dict(self.docs[1],risk_level='CRITICAL')]
        r=build(self.sources(),None,'digest',NOW,'displayed')
        self.assertTrue(r['skip']);self.assertEqual(r['critical_count'],0);self.assertEqual(r['mark_ids'],[])
    def test_events_cap(self):
        event={'name':'Fixture','event_date':'2026-10-09','source_url':'https://example.org/event','category':'CONFERENCE','confidence':'HIGH','description':'Fixture'}
        with self.assertRaises(ValueError):build(self.sources(events=[event]*201),None,'digest',NOW,'displayed')
    def test_all_low_score_skips_unless_critical(self):
        self.docs=[dict(self.docs[1])]
        result=build(self.sources(),None,'digest',NOW,'fetched');self.assertTrue(result['skip']);self.assertEqual(result['mark_ids'],[])
    def test_bridge_node(self):
        import subprocess
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        out=subprocess.run(['node',str(root/'feature_mail_mount/test_bridge.js')],capture_output=True,text=True,timeout=10)
        self.assertEqual(out.returncode,0,out.stdout+out.stderr)


class HardeningTests(unittest.TestCase):
    setUp = Tests.setUp
    prepared = Tests.prepared
    started = Tests.started
    def test_ack_after_process_restart(self):
        r=self.started()
        replacement=MongoMailStore(self.client,review=REVIEW,channel_id=CHANNEL,marking_policy='displayed')
        replacement.acknowledge(r['_id'],r['hash'],'a'*24,NOW)
        self.assertEqual(replacement.status(r['_id'])['state'],'acknowledged')
    def test_unknown_commit_may_have_landed(self):
        r=self.prepared()
        session=Session(self.client)
        def commit():
            session.before=copy.deepcopy(self.client.rows)
            raise ValueError('Response lost after database commit')
        session.commit_transaction=commit
        with patch.object(self.client,'start_session',return_value=session):
            with self.assertRaises(MailUnavailable):self.store.claim(r['_id'],r['hash'],'a'*24)
        self.assertEqual(self.store.status(r['_id'])['state'],'started')
        self.assertFalse(self.store.claim(r['_id'],r['hash'],'a'*24)['permit'])
    def test_wrong_attempt_no_mark(self):
        r=self.started()
        with self.assertRaises(MailUnavailable):self.store.acknowledge(r['_id'],r['hash'],'b'*24,NOW)
        self.assertFalse(self.client.rows['articles'][ObjectId(ID)]['emailed'])
    def test_control_mismatch_no_operations(self):
        self.client.rows['mail_control']['mail-v1']['channel_id']='x'*64
        with self.assertRaises(MailUnavailable):self.prepared()
        self.assertFalse(self.client.rows['mail_receipts'])
    def test_http_closed_ack_schema_no_arbitrary_ids(self):
        app=Flask(__name__);app.register_blueprint(blueprint(self.store,secret='s'*48,clock=lambda:NOW));c=app.test_client()
        r=c.post('/internal/mail/v1/ack',headers={'Authorization':'Bearer '+'s'*48},json={'article_ids':[ID]})
        self.assertEqual(r.status_code,400);self.assertFalse(self.client.rows['articles'][ObjectId(ID)]['emailed'])
    def test_http_size_and_secret_errors_sanitized(self):
        app=Flask(__name__);app.register_blueprint(blueprint(self.store,secret='s'*48,clock=lambda:NOW));c=app.test_client()
        r=c.post('/internal/mail/v1/prepare',headers={'Authorization':'Bearer '+'s'*48},data='x'*4097,content_type='application/json')
        self.assertEqual(r.status_code,400);self.assertNotIn('s'*48,r.text)
        self.client.fail='replace'
        r=c.post('/internal/mail/v1/prepare',headers={'Authorization':'Bearer '+'s'*48},json={'kind':'digest','nonce':'n'*24})
        self.assertEqual(r.status_code,503);self.assertFalse(r.json['retry_send']);self.assertNotIn('s'*48,r.text)
