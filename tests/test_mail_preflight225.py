import ast,copy,importlib,subprocess,sys,unittest
from pathlib import Path
from unittest.mock import patch
from tests.test_native_mail_projection224 import fixture
from tests.test_mail_exclusion223 import args as candidate,rebuild
from tests.test_digest_email218 import row
s=importlib.import_module('integration.mail_preflight225')
n=importlib.import_module('integration.native_mail_projection224');v=importlib.import_module('integration.mail_exclusion223')
def inputs(state='acknowledged'):
 from bson import ObjectId
 d=candidate();d.pop('exclusion_projection');d.update(fixture(state));d['displayed_receipts']={**d['displayed_receipts'],'email':(ObjectId(f'{1:024x}'),)}if state=='acknowledged'else d['displayed_receipts'];rebuild(d);return d
class Tests(unittest.TestCase):
 def refuse(self,d):
  with self.assertRaises(ValueError)as e:s.check_supplied(enabled=True,**d)
  self.assertEqual(str(e.exception),'Composed preflight held');self.assertIsNone(e.exception.__cause__);self.assertIsNone(e.exception.__context__);self.assertTrue(e.exception.__suppress_context__);self.assertNotIn('CANARY',repr(e.exception))
 def test_real_match_closed_constants_all_inputs_unchanged(self):
  d=inputs();before=copy.deepcopy(d);p=s.check_supplied(enabled=True,**d);self.assertEqual(d,before);self.assertEqual(set(p),{'state','preflight_match','note',*s._FLAGS});self.assertTrue(p['preflight_match']);self.assertEqual(p['note'],s._NOTE)
  for k in s._FLAGS:self.assertIs(p[k],False)
  for secret in (d['recipient_set_fingerprint'],d['nonce'],str(row(1)['_id']),d['control_row']['_id']):self.assertNotIn(secret,repr(p))
 def test_full_ack_set_subset_superset_and_other_channels(self):
  d=inputs();d['displayed_receipts']={**d['displayed_receipts'],'email':()};rebuild(d);self.refuse(d)
  d=inputs();d['displayed_receipts']={**d['displayed_receipts'],'email':(row(1)['_id'],row(999)['_id'])};self.refuse(d)
  d=inputs();d['displayed_receipts']={**d['displayed_receipts'],'telegram':(row(2)['_id'],),'whatsapp':(row(2)['_id'],)};self.assertTrue(s.check_supplied(enabled=True,**d)['preflight_match'])
  d=inputs();d['receipt_rows']=[];self.assertTrue(s.check_supplied(enabled=True,**d)['preflight_match'])
 def test_unresolved_wrong_inputs_changed_originals(self):
  for state in ('prepared','started'):self.refuse(inputs(state))
  for k,value in [('recipient_set_fingerprint','f'*64),('history_manifest','f'*64),('nonce','z'*20),('blob',b'CANARY'),('limit',0)]:self.refuse({**inputs(),k:value})
  d=inputs();d['rows'][1]['title']='CANARY changed';self.refuse(d);rebuild(d);self.assertTrue(s.check_supplied(enabled=True,**d)['preflight_match'])
  d=inputs();d['control_row']['channel']='f'*64;self.refuse(d)
 def test_extras_no_override_invented_empty_graph_replay(self):
  for extra in ('exclusion_projection','stage_result','sender_scope','recipients'):self.refuse({**inputs(),extra:'CANARY'})
  d=inputs();d['receipt_rows']=[];d['article_rows']=[];d['displayed_receipts']={**d['displayed_receipts'],'email':()};rebuild(d)
  self.assertTrue(s.check_supplied(enabled=True,**d)['preflight_match']);self.assertTrue(s.check_supplied(enabled=True,**d)['preflight_match']);self.assertIn('Invented',s._NOTE)
 def test_identity_order_generated_projection_only_errors_mutation(self):
  d=inputs();calls=[];projection={'CANARY':'stage private'}
  def first(**kw):
   calls.append('224');self.assertEqual(set(kw),{'enabled',*s._NATIVE})
   for k in s._NATIVE:self.assertIs(kw[k],d[k])
   return {'projection':projection}
  def second(**kw):
   calls.append('223');self.assertIs(kw['exclusion_projection'],projection)
   for k in s._FIELDS-set(('control_row','receipt_rows','article_rows','history_manifest')):self.assertIs(kw[k],d[k])
   return {'CANARY':'ignored'}
  with patch.object(n,'project_supplied',first),patch.object(v,'check_supplied',second):p=s.check_supplied(enabled=True,**d)
  self.assertEqual(calls,['224','223']);self.assertNotIn('CANARY',repr(p))
  with patch.object(n,'project_supplied',side_effect=ValueError('CANARY224')),patch.object(v,'check_supplied')as mock:self.refuse(d);mock.assert_not_called()
  with patch.object(n,'project_supplied',first),patch.object(v,'check_supplied',side_effect=ValueError('CANARY223')):self.refuse(d)
  def mutate(**kw):kw['rows'][0]['title']='CANARY';return {}
  with patch.object(n,'project_supplied',first),patch.object(v,'check_supplied',mutate):self.refuse(d)
 def test_caps_before_stage_missing_subclasses_and_allfield_canaries(self):
  class L(list):pass
  class T(tuple):pass
  for key,cap in [('rows',1000),('receipt_rows',128),('article_rows',10000)]:
   for value in (L([]),[{}]*(cap+1),()):
    with patch.object(n,'project_supplied')as mock:self.refuse({**inputs(),key:value});mock.assert_not_called()
  for value in ([],T(()),(row(1)['_id'],)*10001):
   d=inputs();d['displayed_receipts']['email']=value
   with patch.object(n,'project_supplied')as mock:self.refuse(d);mock.assert_not_called()
  d=inputs()
  for key in d:
   with patch.object(n,'project_supplied')as mock:self.refuse({k:v for k,v in d.items()if k!=key});mock.assert_not_called()
  for location in ('control_row','receipt_rows','article_rows','rows'):
   base=inputs();target=base[location]if location=='control_row'else base[location][0]
   for key in target:
    d=copy.deepcopy(base);r=d[location]if location=='control_row'else d[location][1 if location=='rows'else 0];r[key]='CANARY';self.refuse(d)
 def test_off_sysmodules_ast(self):
  class Bad:
   def __getattribute__(self,k):raise AssertionError('CANARY')
  self.assertEqual(s.check_supplied(blob=Bad(),rows=Bad())['state'],'disabled')
  for enabled in (1,None,'true'):
   with self.assertRaises(ValueError):s.check_supplied(enabled=enabled)
  tree=ast.parse(Path(s.__file__).read_text());mods=set()
  for node in ast.walk(tree):
   if isinstance(node,ast.Import):mods.update(a.name for a in node.names)
   elif isinstance(node,ast.ImportFrom):mods.add(node.module)
  self.assertEqual(mods,{'copy','integration.native_mail_projection224','integration.mail_exclusion223'})
  code="import sys;from integration.mail_preflight225 import check_supplied;check_supplied();assert not any(x in sys.modules for x in ['bson','pymongo','integration.native_mail_projection224','integration.mail_exclusion223','integration.mail_rederive221','integration.mail_candidate219','integration.digest_email218','integration.mail_ledger212'])"
  r=subprocess.run([sys.executable,'-c',code],cwd=Path(s.__file__).parents[1],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
