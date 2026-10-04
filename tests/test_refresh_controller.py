import subprocess,unittest
from pathlib import Path
class RefreshControllerTests(unittest.TestCase):
 def test_dormant_original_news_timer(self):
  root=Path(__file__).resolve().parents[1];r=subprocess.run(['node','tests/news_refresh_test.mjs'],cwd=root,capture_output=True,text=True,timeout=15);self.assertEqual(r.returncode,0,r.stderr+r.stdout)
