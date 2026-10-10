from scripts.doc_lookup import source_bytes
import hashlib,json,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def test_inventory(self):
  for p,h in json.loads((ROOT/'updater_runtime/gst154-inventory.json').read_text()).items():self.assertEqual(hashlib.sha256(source_bytes(ROOT/p)).hexdigest(),h,p)
 def test_evidence_and_pdf(self):
  r=subprocess.run(['node','tests/updater_runtime/test_gst_grounding.mjs'],cwd=ROOT,capture_output=True,text=True,timeout=20);self.assertEqual(r.returncode,0,r.stderr)
