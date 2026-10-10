# 231: CSS-only weather wrapping, derived snapshot pins.
"""229 source pins plus opt-in simulated browser test, not provider availability."""
import hashlib,importlib.util,os,shutil,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class FinderBrowser229(unittest.TestCase):
 def test_exact_source_and_own_key_seams(self):
  pins={'src/app.js':'bcd406d75b27b053fc5716d141ca278932115f14e39eca74d19a2284fc59d313','index.html':'8e1ce9c7fa5da880085afb2b8a20e6fbc3195d8b24f4ffdde4bee09c787d0967'}
  for name,sha in pins.items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),sha)
  text=(ROOT/'src/app.js').read_text()
  start=text.index('const ownProvider = () => {');end=text.index('\n};',start)+3
  self.assertEqual(hashlib.sha256(text[start:end].encode()).hexdigest(),'43bc397649b5d507858b9633f59b58815ae363f3ee7ac414ea39060b619b217e')
  start=text.index('async function aiReportText(');end=text.index('/* ---------- small helpers ---------- */',start)
  self.assertEqual(hashlib.sha256(text[start:end].encode()).hexdigest(),'95dc3562eaa83a65c957fb38f6019c9e786db3592686e4d5d288c67f9b37ee11')
  for name in ['AI_PROXY_URL','BUILTIN_GEMINI_KEYS','BUILTIN_GROQ_KEYS','BUILTIN_MISTRAL_KEYS','BUILTIN_NVIDIA_KEYS']:self.assertIn("const "+name+" = '';",text)
  # Shared rescue code exists but all its configuration is empty. Not removed code.
 def test_fixture_scope_logs_and_no_production_patch(self):
  text=(ROOT/'tests/browser_feature_finder.py').read_text()
  self.assertIn('SIMULATED TEST TEXT',text);self.assertIn("u.path",text)
  for token in ['hsn-ai-proxy.onrender.com','tplNarrative=','wait_for_timeout','print(r.request.headers','post_data_json']:self.assertNotIn(token,text)
  self.assertNotRegex(text,r'AI_PROXY_URL\s*=(?!=)')
  self.assertIn("u.hostname!='api.mistral.ai' or u.path!='/v1/chat/completions'",text)
 def test_browser_opt_in(self):
  if os.environ.get('RUN_FINDER229_BROWSER')!='1':self.skipTest('Opt-in simulated browser: RUN_FINDER229_BROWSER=1 required; no browser PASS implied')
  if not Path('/usr/bin/google-chrome').exists() or not shutil.which('pdftotext') or not shutil.which('pdftoppm') or importlib.util.find_spec('playwright') is None:self.skipTest('Chromium/Playwright/PDF tools missing; simulated browser NOT run')
  run=subprocess.run([sys.executable,'tests/browser_feature_finder.py'],cwd=ROOT,capture_output=True,text=True,timeout=120)
  self.assertEqual(run.returncode,0,run.stdout+run.stderr)
