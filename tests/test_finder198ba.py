import unittest,copy
from types import SimpleNamespace
from integration.finder198_budget import ProxyCallBudget,BudgetRefused,ID
from integration.finder198_connector import plan_ai,plan_ships,validate_backend,ConnectorRefused,MODEL_CATALOG
class Collection:
 def __init__(self):
  self.name='finder_budget198';self.database=SimpleNamespace(name='geo_intel');self.write_concern=SimpleNamespace(document={'w':'majority','j':True,'wtimeout':5000});self.read_concern=SimpleNamespace(document={'level':'majority'});self.doc={'_id':ID,'revision':0,'window_start':100,'calls':0,'fence':0,'active':None,'last_clock':100};self.writes=0;self.ack=True
 def find_one(self,*a,**kw):return copy.deepcopy(self.doc)
 def replace_one(self,q,d,upsert):
  assert upsert is False;self.writes+=1
  if q['revision']!=self.doc['revision']:return SimpleNamespace(acknowledged=True,matched_count=0)
  self.doc=copy.deepcopy(d);return SimpleNamespace(acknowledged=self.ack,matched_count=1)
R={'mapping':('geo_intel','finder_budget198'),'preprovisioned_state_verified':True,'no_ttl_verified':True,'role_verified':True,'write_permission':True}
class Tests(unittest.TestCase):
 def setUp(self):self.c=Collection();self.b=ProxyCallBudget(self.c,review=R)
 def test_reserved_before_transport_consumed_global(self):
  t=self.b.reserve('n'*24,101);self.assertEqual(self.c.doc['calls'],1)
  with self.assertRaises(BudgetRefused):self.b.reserve('m'*24,102)
  self.assertEqual(self.b.settle(t,103,known_complete=True)['state'],'complete');self.assertEqual(self.c.doc['calls'],1)
 def test_unknown_expired_never_released_or_taken_over(self):
  for known,now in ((False,102),(True,126)):
   self.setUp();t=self.b.reserve('n'*24,101);self.assertEqual(self.b.settle(t,now,known_complete=known)['state'],'unknown_held')
   with self.assertRaises(BudgetRefused):self.b.reserve('m'*24,1000)
   with self.assertRaises(BudgetRefused):self.b.settle(t,1000,known_complete=True)
 def test_full_budget_and_new_window(self):
  self.c.doc['calls']=60
  with self.assertRaises(BudgetRefused):self.b.reserve('n'*24,101)
  self.b.reserve('n'*24,700);self.assertEqual(self.c.doc['calls'],1)
 def test_clockrollback_receipt_unknown_failclosed(self):
  with self.assertRaises(BudgetRefused):self.b.reserve('n'*24,99)
  self.c.ack=False
  with self.assertRaises(BudgetRefused):self.b.reserve('n'*24,101)
  self.assertIsNotNone(self.c.doc['active'])
 def test_missing_schema_concerns_review(self):
  self.c.doc=None
  with self.assertRaises(BudgetRefused):self.b.reserve('n'*24,101)
  self.c.write_concern.document['j']=False
  with self.assertRaises(BudgetRefused):ProxyCallBudget(self.c,review=R)
 def test_wrong_ticket_no_release(self):
  t=self.b.reserve('n'*24,101);t['fence']+=1
  with self.assertRaises(BudgetRefused):self.b.settle(t,102,known_complete=True)
  self.assertIsNotNone(self.c.doc['active'])
 def test_disabled_model_catalog_three_only(self):
  self.assertEqual(MODEL_CATALOG,())
  for p in ('groq','gemini','mistral','nvidia'):
   with self.assertRaises(ConnectorRefused):plan_ai(p,'invented',now=101)
 def test_exact_ports_no_arbitrary_url(self):
  self.assertEqual(plan_ships('INNSA')['path'],'/ships?port=INNSA')
  for p in ('inNSA','EVIL','ALL&x=1','https://evil.example'):
   with self.assertRaises(ConnectorRefused):plan_ships(p)
 def test_backend_secret_not_returned_no_url_override(self):
  v={'FINDER_PROXY_BASE_URL':'https://hsn-ai-proxy.onrender.com','FINDER_PROXY_SECRET':'x'*48};self.assertNotIn('x'*48,str(validate_backend(v)))
  for base in ('https://evil.example','https://hsn-ai-proxy.onrender.com/','http://hsn-ai-proxy.onrender.com'):
   with self.assertRaises(ConnectorRefused):validate_backend({**v,'FINDER_PROXY_BASE_URL':base})
 def test_cas_contention_and_exact_scalar_states(self):
  self.c.replace_one=lambda *a,**kw:SimpleNamespace(acknowledged=True,matched_count=0)
  with self.assertRaises(BudgetRefused):self.b.reserve('n'*24,101)
  self.setUp();self.c.doc['calls']=True
  with self.assertRaises(BudgetRefused):self.b.reserve('n'*24,101)
 def test_role_preflight_read_only(self):
  from integration.finder198_budget import inspect_budget
  from tests.test_collector197b_preflight import Client,Cursor
  c=Client();col=self.c
  col.list_indexes=lambda **kw:Cursor([{'key':{'_id':1}}])
  def collection(name,**kw):
   self.assertEqual(name,'finder_budget198');col.write_concern=kw['write_concern'];col.read_concern=kw['read_concern'];return col
  c.db.get_collection=collection;c.grants=[{'resource':{'db':'geo_intel','collection':'finder_budget198'},'actions':['find','listIndexes','update']}]
  self.assertIs(inspect_budget(c),col);self.assertEqual(col.writes,0)
  c.grants[0]['actions'].append('insert')
  with self.assertRaises(BudgetRefused):inspect_budget(c)
