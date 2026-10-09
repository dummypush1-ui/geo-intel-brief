import ast,copy,json,subprocess,sys,unittest
from pathlib import Path
from integration import mail_candidate219 as s
from tests.test_digest_email218 import render,row
PINS={'proposed_channel':'0d2e8130c884b0468d594ffb9446105dfed955c1f36f9a0ff982e470209d80bc','proposed_control_key':'fe75832b52ec42303a6dc66127957d52e7b4e9a2387326fc5c6c61d20dc55817','proposed_binding_hash':'8bdfd12e2e1100cef76772f31e178d1e0031a5cafacf58fd85403931f586cfe9','proposed_nonce_key':'7e9341e36879c0ea370d7cb9ffcdf4cbdb3e581422398c38d4d0881772382137','proposed_content_digest':'4d16137017b1d9b121404b4476bdc48ba8fe417d7cc94561e8a0bab6a373f604'}
def freeze(c=None,fp='a'*64,nonce='n'*20):return s.freeze_candidate(enabled=True,candidate_result=c or render([row(1),row(2)]),recipient_set_fingerprint=fp,nonce=nonce)
class Tests(unittest.TestCase):
 def test_pins_and_real212_vectors(self):
  from integration.mail_ledger212 import MailLedger,logical_channel,_hash
  _,p=freeze()
  for k,v in PINS.items():self.assertEqual(p[k],v)
  for fp in ('a'*64,'b'*64,'0'*64):
   for nonce in ('n'*20,'A_-'*26+'ZZ','z'*80):
    for ids in ([f'{1:024x}'],[f'{1:024x}',f'{2:024x}'],[f'{i:024x}'for i in range(1,121)]):
     c={'sorted_union_ids':ids};content='c'*64;actual=s._proposals(c,fp,nonce,content)
     channel=logical_channel('email',fp);control=_hash({'channel':channel,'purpose':'digest'})
     ledger=object.__new__(MailLedger);ledger.channel=channel;ledger.purpose='digest'
     self.assertEqual(actual['proposed_channel'],channel);self.assertEqual(actual['proposed_control_key'],control)
     self.assertEqual(actual['proposed_binding_hash'],ledger._binding(ids,content));self.assertEqual(actual['proposed_nonce_key'],_hash({'control':control,'nonce':nonce}))
  # Compatibility hashes keep exact closed key sets, not added219domains.
 def test_freeze_verify_independence(self):
  c=render([row(1),row(2)]);before=copy.deepcopy(c);b,p=freeze(c);self.assertIs(type(b),bytes);self.assertEqual(c,before);self.assertEqual(s.verify_snapshot(b,p),c['candidate'])
  restored=s.verify_snapshot(b,p);restored['sections'][0]['ids'].clear();self.assertEqual(s.verify_snapshot(b,p),c['candidate']);p['proposed_ids'].clear();self.assertTrue(freeze(c)[1]['proposed_ids'])
  self.assertEqual(freeze(c),freeze(copy.deepcopy(c)))
 def test_new_domains_differ_and_swaps_change(self):
  b,p=freeze();values=[p[k]for k in PINS]
  self.assertNotIn(p['snapshot_identity'],values);self.assertNotIn(p['byte_integrity'],values);self.assertNotEqual(p['snapshot_identity'],p['byte_integrity'])
  q=s._proposals({'sorted_union_ids':p['proposed_ids']},'b'*64,'a'*64,p['proposed_content_digest']);self.assertNotEqual(q['proposed_nonce_key'],p['proposed_nonce_key'])
  swapped=copy.deepcopy(p);swapped['nonce'],swapped['recipient_set_fingerprint']='a'*64,'b'*64
  self.assertNotEqual(s._hash({'domain':'mail_candidate219.snapshot_identity.v1','binding':swapped}),p['snapshot_identity'])
 def test_every_binding_leaf_tamper(self):
  b,p=freeze()
  for k in p:
   bad=copy.deepcopy(p)
   if type(bad[k])is str:bad[k]+='X'
   elif type(bad[k])is bool:bad[k]=not bad[k]
   else:bad[k].reverse()
   with self.subTest(k=k),self.assertRaises(ValueError):s.verify_snapshot(b,bad)
  with self.assertRaises(ValueError):s.verify_snapshot(b,{**p,'extra':False})
 def test_noncanonical_and_sampled_byte_mutation(self):
  b,p=freeze()
  wrong=[b+'\n'.encode(),b' '+b,b+b'{}',b'\xef\xbb\xbf'+b,b.replace(b'Geo',b'\\u0047eo',1),json.dumps(json.loads(b),indent=2).encode(),b'{"candidate":{},"candidate":{},"proposed_content_digest":NaN}']
  for i in range(0,len(b),max(1,len(b)//80)):wrong.append(b[:i]+bytes([b[i]^1])+b[i+1:])
  for blob in wrong:
   with self.assertRaises(ValueError):s.verify_snapshot(blob,p)
  other=freeze(render([row(3)]))[1]
  with self.assertRaises(ValueError):s.verify_snapshot(b,other)
 def test_forgery_internal_consistency_only(self):
  c=render([row()]);c['candidate']['html']='<script>SELF_CONSISTENT_UNTRUSTED</script>';c['content_digest']=s._hash(c['candidate']);b,p=freeze(c);self.assertEqual(s.verify_snapshot(b,p)['html'],c['candidate']['html'])
 def test_types_empty_limits_fixed_refusal(self):
  class B(bytes):pass
  class D(dict):pass
  b,p=freeze()
  for blob in (bytearray(b),memoryview(b),B(b),b'x'*(s.CAP+1)):
   with self.assertRaises(ValueError):s.verify_snapshot(blob,p)
  with self.assertRaises(ValueError):s.verify_snapshot(b,D(p))
  for c in (render([]),{**render([row()]),'content_digest':'SECRET_CANARY'},{**render([row()]),'send_allowed':True}):
   with self.assertRaises(ValueError)as e:freeze(c)
   self.assertEqual(str(e.exception),'Candidate bytes held');self.assertIsNone(e.exception.__cause__);self.assertIsNone(e.exception.__context__)
  for fp in ('A'*64,'a'*63,True):
   with self.assertRaises(ValueError):freeze(fp=fp)
  for nonce in ('x'*19,'x'*81,'é'*20):
   with self.assertRaises(ValueError):freeze(nonce=nonce)
 def test_candidate_schema_ids_and_bytes(self):
  base=render([row(1),row(2)])
  for k,v in [('skip',True),('offset_minutes',True),('offset_label','IST'),('asof_utc','2026-10-10'),('subject','bad'),('sorted_union_ids',[]),('renderer_version','other')]:
   c=copy.deepcopy(base);c['candidate'][k]=v;c['content_digest']=s._hash(c['candidate'])
   with self.assertRaises(ValueError):freeze(c)
  c=copy.deepcopy(base);c['candidate']['html']='x'*61441;c['content_digest']=s._hash(c['candidate'])
  with self.assertRaises(ValueError):freeze(c)
 def test_off_imports_ast_and_no_external_effects(self):
  class Bad:
   def __getattribute__(self,k):raise AssertionError()
  p=s.freeze_candidate(candidate_result=Bad(),recipient_set_fingerprint=Bad(),nonce=Bad());self.assertEqual(p['state'],'disabled')
  for k in ('archived','durable','send_allowed','ready'):self.assertIs(p[k],False)
  tree=ast.parse(Path(s.__file__).read_text());mods=set()
  for n in ast.walk(tree):
   if isinstance(n,ast.Import):mods.update(a.name for a in n.names)
   elif isinstance(n,ast.ImportFrom):mods.add(n.module)
  self.assertEqual(mods,{'copy','hashlib','json','re','datetime'})
  root=Path(s.__file__).parents[1]
  code="import sys;from integration.mail_candidate219 import freeze_candidate;freeze_candidate();assert not any(x in sys.modules for x in ['integration.mail_ledger212','integration.digest_email218','pymongo'])"
  r=subprocess.run([sys.executable,'-c',code],cwd=root,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
