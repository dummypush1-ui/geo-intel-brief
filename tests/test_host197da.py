import unittest,time,sys
from unittest.mock import patch
from integration.collector197_host_probe import create_host_probe,host_facts,validate_facts,isolation_probe,worker_timeout,memory_available
class Tests(unittest.TestCase):
 def test_default_off_no_probe(self):
  app=create_host_probe({},probe=lambda:(_ for _ in ()).throw(AssertionError()))
  self.assertEqual(app.test_client().get('/api/collector-host-probe').status_code,503)
 def test_auth_before_probe(self):
  app=create_host_probe({'COLLECTOR_HOST_PROBE_ENABLED':'true','COLLECTOR_HOST_PROBE_SECRET':'x'*48},probe=lambda:(_ for _ in ()).throw(AssertionError()))
  self.assertEqual(app.test_client().get('/api/collector-host-probe').status_code,401)
 def test_origin_query_no_probe(self):
  c=create_host_probe({'COLLECTOR_HOST_PROBE_ENABLED':'true','COLLECTOR_HOST_PROBE_SECRET':'x'*48},probe=lambda:(_ for _ in ()).throw(AssertionError())).test_client()
  h={'Authorization':'Bearer '+'x'*48}
  self.assertEqual(c.get('/api/collector-host-probe',headers={**h,'Origin':'https://example.com'}).status_code,400)
  self.assertEqual(c.get('/api/collector-host-probe?debug=1',headers=h).status_code,400)
 def test_real_nested_bwrap_pid_namespace(self):
  self.assertTrue(isolation_probe());self.assertTrue(isolation_probe(True))
 def test_schema_only_no_secret(self):
  facts=host_facts();self.assertEqual(validate_facts(facts),facts)
  self.assertFalse(facts['activation_authority']);self.assertFalse(facts['runtime_evidence_provider'])
  facts['secret']='never'
  with self.assertRaises(ValueError):validate_facts(facts)
 def test_unknown_wsgi_not_environment_guess(self):
  with patch.dict('os.environ',{'GUNICORN_CMD_ARGS':'--timeout 300 --workers 1'}):
   self.assertEqual(worker_timeout()['state'],'unavailable')
 def test_probe_timeout_kills(self):
  with patch('integration.collector197_host_probe._isolation_command',return_value=[sys.executable,'-c','import time;time.sleep(60)']):
   start=time.monotonic();self.assertFalse(isolation_probe());self.assertLess(time.monotonic()-start,4)
 def test_public_mount_preserves_health(self):
  from production_entry import build_production_app
  from flask import Flask
  a=Flask('hostprobe_fixture');a.add_url_rule('/health',view_func=lambda:'publichealth')
  app=build_production_app({'COLLECTOR_HOST_PROBE_ENABLED':'true','COLLECTOR_HOST_PROBE_SECRET':'x'*48},lambda e:a)
  c=app.test_client();self.assertEqual(c.get('/health').data,b'publichealth');self.assertEqual(c.get('/api/collector-host-probe').status_code,401)
 def test_reply_header_and_no_extra_output(self):
  c=create_host_probe({'COLLECTOR_HOST_PROBE_ENABLED':'true','COLLECTOR_HOST_PROBE_SECRET':'x'*48}).test_client()
  r=c.get('/api/collector-host-probe',headers={'Authorization':'Bearer '+'x'*48})
  self.assertEqual(r.status_code,200);self.assertEqual(r.headers['Cache-Control'],'no-store')
  self.assertNotIn('secret',r.json)
