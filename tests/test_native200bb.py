import unittest,copy,hashlib
from unittest.mock import patch
from tests import test_native200ba as setup
from integration.native200_core import NativeArchiveCore
from integration.native200_adapters import NativeArchivedCollectorLedger,NativeArchivedProxyReceiptBudget
from integration.replay199_adapters import ArchivedCollectorLedger,ArchivedProxyReceiptBudget
from integration.native200_transactions import NativeNoRetryProvider
class Tests(unittest.TestCase):
 setup_server=setup.Tests.setup_server
 def core(self,c,f):return NativeArchiveCore(c,family=f.family,fingerprint='a'*64 if f.family=='collector'else None,enabled=True)
 def test_exact_type_old_gates_unchanged(self):
  for family,old,new in [('collector',ArchivedCollectorLedger,NativeArchivedCollectorLedger),('broker',ArchivedProxyReceiptBudget,NativeArchivedProxyReceiptBudget)]:
   s,c,f,key=self.setup_server(family);core=self.core(c,f)
   with self.assertRaises(ValueError):old(core)
   new(core)
   with self.assertRaises(ValueError):new(NativeArchiveCore(None,family=family))
 def test_collector_submit_replay_status_one_mutation_guardheld(self):
  s,c,f,key=self.setup_server('collector');ledger=NativeArchivedCollectorLedger(self.core(c,f));nonce='z'*24;job=ledger.submit(nonce,200);self.assertEqual(job['phase'],'accepted');self.assertEqual(ledger.submit(nonce,200),job);self.assertEqual(ledger.status(job['key'])['phase'],'accepted')
  self.assertEqual(len(s.data['native_operations200']),1);self.assertEqual(len(s.data['native_outcomes200']),1);self.assertEqual(s.data['native_guards200'][key]['phase'],'acknowledged')
  with self.assertRaises(ValueError):ledger.heartbeat(job['key'],job['fence'],201)
  self.assertEqual(s.data[f.sn][f.identity]['active'],job)
 def test_broker_claim_replay_scope_status_guardheld(self):
  s,c,f,key=self.setup_server();budget=NativeArchivedProxyReceiptBudget(self.core(c,f));nonce='z'*24;out=budget.claim(nonce,'b'*64,'c'*64,200);self.assertEqual(out['state'],'claimed');r=out['receipt'];self.assertEqual(budget.claim(nonce,'b'*64,'c'*64,200)['state'],'replay_status_only');self.assertEqual(budget.status(nonce,'b'*64,'c'*64)['receipt'],r)
  with self.assertRaises(ValueError):budget.claim(nonce,'a'*64,'c'*64,200)
  with self.assertRaises(ValueError):budget.start(r,201)
  self.assertEqual(s.data[f.sn][f.identity]['calls'],3);self.assertEqual(s.data[f.sn][f.identity]['receipts'][-1],r)
 def test_readonly_archived_replay_no_journal_reservation(self):
  for family in ('collector','broker'):
   s,c,f,key=self.setup_server(family);core=self.core(c,f)
   from integration.native200_store import NativeStore
   core.rollover(expected_revision=0,checkpoints=NativeStore(core.provider,'collector_checkpoints197')if family=='collector'else None)
   writes=sum('insert'in d or'update'in d for d in s.commands)
   row=next(v for v in s.data[f.an].values()if v.get('kind')=='record')['row']
   if family=='collector':out=NativeArchivedCollectorLedger(core).status(row['key']);self.assertTrue(out['archived'])
   else:
    out=core.lookup(row['nonce_hash'],body_hash=row['body_hash'],identity_hash=row['identity_hash']);self.assertTrue(out['archived'])
   self.assertEqual(sum('insert'in d or'update'in d for d in s.commands),writes)
 def test_plan_failure_no_guard_and_bad_chain(self):
  s,c,f,key=self.setup_server();del s.data[f.an]['batch:0'];budget=NativeArchivedProxyReceiptBudget(self.core(c,f))
  with self.assertRaises(ValueError):budget.claim('z'*24,'b'*64,'c'*64,200)
  self.assertIsNone(s.data['native_guards200'][key]['operation'])
 def test_mutation_marker_and_source_same_txn(self):
  s,c,f,key=self.setup_server();budget=NativeArchivedProxyReceiptBudget(self.core(c,f));budget.claim('z'*24,'b'*64,'c'*64,200)
  update=next(d for d in s.commands if d.get('update')==f.sn);marker=next(d for d in s.commands if d.get('insert')=='native_outcomes200');self.assertEqual(update['txnNumber'],marker['txnNumber']);self.assertEqual(update['lsid'],marker['lsid']);self.assertFalse(update['autocommit'])
  intent=next(d for d in s.commands if d.get('insert')=='native_operations200');self.assertNotIn('autocommit',intent);self.assertLess(s.commands.index(intent),s.commands.index(update))
 def test_collector_each_transition_on_independent_preseed_no_closure(self):
  for action in ('advance','heartbeat','terminal'):
   s,c,f,key=self.setup_server('collector',count=0);old=ArchivedCollectorLedger(f.core());job=old.submit('n'*24,100)
   if action=='terminal':job=old.advance(job['key'],job['fence'],'running',101,{})
   s.data[f.sn]=copy.deepcopy(f.data[f.sn]);ledger=NativeArchivedCollectorLedger(self.core(c,f))
   if action=='advance':out=ledger.advance(job['key'],job['fence'],'running',102,{'fetched':1});self.assertEqual(out['phase'],'running')
   elif action=='heartbeat':out=ledger.heartbeat(job['key'],job['fence'],102);self.assertEqual(out['lease_until'],222)
   else:out=ledger.advance(job['key'],job['fence'],'failed_before_write',102,{});self.assertIsNone(s.data[f.sn][f.identity]['active'])
   self.assertEqual(s.data['native_guards200'][key]['phase'],'acknowledged');self.assertEqual(len(s.data['native_operations200']),1)
 def test_broker_each_transition_preseed_and_unknown_never_refund(self):
  for action in ('start','finish','hold','expired'):
   s,c,f,key=self.setup_server(count=0);f.data[f.sn][f.identity]['last_clock']=100;old=ArchivedProxyReceiptBudget(f.core());ticket=old.claim('n'*24,'b'*64,'c'*64,100)['receipt']
   if action!='start':ticket=old.start(ticket,101)
   s.data[f.sn]=copy.deepcopy(f.data[f.sn]);budget=NativeArchivedProxyReceiptBudget(self.core(c,f));now=126 if action=='expired'else 102
   if action=='start':out=budget.start(ticket,now);self.assertEqual(out['phase'],'send_started')
   elif action=='hold':out=budget.hold(ticket,now);self.assertEqual(out['phase'],'unknown_held')
   else:out=budget.finish(ticket,now,status=200,response_hash='d'*64,response_bytes=20);self.assertEqual(out['phase'],'unknown_held'if action=='expired'else'complete')
   d=s.data[f.sn][f.identity];self.assertEqual(d['calls'],1)
   if action in('hold','expired'):self.assertEqual(d['active']['phase'],'unknown_held')
   self.assertEqual(s.data['native_guards200'][key]['phase'],'acknowledged')
 def test_unknown_commit391_no_ticket_retry_or_release(self):
  for family in ('collector','broker'):
   s,c,f,key=self.setup_server(family,fail=lambda d:'commitTransaction'in d and d.get('txnNumber')==2);core=self.core(c,f);adapter=NativeArchivedCollectorLedger(core)if family=='collector'else NativeArchivedProxyReceiptBudget(core)
   with self.assertRaises(ValueError):adapter.submit('n'*24,200)if family=='collector'else adapter.claim('n'*24,'b'*64,'c'*64,200)
   self.assertTrue(core.uncertain);self.assertEqual(s.data['native_guards200'][key]['phase'],'commit_attempt');self.assertEqual(sum('commitTransaction'in d and d.get('txnNumber')==2 for d in s.commands),1)
   restart=NativeArchivedCollectorLedger(self.core(c,f))if family=='collector'else NativeArchivedProxyReceiptBudget(self.core(c,f))
   with self.assertRaises(ValueError):restart.submit('z'*24,201)if family=='collector'else restart.claim('z'*24,'b'*64,'c'*64,201)
 def test_invalid_scope_clock_full_hot_no_reservation(self):
  cases=[('collector',64,'n'*24,200),('broker',64,'n'*24,200),('collector',0,'short',200),('broker',0,'n'*24,1)]
  for family,count,nonce,now in cases:
   s,c,f,key=self.setup_server(family,count=count);core=self.core(c,f);adapter=NativeArchivedCollectorLedger(core)if family=='collector'else NativeArchivedProxyReceiptBudget(core)
   with self.assertRaises(ValueError):adapter.submit(nonce,now)if family=='collector'else adapter.claim(nonce,'b'*64,'c'*64,now)
   self.assertIsNone(s.data['native_guards200'][key]['operation']);self.assertEqual(len(s.data['native_operations200']),0)
 def test_source391_before_commit_holds_and_aborts_once(self):
  s,c,f,key=self.setup_server(fail=lambda d:d.get('update')=='finder_budget198');core=self.core(c,f);adapter=NativeArchivedProxyReceiptBudget(core)
  with self.assertRaises(ValueError):adapter.claim('n'*24,'b'*64,'c'*64,200)
  self.assertEqual(sum(d.get('update')==f.sn for d in s.commands),1);self.assertEqual(sum('abortTransaction'in d for d in s.commands),1);self.assertEqual(sum('commitTransaction'in d for d in s.commands),1);self.assertIsNotNone(s.data['native_guards200'][key]['operation'])
 def test_old_broker_transport_exact_gate_still_rejects(self):
  from integration.replay199_broker import proxy_request_archive
  s,c,f,key=self.setup_server();adapter=NativeArchivedProxyReceiptBudget(self.core(c,f))
  with self.assertRaises(ValueError):proxy_request_archive(adapter,None,nonce='n'*24,operation='ships',clock=lambda:200)
