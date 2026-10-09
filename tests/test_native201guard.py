import unittest,copy
from unittest.mock import patch
from integration.native200_admission_preflight import VALIDATORS,inspect_admission_existing
from integration.native201_schemas import FIXED_VALIDATORS
from integration.native200_admission_store import AdmissionStore
from integration.native200_transactions import NativeNoRetryProvider
from tests import test_native200ba as setup
class Tests(unittest.TestCase):
 setup_server=setup.Tests.setup_server
 def test_all8_bare_recreation_refuses_before_nextwrite(self):
  with patch('integration.native200_preflight.VALIDATORS',VALIDATORS):s,c,f,key=self.setup_server()
  p=NativeNoRetryProvider(c,enabled=True)
  for name in sorted(VALIDATORS):
   store=AdmissionStore(p,name);reply={'ok':1,'cursor':{'id':0,'ns':'geo_intel.$cmd.listCollections','firstBatch':[{'name':name,'type':'collection','options':{}}]}}
   with patch.object(store,'_command',return_value=reply)as command:
    with self.assertRaises(ValueError):store.insert_one({'_id':'a'*64})
    self.assertEqual(command.call_count,1);self.assertEqual(next(iter(command.call_args.args[0])),'listCollections')
 def test_all8_exact_schema_and_existing_other_gates(self):
  with patch('integration.native200_preflight.VALIDATORS',VALIDATORS):
   s,c,f,key=self.setup_server();p=NativeNoRetryProvider(c,enabled=True)
   for name in sorted(VALIDATORS):self.assertTrue(inspect_admission_existing(AdmissionStore(p,name)))
  self.assertEqual(len(VALIDATORS),8);self.assertEqual(len(FIXED_VALIDATORS),5)
 def test_source_and_archive_envelopes_strict_closed(self):
  for schema in FIXED_VALIDATORS.values():
   root=schema['$jsonSchema'];variants=root.get('oneOf',[root])
   for item in variants:
    self.assertFalse(item['additionalProperties']);self.assertEqual(set(item['required']),set(item['properties']))
 def test_checkpoint_v1_and_v2_legitimate_retained_variants(self):
  root=FIXED_VALIDATORS['collector_checkpoints197']['$jsonSchema'];self.assertEqual([s['properties']['version']['enum']for s in root['oneOf']],[[1],[2]])
  for schema in root['oneOf']:self.assertEqual(schema['properties']['inputs']['maxItems'],1000)
 def test_changed_validationaction_schema_ttl_refuses(self):
  with patch('integration.native200_preflight.VALIDATORS',VALIDATORS):s,c,f,key=self.setup_server()
  p=NativeNoRetryProvider(c,enabled=True);name='collector_checkpoints197';store=AdmissionStore(p,name)
  for options in({'validator':{}},{'validator':VALIDATORS[name],'validationAction':'warn'},{'validator':VALIDATORS[name],'validationLevel':'moderate'}):
   reply={'ok':1,'cursor':{'id':0,'ns':'geo_intel.$cmd.listCollections','firstBatch':[{'name':name,'type':'collection','options':options}]}}
   with patch.object(store,'_command',return_value=reply):
    with self.assertRaises(ValueError):inspect_admission_existing(store)
