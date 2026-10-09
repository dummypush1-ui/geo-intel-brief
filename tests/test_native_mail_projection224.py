import ast,copy,hashlib,importlib,json,subprocess,sys,unittest
from pathlib import Path
from tests.test_mail_exclusion223 import args as candidate,rebuild
s=importlib.import_module('integration.native_mail_projection224')
def h(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
FP='a'*64;HISTORY='b'*64;CHANNEL=h({'kind':'email','recipients':FP});CONTROL=h({'channel':CHANNEL,'purpose':'digest'})
def fixture(state='acknowledged',i=1,key='c'*64):
 id=f'{i:024x}';digest='d'*64;binding=h({'logical_channel':CHANNEL,'purpose':'digest','ids':[id],'content_digest':digest})
 reference='e'*64 if state=='operator_resolved_unsent' else None
 scope='bridge_send_returned_not_delivery'if state=='acknowledged'else'operator_asserted_unsent'if state=='operator_resolved_unsent'else'no_send_proof'
 control={'_id':CONTROL,'schema':1,'channel':CHANNEL,'purpose':'digest','history_manifest':HISTORY,'history_complete':True,'revision':0,'active':key if state in ('prepared','started')else None}
 receipt={'_id':key,'schema':1,'channel':CHANNEL,'purpose':'digest','ids':[id],'hash':binding,'content_digest':digest,'rail':'apps_script','state':state,'attempt':'n'*20 if state in ('started','acknowledged','operator_resolved_unsent')else None,'resolution_reference':reference,'scope':scope}
 article={'_id':h({'channel':CHANNEL,'purpose':'digest','article':id}),'schema':1,'channel':CHANNEL,'purpose':'digest','article':id,'receipt':key,'hash':binding,'state':state}
 return dict(control_row=control,receipt_rows=[receipt],article_rows=[article],recipient_set_fingerprint=FP,history_manifest=HISTORY)
class Tests(unittest.TestCase):
 def refuse(self,d):
  with self.assertRaises(ValueError)as e:s.project_supplied(enabled=True,**d)
  self.assertEqual(str(e.exception),'Native projection held');self.assertIsNone(e.exception.__cause__);self.assertIsNone(e.exception.__context__);self.assertNotIn('CANARY',repr(e.exception))
 def test_states_inputs_unchanged_closed_output(self):
  from bson import ObjectId
  for state in s._STATES:
   d=fixture(state);before=copy.deepcopy(d);p=s.project_supplied(enabled=True,**d);self.assertEqual(d,before)
   self.assertEqual(set(p),{'state','projection','note',*s._FLAGS});self.assertEqual(set(p['projection']),{'schema','logical_channel','purpose','acknowledged_ids','active_state'})
   self.assertEqual(p['projection']['acknowledged_ids'],(ObjectId(f'{1:024x}'),)if state=='acknowledged'else());self.assertEqual(p['projection']['active_state'],state if state in ('prepared','started')else None)
   for k in s._FLAGS:self.assertIs(p[k],False)
   self.assertNotIn('n'*20,repr(p));self.assertNotIn(HISTORY,repr(p))
  d=fixture();d['receipt_rows'][0]['resolution_reference']='e'*64;d['receipt_rows'][0]['scope']='operator_asserted_sent_not_delivery';self.assertTrue(s.project_supplied(enabled=True,**d))
 def test_real212_validators_and_equation_vectors(self):
  m=importlib.import_module('integration.mail_ledger212');ledger=object.__new__(m.MailLedger);ledger.enabled=True;ledger.channel=CHANNEL;ledger.purpose='digest';ledger.history=HISTORY;ledger.control_id=CONTROL
  self.assertEqual(CHANNEL,'0d2e8130c884b0468d594ffb9446105dfed955c1f36f9a0ff982e470209d80bc');self.assertEqual(CHANNEL,m.logical_channel('email',FP));self.assertEqual(CONTROL,'fe75832b52ec42303a6dc66127957d52e7b4e9a2387326fc5c6c61d20dc55817')
  class Collection:
   def __init__(self,row):self.row=row
   def find_one(self,*a,**kw):return self.row
  for state in s._STATES:
   d=fixture(state);self.assertEqual(ledger._control({m.CONTROL:Collection(d['control_row'])},None),d['control_row']);self.assertEqual(ledger._receipt({m.RECEIPTS:Collection(d['receipt_rows'][0])},None,'c'*64),d['receipt_rows'][0]);self.assertEqual(ledger._article(d['article_rows'][0],d['article_rows'][0]['_id']),d['article_rows'][0]);self.assertTrue(s.project_supplied(enabled=True,**d))
 def test_released_receipt_overwritten_current_keys(self):
  for released in ('cancelled','operator_resolved_unsent'):
   d=fixture(released);d['article_rows']=[];self.assertTrue(s.project_supplied(enabled=True,**d))
   newer=fixture('prepared',key='f'*64);d['control_row']=newer['control_row'];d['receipt_rows']+=newer['receipt_rows'];d['article_rows']=newer['article_rows'];self.assertTrue(s.project_supplied(enabled=True,**d))
   d['article_rows'][0]['receipt']='9'*64;d['article_rows'][0]['state']='acknowledged';d['control_row']['active']=None;d['receipt_rows']=d['receipt_rows'][:1];p=s.project_supplied(enabled=True,**d);self.assertEqual(len(p['projection']['acknowledged_ids']),1)
 def test_unsupplied_receipts_ack_released_not_unresolved(self):
  for state in ('acknowledged','cancelled','operator_resolved_unsent'):
   d=fixture(state);d['receipt_rows']=[];self.assertTrue(s.project_supplied(enabled=True,**d))
  for state in ('prepared','started'):
   d=fixture(state);d['receipt_rows']=[];self.refuse(d)
 def test_required_rows_duplicates_active_and_graph_conflicts(self):
  for state in ('prepared','started','acknowledged'):
   d=fixture(state);d['article_rows']=[];self.refuse(d)
   for field,value in [('receipt','f'*64),('hash','f'*64),('state','cancelled')]:
    d=fixture(state);d['article_rows'][0][field]=value;self.refuse(d)
  d=fixture('prepared');d['control_row']['active']=None;self.refuse(d)
  d=fixture();d['control_row']['active']='c'*64;self.refuse(d)
  for collection in ('receipt_rows','article_rows'):
   d=fixture();d[collection].append(copy.deepcopy(d[collection][0]));self.refuse(d)
  d=fixture();extra=copy.deepcopy(d['article_rows'][0]);extra['_id']='f'*64;d['article_rows'].append(extra);self.refuse(d)
  d=fixture('started');other=fixture('prepared',2,'f'*64);d['receipt_rows']+=other['receipt_rows'];d['article_rows']+=other['article_rows'];self.refuse(d)
 def test_order_independent_empty_invented_omitted_graph(self):
  d=fixture();other=fixture('acknowledged',2,'f'*64);d['receipt_rows']+=other['receipt_rows'];d['article_rows']+=other['article_rows'];p=s.project_supplied(enabled=True,**d)
  d['receipt_rows'].reverse();d['article_rows'].reverse();self.assertEqual(s.project_supplied(enabled=True,**d),p)
  d['receipt_rows']=[];d['article_rows']=[];self.assertEqual(s.project_supplied(enabled=True,**d)['projection']['acknowledged_ids'],())
  self.assertIn('invented',p['note'])
 def test_223_roundtrip_ack_accepts_prepared_holds(self):
  from bson import ObjectId
  x=importlib.import_module('integration.mail_exclusion223')
  for state in ('acknowledged','prepared'):
   view=s.project_supplied(enabled=True,**fixture(state))['projection'];d=candidate();d['exclusion_projection']=view
   if state=='acknowledged':d['displayed_receipts']={**d['displayed_receipts'],'email':(ObjectId(f'{1:024x}'),)};rebuild(d);self.assertTrue(x.check_supplied(enabled=True,**d)['consistency_match'])
   else:
    with self.assertRaises(ValueError):x.check_supplied(enabled=True,**d)
 def test_all_fields_canaries_types_caps(self):
  for location in ('control_row','receipt_rows','article_rows'):
   base=fixture();row=base[location]if location=='control_row'else base[location][0]
   for key in row:
    d=copy.deepcopy(base);target=d[location]if location=='control_row'else d[location][0];target[key]='CANARY';self.refuse(d)
  class D(dict):pass
  class L(list):pass
  class S(str):pass
  for k in ('recipient_set_fingerprint','history_manifest'):self.refuse({**fixture(),k:S('a'*64)})
  for rev in (True,-1,2**53-1,'0'):
   d=fixture();d['control_row']['revision']=rev;self.refuse(d)
  for val in ('A'*24,'１'*24):
   d=fixture();d['article_rows'][0]['article']=val;self.refuse(d)
  for k in ('control_row','receipt_rows','article_rows'):
   d=fixture();d[k]=D(d[k])if k=='control_row'else L(d[k]);self.refuse(d)
  for k in fixture():self.refuse({n:v for n,v in fixture().items()if n!=k})
  self.refuse({**fixture(),'extra':'CANARY'})
  d=fixture();d['receipt_rows']*=129;self.refuse(d)
  d=fixture();d['article_rows']*=10001;self.refuse(d)
 def test_off_sysmodules_ast(self):
  class Bad:
   def __getattribute__(self,k):raise AssertionError('CANARY')
  self.assertEqual(s.project_supplied(control_row=Bad())['state'],'disabled')
  for value in (1,None,'true'):
   with self.assertRaises(ValueError):s.project_supplied(enabled=value)
  tree=ast.parse(Path(s.__file__).read_text());mods=set()
  for n in ast.walk(tree):
   if isinstance(n,ast.Import):mods.update(a.name for a in n.names)
   elif isinstance(n,ast.ImportFrom):mods.add(n.module)
  self.assertEqual(mods,{'hashlib','json','re','bson'})
  code="import sys;from integration.native_mail_projection224 import project_supplied;project_supplied();assert not any(x in sys.modules for x in ['bson','pymongo','integration.mail_ledger212'])"
  r=subprocess.run([sys.executable,'-c',code],cwd=Path(s.__file__).parents[1],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
