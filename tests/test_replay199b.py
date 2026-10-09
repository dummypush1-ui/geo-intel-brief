import unittest,copy,hashlib
from integration.replay199_adapters import ArchivedCollectorLedger,ArchivedProxyReceiptBudget
from integration.replay199_schema import ReplayRefused
from tests.test_replay199a import Client
class Tests(unittest.TestCase):
 def test_collector_old_nonce_after_rollover_no_new_fence_status_retained(self):
  c=Client('collector');c.provision(0);core=c.core();a=ArchivedCollectorLedger(core);j=a.submit('n'*24,100);a.advance(j['key'],j['fence'],'running',100,{});a.advance(j['key'],j['fence'],'failed_before_write',100,{});core.rollover(expected_revision=3,checkpoints=c.cp);before=copy.deepcopy(c.data[c.sn]);old=a.submit('n'*24,101);self.assertEqual(old['phase'],'failed_before_write');self.assertEqual(c.data[c.sn],before);self.assertTrue(a.status(j['key'])['archived']);new=a.submit('z'*24,101);self.assertEqual(new['fence'],2)
 def test_broker_old_nonce_after_rollover_hash_scope_budget_retained(self):
  c=Client('broker');c.provision(0);c.data[c.sn][c.identity]['last_clock']=100;core=c.core();a=ArchivedProxyReceiptBudget(core);r=a.claim('n'*24,'b'*64,'c'*64,100)['receipt'];r=a.start(r,101);a.finish(r,102,status=200,response_hash='d'*64,response_bytes=20);core.rollover(expected_revision=3);before=copy.deepcopy(c.data[c.sn]);replay=a.claim('n'*24,'b'*64,'c'*64,103);self.assertEqual(replay['state'],'replay_status_only');self.assertEqual(c.data[c.sn],before);self.assertTrue(a.status('n'*24,'b'*64,'c'*64)['archived']);new=a.claim('z'*24,'b'*64,'c'*64,103)['receipt'];self.assertEqual(new['fence'],2);self.assertEqual(c.data[c.sn][c.identity]['calls'],2)
 def test_broker_cross_principal_or_body_mismatch_denied(self):
  for body,identity in (('e'*64,'c'*64),('b'*64,'f'*64)):
   c=Client('broker');c.provision(0);c.data[c.sn][c.identity]['last_clock']=100;core=c.core();a=ArchivedProxyReceiptBudget(core);r=a.claim('n'*24,'b'*64,'c'*64,100)['receipt'];r=a.start(r,101);a.finish(r,102,status=200,response_hash='d'*64,response_bytes=0);core.rollover(expected_revision=3);before=copy.deepcopy(c.data)
   with self.assertRaises(ReplayRefused):a.claim('n'*24,body,identity,103)
   self.assertEqual(before,c.data)
 def test_broker_unknown_expired_never_release_refund_or_rollover(self):
  c=Client('broker');c.provision(0);c.data[c.sn][c.identity]['last_clock']=100;core=c.core();a=ArchivedProxyReceiptBudget(core);r=a.claim('n'*24,'b'*64,'c'*64,100)['receipt'];r=a.start(r,101);r=a.finish(r,126,status=200,response_hash='d'*64,response_bytes=20);self.assertEqual(r['phase'],'unknown_held');self.assertEqual(c.data[c.sn][c.identity]['calls'],1)
  with self.assertRaises(ReplayRefused):a.claim('z'*24,'b'*64,'c'*64,1000)
  with self.assertRaises(ReplayRefused):c.core().rollover(expected_revision=3)
  self.assertIsNotNone(c.data[c.sn][c.identity]['active'])
 def test_collector_expired_ticket_no_takeover_or_heartbeat(self):
  c=Client('collector');c.provision(0);core=c.core();a=ArchivedCollectorLedger(core);j=a.submit('n'*24,100)
  with self.assertRaises(ReplayRefused):a.heartbeat(j['key'],j['fence'],220)
  with self.assertRaises(ReplayRefused):ArchivedCollectorLedger(c.core()).submit('z'*24,221)
  self.assertEqual(c.data[c.sn][c.identity]['active']['key'],j['key'])
 def test_full_hot64_before_rollover_held_then_old_replay_safe(self):
  for family in ('collector','broker'):
   c=Client(family);c.provision(64);core=c.core();a=ArchivedCollectorLedger(core)if family=='collector'else ArchivedProxyReceiptBudget(core)
   with self.assertRaises(ReplayRefused):a.submit('n'*24,101)if family=='collector'else a.claim('n'*24,'b'*64,'c'*64,126)
   core=c.core();core.rollover(expected_revision=0,checkpoints=c.cp if family=='collector'else None);a=ArchivedCollectorLedger(core)if family=='collector'else ArchivedProxyReceiptBudget(core)
   if family=='collector':self.assertEqual(a.submit('n'*24,101)['fence'],65)
   else:
    # Rollover never refunds the original60 calls; later normalwindowreset only.
    with self.assertRaises(ReplayRefused):a.claim('n'*24,'b'*64,'c'*64,126)
    a=ArchivedProxyReceiptBudget(c.core());self.assertEqual(a.claim('n'*24,'b'*64,'c'*64,700)['receipt']['fence'],65)
 def test_corrupt_archive_no_new_nonce_before_write(self):
  for family in ('collector','broker'):
   c=Client(family);c.provision();core=c.core();core.rollover(expected_revision=0,checkpoints=c.cp if family=='collector'else None);del c.data[c.an]['batch:1'];a=ArchivedCollectorLedger(c.core())if family=='collector'else ArchivedProxyReceiptBudget(c.core());before=copy.deepcopy(c.data);writes=c.replaces
   with self.assertRaises(ReplayRefused):a.submit('n'*24,126)if family=='collector'else a.claim('n'*24,'b'*64,'c'*64,126)
   self.assertEqual(before,c.data);self.assertEqual(c.replaces,writes)
 def test_lost_claim_commit_no_retry_transport_permission(self):
  c=Client('broker');c.provision(0);c.data[c.sn][c.identity]['last_clock']=100;core=c.core();a=ArchivedProxyReceiptBudget(core);c.fail='commit_after'
  with self.assertRaises(ReplayRefused):a.claim('n'*24,'b'*64,'c'*64,100)
  self.assertEqual(c.commits,1);self.assertTrue(core.uncertain);c.fail=''
  with self.assertRaises(ReplayRefused):a.claim('z'*24,'b'*64,'c'*64,101)
  # Separate readonly current-state status does not retry or settle.
  a=ArchivedProxyReceiptBudget(c.core());self.assertEqual(a.status('n'*24,'b'*64,'c'*64)['receipt']['phase'],'reserved');self.assertEqual(c.data[c.sn][c.identity]['calls'],1)
 def test_collector_compatibility_counts_heartbeat_terminal_exactticket(self):
  c=Client('collector');c.provision(0);a=ArchivedCollectorLedger(c.core());j=a.submit('n'*24,100);j=a.advance(j['key'],1,'running',101,{});j=a.heartbeat(j['key'],1,102);self.assertEqual(j['lease_until'],222);j=a.advance(j['key'],1,'failed_before_write',103,{'fetched':0});self.assertEqual(a.status(j['key'])['counts'],{'fetched':0})
  with self.assertRaises(ReplayRefused):a.advance(j['key'],1,'completed',104,{})
 def test_invalid_counts_nonce_ticket_before_any_mutation(self):
  c=Client('collector');c.provision(0);a=ArchivedCollectorLedger(c.core())
  with self.assertRaises(ReplayRefused):a.submit('short',100)
  j=a.submit('n'*24,100);before=c.replaces
  with self.assertRaises(ReplayRefused):a.advance(j['key'],1,'running',101,{'fetched':True})
  self.assertEqual(before,c.replaces)
 def test_old_exact_types_and_production_unchanged_no_automatic_rollover(self):
  from pathlib import Path
  root=Path(__file__).resolve().parents[1]
  self.assertNotIn('replay199',(root/'production_entry.py').read_text());self.assertNotIn('Archived',(root/'integration/collector197_orchestrator.py').read_text());self.assertNotIn('Archived',(root/'integration/finder198_server.py').read_text())
  self.assertNotIn('.rollover(',(root/'integration/replay199_adapters.py').read_text())
 def test_claim_cas_conflict_abort_no_ticket_then_readonly_absence(self):
  for family in ('broker','collector'):
   c=Client(family);c.provision(0);c.data[c.sn][c.identity].update(last_clock=100)if family=='broker'else None;core=c.core();a=ArchivedProxyReceiptBudget(core)if family=='broker'else ArchivedCollectorLedger(core);before=copy.deepcopy(c.data);c.fail='cas_miss'
   with self.assertRaises(ReplayRefused):a.claim('n'*24,'b'*64,'c'*64,100)if family=='broker'else a.submit('n'*24,100)
   self.assertEqual(c.data,before);self.assertEqual(c.commits,0);self.assertEqual(c.starts,1)
 def test_wrong_ticket_no_settlement_after_claim(self):
  c=Client('broker');c.provision(0);c.data[c.sn][c.identity]['last_clock']=100;a=ArchivedProxyReceiptBudget(c.core());r=a.claim('n'*24,'b'*64,'c'*64,100)['receipt'];bad=copy.deepcopy(r);bad['fence']=2
  with self.assertRaises(ReplayRefused):a.start(bad,101)
  self.assertEqual(c.data[c.sn][c.identity]['receipts'][0]['phase'],'reserved')
 def test_collector_archived_heartbeat_cannot_reactivate(self):
  c=Client('collector');c.provision(0);core=c.core();a=ArchivedCollectorLedger(core);j=a.submit('n'*24,100);a.advance(j['key'],1,'running',100,{});a.advance(j['key'],1,'failed_before_write',100,{});core.rollover(expected_revision=3,checkpoints=c.cp);before=copy.deepcopy(c.data)
  with self.assertRaises(ReplayRefused):a.heartbeat(j['key'],1,101)
  self.assertEqual(before,c.data)
