import copy
import json
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import patch
from bson import ObjectId
from pymongo.errors import DuplicateKeyError, OperationFailure
from integration import mail_ledger212 as m

RECIPIENT = 'a'*64
HISTORY = 'b'*64
CONTENT = 'c'*64
REVIEW = {'mapping': (m.DB,m.CONTROL,m.RECEIPTS,m.ARTICLES), 'transaction_supported':True,
          'write_permission':True,'control_provisioned':True,'history_manifest':HISTORY,'history_complete':True}


def failure(label, code=91):
    return OperationFailure('PRIVATE', code=code, details={'errorLabels':[label]})


class Cursor:
    def __init__(self, rows): self.rows=rows;self.closed=False
    def __iter__(self): return iter(self.rows)
    def close(self): self.closed=True


class Collection:
    def __init__(self,client,name): self.client=client;self.name=name
    def list_indexes(self, **kw):
        self.client.index_reads+=1
        return Cursor(copy.deepcopy(self.client.indexes[self.name]))
    def rows(self,session): return session.rows[self.name]
    def find_one(self,q,*,session,**kw):
        self.client.reads.append((self.name,copy.deepcopy(q)))
        return copy.deepcopy(self.rows(session).get(q['_id']))
    def find(self,q,*,session,**kw):
        self.client.reads.append((self.name,copy.deepcopy(q)))
        if set(q)!={'_id'} or type(q['_id'])is not dict or set(q['_id'])!={'$in'}:raise AssertionError('scan')
        if len(q['_id']['$in'])>120:raise AssertionError('unbounded')
        return Cursor([copy.deepcopy(self.rows(session)[key])for key in q['_id']['$in']if key in self.rows(session)])
    def insert_one(self,row,*,session):
        if self.client.fail_write:
            raise self.client.fail_write
        if row['_id']in self.rows(session):raise DuplicateKeyError('PRIVATE')
        self.rows(session)[row['_id']]=copy.deepcopy(row)
        session.changed.add((self.name,row['_id']))
        return SimpleNamespace(acknowledged=True)
    def replace_one(self,q,row,*,session):
        if self.client.fail_write:raise self.client.fail_write
        prior=self.rows(session).get(q['_id'])
        ok=prior is not None and all(prior.get(k)==v for k,v in q.items())
        if ok:self.rows(session)[q['_id']]=copy.deepcopy(row);session.changed.add((self.name,q['_id']))
        return SimpleNamespace(acknowledged=True,matched_count=int(ok))


class Database:
    def __init__(self,client):self.client=client
    def __getitem__(self,name):return Collection(self.client,name)


class Session:
    def __init__(self,client):self.client=client;self.changed=set();self.commit_attempted=False
    def start_transaction(self,**kw):
        self.client.tx_options.append(kw)
        with self.client.lock:self.before=copy.deepcopy(self.client.data)
        self.rows=copy.deepcopy(self.before)
        if self.client.barrier:self.client.barrier.wait(timeout=5)
    def commit_transaction(self):
        self.commit_attempted=True;self.client.commits+=1
        if self.client.fail_commit=='before':raise failure('UnknownTransactionCommitResult')
        with self.client.lock:
            for name,key in self.changed:
                if self.client.data[name].get(key)!=self.before[name].get(key):raise failure('TransientTransactionError',112)
            for name,key in self.changed:self.client.data[name][key]=copy.deepcopy(self.rows[name][key])
        if self.client.fail_commit=='after':raise failure('UnknownTransactionCommitResult')
    def abort_transaction(self):self.client.aborts+=1
    def end_session(self):self.client.ends+=1


class Client:
    def __init__(self):
        self.data={m.CONTROL:{},m.RECEIPTS:{},m.ARTICLES:{}}
        self.indexes={name:[{'name':'_id_','key':{'_id':1}}]for name in self.data}
        self.lock=threading.Lock();self.fail_commit=None;self.fail_write=None;self.fail_session=False
        self.barrier=None;self.reads=[];self.index_reads=0;self.commits=0;self.aborts=0;self.ends=0;self.sessions=0;self.tx_options=[]
    def __getitem__(self,name):
        if name!=m.DB:raise AssertionError('database')
        return Database(self)
    def start_session(self,**kw):
        self.sessions+=1
        if self.fail_session:raise RuntimeError('PRIVATE')
        return Session(self)
    def provision(self,kind='email',purpose='digest',recipient=RECIPIENT):
        channel=m.logical_channel(kind,recipient);identity=m._hash({'channel':channel,'purpose':purpose})
        self.data[m.CONTROL][identity]={'_id':identity,'schema':1,'channel':channel,'purpose':purpose,'history_manifest':HISTORY,'history_complete':True,'revision':0,'active':None}


