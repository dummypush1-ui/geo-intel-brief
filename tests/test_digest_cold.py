import subprocess,sys,unittest,os
from pathlib import Path
class ColdPreviewTests(unittest.TestCase):
 def test_fresh_process_before_import(self):
  root=Path(__file__).resolve().parents[1]
  r=subprocess.run([sys.executable,str(root/'tests/digest_cold_probe.py')],cwd=root,env={**os.environ,'PYTHONPATH':str(root)},capture_output=True,text=True,timeout=25)
  self.assertEqual(r.returncode,0,r.stderr+r.stdout);self.assertIn('"original_module_imports": 0',r.stdout)
