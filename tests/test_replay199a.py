import unittest,copy
from types import SimpleNamespace
from integration.replay199_schema import manifest,source,ReplayRefused
from integration.replay199_core import ArchiveCore
from integration.replay199_transactions import NoRetryTransactionProvider
class Tx:
 def __init__(self,client):self.c=client;self.working=None;self.committed=False
 def start_transaction(self,**kwargs):self.c.starts+=1;self.working=copy.deepcopy(self.c.data)
 def commit_transaction(self):
  self.c.commits+=1
  if self.c.fail=='commit_before':raise ValueError()
  self.c.data=self.working;self.committed=True
  if self.c.fail=='commit_after':raise ValueError()
 def abort_transaction(self):self.c.aborts+=1;self.working=None
 def end_session(self):self.c.ends+=1
class Collection:
 def __init__(self,client,name):
  self.database=SimpleNamespace(name='geo_intel',client=client);self.name=name;self.write_concern=SimpleNamespace(document={'w':'majority','j':True,'wtimeout':5000});self.read_concern=SimpleNamespace(document={'level':'majority'})
 def rows(self,session):return session.working[self.name]if session else self.database.client.data[self.name]
 def find_one(self,q,session=None,**kw):
  c=self.database.client
  if c.fail=='read':raise ValueError()
  r=copy.deepcopy(self.rows(session).get(q['_id']))
  if c.fail=='archive_readback'and self.name.endswith('replay199')and r and r.get('kind')=='record':r['sha256']='0'*64
  return r
 def insert_one(self,r,session=None):
  c=self.database.client;c.inserts+=1
  if c.fail=='insert':raise ValueError()
  rows=self.rows(session)
  if r['_id']in rows:raise ValueError()
  rows[r['_id']]=copy.deepcopy(r);return SimpleNamespace(acknowledged=c.fail!='insert_ack')
 def replace_one(self,q,r,upsert=False,session=None):
  c=self.database.client;c.replaces+=1
  if c.fail=='cas_raise':raise ValueError()
  rows=self.rows(session);before=rows.get(q['_id']);match=before and all(before.get(k)==v for k,v in q.items())and c.fail!='cas_miss'
  if match:rows[r['_id']]=copy.deepcopy(r)
  return SimpleNamespace(acknowledged=c.fail!='cas_ack',matched_count=int(bool(match)))
class Client:
 def __init__(self,family):
  self.starts=self.commits=self.aborts=self.ends=self.inserts=self.replaces=0;self.fail='';self.family=family
  from integration.replay199_schema import FAMILIES
  self.sn,self.an,self.identity,_=FAMILIES[family];self.data={self.sn:{},self.an:{'batch:0':manifest(family,0,'0'*64,[])},'collector_checkpoints197':{}}
  self.s=Collection(self,self.sn);self.a=Collection(self,self.an);self.cp=Collection(self,'collector_checkpoints197')
 def start_session(self,**kw):return Tx(self)
 def core(self):return ArchiveCore(self,self.s,self.a,family=self.family,fingerprint='a'*64 if self.family=='collector'else None,enabled=True,transaction_provider=NoRetryTransactionProvider(self,synthetic_session_factory=lambda:Tx(self)))
 def provision(self,count=2):
  if self.family=='collector':
   rows=[{'key':f'{i:064x}','fence':i,'phase':'failed_before_write','lease_until':220,'counts':{},'updated_at':100}for i in range(1,count+1)]
   d={'_id':self.identity,'schema':2,'revision':0,'fingerprint':'a'*64,'fence':count,'active':None,'history':rows}
  else:
   rows=[{'nonce_hash':f'{i:064x}','body_hash':'b'*64,'identity_hash':'c'*64,'fence':i,'phase':'complete','started_at':100,'deadline':125,'status':500,'response_hash':'d'*64,'response_bytes':0}for i in range(1,count+1)]
   d={'_id':self.identity,'schema':3,'revision':0,'window_start':100,'calls':min(count,60),'fence':count,'active':None,'last_clock':125,'receipts':rows}
  d.update(archive_epoch=0,archived_count=0,chain_head=self.data[self.an]['batch:0']['sha256']);self.data[self.sn][self.identity]=d
