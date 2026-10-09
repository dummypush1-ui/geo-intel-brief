import unittest,subprocess
from pathlib import Path
class Cors(unittest.TestCase):
 def test_policy(self):
  r=subprocess.run(['node','tests/proxy_runtime/test_cors190.cjs'],capture_output=True,text=True,timeout=15);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
 def test_no_wildcard_proxy_paths_and_early_guard(self):
  s=Path('proxy.js').read_text();self.assertNotIn("'Access-Control-Allow-Origin': '*'",s);self.assertNotIn("setHeader('Access-Control-Allow-Origin', '*')",s);self.assertLess(s.index('corsPolicy.check(req,res)'),s.index("const path = req.url.split('?')[0]"));self.assertIn("process.env.PROXY_ALLOWED_ORIGINS || ''",s)
 def test_existing_proxy_fake_fixtures(self):
  for f in ['tests/proxy_runtime/test_identity_proxy.cjs','tests/proxy_runtime/test_ais_proxy.cjs']:
   r=subprocess.run(['node',f],capture_output=True,text=True,timeout=15);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
