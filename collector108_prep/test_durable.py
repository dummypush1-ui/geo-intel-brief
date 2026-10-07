import unittest,copy,threading
from types import SimpleNamespace
from durable_ledger import DurableLedger,LedgerRefused
from endpoint import create_fixture_app
class CASCollection:
 def __init__(self):self.doc=None;self.lock=threading.Lock();self.calls=0
 def update_one(self,q,u,upsert=False):
  with self.lock:
   self.calls+=1
   if self.doc is None:self.doc={'_id':q['_id'],**copy.deepcopy(u['$setOnInsert'])}
   return SimpleNamespace(acknowledged=True)
 def find_one(self,q):
  with self.lock:self.calls+=1;return copy.deepcopy(self.doc)
 def replace_one(self,q,d):
  with self.lock:
   self.calls+=1;ok=all(self.doc.get(k)==v for k,v in q.items())
   if ok:self.doc=copy.deepcopy(d)
   return SimpleNamespace(acknowledged=True,matched_count=int(ok))
class Tests(unittest.TestCase):
 def setUp(self):self.c=CASCollection();self.l=DurableLedger(self.c,'geo108','a'*64);self.l.initialize()
 def test_reinstantiated_adapter_retains_active_replay(self):
  j=self.l.submit('n'*24,100);l2=DurableLedger(self.c,'geo108','a'*64);self.assertEqual(j,l2.submit('n'*24,110))
 def test_expiry_never_steals_or_heartbeats(self):
  j=self.l.submit('n'*24,100)
  with self.assertRaises(LedgerRefused):self.l.submit('q'*24,500)
  with self.assertRaises(LedgerRefused):self.l.heartbeat(j['key'],j['fence'],220)
 def test_parallel_multi_adapter_exclusion(self):
  out=[]
  def run(n):
   try:out.append(DurableLedger(self.c,'geo108','a'*64).submit(n*24,100))
   except LedgerRefused:out.append(None)
  ts=[threading.Thread(target=run,args=(n,))for n in 'np']
  for t in ts:t.start()
  for t in ts:t.join()
  self.assertEqual(sum(x is not None for x in out),1)
 def test_terminal_replay_and_fence_progression(self):
  j=self.l.submit('n'*24,100)
  for p in ('running','fetch_complete','prepare_complete','write_started','completed'):out=self.l.advance(j['key'],j['fence'],p,101,{})
  self.assertEqual(self.l.submit('n'*24,102)['phase'],'completed')
  self.assertGreater(self.l.submit('p'*24,102)['fence'],j['fence'])
 def test_uncertain_write_latches_profile(self):
  j=self.l.submit('n'*24,100)
  for p in ('running','fetch_complete','prepare_complete','write_started','uncertain_after_write'):self.l.advance(j['key'],j['fence'],p,101,{})
  with self.assertRaises(LedgerRefused):self.l.submit('q'*24,102)
  self.assertEqual(self.c.doc['active']['phase'],'uncertain_after_write')
 def test_wrong_fingerprint(self):
  with self.assertRaises(LedgerRefused):DurableLedger(self.c,'geo108','b'*64).submit('n'*24,100)
 def test_auth_precedes_ledger_and_malformed(self):
  app=create_fixture_app(self.l,'x'*48,lambda:100);c=app.test_client();before=self.c.calls
  r=c.post('/internal/collector108/jobs',data='{}',content_type='application/json');self.assertEqual(r.status_code,401);self.assertEqual(self.c.calls,before)
  h={'Authorization':'Bearer '+'x'*48}
  for body in ('{}','{"profile":"geo108","profile":"geo108"}','{"profile":"geo108","nonce":"nnnnnnnnnnnnnnnnnnnnnnnn","created_at":true}'):
   self.assertEqual(c.post('/internal/collector108/jobs',data=body,content_type='application/json',headers=h).status_code,400)
  self.assertEqual(self.c.calls,before)
 def test_endpoint_receipt_no_secret(self):
  c=create_fixture_app(self.l,'x'*48,lambda:100).test_client();r=c.post('/internal/collector108/jobs',json={'profile':'geo108','nonce':'n'*24,'created_at':100},headers={'Authorization':'Bearer '+'x'*48});self.assertEqual(r.status_code,202);self.assertEqual(set(r.json),{'job','phase','counts'})
 def test_status_auth_precedes_store_and_sanitizes(self):
  j=self.l.submit('n'*24,100);c=create_fixture_app(self.l,'x'*48,lambda:100).test_client();before=self.c.calls;path='/internal/collector108/jobs/'+j['key']
  self.assertEqual(c.get(path).status_code,401);self.assertEqual(self.c.calls,before)
  h={'Authorization':'Bearer '+'x'*48};r=c.get(path,headers=h);self.assertEqual(r.status_code,200);self.assertEqual(set(r.json),{'job','phase','counts'})
  self.c.doc['active']['counts']={'token':'private'};r=c.get(path,headers=h);self.assertEqual(r.status_code,503);self.assertNotIn('private',r.get_data(as_text=True))
 def test_nested_schema_and_backward_clock_refused(self):
  j=self.l.submit('n'*24,100)
  with self.assertRaises(LedgerRefused):self.l.advance(j['key'],j['fence'],'running',99,{})
  with self.assertRaises(LedgerRefused):self.l.heartbeat(j['key'],j['fence'],99)
  self.c.doc['active']['extra']='notallowed'
  with self.assertRaises(LedgerRefused):self.l.submit('n'*24,100)
 def test_harmless_health(self):
  c=create_fixture_app(self.l,'x'*48,lambda:100).test_client();before=self.c.calls;r=c.get('/health');self.assertEqual(r.status_code,200);self.assertFalse(r.json['collection']);self.assertEqual(self.c.calls,before)
 def test_bound_request(self):
  c=create_fixture_app(self.l,'x'*48,lambda:100).test_client();self.assertEqual(c.post('/internal/collector108/jobs',data='x'*5000,content_type='application/json',headers={'Authorization':'Bearer '+'x'*48}).status_code,413)
if __name__=='__main__':unittest.main(verbosity=2)
