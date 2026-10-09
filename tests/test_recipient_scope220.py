import ast,copy,hashlib,json,subprocess,sys,unittest,importlib
from pathlib import Path
from integration.recipient_scope220 import fingerprint,POLICY
VECTORS=[(['a@example.invalid'],'d13ea0098a71bdb978e3073921e18638a5fa54842aebc606f7689a251d2fc21b'),(['a@example.invalid','b@example.invalid'],'146b4f008468be693d27ed3a7ae387f8a2ffb3b5960460103232aa3a590fd102'),([f'a{i}@example.invalid'for i in range(20)],'9a9bded739dc8f76645eecc4f013c4499b3377b733c1d6c35ef833873a101391')]
class Tests(unittest.TestCase):
 def test_vectors_permutation_case_copies(self):
  for values,expected in VECTORS:
   before=copy.deepcopy(values);p=fingerprint(enabled=True,recipients=values)
   self.assertEqual(p['fingerprint'],expected);self.assertEqual(fingerprint(enabled=True,recipients=list(reversed(values))),p);self.assertEqual(fingerprint(enabled=True,recipients=[v.upper()for v in values]),p);self.assertEqual(values,before)
   self.assertEqual(set(p),{'fingerprint','policy','count','send_allowed','ready','owner_approval'});self.assertEqual(p['policy'],POLICY);self.assertEqual(p['count'],len(values))
   for k in ('send_allowed','ready','owner_approval'):self.assertIs(p[k],False)
   self.assertNotIn('@',repr(p));self.assertEqual(json.loads(json.dumps(p)),p)
  self.assertNotEqual(fingerprint(enabled=True,recipients=['a@example.invalid']),fingerprint(enabled=True,recipients=['b@example.invalid']))
 def test_grammar_matches213_and_canary_errors(self):
  _address=importlib.import_module("integration.smtp_caller213")._address
  bad=['a@example.invalid\n',' a@example.invalid','a\t@example.invalid','a@example.invalid,b@example.invalid','x'*243+'@example.com','é@example.invalid','A <a@b.com>','a(comment)@b.com','"a"@b.com']
  for value in bad:
   with self.assertRaises(ValueError):_address(value)
   with self.assertRaises(ValueError)as e:fingerprint(enabled=True,recipients=[value])
   self.assertEqual(str(e.exception),'Recipient fingerprint refused');self.assertNotIn(value,repr(e.exception));self.assertIsNone(e.exception.__cause__);self.assertIsNone(e.exception.__context__)
  for index in range(20):
   rows=[f'a{i}@example.invalid'for i in range(20)];rows[index]='CANARY_ADDRESS@bad.invalid\n'
   with self.assertRaises(ValueError)as e:fingerprint(enabled=True,recipients=rows)
   self.assertNotIn('CANARY',repr(e.exception))
 def test_types_duplicates_no_silent_dedup(self):
  class S(str):pass
  class L(list):pass
  for value in [(),set(),(x for x in []),'a@example.invalid',L(['a@example.invalid']),[],['a@example.invalid']*2,['a@example.invalid','A@EXAMPLE.INVALID'],[S('a@example.invalid')],[True],[f'a{i}@example.invalid'for i in range(21)]]:
   with self.assertRaises(ValueError):fingerprint(enabled=True,recipients=value)
 def test_real219212_and_not_bridge_identity(self):
  from integration.mail_candidate219 import freeze_candidate,verify_snapshot
  from integration.mail_ledger212 import logical_channel
  from tests.test_digest_email218 import render,row
  fp=fingerprint(enabled=True,recipients=['a@example.invalid'])['fingerprint'];b,p=freeze_candidate(enabled=True,candidate_result=render([row()]),recipient_set_fingerprint=fp,nonce='n'*20)
  self.assertTrue(verify_snapshot(b,p));self.assertEqual(p['proposed_channel'],logical_channel('email',fp));self.assertEqual(logical_channel('email',fp),logical_channel('email',fp))
  bridge=hashlib.sha256(json.dumps({'sender':'sender@example.invalid','recipients':['a@example.invalid']},separators=(',',':')).encode()).hexdigest();self.assertNotEqual(fp,bridge)
  # Sender is absent from220inputs: changing sender cannot change its fingerprint.
  self.assertEqual(fingerprint(enabled=True,recipients=['a@example.invalid'])['fingerprint'],fp)
 def test_off_hostile_and_static_ast(self):
  class Bad:
   def __getattribute__(self,k):raise AssertionError()
  self.assertEqual(fingerprint(recipients=Bad())['state'],'disabled')
  for v in (1,None,'true'):
   with self.assertRaises(ValueError):fingerprint(enabled=v,recipients=Bad())
  path=Path(__file__).parents[1]/'integration/recipient_scope220.py';tree=ast.parse(path.read_text());modules=[]
  for n in ast.walk(tree):
   if isinstance(n,ast.Import):modules.extend(a.name for a in n.names)
   if isinstance(n,ast.ImportFrom):modules.append(n.module)
  self.assertEqual(set(modules),{'hashlib','json','re'})
  code="import sys;from integration.recipient_scope220 import fingerprint;fingerprint();assert not any(x in sys.modules for x in ['integration.mail_ledger212','integration.smtp_caller213','integration.mail_candidate219','pymongo'])"
  r=subprocess.run([sys.executable,'-c',code],cwd=path.parents[1],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
