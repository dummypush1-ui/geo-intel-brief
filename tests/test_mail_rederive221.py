import ast,copy,importlib,json,subprocess,sys,unittest
from datetime import timedelta,datetime
from pathlib import Path
from unittest.mock import patch
from tests.test_digest_email218 import render,row,N,R
s=importlib.import_module('integration.mail_rederive221')
f=importlib.import_module('integration.mail_candidate219')
def inputs(rows=None,**changes):
 rows=[row(1),row(2)]if rows is None else rows
 b,p=f.freeze_candidate(enabled=True,candidate_result=render(rows),recipient_set_fingerprint='a'*64,nonce='n'*20)
 d=dict(blob=b,binding=p,rows=rows,now=N,date_field='published',displayed_receipts=R,offset_minutes=330,offset_label='+05:30',limit=60,recipient_set_fingerprint='a'*64,nonce='n'*20);d.update(changes);return d
class Tests(unittest.TestCase):
 def refuse(self,d):
  with self.assertRaises(ValueError)as e:s.verify_rederived(enabled=True,**d)
  self.assertEqual(str(e.exception),'Row rederivation held');self.assertIsNone(e.exception.__cause__);self.assertIsNone(e.exception.__context__);self.assertNotIn('CANARY',repr(e.exception))
 def test_match_closed_constants_copy_replay(self):
  d=inputs();before=copy.deepcopy(d);p=s.verify_rederived(enabled=True,**d)
  self.assertEqual(d,before);self.assertEqual(s.verify_rederived(enabled=True,**d),p)
  self.assertEqual(set(p),{'state','row_derivation_match','note','send_allowed','ready','archive_proof','durable','source_complete','receipt_membership_verified','owner_approval'})
  self.assertTrue(p['row_derivation_match']);self.assertEqual(p['state'],'supplied_rows_rederived_match')
  for k in s._FLAGS:self.assertIs(p[k],False)
  self.assertEqual(p['note'],s._NOTE);self.assertNotIn('Fixture story',repr(p));self.assertNotIn('n'*20,repr(p));self.assertNotIn('a'*64,repr(p))
 def test_consistent_forgery_and_changed_originals(self):
  d=inputs();c=render(d['rows']);c['candidate']['html']='SELF_CONSISTENT_CANARY';c['content_digest']=f._hash(c['candidate']);d['blob'],d['binding']=f.freeze_candidate(enabled=True,candidate_result=c,recipient_set_fingerprint=d['recipient_set_fingerprint'],nonce=d['nonce']);self.assertTrue(f.verify_snapshot(d['blob'],d['binding']));self.refuse(d)
  d=inputs();d['rows'][0]['title']='CHANGED_CANARY';self.refuse(d)
  c=render(d['rows']);d['blob'],d['binding']=f.freeze_candidate(enabled=True,candidate_result=c,recipient_set_fingerprint=d['recipient_set_fingerprint'],nonce=d['nonce']);self.assertTrue(s.verify_rederived(enabled=True,**d)['row_derivation_match'])
 def test_render_changes_old_blob_refuse(self):
  for key in ('title','summary','source','category','url'):
   d=inputs();d['rows'][0][key]='https://example.invalid/changed'if key=='url'else'CHANGED_CANARY';self.refuse(d)
  for kw in [dict(now=N+timedelta(seconds=1)),dict(offset_minutes=0,offset_label='+00:00'),dict(limit=1),dict(displayed_receipts={**R,'email':(row(1)['_id'],)})]:self.refuse(inputs(**kw))
  d=inputs();d['rows'][0]['published']=(N-timedelta(days=30)).isoformat();self.refuse(d)
  d=inputs();d['rows'][0]['_id']=row(3)['_id'];self.refuse(d)
  d=inputs();d['rows'][0]['created_at']=(N-timedelta(days=30)).isoformat();d['date_field']='created_at';self.refuse(d)
 def test_subset_completeness_not_proven(self):
  d=inputs();d['rows'].append(row(3,published=(N-timedelta(days=30)).isoformat()));self.assertTrue(s.verify_rederived(enabled=True,**d)['row_derivation_match']);d['rows'].pop();self.assertTrue(s.verify_rederived(enabled=True,**d)['row_derivation_match'])
  rows=[row(1),row(2)];receipt={**R,'email':(rows[1]['_id'],)};d=inputs([rows[0]],displayed_receipts=receipt);d['rows']=rows;self.assertTrue(s.verify_rederived(enabled=True,**d)['row_derivation_match']);d['rows'].pop();self.assertTrue(s.verify_rederived(enabled=True,**d)['row_derivation_match'])
  self.assertIn('Completeness',s._NOTE)
 def test_all_bad_types_and_binding_leaves(self):
  class B(bytes):pass
  class S(str):pass
  class D(dict):pass
  class L(list):pass
  class DT(datetime):pass
  d=inputs()
  for b in (bytearray(d['blob']),memoryview(d['blob']),B(d['blob']),b'CANARY',b'') :self.refuse({**d,'blob':b})
  for fp in ('CANARY_FINGERPRINT','b'*64,S('a'*64)):self.refuse({**d,'recipient_set_fingerprint':fp})
  for nonce in ('CANARY_NONCE','z'*20,S('n'*20)):self.refuse({**d,'nonce':nonce})
  for rows in ([],(),L(d['rows']),[D(d['rows'][0])],[row(title=S('CANARY'))],[row(published=DT(2026,10,10))],[row(title='\ud800CANARY')]):self.refuse({**d,'rows':rows})
  for k in d:self.refuse({x:v for x,v in d.items()if x!=k})
  self.refuse({**d,'extra':'CANARY'})
  for k in d['binding']:
   bad=copy.deepcopy(d['binding']);v=bad[k];bad[k]=not v if type(v)is bool else ('CANARY'if type(v)is str else [])
   self.refuse({**d,'binding':bad})
 def test_order_and_failures_canaries(self):
  a=importlib.import_module('integration.digest_email218');d=inputs();calls=[]
  realv=f.verify_snapshot;realr=a.render_candidate;realf=f.freeze_candidate
  def v(*x,**kw):calls.append('verify');return realv(*x,**kw)
  def r(*x,**kw):calls.append('render');return realr(*x,**kw)
  def freeze(*x,**kw):calls.append('freeze');return realf(*x,**kw)
  with patch.object(f,'verify_snapshot',v),patch.object(a,'render_candidate',r),patch.object(f,'freeze_candidate',freeze):s.verify_rederived(enabled=True,**d)
  self.assertEqual(calls,['verify','render','freeze'])
  for module,name in ((f,'verify_snapshot'),(a,'render_candidate'),(f,'freeze_candidate')):
   d=inputs();d['rows'][0]['title']='CANARY_TITLE'
   with patch.object(module,name,side_effect=ValueError('CANARY upstream')):self.refuse(d)
 def test_off_imports_ast(self):
  class Hostile:
   def __getattribute__(self,k):raise AssertionError('CANARY')
  self.assertEqual(s.verify_rederived(blob=Hostile(),rows=Hostile())['state'],'disabled')
  for enabled in (1,None,'true'):
   with self.assertRaises(ValueError):s.verify_rederived(enabled=enabled)
  tree=ast.parse(Path(s.__file__).read_text());mods=set()
  for n in ast.walk(tree):
   if isinstance(n,ast.Import):mods.update(a.name for a in n.names)
   elif isinstance(n,ast.ImportFrom):mods.add(n.module)
  self.assertEqual(mods,{'copy','json','datetime','bson','integration.mail_candidate219','integration.digest_email218'})
  code="import sys;from integration.mail_rederive221 import verify_rederived;verify_rederived();assert not any(x in sys.modules for x in ['integration.digest_email218','integration.mail_candidate219','bson','pymongo'])"
  r=subprocess.run([sys.executable,'-c',code],cwd=Path(s.__file__).parents[1],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
