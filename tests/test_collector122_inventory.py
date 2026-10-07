import unittest,importlib,json,hashlib
from scripts.package_manifest import ROOT,commit_files
class Inventory(unittest.TestCase):
 def test_package_imports(self):
  for name in ('collector122_prep','collector122_prep.packing','collector122_prep.receipt_state'):self.assertIsNotNone(importlib.import_module(name))
 def test_packaged_paths_and_hashes(self):
  m=json.loads((ROOT/'staging-manifest.json').read_text());actual={str(p.relative_to(ROOT))for p in commit_files()};rows={r['path']:r for r in m['files']}
  expected={'collector122_prep/__init__.py','collector122_prep/packing.py','collector122_prep/receipt_state.py','collector122_prep/TELEGRAM-SAFE-PACKING-DESIGN.md'}
  self.assertTrue(expected<=actual);self.assertTrue(expected<=set(rows))
  for name in expected:self.assertEqual(rows[name]['sha256'],hashlib.sha256((ROOT/name).read_bytes()).hexdigest())