class Tests(unittest.TestCase):
 def test_default_disabled_no_access(self):
  c=ArchiveCore(None,None,None,family='broker')
  with self.assertRaises(ReplayRefused):c.lookup('a'*64,body_hash='b'*64,identity_hash='c'*64)
 def test_both_rollover_atomic_lookup_status_and_counters(self):
  for family in ('collector','broker'):
   c=Client(family);c.provision();before=copy.deepcopy(c.data[c.sn][c.identity]);out=c.core().rollover(expected_revision=0,checkpoints=c.cp if family=='collector'else None);self.assertEqual(out['records'],2);after=c.data[c.sn][c.identity]
   for key in ('fence','calls','window_start','last_clock'):
    if key in before:self.assertEqual(before[key],after[key])
   opts={'body_hash':'b'*64,'identity_hash':'c'*64}if family=='broker'else{}
   replay=c.core().lookup(f'{1:064x}',**opts);self.assertTrue(replay['archived']);self.assertEqual(replay['state'],'status_only');self.assertFalse(out['cadence_ready']);self.assertEqual(c.core().lookup('f'*64,**opts)['state'],'verified_absent')
 def test_each_failure_cut_atomic_or_unknown_no_retry(self):
  for failure in ('read','insert','insert_ack','archive_readback','cas_raise','cas_miss','cas_ack','commit_before','commit_after'):
   c=Client('broker');c.provision();old=copy.deepcopy(c.data);c.fail=failure
   with self.assertRaises(ReplayRefused):c.core().rollover(expected_revision=0)
   self.assertEqual(c.starts,1);self.assertLessEqual(c.commits,1)
   if failure=='commit_after':self.assertNotEqual(old,c.data);c.fail='';self.assertTrue(c.core().lookup(f'{1:064x}',body_hash='b'*64,identity_hash='c'*64)['archived'])
   else:self.assertEqual(old,c.data)
 def test_missing_corrupt_chain_record_lookup_held_not_absent(self):
  for failure in ('manifest_missing','record_missing','record_corrupt','head_wrong'):
   c=Client('broker');c.provision();c.core().rollover(expected_revision=0)
   if failure=='manifest_missing':del c.data[c.an]['batch:1']
   if failure=='record_missing':del c.data[c.an][f'{1:064x}']
   if failure=='record_corrupt':c.data[c.an][f'{1:064x}']['row']['status']=200
   if failure=='head_wrong':c.data[c.sn][c.identity]['chain_head']='f'*64
   with self.assertRaises(ReplayRefused):c.core().lookup('e'*64,body_hash='b'*64,identity_hash='c'*64)
 def test_broker_cross_uid_or_body_mismatch_no_disclosure(self):
  c=Client('broker');c.provision();c.core().rollover(expected_revision=0)
  for body,identity in (('e'*64,'c'*64),('b'*64,'f'*64)):
   with self.assertRaises(ReplayRefused):c.core().lookup(f'{1:064x}',body_hash=body,identity_hash=identity)
 def test_held_active_no_rollover_expiry_not_release(self):
  c=Client('collector');c.provision();d=c.data[c.sn][c.identity];d['active']=d['history'].pop();d['active']['phase']='uncertain_after_write';old=copy.deepcopy(c.data)
  with self.assertRaises(ReplayRefused):c.core().rollover(expected_revision=0,checkpoints=c.cp)
  self.assertEqual(old,c.data);self.assertEqual(c.inserts,0)
 def test_stale_revision_no_insert_and_no_auto_migration(self):
  c=Client('broker');c.provision()
  with self.assertRaises(ReplayRefused):c.core().rollover(expected_revision=99)
  self.assertEqual(c.inserts,0);d=c.data[c.sn][c.identity];d['schema']=2
  with self.assertRaises(ReplayRefused):source('broker',d)
 def test_full64_and_repeated_empty_rollover_refused(self):
  c=Client('broker');c.provision(64);out=c.core().rollover(expected_revision=0);self.assertEqual(out['records'],64)
  with self.assertRaises(ReplayRefused):c.core().rollover(expected_revision=1)
  self.assertEqual(c.data[c.sn][c.identity]['archived_count'],64)
 def test_checkpoint_completed_full_v2_and_missing_held(self):
  from tests.test_collector197c import inputs,cov
  from tests.test_collector197a import Checkpoints
  from integration.collector197_coverage import CoverageCheckpoints
  c=Client('collector');c.provision(1);row=c.data[c.sn][c.identity]['history'][0];row['phase']='completed'
  with self.assertRaises(ReplayRefused):c.core().rollover(expected_revision=0,checkpoints=c.cp)
  cp=Checkpoints();CoverageCheckpoints(cp).put(row['key'],1,inputs(),cov());c.data['collector_checkpoints197']=copy.deepcopy(cp.rows)
  c.core().rollover(expected_revision=0,checkpoints=c.cp);self.assertEqual(c.data[c.an][row['key']]['checkpoint'],cp.rows[row['key']])
 def test_source_archive_fence_collision_refused(self):
  c=Client('collector');c.provision();c.core().rollover(expected_revision=0,checkpoints=c.cp);d=c.data[c.sn][c.identity];d['history']=[{'key':'f'*64,'fence':1,'phase':'failed_before_write','lease_until':220,'counts':{},'updated_at':100}]
  with self.assertRaises(ReplayRefused):c.core().lookup('e'*64)
 def test_no_with_transaction_or_runtime_import(self):
  from pathlib import Path
  root=Path(__file__).resolve().parents[1];s=(root/'integration/replay199_core.py').read_text();self.assertNotIn('.with_transaction(',s);self.assertNotIn('replay199',(root/'production_entry.py').read_text())
 def test_lost_commit_exact_reconcile_no_clear_or_retry(self):
  c=Client('broker');c.provision();core=c.core();c.fail='commit_after'
  with self.assertRaises(ReplayRefused):core.rollover(expected_revision=0)
  operation=copy.deepcopy(core.last_operation);self.assertTrue(core.uncertain);c.fail='';result=core.reconcile(operation);self.assertEqual(result['state'],'verified_committed_archive_only');self.assertFalse(result['holds_cleared'])
  with self.assertRaises(ReplayRefused):core.rollover(expected_revision=1)
  operation['chain_head']='f'*64
  with self.assertRaises(ReplayRefused):core.reconcile(operation)
 def test_transaction_deadline_and_byte_cap_prefix_not_truncated(self):
  from unittest.mock import patch
  c=Client('broker');c.provision();clock=iter([0,25]);core=ArchiveCore(c,c.s,c.a,family='broker',enabled=True,clock=lambda:next(clock),transaction_provider=NoRetryTransactionProvider(c,synthetic_session_factory=lambda:Tx(c)))
  with self.assertRaises(ReplayRefused):core.rollover(expected_revision=0)
  self.assertEqual(c.inserts,0)
  c=Client('broker');c.provision(4)
  # Small injected test budget forces an oldest-prefix rollover, never cut rows.
  with patch('integration.replay199_core.LIMIT_BYTES',2600):
   out=c.core().rollover(expected_revision=0)
   self.assertTrue(0<out['records']<4)
  d=c.data[c.sn][c.identity];self.assertEqual(len(d['receipts'])+d['archived_count'],4);self.assertEqual(d['receipts'][0]['fence'],out['records']+1)
 def test_readonly_preflight_exact_roles_genesis_no_mutations(self):
  from integration.replay199_preflight import inspect_archive
  class Cursor(list):
   def close(self):pass
  for family in ('broker','collector'):
   c=Client(family);c.provision();collections={c.sn:c.s,c.an:c.a,'collector_checkpoints197':c.cp}
   for item in collections.values():item.list_indexes=lambda **kw:Cursor([{'key':{'_id':1}}])
   grants=[{'resource':{'db':'geo_intel','collection':c.sn},'actions':['find','listIndexes','update']},{'resource':{'db':'geo_intel','collection':c.an},'actions':['find','listIndexes','insert']}]
   if family=='collector':grants.append({'resource':{'db':'geo_intel','collection':'collector_checkpoints197'},'actions':['find','listIndexes']})
   class Admin:
    def command(self,q):
     if 'hello'in q:return {'ok':1,'setName':'fixture','isWritablePrimary':True,'logicalSessionTimeoutMinutes':30,'maxWireVersion':17}
     return {'ok':1,'authInfo':{'authenticatedUsers':[{}],'authenticatedUserPrivileges':grants}}
   class DB:
    def get_collection(self,name,**kw):return collections[name]
   c.admin=Admin();Client.__getitem__=lambda self,name:DB()
   result=inspect_archive(c,family=family,fingerprint='a'*64 if family=='collector'else None);self.assertFalse(result['archive_completeness_verified']);self.assertEqual(c.starts+c.inserts+c.replaces,0)
   grants[1]['actions'].append('remove')
   with self.assertRaises(ReplayRefused):inspect_archive(c,family=family,fingerprint='a'*64 if family=='collector'else None)
 def test_checkpoint_v1_exact_and_corruption_fails(self):
  from tests.test_collector197c import inputs
  from tests.test_collector197a import Checkpoints
  from collector110_prep.durable_checkpoint import DurableCheckpoints
  c=Client('collector');c.provision(1);j=c.data[c.sn][c.identity]['history'][0];j['phase']='completed';pc=Checkpoints();DurableCheckpoints(pc).put(j['key'],1,inputs());c.data['collector_checkpoints197']=copy.deepcopy(pc.rows);c.data['collector_checkpoints197'][j['key']]['hash']='f'*64
  with self.assertRaises(ReplayRefused):c.core().rollover(expected_revision=0,checkpoints=c.cp)
  c.data['collector_checkpoints197']=copy.deepcopy(pc.rows);c.core().rollover(expected_revision=0,checkpoints=c.cp);self.assertEqual(c.data[c.an][j['key']]['checkpoint']['version'],1)
 def test_epoch_counter_and_manifest_corruption_refused(self):
  for change in (lambda d:d.update(archive_epoch=1025),lambda d:d.update(archived_count=4097),lambda d:d.update(archive_epoch=1)):
   c=Client('broker');c.provision();change(c.data[c.sn][c.identity])
   with self.assertRaises(ReplayRefused):c.core().lookup('e'*64,body_hash='b'*64,identity_hash='c'*64)
  c=Client('broker');c.provision();c.data[c.an]['batch:0']['previous']='f'*64
  with self.assertRaises(ReplayRefused):c.core().rollover(expected_revision=0)

 def test_native_no_provider_rejected_before_session(self):
  c=Client('broker');c.provision()
  with self.assertRaises(ReplayRefused):ArchiveCore(c,c.s,c.a,family='broker',enabled=True)
  self.assertEqual(c.starts,0)
  from pymongo import MongoClient
  native=MongoClient(connect=False)
  try:
   with self.assertRaises(ReplayRefused):NoRetryTransactionProvider(native,synthetic_session_factory=lambda:None)
  finally:native.close()
