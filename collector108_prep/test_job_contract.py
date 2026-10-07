import unittest,threading
from job_contract import FixtureLedger,Refused
class ContractTests(unittest.TestCase):
 def setUp(self):self.ledger=FixtureLedger('fixture-'+('x'*48),'geo108');self.h='Bearer fixture-'+('x'*48);self.b={'profile':'geo108','nonce':'n'*24,'created_at':100}
 def submit(self):return self.ledger.submit(self.h,self.b,100)[0]
 def test_auth_never_optional(self):
  for h in (None,'','Bearer wrong','key=anything',{'token':'x'}):
   with self.assertRaises(Refused):self.ledger.submit(h,self.b,100)
 def test_reject_extra_fields_and_clock(self):
  for k in ('uri','source_url','collection','send_to','callback'):
   with self.assertRaises(Refused):self.ledger.submit(self.h,dict(self.b,**{k:'anything'}),100)
  with self.assertRaises(Refused):self.ledger.submit(self.h,self.b,401)
 def test_nonce_idempotent_no_reexecute(self):
  k=self.submit();self.assertEqual(k,self.submit());f=self.ledger.claim(k,100)
  self.assertEqual(self.ledger.submit(self.h,self.b,100)[1]['phase'],'running')
  with self.assertRaises(Refused):self.ledger.claim(k,100)
 def test_single_profile_parallel_claim(self):
  k=self.submit();self.b['nonce']='z'*24;k2=self.submit();results=[]
  def run(key):
   try:results.append(self.ledger.claim(key,100))
   except Refused:results.append('refused')
  ts=[threading.Thread(target=run,args=(x,))for x in (k,k2)]
  for t in ts:t.start()
  for t in ts:t.join()
  self.assertEqual(results.count('refused'),1)
 def test_transition_sequence_and_aggregate_only(self):
  k=self.submit();f=self.ledger.claim(k,100)
  with self.assertRaises(Refused):self.ledger.transition(k,f,'write_started',101,{})
  with self.assertRaises(Refused):self.ledger.transition(k,f,'fetch_complete',101,{'uri':1})
  with self.assertRaises(Refused):self.ledger.transition(k,f,'fetch_complete',101,{'fetched':True})
  for phase in ('fetch_complete','prepare_complete','write_started','completed'):self.ledger.transition(k,f,phase,101,{'attempted':1})
  self.assertIsNone(self.ledger.active)
 def test_expired_lease_never_frees_claim(self):
  k=self.submit();f=self.ledger.claim(k,100);self.ledger.reconcile_expired(k,220);self.assertEqual(self.ledger.active,k)
  with self.assertRaises(Refused):self.ledger.transition(k,f,'fetch_complete',221,{})
  self.b['nonce']='q'*24;k2=self.submit()
  with self.assertRaises(Refused):self.ledger.claim(k2,221)
 def test_write_uncertainty_not_safe_retry(self):
  k=self.submit();f=self.ledger.claim(k,100)
  for phase in ('fetch_complete','prepare_complete','write_started'):self.ledger.transition(k,f,phase,101,{})
  self.assertEqual(self.ledger.reconcile_expired(k,220)['phase'],'uncertain_after_write')
  with self.assertRaises(Refused):self.ledger.claim(k,221)
 def test_explicit_uncertainty_keeps_profile_ownership(self):
  k=self.submit();f=self.ledger.claim(k,100)
  for phase in ('fetch_complete','prepare_complete','write_started','uncertain_after_write'):self.ledger.transition(k,f,phase,101,{})
  self.assertEqual(self.ledger.active,k)
  self.b['nonce']='u'*24;k2=self.submit()
  with self.assertRaises(Refused):self.ledger.claim(k2,102)
  with self.assertRaises(Refused):self.ledger.claim(k,102)
 def test_stale_fence_no_mutation(self):
  k=self.submit();f=self.ledger.claim(k,100)
  with self.assertRaises(Refused):self.ledger.transition(k,f+1,'fetch_complete',101,{})
  self.assertEqual(self.ledger.jobs[k]['phase'],'running')
if __name__=='__main__':unittest.main(verbosity=2)
