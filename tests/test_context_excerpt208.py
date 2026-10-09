import hashlib
import subprocess
import unittest
from pathlib import Path
from integration.news_api import create_app

ROOT=Path(__file__).resolve().parents[1]
class Context208(unittest.TestCase):
 def test_node_boundaries(self):
  r=subprocess.run(['node',str(ROOT/'tests/context_excerpt208_test.mjs')],capture_output=True,text=True,timeout=10)
  self.assertEqual(r.returncode,0,r.stdout+r.stderr)
 def test_private_asset_and_parent_notice(self):
  self.assertEqual(create_app().test_client().get('/workspace/assets/context_excerpt208.js').status_code,403)
  c=create_app(authorize=lambda req:True).test_client()
  r=c.get('/workspace/assets/context_excerpt208.js');self.assertEqual(r.status_code,200);r.close()
  html=c.get('/workspace').get_data(as_text=True)
  self.assertIn('View description excerpt used for matching',html)
  self.assertIn('Matching may miss details outside the excerpt.',html)
 def test_preserved_finder_bytes(self):
  self.assertEqual(hashlib.sha256((ROOT/'data.d6d1b417562b.js').read_bytes()).hexdigest(),'d6d1b417562bad99e7b434605d63966772749d573375fb10d74ee52cb6bb82f6')
