import unittest,copy
from unittest.mock import patch
from pymongo import MongoClient
from integration.native200_store import NativeStore
from integration.native200_journal import OperationJournal
from integration.native200_transactions import NativeNoRetryProvider
from integration.native200_core import NativeArchiveCore
from integration.replay199_schema import FAMILIES,digest
from tests import test_replay199a as fixtures
from tests.native200_state_fixture import StateServer
class Tests(unittest.TestCase):
 def setup_server(self,family='broker',fail=None,count=2):
  f=fixtures.Client(family);f.provision(count);data=f.data;key=family+':'+f.identity;
  from integration.native200_store import NAMES
  for name in NAMES:data.setdefault(name,{})
  data.update(native_operations200={},native_outcomes200={},native_guards200={key:{'_id':key,'schema':1,'family':family,'serial':0,'operation':None,'phase':'idle'}});s=StateServer(data,fail);self.addCleanup(s.close);c=MongoClient('mongodb://127.0.0.1:'+str(s.port)+'/?replicaSet=fixture',retryWrites=False,retryReads=False,serverSelectionTimeoutMS=600,connectTimeoutMS=600,socketTimeoutMS=600,heartbeatFrequencyMS=500);c.admin.command('ping');self.addCleanup(c.close);return s,c,f,key
 def plan(self,f):
  d=f.data[f.sn][f.identity];return {'family':f.family,'source':f.identity,'expected_revision':0,'epoch':0,'head':d['chain_head'],'after_hash':'a'*64}
 def test_body391_reservation_intent_phase_one_frame_and_restart_hold(self):
  targets=[lambda d:'update'in d and d['update']=='native_guards200'and d['updates'][0]['u']['phase']=='reserved',lambda d:'insert'in d and d['insert']=='native_operations200',lambda d:'update'in d and d['update']=='native_guards200'and d['updates'][0]['u']['phase']=='commit_attempt']
  for target in targets:
   with self.subTest(target=target):
    s,c,f,key=self.setup_server(fail=target);j=OperationJournal(NativeNoRetryProvider(c,enabled=True),family='broker')
    with patch.object(MongoClient,'_retry_internal',side_effect=AssertionError):
     with self.assertRaises(Exception):
      intent=j.reserve(self.plan(f));j.phase(intent,'commit_attempt')
    self.assertTrue(s.failed);self.assertEqual(sum(target(d)for d in s.commands),1)
    restart=OperationJournal(NativeNoRetryProvider(c,enabled=True),family='broker')
    with self.assertRaises(ValueError):restart.reserve(self.plan(f))
    self.assertIsNotNone(s.data['native_guards200'][key]['operation']);self.assertEqual(sum('commitTransaction'in d for d in s.commands),0)
 def test_both_rollover_marker_ackheld_restart_newwrite_blocked(self):
  for family in ('collector','broker'):
   with self.subTest(family=family):
    s,c,f,key=self.setup_server(family);core=NativeArchiveCore(c,family=family,fingerprint='a'*64 if family=='collector'else None,enabled=True);cp=NativeStore(core.provider,'collector_checkpoints197')if family=='collector'else None
    with patch.object(MongoClient,'_retry_internal',side_effect=AssertionError):out=core.rollover(expected_revision=0,checkpoints=cp)
    self.assertEqual(out['records'],2);guard=s.data['native_guards200'][key];self.assertEqual(guard['phase'],'acknowledged');self.assertIsNotNone(guard['operation']);self.assertEqual(len(s.data['native_operations200']),1);self.assertEqual(len(s.data['native_outcomes200']),1)
    txinserts=[d for d in s.commands if d.get('insert')=='native_outcomes200'];self.assertFalse(txinserts[0]['autocommit']);self.assertEqual(txinserts[0]['txnNumber'],next(d for d in s.commands if d.get('update')==f.sn)['txnNumber'])
    restart=NativeArchiveCore(c,family=family,fingerprint='a'*64 if family=='collector'else None,enabled=True);self.assertEqual(restart.reconcile_pending()['state'],'committed_observed_guard_still_held');self.assertFalse(restart.reconcile_pending()['holds_cleared'])
    with self.assertRaises(ValueError):restart.journal.reserve(self.plan(f))
 def test_crashcuts_and_commit391_no_release_reconcile_not_retry_permission(self):
  cuts=[lambda d:d.get('insert')=='native_outcomes200',lambda d:'commitTransaction'in d and d.get('txnNumber')==2,lambda d:d.get('update')=='native_guards200'and d['updates'][0]['u']['phase']=='acknowledged']
  for cut in cuts:
   s,c,f,key=self.setup_server(fail=cut);core=NativeArchiveCore(c,family='broker',enabled=True)
   with self.assertRaises(ValueError):core.rollover(expected_revision=0)
   self.assertTrue(core.uncertain);self.assertIsNotNone(s.data['native_guards200'][key]['operation']);self.assertEqual(sum(cut(d)for d in s.commands),1)
   restart=NativeArchiveCore(c,family='broker',enabled=True);r=restart.reconcile_pending();self.assertFalse(r['retry_safe']);self.assertFalse(r['holds_cleared'])
   with self.assertRaises(ValueError):restart.journal.reserve(self.plan(f))
 def test_journal_capacity_missing_guard_no_begin_no_creation(self):
  s,c,f,key=self.setup_server();j=OperationJournal(NativeNoRetryProvider(c,enabled=True),family='broker');s.data['native_guards200'][key]['serial']=4096
  with self.assertRaises(ValueError):j.reserve(self.plan(f))
  del s.data['native_guards200'][key]
  with self.assertRaises(ValueError):j.reserve(self.plan(f))
  self.assertFalse(any('update'in d or'insert'in d or'commitTransaction'in d for d in s.commands))
 def test_raw_cursor_writeerrors_concerns_fixed_names(self):
  s,c,f,key=self.setup_server();p=NativeNoRetryProvider(c,enabled=True);store=NativeStore(p,'native_guards200');self.assertEqual(store.find_one({'_id':key})['phase'],'idle');d=next(d for d in s.commands if d.get('find')=='native_guards200');self.assertEqual(d['readConcern'],{'level':'majority'});self.assertTrue(d['singleBatch']);self.assertEqual(d['limit'],2)
  with self.assertRaises(ValueError):NativeStore(p,'unreviewed')
  with self.assertRaises(ValueError):store.replace_one({'_id':key},{'_id':key},upsert=True)
  with self.assertRaises(ValueError):store.insert_one(copy.deepcopy(s.data['native_guards200'][key]))
 def test_default_off_no_access_old_exact_types_refuse_nativecore(self):
  from integration.replay199_adapters import ArchivedCollectorLedger,ArchivedProxyReceiptBudget
  core=NativeArchiveCore(None,family='broker')
  with self.assertRaises(ValueError):core.rollover(expected_revision=0)
  with self.assertRaises(ValueError):ArchivedProxyReceiptBudget(core)
 def test_two_journal_instances_onlyone_guard_winner(self):
  import threading
  s,c,f,key=self.setup_server();j1=OperationJournal(NativeNoRetryProvider(c,enabled=True),family='broker');j2=OperationJournal(NativeNoRetryProvider(c,enabled=True),family='broker');barrier=threading.Barrier(2);results=[]
  def work(j):
   try:barrier.wait();results.append(j.reserve(self.plan(f)))
   except Exception:results.append(None)
  threads=[threading.Thread(target=work,args=(j,))for j in(j1,j2)]
  for t in threads:t.start()
  for t in threads:t.join(3)
  self.assertEqual(sum(r is not None for r in results),1);self.assertEqual(len(s.data['native_operations200']),1);self.assertEqual(s.data['native_guards200'][key]['serial'],1)
 def test_inspection_missing_collection_before_anyinsert(self):
  from integration.native200_preflight import inspect_existing
  s,c,f,key=self.setup_server();p=NativeNoRetryProvider(c,enabled=True);store=NativeStore(p,'native_operations200');del s.data['native_operations200']
  with self.assertRaises(ValueError):store.insert_one({'_id':'a'*64})
  self.assertFalse(any(d.get('insert')=='native_operations200'for d in s.commands))
 def test_source_before_after_counts_not_reset(self):
  s,c,f,key=self.setup_server();before=copy.deepcopy(s.data[f.sn][f.identity]);core=NativeArchiveCore(c,family='broker',enabled=True);core.rollover(expected_revision=0);after=s.data[f.sn][f.identity]
  for k in ('fence','calls','window_start','last_clock'):self.assertEqual(before[k],after[k])
  self.assertEqual(after['archived_count'],2);self.assertEqual(len(s.data[f.an]),4)
 def test_broken_archive_before_reservation(self):
  s,c,f,key=self.setup_server();del s.data[f.an]['batch:0'];core=NativeArchiveCore(c,family='broker',enabled=True)
  with self.assertRaises(ValueError):core.rollover(expected_revision=0)
  self.assertIsNone(s.data['native_guards200'][key]['operation']);self.assertFalse(any(d.get('insert')=='native_operations200'for d in s.commands))
 def test_inspection_invalid_schema_ttl_cursor_unique_namespace(self):
  from integration.native200_preflight import inspect_existing,VALIDATORS
  s,c,f,key=self.setup_server();store=NativeStore(NativeNoRetryProvider(c,enabled=True),'native_operations200')
  collection={'ok':1,'cursor':{'id':0,'ns':'geo_intel.$cmd.listCollections','firstBatch':[{'name':store.name,'type':'collection','options':{'validator':VALIDATORS[store.name]}}]}}
  indexes={'ok':1,'cursor':{'id':0,'ns':'geo_intel.'+store.name,'firstBatch':[{'name':'_id_','key':{'_id':1}}]}}
  mutations=[('collection',lambda r:r['cursor'].update(id=1)),('collection',lambda r:r['cursor']['firstBatch'][0]['options'].update(validator={})),('collection',lambda r:r['cursor']['firstBatch'][0].update(type='view')),('collection',lambda r:r['cursor']['firstBatch'][0]['options'].update(validationAction='warn')),('indexes',lambda r:r['cursor']['firstBatch'][0].update(expireAfterSeconds=0)),('indexes',lambda r:r['cursor']['firstBatch'][0].update(unique=False)),('indexes',lambda r:r['cursor'].update(id=1)),('indexes',lambda r:r['cursor'].update(ns='other'))]
  for where,mutate in mutations:
   a,b=copy.deepcopy(collection),copy.deepcopy(indexes);mutate(a if where=='collection'else b)
   with patch.object(store,'_command',side_effect=[a,b]):
    with self.assertRaises(ValueError):inspect_existing(store)
  with patch.object(store,'_command',side_effect=[collection,indexes]):self.assertTrue(inspect_existing(store))
 def test_find_bad_cursor_and_update_ack_hold(self):
  s,c,f,key=self.setup_server();store=NativeStore(NativeNoRetryProvider(c,enabled=True),'native_guards200')
  for cursor in ({'id':1,'ns':'geo_intel.native_guards200','firstBatch':[]},{'id':0,'ns':'other','firstBatch':[]},{'id':0,'ns':'geo_intel.native_guards200','firstBatch':[{},{}]}):
   with patch.object(store,'_command',return_value={'ok':1,'cursor':cursor}):
    with self.assertRaises(ValueError):store.find_one({'_id':key})
  for n in (True,-1,2,None):
   with patch('integration.native200_preflight.inspect_existing',return_value=True),patch.object(store,'_command',return_value={'ok':1,'n':n}):
    with self.assertRaises(ValueError):store.replace_one({'_id':key},{'_id':key})
 def test_explicit_writeconcern_and_no_provision_command(self):
  s,c,f,key=self.setup_server();j=OperationJournal(NativeNoRetryProvider(c,enabled=True),family='broker');j.reserve(self.plan(f))
  for d in s.commands:
   if next(iter(d))in ('insert','update'):self.assertEqual(d['writeConcern'],{'w':'majority','j':True,'wtimeout':5000});self.assertEqual(d['maxTimeMS'],2000)
  self.assertFalse(any(next(iter(d))in('create','collMod','createIndexes','drop','delete')for d in s.commands))
  with self.assertRaises(ValueError):j.g._command({'drop':'native_guards200'})
 def test_readonly_inspection391_one_frame(self):
  for action in ('listCollections','listIndexes'):
   s,c,f,key=self.setup_server(fail=lambda d:action in d)
   with self.assertRaises(Exception):NativeArchiveCore(c,family='broker',enabled=True)
   self.assertEqual(sum(action in d for d in s.commands),1);self.assertFalse(any('insert'in d or'update'in d for d in s.commands))
