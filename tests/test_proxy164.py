"""Node identity and real-handler integration in a fake network only."""
import subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ProxyIdentityTests(unittest.TestCase):
 def test_pure_identity(self):
  subprocess.run(['node','tests/proxy_runtime/test_identity.cjs'],cwd=ROOT,check=True,timeout=20)
 def test_fake_server_budget(self):
  subprocess.run(['node','tests/proxy_runtime/test_identity_proxy.cjs'],cwd=ROOT,check=True,timeout=20)
