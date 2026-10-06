import unittest,threading,copy
from integration.manage_fixture95.core import Fixture,Refused,CATALOG
P=object()
def fresh():return Fixture(lambda p:p is P)
def op(i='nilgiri_watch',a='tune',v=None):return {'id':i,'action':a,'value':{'cadence_seconds':3600}if v is None and a=='tune'else v}
class Tests(unittest.TestCase):
 def test_three_states_and_partial(self):
  v=fresh().view(P);self.assertIn('PARTIAL',v['scope'])
  for r in v['rows']:self.assertEqual(r['effective'],'unwired_unknown');self.assertFalse(r['activation_enabled']);self.assertEqual(r['last_known_configured'],'unknown')
  self.assertTrue(all(r['requested']=='unspecified'for r in v['rows']))
 def test_catalog_immutable(self):
  self.assertIs(type(CATALOG),bytes)
  import json
  rows=json.loads(CATALOG);rows[0]['settings']['cadence_seconds']=1
  self.assertEqual(fresh().view(P)['rows'][0]['settings']['cadence_seconds'],3600)
  with self.assertRaises(TypeError):CATALOG[0]=0
 def test_request_not_activation(self):
  v=fresh().mutate(P,0,[op('nilgiri_watch','request','on')]);r=v['rows'][0]
  self.assertEqual(r['requested'],'on_not_applied');self.assertEqual(r['effective'],'unwired_unknown');self.assertFalse(r['activation_enabled'])
 def test_bad_register_value(self):
  f=fresh()
  with self.assertRaises(Refused):f.mutate(P,0,[op('tenders','register',True)])
  self.assertEqual(f.view(P)['revision'],0)
 def test_evidence_hashes(self):
  import json,hashlib,os
  from pathlib import Path
  root=Path(__file__).resolve().parents[1]
  evidence=json.loads((root/'integration/manage_fixture95/evidence.json').read_text())
  for r in json.loads(CATALOG):
   for p in r['evidence']:
    self.assertTrue((root/p).is_file(),p);self.assertEqual(hashlib.sha256((root/p).read_bytes()).hexdigest(),evidence['files'][p])
 def test_deny(self):
  f=fresh()
  for p in (None,True,{'admin':True},object()):
   with self.assertRaises(Refused):f.mutate(p,0,[op()])
  self.assertEqual(f.view(P)['revision'],0)
  with self.assertRaises(Refused):Fixture().view(P)
 def test_atomic_bad_batch(self):
  f=fresh();before=f.view(P)
  for bad in (op('unknown'),{'id':'nilgiri_watch','action':'activate','value':None},{'id':'tenders','action':'request','value':'maybe'}):
   with self.assertRaises(Refused):f.mutate(P,0,[op(),bad])
   self.assertEqual(f.view(P),before)
 def test_closed_shapes_hooks(self):
  class S(str):
   def __eq__(self,o):raise AssertionError('hook')
  class D(dict):pass
  class I(int):pass
  f=fresh()
  for ops in ([op(S('nilgiri_watch'))],[D(op())],[op(v={'cadence_seconds':True})],[op(v={'cadence_seconds':I(3600)})],[op(v={'url':'https://x'})],(op(),),[op(),op()]):
   with self.assertRaises(Refused):f.mutate(P,0,ops)
  self.assertEqual(f.view(P)['revision'],0)
 def test_ranges(self):
  for n in (3599,86401,-1,0):
   with self.assertRaises(Refused):fresh().mutate(P,0,[op(v={'cadence_seconds':n})])
  for n in (3600,86400):self.assertEqual(fresh().mutate(P,0,[op(v={'cadence_seconds':n})])['revision'],1)
 def test_register_known_only(self):
  f=fresh();v=f.mutate(P,0,[op('tenders','register')]);self.assertTrue(v['rows'][1]['registered']);self.assertEqual(v['rows'][1]['effective'],'unwired_unknown')
  with self.assertRaises(Refused):f.mutate(P,1,[op('other','register')])
 def test_copy_history(self):
  f=fresh();batch=[op()];v=f.mutate(P,0,batch);batch[0]['value']['cadence_seconds']=1;v['rows'][0]['settings']['cadence_seconds']=1;v['history'][0]['prior']['nilgiri_watch']['settings']['cadence_seconds']=1
  self.assertEqual(f.view(P)['rows'][0]['settings']['cadence_seconds'],3600)
  for n in range(1,12):f.mutate(P,n,[op(v={'cadence_seconds':3600+n})])
  self.assertEqual(len(f.view(P)['history']),8)
 def test_cas_race(self):
  f=fresh();results=[];barrier=threading.Barrier(2)
  def run():
   barrier.wait()
   try:f.mutate(P,0,[op()]);results.append('ok')
   except Refused:results.append('stale')
  ts=[threading.Thread(target=run)for _ in range(2)]
  for t in ts:t.start()
  for t in ts:t.join()
  self.assertCountEqual(results,['ok','stale']);self.assertEqual(f.view(P)['revision'],1)
 def test_undo_new_revision_conflict(self):
  f=fresh();f.mutate(P,0,[op(v={'cadence_seconds':7200})]);v=f.undo(P,1,1);self.assertEqual(v['revision'],2);self.assertEqual(v['rows'][0]['settings']['cadence_seconds'],3600)
  with self.assertRaises(Refused):f.undo(P,1,1)
  with self.assertRaises(Refused):f.undo(P,2,1)
  with self.assertRaises(Refused):f.undo(P,2,2)
 def test_auth_once_bound_entire_mutation(self):
  calls=[]
  def auth(p):calls.append(p);return len(calls)==1
  f=Fixture(auth);v=f.mutate(P,0,[op()]);self.assertEqual(v['revision'],1);self.assertEqual(len(calls),1)
 def test_no_user_coupling(self):
  f=fresh()
  with self.assertRaises(Refused):f.mutate(P,0,[op('stored_news','tune',{'watchlist':[]})])
  self.assertEqual(f.view(P)['revision'],0)
if __name__=='__main__':unittest.main(verbosity=2)

class InventoryTests(unittest.TestCase):
 def test_exact_additive_paths_and_hashes(self):
  import json,hashlib,ast
  from pathlib import Path
  root=Path(__file__).resolve().parents[1];base=root/'integration/manage_fixture95'
  pins=json.loads((base/'inventory.json').read_text())
  actual={str(p.relative_to(root))for p in base.iterdir()if p.is_file()and p.name!='inventory.json'}|{'tests/test_manage_fixture95.py'}
  self.assertEqual(actual,set(pins))
  for p,h in pins.items():
   self.assertEqual(hashlib.sha256((root/p).read_bytes()).hexdigest(),h,p)
   if p.endswith('.py'):ast.parse((root/p).read_bytes())
