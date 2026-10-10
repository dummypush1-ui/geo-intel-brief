"""231 scoped CSS regression and opt-in local SIMULATED browser."""
import hashlib,importlib.util,os,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Weather231(unittest.TestCase):
 def test_scoped_style_and_markup(self):
  css=(ROOT/'src/style.css').read_text();section=css[css.index('/* 231: only'):]
  self.assertEqual(section.count('#portwx-pick + .report-table-wrap .report-table'),3)
  for token in ['min-width: 0','table-layout: fixed','overflow-wrap: anywhere','td:first-child { width: 40%; overflow-wrap: normal;']:self.assertIn(token,section)
  for token in ['display: none','text-overflow','font-size','max-height']:self.assertNotIn(token,section)
  self.assertIn('.report-table { border-collapse: collapse; min-width: 680px;',css)
  app=(ROOT/'src/app.js').read_bytes();self.assertEqual(hashlib.sha256(app).hexdigest(),'bcd406d75b27b053fc5716d141ca278932115f14e39eca74d19a2284fc59d313')
  text=app.decode();self.assertIn("'</option>').join('') + '</select>' +\n    body",text)
  for path,sha in [('index.html','8e1ce9c7fa5da880085afb2b8a20e6fbc3195d8b24f4ffdde4bee09c787d0967'),('offline.html','0e2e85ea54f276c3c50984e8c26b9400e1deee9f4b8a035a8866e56c2455b65b'),('sw.js','477ca5f0aa5b784932e11f3f75d67a873798ac5ea85d463b09560c33bcdbcbb6')]:self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),sha)
 def test_live_scope_mutations_and_no_style_patch_for_pass(self):
  text=(ROOT/'tests/browser_weather231.py').read_text()
  self.assertIn("assert panel.locator(selector).count()==0",text);self.assertIn('scope_mutations_detected',text)
  self.assertIn("minWidth!=='680px'",text);self.assertIn("scrollWidth>e.closest('.report-table-wrap').clientWidth",text)
  for token in ['wait_for_timeout','time.sleep','post_data','AI_PROXY_URL =','AIS_PROXY_URL =']:self.assertNotIn(token,text)
 def test_browser_opt_in(self):
  if os.environ.get('RUN_WEATHER231_BROWSER')!='1':self.skipTest('Set RUN_WEATHER231_BROWSER=1; no simulated browser/pixel PASS implied')
  if not Path('/usr/bin/google-chrome').exists() or importlib.util.find_spec('playwright')is None:self.skipTest('Chromium/Playwright missing, weather browser NOT run')
  r=subprocess.run([sys.executable,'tests/browser_weather231.py'],cwd=ROOT,capture_output=True,text=True,timeout=120);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
