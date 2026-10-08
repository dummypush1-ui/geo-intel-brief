import hashlib,json,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def test_exact_inventory(self):
  m=json.loads((ROOT/'updater_runtime/sanctions152-inventory.json').read_text())
  for p,h in m.items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h,p)
 def test_supplied_synthetic_policy(self):
  r=subprocess.run(['node','tests/updater_runtime/test_sanctions_policy.mjs'],cwd=ROOT,capture_output=True,text=True,timeout=20)
  self.assertEqual(r.returncode,0,r.stderr);self.assertIn('cases pass',r.stdout)
