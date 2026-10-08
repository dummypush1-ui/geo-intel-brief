import hashlib,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ClassifierInventory(unittest.TestCase):
 def test_exact_paths_and_hashes(self):
  m=json.loads((ROOT/'integration/text_matching/inventory.json').read_text())
  self.assertEqual(set(m['files']),{'integration/text_matching/matcher.py','tests/text_matching/test_matching.py','tests/text_matching/__init__.py'})
  self.assertEqual(m['excluded_exact'],['integration/text_matching/inventory.json','tests/test_classifier146_inventory.py'])
  for f,h in m['files'].items():self.assertEqual(hashlib.sha256((ROOT/f).read_bytes()).hexdigest(),h)
 def test_live_effects_not_enabled(self):
  m=json.loads((ROOT/'integration/cross-connections.json').read_text());self.assertFalse(m['collection_enabled'])
