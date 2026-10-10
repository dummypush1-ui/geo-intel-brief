from scripts.doc_lookup import documentation
import json,unittest
from pathlib import Path
from scripts.audit_connections import inventory
ROOT=Path(__file__).resolve().parents[1]
class FileAuditTests(unittest.TestCase):
 def test_all_preserved_files_in_map(self):
  d=inventory();paths={r['path'] for r in d['files']}|set(documentation(ROOT))
  for r in json.loads((ROOT/'preservation-manifest.json').read_text())['source_files']:self.assertIn(r['path'],paths)
 def test_finder_imports_resolved(self):
  rows={r['path']:r for r in inventory()['files']}
  self.assertIn('src/data.ts',rows['src/app.js']['static_file_edges']);self.assertIn('src/datachunk0.ts',rows['src/data.ts']['static_file_edges'])
 def test_no_internal_missing_import(self):
  for r in inventory()['files']:self.assertEqual(r['unresolved_internal_imports'],[],r['path'])
