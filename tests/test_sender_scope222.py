import ast,copy,hashlib,importlib,json,subprocess,sys,unittest
from pathlib import Path
from integration.sender_scope222 import binding_data
V=[('sender@example.invalid',['a@example.invalid'],'f15595ecf92d0b02390cab82b5b3d1d791ec3b1ed1f6005270ae743094fc6863','b6a16ae5c60e6417170f8d35ac1a4ad3e7e353772341e043e306b275678cebf8'),('sender@example.invalid',['a@example.invalid','b@example.invalid'],'f15595ecf92d0b02390cab82b5b3d1d791ec3b1ed1f6005270ae743094fc6863','a7968e6ca24b85484dca24a231a3bf3da3661484d8817bed5f505af5b09a1c6f'),('sender@example.invalid',[f'a{i}@example.invalid'for i in range(20)],'f15595ecf92d0b02390cab82b5b3d1d791ec3b1ed1f6005270ae743094fc6863','a4935ea92abb2ac797b73c1b21ad6d5d276f1d2970a0324e408ec2bfdbe5499d'),('changed@example.invalid',['a@example.invalid'],'1379762a35f7688f1ee384eefa785b9a298a152ff7a5582fe73e41fa4a34169d','475418e44ca65f4c5c3e5f6ed5641475ea82eb8442ddc6d34990e1ca4ea2e022'),('sender@example.invalid',['changed@example.invalid'],'f15595ecf92d0b02390cab82b5b3d1d791ec3b1ed1f6005270ae743094fc6863','2ff860a1441cb0809f0b1ee1df2fb92e41c6badab45f956b3fb0a48927825586')]
class Tests(unittest.TestCase):
 def test_vectors_closed_case_sort_copy_real220(self):
  real=importlib.import_module('integration.recipient_scope220').fingerprint
  for sender,rows,senderfp,scopefp in V:
   before=copy.deepcopy(rows);p=binding_data(enabled=True,sender=sender,recipients=rows)
   self.assertEqual(p['sender_fingerprint'],senderfp);self.assertEqual(p['sender_recipient_scope_fingerprint'],scopefp);self.assertEqual(p['recipient_set_fingerprint'],real(enabled=True,recipients=rows)['fingerprint']);self.assertEqual(rows,before)
   self.assertEqual(binding_data(enabled=True,sender=sender.upper(),recipients=[v.upper()for v in reversed(rows)]),p)
   self.assertEqual(set(p),{'sender_fingerprint','recipient_set_fingerprint','sender_recipient_scope_fingerprint','policy','note','send_allowed','ready','owner_approval','ledger_wired','bridge_wired'})
   for k in ('send_allowed','ready','owner_approval','ledger_wired','bridge_wired'):self.assertIs(p[k],False)
   self.assertNotIn('@',repr(p));self.assertIn('guessed',p['note'])
 def test_sender_changes_still_invisible212(self):
  from integration.mail_ledger212 import logical_channel
  a=binding_data(enabled=True,sender=V[0][0],recipients=V[0][1]);b=binding_data(enabled=True,sender=V[3][0],recipients=V[3][1])
  self.assertNotEqual(a['sender_fingerprint'],b['sender_fingerprint']);self.assertNotEqual(a['sender_recipient_scope_fingerprint'],b['sender_recipient_scope_fingerprint']);self.assertEqual(a['recipient_set_fingerprint'],b['recipient_set_fingerprint']);self.assertEqual(logical_channel('email',a['recipient_set_fingerprint']),logical_channel('email',b['recipient_set_fingerprint']))
 def test_selfsend_is_separate_and_legacy_acceptance_not_validity(self):
  p=binding_data(enabled=True,sender='a@example.invalid',recipients=['a@example.invalid','b@example.invalid']);self.assertEqual(p,binding_data(enabled=True,sender='a@example.invalid',recipients=['b@example.invalid','a@example.invalid']))
  self.assertTrue(binding_data(enabled=True,sender='a@b..com',recipients=['a@example.invalid']))
 def test_sender_grammar_fixed_canary_error_and_220_failures(self):
  class S(str):pass
  bad=['a@example.invalid\n',' a@example.invalid','a\t@example.invalid','a@example.invalid,b@example.invalid','x'*243+'@example.com','é@example.invalid','A <a@b.com>','a(comment)@b.com','"a"@b.com','a@[127.0.0.1]','a@localhost',[],b'a@example.invalid',S('a@example.invalid'),None]
  for sender in bad:
   with self.assertRaises(ValueError)as e:binding_data(enabled=True,sender=sender,recipients=['CANARY@example.invalid'])
   self.assertEqual(str(e.exception),'Sender scope held');self.assertIsNone(e.exception.__cause__);self.assertIsNone(e.exception.__context__);self.assertNotIn('CANARY',repr(e.exception))
  with self.assertRaises(ValueError):binding_data(enabled=True,recipients=['a@example.invalid'])
  for rows in (['CANARY@example.invalid\n'],['CANARY@example.invalid','canary@example.invalid'],[],(),['a@example.invalid']*21):
   with self.assertRaises(ValueError)as e:binding_data(enabled=True,sender='CANARY@example.invalid',recipients=rows)
   self.assertEqual(str(e.exception),'Sender scope held');self.assertIsNone(e.exception.__cause__);self.assertIsNone(e.exception.__context__)
 def test_bridge_own_digest_vm_order_and_trim(self):
  root=Path(__file__).parents[1]
  script=r'''const fs=require('fs'),vm=require('vm'),crypto=require('crypto');
const sender=' Sender@Example.Invalid ',to='a@example.invalid, B@example.invalid';let captured;
const props={getProperty:k=>({MAIL_V1_ENABLED:'true',MAIL_V1_BASE:'https://example.invalid',MAIL_V1_HEADER_SECRET:'x'.repeat(48),MAIL_V1_EMAIL_TO:to,MAIL_V1_CHANNEL:'a'.repeat(64)})[k]};
const context={PropertiesService:{getScriptProperties:()=>props},Session:{getEffectiveUser:()=>({getEmail:()=>sender})},Utilities:{DigestAlgorithm:{SHA_256:'sha256'},Charset:{UTF_8:'utf8'},computeDigest:(a,s,c)=>{captured=s;throw Error('STOP_AT_DIGEST_TEST_ONLY')}}};
vm.createContext(context);vm.runInContext(fs.readFileSync('feature_mail_mount/bridge.gs','utf8'),context);try{context.runMailV1('digest')}catch(e){if(e.message!=='STOP_AT_DIGEST_TEST_ONLY')throw e;}console.log(JSON.stringify({wire:captured,hash:crypto.createHash('sha256').update(captured).digest('hex')}));'''
  r=subprocess.run(['node','-e',script],cwd=root,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);v=json.loads(r.stdout)
  wire=json.dumps({'sender':'sender@example.invalid','recipients':['a@example.invalid','b@example.invalid']},separators=(',',':'))
  self.assertEqual(v['wire'],wire);self.assertEqual(v['hash'],hashlib.sha256(wire.encode()).hexdigest())
  p=binding_data(enabled=True,sender='sender@example.invalid',recipients=['a@example.invalid','b@example.invalid'])
  for k in ('sender_fingerprint','recipient_set_fingerprint','sender_recipient_scope_fingerprint'):self.assertNotEqual(p[k],v['hash'])
  for sender,rows in [(' sender@example.invalid',['a@example.invalid']),('sender@example.invalid',['a@example.invalid',' B@example.invalid'])]:
   with self.assertRaises(ValueError):binding_data(enabled=True,sender=sender,recipients=rows)
 def test_off_sysmodules_and_ast(self):
  class Hostile:
   def __getattribute__(self,k):raise AssertionError('CANARY')
  self.assertEqual(binding_data(sender=Hostile(),recipients=Hostile())['state'],'disabled')
  for enabled in (None,1,'true'):
   with self.assertRaises(ValueError):binding_data(enabled=enabled,sender=Hostile())
  path=Path(__file__).parents[1]/'integration/sender_scope222.py';tree=ast.parse(path.read_text());mods=set();top=set()
  for n in ast.walk(tree):
   if isinstance(n,ast.Import):mods.update(a.name for a in n.names)
   if isinstance(n,ast.ImportFrom):mods.add(n.module)
  for n in tree.body:
   if isinstance(n,ast.Import):top.update(a.name for a in n.names)
  self.assertEqual(top,{'hashlib','json','re'});self.assertEqual(mods,{'hashlib','json','re','integration.recipient_scope220'})
  code="import sys;from integration.sender_scope222 import binding_data;binding_data();assert 'integration.recipient_scope220' not in sys.modules"
  r=subprocess.run([sys.executable,'-c',code],cwd=path.parents[1],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
