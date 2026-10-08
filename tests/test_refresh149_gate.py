import unittest,subprocess
from pathlib import Path
class RefreshGate(unittest.TestCase):
 def test_mocked_refresh_and_isolated_build(self):
  root=Path(__file__).resolve().parents[1]
  result=subprocess.run(['node','tests/updater_runtime/test_refresh_bundle.mjs'],cwd=root,capture_output=True,text=True,timeout=45)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)

 def test_missing_checkout_preflight(self):
  root=Path(__file__).resolve().parents[1]
  result=subprocess.run(['node','tests/updater_runtime/test_refresh_preflight.mjs'],cwd=root,capture_output=True,text=True,timeout=10)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)
