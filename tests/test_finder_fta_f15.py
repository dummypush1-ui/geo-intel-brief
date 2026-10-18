import unittest,subprocess,hashlib
from pathlib import Path
from unittest.mock import patch
from integration import finder_fta_f15 as m,finder_composition_f9 as f9,finder_device_f10 as f10
from integration.public_preview_builder import build_public_preview
from tests import test_finder_composition_f9 as fixture
from tests.test_code_news_coverage_binding_prep import ORIGIN
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  fixture.Tests.setUpClass();cls.binding=fixture.Tests.binding;cls.env=dict(fixture.Tests.env,**{m.FLAG:'true'});cls.selection=f9.prepare(cls.env,cls.binding)
 @classmethod
 def tearDownClass(cls):fixture.Tests.tearDownClass()
 def test_default_suite_actual_drawer_VM(self):
  r=subprocess.run(['node',str(Path(__file__).with_name('finder_fta_f15.mjs'))],capture_output=True,text=True,timeout=10);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
 def test_flag_off_no_selection_or_source_access(self):
  with patch.object(f9.Selection,'verify',side_effect=AssertionError):self.assertIsNone(m.prepare({},None))
  for v in ('1','TRUE',''):
   with self.assertRaises(ValueError):m.prepare({m.FLAG:v},None)
  with self.assertRaises(ValueError):m.prepare({m.FLAG:'true'},None)
  with self.assertRaises(ValueError):m.prepare(self.env,object())
 def test_transform_csp_metadata_no_original_mutation(self):
  raw=self.selection.rendered;out=m.transform(raw,self.selection);self.assertNotEqual(out,raw);self.assertEqual(out.count('id="f15-staging-style"'),1);self.assertIn(self.binding.package_sha256,out);self.assertIn('FTA schedule staging comparison',out);self.assertIn("connect-src 'none'",out);self.assertEqual(self.selection.rendered,raw)
  with self.assertRaises(ValueError):m.transform(out,self.selection)
  with patch.object(type(self.binding),'verify',side_effect=ValueError('drift')):
   with self.assertRaises(ValueError):m.transform(raw,self.selection)
 def test_source_attribution_seam_drift_refused(self):
  read=Path.read_text
  def changed(p,*a,**k):
   s=read(p,*a,**k);return s.replace('India-UAE CEPA Appendix 2A-A','CHANGED')if p.name=='offline.html'else s
  with patch.object(f9.Selection,'verify'),patch.object(Path,'read_text',changed):
   with self.assertRaisesRegex(ValueError,'attribution seam'):m.prepare(self.env,self.selection)
 def test_selected_route_only_and_flag_off_exact(self):
  off=build_public_preview(dict(self.env,**{m.FLAG:'false'}),finder_candidate_binding=self.binding);on=build_public_preview(self.env,finder_candidate_binding=self.binding)
  for app in (off,on):self.addCleanup(app.extensions['finder_composition_close_f9'])
  a=off.test_client().get('/workspace/finder/offline.html',base_url=ORIGIN);b=on.test_client().get('/workspace/finder/offline.html',base_url=ORIGIN);self.assertNotIn('f15-staging-style',a.text);self.assertIn('f15-staging-style',b.text);self.assertEqual(b.status_code,200);self.assertIn("connect-src 'none'",b.headers['Content-Security-Policy']);self.assertEqual(b.headers['Cache-Control'],'no-store');self.assertEqual(on.test_client().head('/workspace/finder/offline.html',base_url=ORIGIN).data,b'')
 def test_f12_and_f10_coexist_without_cached_drawer(self):
  env=dict(self.env,**{'PUBLIC_FINDER_PROXY_FEATURES_ENABLED':'true','PUBLIC_FINDER_DATA_REPORT_ENABLED':'true',f10.FLAG:'true'});app=build_public_preview(env,finder_candidate_binding=self.binding);self.addCleanup(app.extensions['finder_composition_close_f9']);client=app.test_client();live=client.get('/workspace/finder/offline.html',base_url=ORIGIN).text;self.assertIn('finder-proxy-f12-request',live);self.assertIn('f15-staging-style',live);d=app.extensions[f10.KEY];cached=client.get(d.base+'snapshot.html',base_url=ORIGIN);self.assertEqual(cached.data,d.selection.rendered.encode()if hasattr(d,'selection')else f9.selected(app).rendered.encode());self.assertNotIn('f15-staging-style',cached.text)
