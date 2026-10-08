import unittest,json,hashlib
from pathlib import Path
ROOT=Path(__file__).parents[1]
class Inventory(unittest.TestCase):
 def test_exact_test_paths(self):
  m=json.loads((ROOT/'tests/collection_outcomes/inventory.json').read_text())
  self.assertEqual(set(m['files']),{'tests/collection_outcomes/__init__.py','tests/collection_outcomes/test_callers.py','tests/collection_outcomes/test_status.py','tests/test_legacy_bulk_outcome.py'})
  self.assertEqual(m['excluded_exact'],['tests/collection_outcomes/inventory.json','tests/test_bulk147_inventory.py'])
  for p,h in m['files'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h)
