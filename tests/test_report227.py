from scripts.doc_lookup import source_bytes, source_text
"""Source-policy pins and opt-in Chromium diagnostic ledger, not live parity."""
import hashlib, importlib.util, os, re, shutil, subprocess, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Report227(unittest.TestCase):
 def test_preserved_source_and_policy_pins(self):
  pins={'src/app.js':'f8ecf57f73c28c376c4508f2ce7315f3ffad0a8a26d925a9782db6bb53e38f91'}
  for path,sha in pins.items():self.assertIn(sha,source_text(ROOT/'integration/REPORT227.md')) # Historical 227 pin, not current source
  self.assertIn('sandbox="allow-scripts allow-same-origin allow-downloads allow-modals allow-popups"',(ROOT/'integration/ui/workspace.html').read_text())
  source=(ROOT/'src/app.js').read_text()
  self.assertIn("if (!aiAvailable()) {\n      V.needKey = true; V.settingsOpen = true; V.briefError = null; paintDetail();",source)
  self.assertIn('esc(prod)',source);self.assertIn('esc(modeLine)',source)
 def test_source_section_inventory_and_network_off(self):
  source=(ROOT/'src/app.js').read_text();report=source[source.index('function buildTemplateReport('):source.index('async function openTemplateReport(')]
  ids=re.findall(r'<section class="tpl-sec"><h2><span class="tpl-num">([^<]+)</span>',report)
  self.assertEqual(ids,['01','01A']+[f'{i:02}'for i in range(2,21)])
  probe=(ROOT/'tests/browser_finder_report227.py').read_text()
  for token in ('finder_network_preview_enabled=True','unsafe-hashes','setTimeout','wait_for_timeout','window.fetch=','tplNarrative=','aiAvailable='):self.assertNotIn(token,probe)
  self.assertIn('SYNTHETIC-PLACEHOLDER-NOT-A-KEY',probe)
  self.assertIn("u.path",probe);self.assertNotIn('post_data',probe);self.assertNotIn('r.request.headers',probe)
 def test_opt_in_chromium_diagnostic(self):
  self.skipTest('superseded by 228; BEFORE-fix method, not valid on current source')
  if not Path('/usr/bin/google-chrome').is_file():self.skipTest('Chromium missing; nested popup/PDF diagnostic NOT run')
  if not shutil.which('pdftotext') or not shutil.which('pdftoppm'):self.skipTest('PDF text/render tools missing; diagnostic NOT run')
  if importlib.util.find_spec('playwright') is None:self.skipTest('Playwright missing; diagnostic NOT run')
  if os.environ.get('RUN_REPORT227_BROWSER')!='1':self.skipTest('Opt-in browser diagnostic: set RUN_REPORT227_BROWSER=1; no popup/PDF result implied')
  result=subprocess.run([sys.executable,str(ROOT/'tests/browser_finder_report227.py')],cwd=ROOT,capture_output=True,text=True,timeout=120)
  self.assertEqual(result.returncode,0,result.stderr+result.stdout)