class Tests(unittest.TestCase):
    def setUp(self):self.client=Client();self.client.provision();self.store=self.make();self.ids=[ObjectId()for _ in range(2)]
    def make(self,kind='email',purpose='digest',recipient=RECIPIENT):
        return m.MailLedger(self.client,enabled=True,kind=kind,purpose=purpose,recipient_set_fingerprint=recipient,review=REVIEW)
    def prepare(self,nonce='n'*24,ids=None,rail='apps_script'):
        return self.store.prepare(nonce,self.ids if ids is None else ids,CONTENT,rail=rail)
    def started(self):
        row=self.prepare();self.assertTrue(self.store.start(row['_id'],row['hash'],'t'*24)['permit']);return row
    def reason(self,fn,expected):
        with self.assertRaises(m.LedgerRefused)as error:fn()
        self.assertEqual(error.exception.reason,expected)
        self.assertNotIn('PRIVATE',str(error.exception))

    def test_off_zero_attributes_repr_and_calls(self):
        class Hostile:
            def __getattribute__(self,k):raise AssertionError('IO')
        off=m.MailLedger(Hostile());self.assertEqual(repr(off),'MailLedger(enabled=False)')
        self.reason(lambda:off.status('x'),'disabled')
        self.reason(lambda:off.prepare('n',[],CONTENT,rail='apps_script'),'disabled')
        self.reason(lambda:m.MailLedger(enabled=1),'invalid')

    def test_exact_history_gate_no_genesis_or_provision(self):
        before=copy.deepcopy(self.client.data)
        for key in REVIEW:
            bad=dict(REVIEW);bad[key]=False
            self.reason(lambda:m.MailLedger(self.client,enabled=True,kind='email',purpose='digest',recipient_set_fingerprint=RECIPIENT,review=bad),'invalid'if key=='history_manifest'else'history_unverified')
        self.assertEqual(before,self.client.data)
        self.client.data[m.CONTROL].clear();self.reason(self.prepare,'schema');self.assertFalse(self.client.data[m.CONTROL])

    def test_ttl_and_schema_index_refusal_no_mutation(self):
        for name in self.client.indexes:
            good=self.client.indexes[name]
            for bad in [[{'name':'ttl','key':{'x':1},'expireAfterSeconds':1}],[],[{'name':'_id_','key':{'_id':1},'sparse':True}]]:
                self.client.indexes[name]=bad;self.reason(self.make,'schema')
            self.client.indexes[name]=good
        self.assertFalse(self.client.data[m.RECEIPTS])

    def test_hash_sorted_ids_no_transport_key_no_body_or_address(self):
        row=self.prepare();again=self.prepare(ids=self.ids[::-1]);self.assertEqual(row,again)
        self.assertEqual(row['ids'],sorted(str(x)for x in self.ids))
        self.assertNotIn('payload',row);self.assertNotIn('html',row);self.assertNotIn('recipient',row)
        self.reason(lambda:self.store.prepare('n'*24,self.ids,'d'*64,rail='apps_script'),'conflict_other_hash')
        self.reason(lambda:self.prepare(rail='smtp'),'conflict_other_hash')
        channel=self.store.channel
        self.assertEqual(channel,m.logical_channel('email',RECIPIENT))
        self.assertNotEqual(channel,m.logical_channel('email','e'*64))

    def test_prepare_overlaps_hold_whole_unit(self):
        self.prepare(ids=self.ids[:1]);before=copy.deepcopy(self.client.data)
        self.reason(lambda:self.prepare('z'*24),'conflict_prepared')
        self.assertEqual(before,self.client.data)
        self.assertNotIn(self.store.article_key(self.ids[1]),self.client.data[m.ARTICLES])

    def test_start_replay_no_new_permit_and_no_release_by_time(self):
        row=self.started()
        for attempt in ['t'*24,'a'*24]:self.assertFalse(self.store.start(row['_id'],row['hash'],attempt)['permit'])
        self.reason(lambda:self.store.exclusions(self.ids),'conflict_started')
        self.reason(lambda:self.prepare('z'*24),'conflict_started')
        result=self.store.cancel(row['_id'],row['hash']);self.assertEqual(result['state'],'held')
        self.assertEqual(self.store.status(row['_id'])['state'],'started')

    def test_ack_readback_atomic_keys_idempotent_no_flags(self):
        row=self.started();result=self.store.acknowledge(row['_id'],row['hash'],'t'*24)
        self.assertEqual(result,{'state':'acknowledged','scope':'bridge_send_returned_not_delivery','send_allowed':False})
        self.assertEqual(result,self.store.acknowledge(row['_id'],row['hash'],'t'*24))
        self.assertEqual(set(self.store.exclusions(self.ids)['excluded_ids']),set(str(i)for i in self.ids))
        self.reason(lambda:self.prepare('z'*24),'conflict_sent')
        self.assertEqual(set(self.client.data),{m.CONTROL,m.RECEIPTS,m.ARTICLES})

    def test_cancel_prepared_releases_by_state_and_preserves_receipt(self):
        row=self.prepare();self.assertEqual(self.store.cancel(row['_id'],row['hash'])['state'],'cancelled')
        self.assertEqual(self.store.exclusions(self.ids)['excluded_ids'],[])
        self.assertEqual(self.store.status(row['_id'])['state'],'cancelled')
        self.prepare('z'*24);self.assertEqual(len(self.client.data[m.RECEIPTS]),2)
        self.assertFalse(self.store.start(row['_id'],row['hash'],'t'*24)['permit'])

    def test_operator_resolve_unsent_or_sent_exact_binding(self):
        for sent in [False,True]:
            self.setUp();row=self.started()
            bad=self.store.resolve(row['_id'],row['hash'],'a'*24,confirmed_sent=sent,authority_reference='f'*64)
            self.assertEqual(bad['state'],'held')
            result=self.store.resolve(row['_id'],row['hash'],'t'*24,confirmed_sent=sent,authority_reference='f'*64)
            self.assertEqual(result['state'],'acknowledged'if sent else'operator_resolved_unsent')
            self.assertEqual(self.store.status(row['_id'])['resolution_reference'],'f'*64)
            if sent:self.assertEqual(len(self.store.exclusions(self.ids)['excluded_ids']),2)
            else:self.prepare('z'*24)
        self.setUp();row=self.prepare()
        self.assertEqual(self.store.resolve(row['_id'],row['hash'],'t'*24,confirmed_sent=False,authority_reference='f'*64)['state'],'held')

    def test_distinct_control_purpose_recipient_and_kind(self):
        self.prepare()
        for kind,purpose,recipient in [('email','critical',RECIPIENT),('email','digest','d'*64),('telegram','digest',RECIPIENT),('whatsapp','digest',RECIPIENT)]:
            self.client.provision(kind,purpose,recipient);store=self.make(kind,purpose,recipient)
            self.assertNotEqual(store.control_id,self.store.control_id)
            store.prepare('n'*24,self.ids,CONTENT,rail='apps_script')
        self.assertEqual(len(self.client.data[m.RECEIPTS]),5)
        self.reason(lambda:self.make(purpose='weekly'),'invalid')

    def test_more_than_10000_retained_keys_120_lookup_only(self):
        row=self.started();self.store.acknowledge(row['_id'],row['hash'],'t'*24)
        for i in range(10001):self.client.data[m.ARTICLES]['historical-'+str(i)]={'opaque':'unqueried'}
        ids=self.ids+[ObjectId()for _ in range(118)]
        self.client.reads.clear();result=self.store.exclusions(ids)
        self.assertEqual(len(result['excluded_ids']),2)
        query=next(q for name,q in self.client.reads if name==m.ARTICLES)
        self.assertEqual(len(query['_id']['$in']),120)
        self.reason(lambda:self.store.exclusions(ids+[ObjectId()]),'capacity')
        self.reason(lambda:self.prepare(ids=[]),'invalid')

    def test_unknown_commit_before_and_after_never_permit(self):
        for mode in ['before','after']:
            self.setUp();row=self.prepare();self.client.fail_commit=mode
            result=self.store.start(row['_id'],row['hash'],'t'*24)
            self.assertFalse(result['permit']);self.assertEqual(result['reason'],'unknown_commit');self.assertTrue(result['status_required'])
            self.client.fail_commit=None
            self.assertEqual(self.store.status(row['_id'])['state'],'prepared'if mode=='before'else'started')
            self.assertEqual(self.client.aborts,0)
            if mode=='after':self.assertFalse(self.store.start(row['_id'],row['hash'],'t'*24)['permit'])

    def test_unknown_ack_only_then_status_no_renewed_send(self):
        row=self.started();self.client.fail_commit='after'
        self.assertEqual(self.store.acknowledge(row['_id'],row['hash'],'t'*24)['state'],'held')
        self.client.fail_commit=None
        self.assertEqual(self.store.status(row['_id'])['state'],'acknowledged')
        self.assertEqual(self.store.acknowledge(row['_id'],row['hash'],'t'*24)['state'],'acknowledged')
        self.assertFalse(self.store.start(row['_id'],row['hash'],'t'*24)['permit'])

    def test_readback_failure_never_permit_or_ack_success(self):
        row=self.prepare()
        with patch.object(self.store,'status',side_effect=m.LedgerRefused('readback')):
            self.assertFalse(self.store.start(row['_id'],row['hash'],'t'*24)['permit'])
        with patch.object(self.store,'status',side_effect=m.LedgerRefused('readback')):
            self.assertEqual(self.store.acknowledge(row['_id'],row['hash'],'t'*24)['state'],'held')
        self.assertEqual(self.store.status(row['_id'])['state'],'acknowledged')

    def test_writeconflict_transient_and_duplicate_no_application_retry(self):
        for failure_value in [failure('TransientTransactionError',112),OperationFailure('PRIVATE',112),DuplicateKeyError('PRIVATE')]:
            self.setUp();before=copy.deepcopy(self.client.data);sessions=self.client.sessions
            self.client.fail_write=failure_value
            self.reason(self.prepare,'conflict')
            self.assertEqual(self.client.sessions-sessions,1);self.assertEqual(self.client.data,before);self.assertEqual(self.client.aborts,1)

    def test_two_racing_instances_exactly_one_commit(self):
        other=self.make();self.client.barrier=threading.Barrier(2)
        def run(store,nonce):
            try:return store.prepare(nonce,self.ids,CONTENT,rail='apps_script')['state']
            except m.LedgerRefused as e:return e.reason
        with ThreadPoolExecutor(2)as pool:
            results=list(pool.map(lambda pair:run(*pair),[(self.store,'n'*24),(other,'z'*24)]))
        self.client.barrier=None
        self.assertEqual(results.count('prepared'),1);self.assertEqual(results.count('conflict'),1)
        self.assertEqual(len(self.client.data[m.RECEIPTS]),1)
        self.assertEqual(len(self.client.data[m.ARTICLES]),2)
        self.assertEqual(self.client.data[m.CONTROL][self.store.control_id]['revision'],1)

    def test_restart_retains_ack_and_unresolved_claim(self):
        row=self.started();other=self.make()
        self.assertFalse(other.start(row['_id'],row['hash'],'t'*24)['permit'])
        other.acknowledge(row['_id'],row['hash'],'t'*24)
        self.assertEqual(len(self.make().exclusions(self.ids)['excluded_ids']),2)

    def test_stored_schema_no_partial_output(self):
        row=self.prepare();key=self.store.article_key(self.ids[0]);self.client.data[m.ARTICLES][key]['state']='invented'
        self.reason(lambda:self.store.exclusions(self.ids),'schema')
        self.assertFalse(self.store.start(row['_id'],row['hash'],'t'*24)['permit'])
        self.client.data[m.RECEIPTS][row['_id']]['ids']=self.client.data[m.RECEIPTS][row['_id']]['ids'][::-1]
        self.reason(lambda:self.store.status(row['_id']),'schema')

    def test_source_pinned_driver_semantics_and_options(self):
        import inspect
        from pymongo.synchronous.client_session import ClientSession
        self.assertEqual(m.verify_driver(),'4.18.2')
        retry=inspect.getsource(ClientSession._finish_transaction_with_retry)
        commit=inspect.getsource(ClientSession.commit_transaction)
        self.assertIn('retryable=True',retry);self.assertIn('_TxnState.COMMITTED',commit)
        self.prepare();option=self.client.tx_options[-1]
        self.assertEqual(option['read_concern'].document,{'level':'snapshot'})
        self.assertEqual(option['write_concern'].document,{'w':'majority','j':True,'wtimeout':5000})
        self.assertEqual(option['max_commit_time_ms'],5000)
        source=inspect.getsource(m.MailLedger)
        self.assertNotIn('with_transaction(',source);self.assertNotIn('delete_one(',source);self.assertNotIn('update_many(',source)


if __name__=='__main__':unittest.main()
