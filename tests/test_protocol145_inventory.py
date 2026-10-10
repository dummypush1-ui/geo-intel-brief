from scripts.doc_lookup import source_bytes, source_text
import unittest,json,hashlib,ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Inventory(unittest.TestCase):
 def test_exact_paths_hashes(self):
  m=json.loads((ROOT/'integration/collection_receipts/inventory.json').read_text())
  self.assertEqual(set(m['files']),{'integration/collection_receipts/protocol.py','integration/collection_receipts/CONTRACT.md','tests/collection_receipts/test_protocol.py','tests/collection_receipts/__init__.py'})
  self.assertEqual(m['excluded_exact'],['integration/collection_receipts/inventory.json','tests/test_protocol145_inventory.py'])
  for p,h in m['files'].items():self.assertEqual(hashlib.sha256(source_bytes(ROOT/p)).hexdigest(),h)
 def test_inert_import_surface(self):
  t=ast.parse((ROOT/'integration/collection_receipts/protocol.py').read_text())
  imports={n.module for n in ast.walk(t)if isinstance(n,ast.ImportFrom)}|{a.name for n in ast.walk(t)if isinstance(n,ast.Import)for a in n.names}
  self.assertEqual(imports,{'copy','hashlib','json','re'})
