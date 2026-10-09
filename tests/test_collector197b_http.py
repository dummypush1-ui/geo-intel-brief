import unittest
from integration.collector197_http import build_collector_app,HTTPRefused
from tests.test_collector197b_preflight import Client
class Tests(unittest.TestCase):
 def values(self):return {'COLLECTION_ENABLED':'true','GEO_WRITER_MONGODB_URI':'fixture-private','COLLECTOR_TRIGGER_SECRET':'x'*48,'COLLECTOR_PROFILE_FINGERPRINT':'a'*64}
 def app(self):
  c=Client();c.close=lambda:None
  return build_collector_app(self.values(),runtime_preflight=lambda:dict.fromkeys(('runtime_bwrap','free_capacity','source_catalog','owner_activation'),True),client_factory=lambda uri:c,clock=lambda:100)
 def test_off_no_clients_or_proof(self):
  def no(*a):raise AssertionError()
  app=build_collector_app({},client_factory=no,runtime_preflight=no)
  self.assertFalse(app.test_client().get('/health').json['ready'])
  self.assertEqual(app.test_client().post('/api/collect').status_code,503)
 def test_flags_before_client(self):
  for flag in ('ENABLE_FULL_TEXT','ENABLE_GNEWS','ENABLE_TELEGRAM_BACKUP'):
   v=self.values();v[flag]='true'
   with self.assertRaises(ValueError):build_collector_app(v,client_factory=lambda uri:(_ for _ in ()).throw(AssertionError()))
 def test_missing_runtime_before_client(self):
  with self.assertRaises(HTTPRefused):build_collector_app(self.values(),client_factory=lambda uri:(_ for _ in ()).throw(AssertionError()))
 def test_auth_before_ledger(self):
  app=self.app();client=app.test_client();r=client.post('/api/collect',data='{}',content_type='application/json')
  self.assertEqual(r.status_code,401)
 def test_origin_query_closed_routes(self):
  c=self.app().test_client();h={'Authorization':'Bearer '+'x'*48}
  self.assertEqual(c.post('/api/collect',headers={**h,'Origin':'https://example.com'}).status_code,400)
  self.assertEqual(c.get('/unknown',headers=h).status_code,404)
  self.assertEqual(c.get('/api/collect/status/x?key=bad',headers=h).status_code,400)
 def test_strict_json_before_work(self):
  c=self.app().test_client();h={'Authorization':'Bearer '+'x'*48}
  for s in ('{}','{"nonce":"a","timestamp":true}','{"nonce":"a","timestamp":100,"timestamp":100}'):
   self.assertEqual(c.post('/api/collect',data=s,content_type='application/json',headers=h).status_code,400)
 def test_no_public_static_or_browser(self):
  c=self.app().test_client()
  self.assertEqual(c.get('/static/test').status_code,401)
  self.assertEqual(c.get('/api/collect/status/a').status_code,401)
