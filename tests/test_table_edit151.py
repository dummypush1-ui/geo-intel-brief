import unittest,subprocess
from pathlib import Path
class TableEdit(unittest.TestCase):
 def test_closed_pure_tables(self):
  root=Path(__file__).resolve().parents[1]
  r=subprocess.run(['node','tests/updater_runtime/test_table_edit.mjs'],cwd=root,capture_output=True,text=True,timeout=15)
  self.assertEqual(r.returncode,0,r.stdout+r.stderr)
 def test_draft_validation_reject_continues(self):
  root=Path(__file__).resolve().parents[1]
  r=subprocess.run(['node','tests/updater_runtime/test_draft_reject.mjs'],cwd=root,capture_output=True,text=True,timeout=15)
  self.assertEqual(r.returncode,0,r.stdout+r.stderr)
