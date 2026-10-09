# 228: reviewed popup CSP repair and local generated snapshot pins.
import unittest,subprocess,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def test_client_state_machine(self):
  p=subprocess.run(['node',str(ROOT/'tests/finder198_client_test.mjs')],capture_output=True,text=True,timeout=10);self.assertEqual(p.returncode,0,p.stderr)
 def test_inert_no_backend_secret_or_storage(self):
  for name in ('client.mjs','panel.mjs'):
   s=(ROOT/'integration/finder198_ui'/name).read_text()
   for value in ('FINDER_PROXY_SECRET','x-app-token','hsn-ai-proxy','localStorage','sessionStorage'):self.assertNotIn(value,s)
  self.assertNotIn('finder198_ui',(ROOT/'production_entry.py').read_text())
 def test_no_signup_reset_serverroutes(self):
  s=(ROOT/'integration/finder198_ui/client.mjs').read_text()
  self.assertNotIn('/account/signup',s);self.assertNotIn('/account/reset',s)
 def test_original_ownkey_files_unchanged(self):
  # Reviewed base bytes, not a claim of live behavior.
  expected={'src/app.js': 'bcd406d75b27b053fc5716d141ca278932115f14e39eca74d19a2284fc59d313', 'offline.html': 'b55d6b0cf2be2ff3ddf366c4afa23d452367265ef2e85a31b9a4fb6cd411b486', 'index.html': 'e2ed3326bfb8ca0805677e026438ff412611eef712526dea17b49d6c7fa30625'}
  for path,digest in expected.items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest,path)
 def test_real_wire_shapes_and_handler_label(self):
  from tests.test_finder198c import Tests as ServerFixture
  from integration.finder198_transport import FixedProxyTransport
  from unittest.mock import patch
  t=ServerFixture();t.setUp()
  self.assertTrue(t.app.route_contract['broker_transport']);self.assertFalse(t.app.route_contract['ui'])
  pre=t.client.get('/account/preauth',base_url='https://geo.example');
  # Match the source fixture's exact configured origin, not a caller override.
  from tests.test_finder198a import O,PW
  pre=t.client.get('/account/preauth',base_url=O);self.assertIsInstance(pre.json['csrf'],str)
  login=t.client.post('/account/login',base_url=O,json={'username':'alice','password':PW,'csrf':pre.json['csrf']},headers={'Origin':O});self.assertEqual(login.status_code,200);self.assertNotIn('session_token',login.json)
  who=t.client.get('/account/whoami',base_url=O);self.assertEqual(who.json['username'],'alice');self.assertIsInstance(who.json['csrf'],str)
  with patch.object(FixedProxyTransport,'execute',return_value={'status':200,'body':b'{"vessels":[]}'}):self.assertEqual(t.post({'nonce':'d'*24,'port':'ALL'},who.json['csrf']).status_code,200)
  logout=t.client.post('/account/logout',base_url=O,json={'csrf':who.json['csrf']},headers={'Origin':O});self.assertEqual(logout.status_code,200);self.assertEqual(t.client.get('/account/whoami',base_url=O).status_code,401)
