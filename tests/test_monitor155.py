from scripts.doc_lookup import source_bytes
import hashlib,json,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def test_inventory(self):
  for p,h in json.loads((ROOT/'updater_runtime/monitor155-inventory.json').read_text()).items():self.assertEqual(hashlib.sha256(source_bytes(ROOT/p)).hexdigest(),h,p)
 def test_issue_health(self):
  r=subprocess.run(['node','tests/updater_runtime/test_issue_health.mjs'],cwd=ROOT,capture_output=True,text=True,timeout=20);self.assertEqual(r.returncode,0,r.stderr)
 def test_pending_monitor(self):
  r=subprocess.run(['node','tests/updater_runtime/test_monitor_pending.mjs'],cwd=ROOT,capture_output=True,text=True,timeout=20);self.assertEqual(r.returncode,0,r.stderr)
