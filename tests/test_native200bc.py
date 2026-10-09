import unittest,copy
from tests import test_native200ba as setup
from integration.native200_admission_core import AdmissionArchiveCore
from integration.native200_admission_adapters import AdmissionCollectorLedger,AdmissionProxyReceiptBudget
from integration.native200_admission_preflight import VALIDATORS
from integration.native200_admission_store import AdmissionStore
from integration.native200_core import NativeArchiveCore
from unittest.mock import patch
class Tests(unittest.TestCase):
 setup_server=setup.Tests.setup_server
 def core(self,c,f):
  # Fixture emits requested schema only. It does not enforce Mongo validators.
  return AdmissionArchiveCore(c,family=f.family,fingerprint='a'*64 if f.family=='collector'else None,enabled=True)
 def test_three_mutations_never_idle_complete_broker(self):
  with patch('integration.native200_preflight.VALIDATORS',VALIDATORS):
   s,c,f,key=self.setup_server(count=0);s.data[f.sn][f.identity]['last_clock']=100;core=self.core(c,f);a=AdmissionProxyReceiptBudget(core);r=a.claim('n'*24,'b'*64,'c'*64,100)['receipt'];r=a.start(r,101);r=a.finish(r,102,status=200,response_hash='d'*64,response_bytes=20)
   self.assertEqual(r['phase'],'complete');self.assertEqual(s.data['native_guards200'][key]['serial'],3);self.assertEqual(s.data['native_guards200'][key]['phase'],'acknowledged');self.assertEqual(len(s.data['native_operations200']),3);self.assertEqual(len(s.data['native_outcomes200']),5);self.assertFalse(any(d.get('update')=='native_guards200'and d['updates'][0]['u']['phase']=='idle'for d in s.commands))
 def test_collector_full_lifecycle_admission_rollover_and_archived_replay(self):
  with patch('integration.native200_preflight.VALIDATORS',VALIDATORS):
   s,c,f,key=self.setup_server('collector',count=0);core=self.core(c,f);a=AdmissionCollectorLedger(core);j=a.submit('n'*24,100);j=a.advance(j['key'],1,'running',101,{});j=a.heartbeat(j['key'],1,102);j=a.advance(j['key'],1,'failed_before_write',103,{})
   core.rollover(expected_revision=4,checkpoints=AdmissionStore(core.provider,'collector_checkpoints197'));self.assertTrue(a.status(j['key'])['archived']);self.assertEqual(a.submit('n'*24,104)['phase'],'failed_before_write');self.assertEqual(s.data['native_guards200'][key]['serial'],5)
 def test_unknown_admission_commit391_holds_restart_no_execution(self):
  with patch('integration.native200_preflight.VALIDATORS',VALIDATORS):
   s,c,f,key=self.setup_server(count=0);s.data[f.sn][f.identity]['last_clock']=100;core=self.core(c,f);a=AdmissionProxyReceiptBudget(core);r=a.claim('n'*24,'b'*64,'c'*64,100)['receipt'];s.fail=lambda d:'commitTransaction'in d and d.get('txnNumber')==5
   with self.assertRaises(ValueError):a.start(r,101)
   self.assertTrue(s.failed);self.assertEqual(sum('commitTransaction'in d and d.get('txnNumber')==5 for d in s.commands),1);self.assertEqual(s.data[f.sn][f.identity]['receipts'][0]['phase'],'reserved');restart=self.core(c,f);self.assertEqual(restart.reconcile_pending()['state'],'admitted_but_never_executed_owner_review_required')
   with self.assertRaises(ValueError):AdmissionProxyReceiptBudget(restart).start(r,101)
 def test_admission_writeahead391_holds_old_no_idle(self):
  with patch('integration.native200_preflight.VALIDATORS',VALIDATORS):
   s,c,f,key=self.setup_server(count=0);s.data[f.sn][f.identity]['last_clock']=100;core=self.core(c,f);a=AdmissionProxyReceiptBudget(core);r=a.claim('n'*24,'b'*64,'c'*64,100)['receipt'];s.fail=lambda d:d.get('update')=='native_guards200'and d['updates'][0]['u']['phase']=='admission_attempt'
   with self.assertRaises(ValueError):a.start(r,101)
   self.assertEqual(s.data['native_guards200'][key]['phase'],'admission_attempt');self.assertEqual(self.core(c,f).reconcile_pending()['state'],'admission_attempt_held_owner_review_required')
 def test_old_core_refuses_extended_validator_and_new_exactpair(self):
  from integration.native200_adapters import NativeArchivedProxyReceiptBudget
  with patch('integration.native200_preflight.VALIDATORS',VALIDATORS):
   s,c,f,key=self.setup_server();core=self.core(c,f)
   with self.assertRaises(ValueError):NativeArchivedProxyReceiptBudget(core)
 def test_ackadmission_then_crash_before_execution_restart_distinct(self):
  from integration.replay199_schema import digest
  with patch('integration.native200_preflight.VALIDATORS',VALIDATORS):
   s,c,f,key=self.setup_server(count=0);s.data[f.sn][f.identity]['last_clock']=100;core=self.core(c,f);a=AdmissionProxyReceiptBudget(core);r=a.claim('n'*24,'b'*64,'c'*64,100)['receipt'];d=copy.deepcopy(s.data[f.sn][f.identity]);after=copy.deepcopy(d);after['revision']+=1;after['last_clock']=101;after['receipts'][0]['phase']='send_started';plan={'family':'broker','source':f.identity,'expected_revision':d['revision'],'epoch':d['archive_epoch'],'head':d['chain_head'],'after_hash':digest(after)}
   intent=core.journal.reserve(plan);self.assertEqual(intent['serial'],2);restart=self.core(c,f);self.assertEqual(restart.reconcile_pending()['state'],'admitted_but_never_executed_owner_review_required')
   with self.assertRaises(ValueError):AdmissionProxyReceiptBudget(restart).start(r,101)
   self.assertEqual(s.data[f.sn][f.identity],d)
 def test_missing_previous_marker_source_changed_or_capacity_no_latch(self):
  with patch('integration.native200_preflight.VALIDATORS',VALIDATORS):
   for cut in ('marker','source','capacity'):
    s,c,f,key=self.setup_server(count=0);s.data[f.sn][f.identity]['last_clock']=100;core=self.core(c,f);a=AdmissionProxyReceiptBudget(core);r=a.claim('n'*24,'b'*64,'c'*64,100)['receipt']
    if cut=='marker':s.data['native_outcomes200'].clear()
    elif cut=='source':s.data[f.sn][f.identity]['last_clock']=101
    else:s.data['native_guards200'][key]['serial']=4096
    old=copy.deepcopy(s.data['native_guards200'][key])
    with self.assertRaises(ValueError):a.start(r,102)
    self.assertEqual(s.data['native_guards200'][key],old)
 def test_admission_atomic_records_share_session_and_txnumber(self):
  with patch('integration.native200_preflight.VALIDATORS',VALIDATORS):
   s,c,f,key=self.setup_server(count=0);s.data[f.sn][f.identity]['last_clock']=100;core=self.core(c,f);a=AdmissionProxyReceiptBudget(core);r=a.claim('n'*24,'b'*64,'c'*64,100)['receipt'];a.start(r,101)
   closure=next(d for d in s.commands if d.get('insert')=='native_outcomes200'and d['documents'][0].get('kind')=='admission');intent=next(d for d in s.commands if d.get('insert')=='native_operations200'and d['documents'][0]['serial']==2);guard=next(d for d in s.commands if d.get('update')=='native_guards200'and d['updates'][0]['u']['serial']==2 and d['updates'][0]['u']['phase']=='reserved')
   for d in (intent,guard):self.assertEqual(d['lsid'],closure['lsid']);self.assertEqual(d['txnNumber'],closure['txnNumber']);self.assertFalse(d['autocommit'])
   latch=next(d for d in s.commands if d.get('update')=='native_guards200'and d['updates'][0]['u']['phase']=='admission_attempt');self.assertNotIn('autocommit',latch);self.assertEqual(latch['writeConcern'],{'w':'majority','j':True,'wtimeout':5000});self.assertLess(s.commands.index(latch),s.commands.index(guard))
 def test_admission_eachbody391_single_frame_latch_held(self):
  with patch('integration.native200_preflight.VALIDATORS',VALIDATORS):
   for cut in ('guard','intent','closure'):
    s,c,f,key=self.setup_server(count=0);s.data[f.sn][f.identity]['last_clock']=100;core=self.core(c,f);a=AdmissionProxyReceiptBudget(core);r=a.claim('n'*24,'b'*64,'c'*64,100)['receipt']
    def target(d):
     if cut=='guard':return d.get('update')=='native_guards200'and d['updates'][0]['u']['phase']=='reserved'and d['updates'][0]['u']['serial']==2
     if cut=='intent':return d.get('insert')=='native_operations200'and d['documents'][0]['serial']==2
     return d.get('insert')=='native_outcomes200'and d['documents'][0].get('kind')=='admission'
    s.fail=target
    with self.assertRaises(ValueError):a.start(r,101)
    self.assertEqual(sum(target(d)for d in s.commands),1);self.assertEqual(s.data['native_guards200'][key]['phase'],'admission_attempt');self.assertEqual(len(s.data['native_operations200']),1);self.assertEqual(len(s.data['native_outcomes200']),1)
 def test_extended_validator_incompatible_old_preflight(self):
  from integration.native200_preflight import inspect_existing
  from integration.native200_store import NativeStore
  with patch('integration.native200_preflight.VALIDATORS',VALIDATORS):s,c,f,key=self.setup_server()
  from integration.native200_transactions import NativeNoRetryProvider
  store=NativeStore(NativeNoRetryProvider(c,enabled=True),'native_guards200')
  reply={'ok':1,'cursor':{'id':0,'ns':'geo_intel.$cmd.listCollections','firstBatch':[{'name':store.name,'type':'collection','options':{'validator':VALIDATORS[store.name]}}]}}
  with patch.object(store,'_command',return_value=reply):
   with self.assertRaises(ValueError):inspect_existing(store)
