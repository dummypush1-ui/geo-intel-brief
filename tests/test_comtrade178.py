import unittest,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def run_script(self,name):
  r=subprocess.run(['node','tests/comtrade_runtime/'+name],cwd=ROOT,capture_output=True,text=True,timeout=20);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
 def test_dry_bytes_and_network(self):self.run_script('test_dry178.mjs')
 def test_publication_fences_and_resume(self):self.run_script('test_publication178.mjs')
 def test_automate_bake_errors_not_skip(self):
  s=(ROOT/'automate.mjs').read_text();self.assertIn("throw new Error(n+' incomplete; last-good output retained')",s);self.assertNotIn("await step('comtrade-",s)
 def test_syntax_all(self):
  for name in ['market','marketx','partners','mirror']:
   r=subprocess.run(['node','--check','comtrade-'+name+'.mjs'],cwd=ROOT,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
