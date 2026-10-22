"""Source ledger consistency only; never treats source presence as live proof."""
import json,hashlib,unittest,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def test_current_source_hashes_and_complete_app_inventory(self):
  d=json.loads((ROOT/'integration/finder_changes_f13/PARITY-FUNCTIONS.json').read_text())
  for name,pin in d['source_file_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),pin,name)
  rows=[r for r in d['functions']if r['file']=='src/app.js'];self.assertEqual(len(rows),271);self.assertEqual(len({r['key']for r in rows}),271)
  self.assertEqual(sum(r['kind']=='declaration'and not r['scope']for r in rows),196)
  self.assertEqual(sum(r['source_relation']=='identical_function'for r in rows),261);self.assertEqual(sum(r['source_relation']=='modified_function'for r in rows),10)
  self.assertTrue(all(r['remaining_gate']and r['consumer']and not r['individual_runtime_certified']for r in rows))
 def test_no_missing_app_and_refactored_old_script_names_are_explicit(self):
  d=json.loads((ROOT/'integration/finder_changes_f13/PARITY-FUNCTIONS.json').read_text());rows=d['functions'];self.assertEqual(len(rows),367)
  absent=[r for r in rows if r['source_relation']=='absent'];self.assertEqual(len(absent),4);self.assertTrue(all(r['code_status']=='built_refactored_not_merged_active'for r in absent))
  self.assertFalse(any(r['file']=='src/app.js'and r['source_relation']=='absent'for r in rows))
 def test_app_counts_block_matches_independent_literals_and_rows(self):
  d=json.loads((ROOT/'integration/finder_changes_f13/PARITY-FUNCTIONS.json').read_text())
  self.assertEqual(d['app_counts'],dict(all_named_and_bound=271,top_level_declarations=196,top_level_bindings=10,nested_bindings=65))
  rows=[r for r in d['functions']if r['file']=='src/app.js']
  self.assertEqual(sum(r['kind']=='function_binding'and not r['scope']for r in rows),10)
  self.assertEqual(sum(r['kind']=='function_binding'and bool(r['scope'])for r in rows),65)
 def test_csv_exact_fields_and_all_rows_match_json_ledger(self):
  rows=json.loads((ROOT/'integration/finder_changes_f13/PARITY-FUNCTIONS.json').read_text())['functions']
  with (ROOT/'integration/finder_changes_f13/PARITY-FUNCTIONS.csv').open(newline='')as stream:
   reader=csv.DictReader(stream);self.assertEqual(reader.fieldnames,list(rows[0]));actual=list(reader)
  expected=[{k:(''if v is None else str(v))for k,v in row.items()}for row in rows]
  self.assertEqual(actual,expected);self.assertEqual(len(actual),367)
