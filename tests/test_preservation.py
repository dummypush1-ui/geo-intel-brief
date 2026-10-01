import ast,json,unittest,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class PreservationTests(unittest.TestCase):
 def test_reviewed_file_hashes(self):
  m=json.loads((ROOT/'preservation-manifest.json').read_text())
  for row in m['source_files']:
   self.assertEqual(hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest(),row['sha256'],row['path'])
 def test_classifier_dedupe_extract_unchanged(self):
  m=json.loads((ROOT/'preservation-manifest.json').read_text())
  for row in m['source_files']:
   if row['source_repo']=='geonews' and row['source_path'] in ['processing/classifier.py','processing/dedupe.py','processing/extract.py']:
    self.assertEqual(row['source_sha256'],row['sha256'],row['path'])
 def test_collection_off_and_no_migration(self):
  m=json.loads((ROOT/'integration/cross-connections.json').read_text())
  self.assertFalse(m['collection_enabled']);self.assertFalse(m['underlying_infrastructure']['migration'])
 def test_all_python_syntax(self):
  for p in (ROOT/'intelligence').rglob('*.py'):ast.parse(p.read_text())
