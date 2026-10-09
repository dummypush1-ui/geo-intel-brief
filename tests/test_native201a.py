import unittest,copy
from unittest.mock import patch
from tests import test_native200ba as setup
from integration.native200_admission_core import AdmissionArchiveCore
from integration.native200_admission_preflight import VALIDATORS
from integration.native200_admission_store import AdmissionStore
from integration.native201_coverage import NativeCoverageCheckpoints,checkpoint_row
from integration.native201_ledger import NativeCheckpointCollectorLedger
from integration.collector197_coverage import catalog_fingerprint
from collector113_prep.feed_composition import original_catalog
class Tests(unittest.TestCase):
 setup_server=setup.Tests.setup_server
 def inputs(self):return {'candidates':[],'active_categories':['TRADE'],'threshold':.85}
 def coverage(self):return {'catalog':catalog_fingerprint(),'source_states':[{'index':i,'state':'unstarted'}for i in range(len(original_catalog()))],'all_sources_healthy':False}
 def setup_native(self):
  s,c,f,key=self.setup_server('collector',count=0);core=AdmissionArchiveCore(c,family='collector',fingerprint='a'*64,enabled=True);ledger=NativeCheckpointCollectorLedger(core);checkpoints=NativeCoverageCheckpoints(AdmissionStore(core.provider,'collector_checkpoints197'));j=ledger.submit('n'*24,100);j=ledger.advance(j['key'],j['fence'],'running',101,{});return s,c,f,key,core,ledger,checkpoints,j
 def test_atomic_checkpoint_source_marker_shared_txn(self):
  with patch('integration.native200_preflight.VALIDATORS',VALIDATORS):
   s,c,f,key,core,ledger,cp,j=self.setup_native();out=ledger.checkpoint_and_advance(cp,j['key'],j['fence'],102,self.inputs(),self.coverage());self.assertEqual(out['phase'],'fetch_complete');self.assertEqual(cp.get(j['key'],j['fence'])['coverage'],self.coverage())
   insert=next(d for d in s.commands if d.get('insert')=='collector_checkpoints197');update=next(d for d in s.commands if d.get('update')==f.sn and d['updates'][0]['u']['active']['phase']=='fetch_complete');marker=next(d for d in s.commands if d.get('insert')=='native_outcomes200'and d['documents'][0].get('serial')==3)
   for d in(update,marker):self.assertEqual(d['lsid'],insert['lsid']);self.assertEqual(d['txnNumber'],insert['txnNumber']);self.assertFalse(d['autocommit'])
   self.assertFalse(hasattr(cp,'put'));self.assertEqual(s.data['native_guards200'][key]['phase'],'acknowledged')
 def test_each_391_failure_atomic_or_unknown_no_retry(self):
  with patch('integration.native200_preflight.VALIDATORS',VALIDATORS):
   for cut in('checkpoint','source','marker','commit'):
    s,c,f,key,core,ledger,cp,j=self.setup_native()
    def target(d):
     if cut=='checkpoint':return d.get('insert')=='collector_checkpoints197'
     if cut=='source':return d.get('update')==f.sn and d['updates'][0]['u']['active']['phase']=='fetch_complete'
     if cut=='marker':return d.get('insert')=='native_outcomes200'and d['documents'][0].get('serial')==3
     return 'commitTransaction'in d and d.get('txnNumber')==10
    s.fail=target
    with self.assertRaises(ValueError):ledger.checkpoint_and_advance(cp,j['key'],j['fence'],102,self.inputs(),self.coverage())
    self.assertTrue(s.failed);self.assertEqual(sum(target(d)for d in s.commands),1)
    d=s.data[f.sn][f.identity];self.assertEqual(bool(s.data['collector_checkpoints197']),d['active']['phase']=='fetch_complete');self.assertIsNotNone(s.data['native_guards200'][key]['operation'])
 def test_wrong_ticket_bad_coverage_or_conflicting_immutable_before_latch(self):
  with patch('integration.native200_preflight.VALIDATORS',VALIDATORS):
   for cut in('ticket','coverage','immutable'):
    s,c,f,key,core,ledger,cp,j=self.setup_native();coverage=self.coverage();fence=j['fence']
    if cut=='ticket':fence+=1
    elif cut=='coverage':coverage['all_sources_healthy']=True
    else:s.data['collector_checkpoints197'][j['key']]={'_id':j['key'],'bad':True}
    guard=copy.deepcopy(s.data['native_guards200'][key])
    with self.assertRaises(ValueError):ledger.checkpoint_and_advance(cp,j['key'],fence,102,self.inputs(),coverage)
    self.assertEqual(s.data['native_guards200'][key],guard)
 def test_existing_identical_checkpoint_no_secondinsert(self):
  with patch('integration.native200_preflight.VALIDATORS',VALIDATORS):
   s,c,f,key,core,ledger,cp,j=self.setup_native();s.data['collector_checkpoints197'][j['key']]=checkpoint_row(j['key'],j['fence'],self.inputs(),self.coverage());ledger.checkpoint_and_advance(cp,j['key'],j['fence'],102,self.inputs(),self.coverage());self.assertFalse(any(d.get('insert')=='collector_checkpoints197'for d in s.commands));self.assertEqual(s.data[f.sn][f.identity]['active']['phase'],'fetch_complete')
 def test_stale_phase_and_expiry_no_latch(self):
  with patch('integration.native200_preflight.VALIDATORS',VALIDATORS):
   for now in(100,221):
    s,c,f,key,core,ledger,cp,j=self.setup_native();old=copy.deepcopy(s.data['native_guards200'][key])
    with self.assertRaises(ValueError):ledger.checkpoint_and_advance(cp,j['key'],j['fence'],now,self.inputs(),self.coverage())
    self.assertEqual(s.data['native_guards200'][key],old);self.assertEqual(s.data['collector_checkpoints197'],{})
 def test_old_checkpoint_or_admissionledger_exact_types_not_silent(self):
  from integration.collector197_coverage import CoverageCheckpoints
  from integration.native200_admission_adapters import AdmissionCollectorLedger
  with patch('integration.native200_preflight.VALIDATORS',VALIDATORS):
   s,c,f,key,core,ledger,cp,j=self.setup_native()
   with self.assertRaises(ValueError):ledger.checkpoint_and_advance(None,j['key'],j['fence'],102,self.inputs(),self.coverage())
   self.assertFalse(hasattr(AdmissionCollectorLedger(core),'checkpoint_and_advance'));self.assertFalse(hasattr(cp,'put'))
 def test_checkpoint_get_corruption_held(self):
  with patch('integration.native200_preflight.VALIDATORS',VALIDATORS):
   s,c,f,key,core,ledger,cp,j=self.setup_native();ledger.checkpoint_and_advance(cp,j['key'],j['fence'],102,self.inputs(),self.coverage());s.data['collector_checkpoints197'][j['key']]['coverage_hash']='f'*64
   with self.assertRaises(ValueError):cp.get(j['key'],j['fence'])
