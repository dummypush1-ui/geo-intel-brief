from scripts.doc_lookup import source_bytes, source_text
import ast,json,unittest,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class PreservationTests(unittest.TestCase):
 def test_reviewed_file_hashes(self):
  m=json.loads((ROOT/'preservation-manifest.json').read_text())
  for row in m['source_files']:
   self.assertEqual(hashlib.sha256(source_bytes(ROOT/row['path'])).hexdigest(),row['sha256'],row['path'])
 def test_classifier_dedupe_extract_unchanged(self):
  m=json.loads((ROOT/'preservation-manifest.json').read_text())
  for row in m['source_files']:
   if row['source_repo']=='geonews' and row['source_path'] in ['processing/dedupe.py','processing/extract.py']:
    self.assertEqual(row['source_sha256'],row['sha256'],row['path'])
 def test_classifier_intentional_reviewed_change(self):
  m=json.loads((ROOT/'preservation-manifest.json').read_text())
  row=next(r for r in m['source_files'] if r['path']=='intelligence/geo/processing/classifier.py')
  self.assertEqual(row['source_sha256'],'445842f362bca71455f562e6d405e6ee860deddb88bab64f56f522e7b67073f9')
  self.assertEqual(row['sha256'],'ee01615307db03b7b511b5de19999a12e49c3302f04f37b024fd550338bafbb0')
  self.assertTrue(any('classifier146' in c for c in row['changes']))
 def test_collection_off_and_no_migration(self):
  m=json.loads((ROOT/'integration/cross-connections.json').read_text())
  self.assertFalse(m['collection_enabled']);self.assertFalse(m['underlying_infrastructure']['migration'])
 def test_all_python_syntax(self):
  for p in (ROOT/'intelligence').rglob('*.py'):ast.parse(p.read_text())
