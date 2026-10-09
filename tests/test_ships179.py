import unittest,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def test_read_quota_cache(self):subprocess.run(['node','tests/proxy_runtime/test_ships179.cjs'],cwd=ROOT,check=True,timeout=20)
 def test_browser_polling_policy(self):subprocess.run(['node','tests/proxy_runtime/test_ships_ui179.cjs'],cwd=ROOT,check=True,timeout=20)
 def test_identity_budgets_separate(self):subprocess.run(['node','tests/proxy_runtime/test_identity_proxy.cjs'],cwd=ROOT,check=True,timeout=20)
