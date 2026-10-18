"""F11 derived safe-render contracts. Synthetic source fixture, no providers."""
import base64,hashlib,re,unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
from integration import finder_report_f11 as m,finder_composition_f9 as f9,finder_device_f10 as f10
from integration.public_preview_builder import build_public_preview
from tests import test_finder_composition_f9 as fixture
from tests.test_code_news_coverage_binding_prep import ORIGIN
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  fixture.Tests.setUpClass();cls.binding=fixture.Tests.binding;cls.env=dict(fixture.Tests.env,**{m.FLAG:'true',f10.FLAG:'true'})
  cls.base=(cls.binding.root/'review/public-offline.html').read_text();cls.derived=m.transform(cls.base)
 @classmethod
 def tearDownClass(cls):fixture.Tests.tearDownClass()
 def app(self,**extra):
  app=build_public_preview(dict(self.env,**extra),finder_candidate_binding=self.binding);self.addCleanup(app.extensions['finder_composition_close_f9']);return app
 def test_default_off_exact_flags_dependency(self):
  self.assertFalse(m.enabled({}));self.assertFalse(m.enabled({m.FLAG:'false'}))
  for flag in ('TRUE','1',''):
   with self.assertRaisesRegex(m.Held,'Exact data-report flag'):f9.prepare({m.FLAG:flag})
  for flag in (None,'false','TRUE'):
   env={m.FLAG:'true'}
   if flag is not None:env[f9.FLAG]=flag
   with self.assertRaisesRegex(m.Held,'requires selected'):f9.prepare(env)
 def test_flag_off_identical_F8_base_and_no_mutation(self):
  selection=f9.prepare(dict(self.env,**{m.FLAG:'false'}),self.binding)
  self.assertEqual(selection.rendered,self.base);self.assertFalse(selection.report_enabled)
  self.assertEqual((self.binding.root/'review/public-offline.html').read_text(),self.base)
  self.assertNotEqual(hashlib.sha256(self.derived.encode()).hexdigest(),hashlib.sha256(self.base.encode()).hexdigest())
 def test_derive_deterministic_closed_and_preserves_data_scripts(self):
  self.assertEqual(m.transform(self.base),self.derived)
  before=re.findall(r'<script>(.*?)</script>',self.base,re.S|re.I);after=re.findall(r'<script>(.*?)</script>',self.derived,re.S|re.I)
  self.assertEqual(len(before),len(after));self.assertGreater(len(before),1)
  # Only app JS changes; standalone dataset script bytes remain exact.
  changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];self.assertEqual(len(changed),1);self.assertIn('function buildTemplateReport',before[changed[0]]);self.assertNotIn('localStorage',self.derived)
  for seam in ('const aiUsed = !!narrative;',"  el('d-tpl').addEventListener('click', () => {",'Every figure, code and rate in this report is exact official data with its data date.'):
   with self.assertRaises((m.Held,ValueError)):m.transform(self.base.replace(seam,'DRIFT',1))
  with self.assertRaises(m.Held):m.transform(self.derived)
  with self.assertRaises(m.Held):m.transform('unsafe')
 def test_UI_button_and_renderer_never_call_provider(self):
  text=self.derived
  openfn=text[text.index('async function openTemplateReport('):text.index('/* ---------- detail view ---------- */')]
  self.assertNotIn('aiAvailable()',openfn);self.assertNotIn('tplNarrative(',openfn);self.assertNotIn('V.apiKey',openfn)
  button=text[text.index("  el('d-tpl').addEventListener"):text.index("  el('d-copy').addEventListener")]
  self.assertNotIn('aiAvailable()',button);self.assertNotIn('settingsOpen',button)
  for phrase in ('Make the data PDF report','TPL_SECTIONS.length','narrative = null; // Data report','Live AI is unavailable in this data report.'):
   self.assertIn(phrase,text)
  for phrase in ('One tap makes the branded 14-section','For a full AI-written','finder refreshes official sources automatically every week'):
   self.assertNotIn(phrase,text)
 def test_exact_derived_identity_and_scoped_cache(self):
  selection=f9.prepare(self.env,self.binding);selection.verify();device=f10.prepare(self.env,selection)
  base=f9.prepare(dict(self.env,**{m.FLAG:'false'}),self.binding);old=f10.prepare(self.env,base)
  self.assertNotEqual(device.digest,old.digest);self.assertNotEqual(device.base,old.base);self.assertNotEqual(device.cache,old.cache)
  for bad in (replace(selection,rendered=selection.rendered+'x'),replace(selection,rendered=self.base)):
   with self.assertRaises(f9.Held):bad.verify()
  with self.assertRaises(f10.Held):replace(device,digest=old.digest).verify()
 def test_routes_headers_exact_render_and_public_AI_still_held(self):
  app=self.app(PUBLIC_AI_ANSWERS_ENABLED='true');client=app.test_client();selection=f9.selected(app);d=app.extensions[f10.KEY]
  self.assertEqual(app.extensions['public_ai_answers']['state'],'held')
  for path in ('/workspace/finder/offline.html',d.base+'snapshot.html'):
   r=client.get(path,base_url=ORIGIN);self.assertEqual(r.status_code,200)
   if path==d.base+'snapshot.html':self.assertEqual(r.data,selection.rendered.encode())
   else:self.assertIn('Make the data PDF report',r.text) # Existing noncached public bridge may compose here.
   self.assertEqual(client.get(path,base_url='https://evil.test').status_code,403)
   csp=r.headers['Content-Security-Policy'];self.assertIn("connect-src 'none'",csp);self.assertNotIn("'unsafe-eval'",csp)
   for script in re.findall(r'<script>(.*?)</script>',r.text,re.S|re.I):
    self.assertIn('sha256-'+base64.b64encode(hashlib.sha256(script.encode()).digest()).decode(),csp)
  with patch.object(f9.Selection,'verify',side_effect=f9.Held('drift')):
   self.assertEqual(client.get(d.base+'snapshot.html',base_url=ORIGIN).status_code,503)
   self.assertEqual(client.head(d.base+'snapshot.html',base_url=ORIGIN).status_code,200)

class BrowserTests(unittest.TestCase):
 def test_browser_opt_in(self):
  import os,importlib.util,subprocess,sys,tempfile,shutil
  if os.environ.get('RUN_FINDER_F11_BROWSER')!='1':self.skipTest('Opt-in actual PDF browser regression not run by default')
  if not Path('/usr/bin/google-chrome').exists()or not all(shutil.which(n)for n in ('pdftotext','pdftoppm'))or any(importlib.util.find_spec(n)is None for n in ('playwright','PIL')):self.skipTest('Chrome/Playwright/Pillow/Poppler missing; no browser pass implied')
  with tempfile.TemporaryDirectory()as out:
   run=subprocess.run([sys.executable,'-B','tests/browser_finder_report_f11.py',out],cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True,timeout=180)
   self.assertEqual(run.returncode,0,run.stdout+run.stderr)
