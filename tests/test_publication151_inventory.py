import unittest,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Inventory(unittest.TestCase):
 def test_exact_paths_hashes(self):
  m=json.loads((ROOT/'integration/publication_dates/inventory.json').read_text())
  self.assertEqual(set(m['files']),{'integration/publication_dates/policy.py','integration/publication_dates/CONTRACT.md','tests/publication_dates/test_policy.py','tests/publication_dates/__init__.py'})
  self.assertEqual(m['excluded_exact'],['integration/publication_dates/inventory.json','tests/test_publication151_inventory.py'])
  for p,h in m['files'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h)
