import unittest
from collector109_prep.fixture_support import CASCollection
from datetime import datetime,timezone
def row():return {'title':'Trade tariff order','url':'https://example.com/news','source':'Fixture','summary':'Supply chain tariff '+'x'*400,'published':datetime(2026,1,1,tzinfo=timezone.utc),'credibility':'HIGH'}
from collector108_prep.durable_ledger import DurableLedger
from collector109_prep.checkpoint import FixtureCheckpoints
from .endpoint_drive import FixtureService,create_drive_fixture_app

class Tests(unittest.TestCase):
 def setUp(self):
  self.c=CASCollection();self.l=DurableLedger(self.c,'geo108','a'*64);self.l.initialize();self.j=self.l.submit('n'*24,100)
  self.s=FixtureService(self.l,FixtureCheckpoints(),lambda:101)
  self.client=create_drive_fixture_app(self.s,'x'*48).test_client();self.h={'Authorization':'Bearer '+'x'*48};self.path='/internal/collector109/jobs/'+self.j['key']
 def test_auth_before_store(self):
  before=self.c.calls
  self.assertEqual(self.client.post(self.path+'/drive',json={}).status_code,401)
  self.assertEqual(self.client.get(self.path).status_code,401)
  self.assertEqual(self.c.calls,before)
 def test_no_input_registration_refuses(self):
  self.assertEqual(self.client.post(self.path+'/drive',json={},headers=self.h).status_code,409)
  self.assertEqual(self.l.status(self.j['key'])['phase'],'accepted')
 def test_registered_drive_holds_honestly(self):
  self.s.register(self.j['key'],self.j['fence'],[row()],['TRADE'],.85)
  r=self.client.post(self.path+'/drive',json={},headers=self.h)
  self.assertEqual(r.status_code,200);self.assertEqual(r.json['state'],'held_before_write')
  status=self.client.get(self.path,headers=self.h)
  self.assertEqual(status.json['phase'],'prepare_complete');self.assertEqual(set(status.json),{'job','phase','counts'})
 def test_payloads_no_ledger_access(self):
  before=self.c.calls
  for body in ('[]','null','{"writer":true}','{"fence":1}','{"x":1,"x":2}','{"candidates":[]}', '{'):
   r=self.client.post(self.path+'/drive',data=body,content_type='application/json',headers=self.h)
   self.assertEqual(r.status_code,400,body)
  self.assertEqual(self.c.calls,before)
 def test_size_and_queries(self):
  self.assertEqual(self.client.post(self.path+'/drive',data='x'*5000,content_type='application/json',headers=self.h).status_code,413)
  self.assertEqual(self.client.post(self.path+'/drive?x=1',json={},headers=self.h).status_code,400)
 def test_new_process_registry_not_recovery(self):
  self.s.register(self.j['key'],self.j['fence'],[row()],['TRADE'],.85)
  fresh=FixtureService(self.l,self.s.checkpoints,lambda:101)
  c=create_drive_fixture_app(fresh,'x'*48).test_client()
  self.assertEqual(c.post(self.path+'/drive',json={},headers=self.h).status_code,409)

if __name__=='__main__':unittest.main(verbosity=2)
