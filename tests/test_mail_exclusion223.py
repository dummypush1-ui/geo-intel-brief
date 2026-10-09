import ast,copy,importlib,subprocess,sys,unittest
from pathlib import Path
from tests.test_digest_email218 import render,row,R
from tests.test_mail_rederive221 import inputs
s=importlib.import_module('integration.mail_exclusion223');f=importlib.import_module('integration.mail_candidate219')
def args():
 d=inputs();d['exclusion_projection']={'schema':'mail_exclusion_projection223_v1','logical_channel':d['binding']['proposed_channel'],'purpose':'digest','acknowledged_ids':(),'active_state':None};return d
def rebuild(d):
 c=render(d['rows'],displayed_receipts=d['displayed_receipts']);d['blob'],d['binding']=f.freeze_candidate(enabled=True,candidate_result=c,recipient_set_fingerprint=d['recipient_set_fingerprint'],nonce=d['nonce']);return d
class Tests(unittest.TestCase):
 def refuse(self,d):
  with self.assertRaises(ValueError)as e:s.check_supplied(enabled=True,**d)
  self.assertEqual(str(e.exception),'Exclusion view held');self.assertIsNone(e.exception.__cause__);self.assertIsNone(e.exception.__context__);self.assertNotIn('CANARY',repr(e.exception))
 def test_match_closed_constant_copy_real212(self):
  from integration.mail_ledger212 import logical_channel
  d=args();d['displayed_receipts']={**R,'email':(row(1)['_id'],)};d['exclusion_projection']['acknowledged_ids']=d['displayed_receipts']['email'];rebuild(d);before=copy.deepcopy(d);p=s.check_supplied(enabled=True,**d)
  self.assertEqual(d,before);self.assertEqual(d['exclusion_projection']['logical_channel'],logical_channel('email',d['recipient_set_fingerprint']))
  self.assertEqual(set(p),{'state','consistency_match','note',*s._FLAGS});self.assertTrue(p['consistency_match']);self.assertEqual(p['note'],s._NOTE)
  for k in s._FLAGS:self.assertIs(p[k],False)
  self.assertNotIn(d['exclusion_projection']['logical_channel'],repr(p));self.assertNotIn(str(row(1)['_id']),repr(p))
 def test_only_email_compared_other_channels_not_excluded(self):
  d=args();d['displayed_receipts']={**R,'telegram':(row(1)['_id'],),'whatsapp':(row(2)['_id'],)};self.assertTrue(s.check_supplied(enabled=True,**d)['consistency_match']);self.assertIn(str(row(1)['_id']),f.verify_snapshot(d['blob'],d['binding'])['sorted_union_ids'])
 def test_set_order_not_dedup(self):
  d=args();d['rows'].append(row(3));d['displayed_receipts']={**R,'email':(row(2)['_id'],row(1)['_id'])};d['exclusion_projection']['acknowledged_ids']=(row(1)['_id'],row(2)['_id']);rebuild(d);self.assertTrue(s.check_supplied(enabled=True,**d)['consistency_match'])
  d['exclusion_projection']['acknowledged_ids']=(row(1)['_id'],)*2;self.refuse(d)
 def test_mismatch_channel_purpose_expectedfp_wholeactive(self):
  for field,value in [('logical_channel','b'*64),('purpose','critical'),('schema','CANARY'),('active_state','prepared'),('active_state','started'),('active_state','cancelled'),('active_state','unknown'),('active_state','resolved'),('active_state',False)]:
   d=args();d['exclusion_projection'][field]=value;self.refuse(d)
  d=args();d['exclusion_projection']['acknowledged_ids']=(row(999)['_id'],);self.refuse(d)
  d=args();d['recipient_set_fingerprint']='b'*64;self.refuse(d)
  #Active holds even with no shared IDs. Projection has none in both views.
  d=args();d['exclusion_projection']['active_state']='prepared';self.refuse(d)
 def test_forgery_includes_acknowledged_id_refused(self):
  d=args();d['displayed_receipts']={**R,'email':(row(1)['_id'],)};d['exclusion_projection']['acknowledged_ids']=(row(1)['_id'],)
  self.assertTrue(f.verify_snapshot(d['blob'],d['binding']));self.refuse(d)
 def test_omission_both_stale_allowed_not_authority(self):
  d=args();self.assertTrue(s.check_supplied(enabled=True,**d)['consistency_match']);self.assertTrue(s.check_supplied(enabled=True,**d)['consistency_match']);self.assertIn('Omission in both',s._NOTE);self.assertIn('stale',s._NOTE)
 def test_types_caps_extra_missing_canary(self):
  class T(tuple):pass
  class D(dict):pass
  from bson import ObjectId
  class O(ObjectId):pass
  for values in ([],T(()),(b'CANARY',),('000000000000000000000001',),(O(),),(row(1)['_id'],)*10001,(row(1)['_id'],)*2):
   for channel in ('email','telegram','whatsapp','projection'):
    d=args()
    if channel=='projection':d['exclusion_projection']['acknowledged_ids']=values
    else:d['displayed_receipts']={**R,channel:values}
    self.refuse(d)
  d=args();d['exclusion_projection']=D(d['exclusion_projection']);self.refuse(d)
  for key in args():self.refuse({k:v for k,v in args().items()if k!=key})
  d=args();d['exclusion_projection']['extra']='CANARY';self.refuse(d)
  self.refuse({**args(),'extra':'CANARY'})
 def test_off_imports_ast(self):
  class Bad:
   def __getattribute__(self,k):raise AssertionError('CANARY')
  self.assertEqual(s.check_supplied(blob=Bad(),exclusion_projection=Bad())['state'],'disabled')
  for enabled in (1,None,'true'):
   with self.assertRaises(ValueError):s.check_supplied(enabled=enabled)
  tree=ast.parse(Path(s.__file__).read_text());mods=set()
  for n in ast.walk(tree):
   if isinstance(n,ast.Import):mods.update(a.name for a in n.names)
   elif isinstance(n,ast.ImportFrom):mods.add(n.module)
  self.assertEqual(mods,{'copy','bson','integration.mail_rederive221','integration.mail_candidate219'})
  code="import sys;from integration.mail_exclusion223 import check_supplied;check_supplied();assert not any(x in sys.modules for x in ['bson','pymongo','integration.mail_rederive221','integration.mail_candidate219','integration.digest_email218','integration.mail_ledger212'])"
  r=subprocess.run([sys.executable,'-c',code],cwd=Path(s.__file__).parents[1],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
