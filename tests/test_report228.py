"""228 source/report behavior with opt-in real Chromium fixture, not live service proof."""
import importlib.util,os,re,shutil,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Report228(unittest.TestCase):
 def test_generator_has_no_inline_execution_and_original_escaping(self):
  text=(ROOT/'src/app.js').read_text();section=text[text.index('function buildTemplateReport('):text.index('// Report behavior stays')]
  self.assertNotIn('<script',section);self.assertNotRegex(section,r'\son[a-z]+\s*=')
  for token in ['esc(prod)','esc(modeLine)','esc(fmtCode(e[0], e[1]))','Copyright (c) 2026 Push. All rights reserved.']:self.assertIn(token,section)
  self.assertEqual(re.findall(r'<section class="tpl-sec"><h2><span class="tpl-num">([^<]+)</span>',section),['01','01A']+[f'{i:02}'for i in range(2,21)])
 def test_opener_helper_policy_and_print_css(self):
  text=(ROOT/'src/app.js').read_text();section=text[text.index('function setupTemplateReportWindow'):text.index('async function openTemplateReport')]
  for token in ['doc.__templateReport228','w.print()','doc.fonts.ready','1500','w.document !== doc','doc.readyState','once: true']:self.assertIn(token,section)
  for token in ['eval(','new Function','fetch(','setInterval','onclick=']:self.assertNotIn(token,section)
  self.assertIn('.tpl-foot { position: static; }',text)
  self.assertIn('sandbox="allow-scripts allow-same-origin allow-downloads allow-modals allow-popups"',(ROOT/'integration/ui/workspace.html').read_text())
 def test_exact_helper_node_lifecycle(self):
  result=subprocess.run(['node','tests/report228_test.mjs'],cwd=ROOT,capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)
 def test_opt_in_browser(self):
  if not Path('/usr/bin/google-chrome').exists() or not shutil.which('pdftotext') or not shutil.which('pdftoppm') or importlib.util.find_spec('playwright') is None:self.skipTest('Chromium/Playwright/PDF tools missing; 228 browser/PDF NOT run')
  if os.environ.get('RUN_REPORT228_BROWSER')!='1':self.skipTest('Set RUN_REPORT228_BROWSER=1; no browser/PDF pass implied')
  result=subprocess.run([sys.executable,str(ROOT/'tests/browser_report228.py')],cwd=ROOT,capture_output=True,text=True,timeout=120)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)
