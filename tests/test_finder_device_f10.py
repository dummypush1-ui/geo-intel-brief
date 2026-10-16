import hashlib,json,unittest
from pathlib import Path
from unittest.mock import patch
from integration import finder_device_f10 as m,finder_composition_f9 as f9
from integration.public_preview_builder import build_public_preview
from tests import test_finder_composition_f9 as fixture_module
from tests.test_code_news_coverage_binding_prep import SAMPLE,ORIGIN
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):fixture_module.Tests.setUpClass();cls.binding=fixture_module.Tests.binding;cls.env=dict(fixture_module.Tests.env,**{m.FLAG:'true'})
 @classmethod
 def tearDownClass(cls):fixture_module.Tests.tearDownClass()
 def app(self):
  a=build_public_preview(self.env,finder_candidate_binding=self.binding);self.addCleanup(a.extensions['finder_composition_close_f9']);return a
 def test_exact_flag_and_off_before_selection(self):
  with patch.object(f9.Selection,'verify',side_effect=AssertionError):self.assertIsNone(m.prepare({}));self.assertIsNone(m.prepare({m.FLAG:'false'},object()))
  selection=f9.prepare(dict(SAMPLE,**{f9.FLAG:'true'}),self.binding)
  for flag in ('TRUE','1',''):
   with patch.object(f9.Selection,'verify',side_effect=AssertionError('flag must precede verify')),self.assertRaisesRegex(m.Held,'Exact device-cache flag'):m.prepare({m.FLAG:flag},selection)
  with self.assertRaisesRegex(m.Held,'environment strings'):m.prepare({m.FLAG:'true','other':1},selection)
  for value in (None,object()):
   with self.assertRaises(m.Held):m.prepare({m.FLAG:'true'},value)
 def test_selected_routes_headers_and_digest(self):
  app=self.app();d=app.extensions[m.KEY];client=app.test_client()
  for path in d.paths:
   r=client.get(path,base_url=ORIGIN);self.assertEqual(r.status_code,200,(path,r.text[:100]));self.assertEqual(r.headers['Cache-Control'],'no-store');self.assertEqual(client.get(path,base_url='https://evil.test').status_code,403)
  r=client.get(d.base+'snapshot.html',base_url=ORIGIN);self.assertEqual(hashlib.sha256(r.data).hexdigest(),d.digest);self.assertEqual(r.headers['X-Finder-Device-Snapshot'],d.digest);self.assertIn("connect-src 'none'",r.headers['Content-Security-Policy']);self.assertIn("script-src 'sha256-",r.headers['Content-Security-Policy']);self.assertNotIn('public-ai-question-v1',r.text)
  self.assertEqual(client.get(d.base+'worker.js',base_url=ORIGIN).headers['Service-Worker-Allowed'],d.base)
  from integration.public_live_builder import build_public_live_preview
  from tests.test_code_news_coverage_binding_prep import LIVE,Client,Binding as CoverageBinding
  env=dict(LIVE,**{k:v for k,v in self.env.items()if k not in SAMPLE});client_fixture=Client()
  with patch('integration.public_live_builder.ReadOnlyNewsReader',return_value=lambda:{'geo':[]}):live=build_public_live_preview(env,client_factory=lambda *a,**k:client_fixture,coverage_binding_provider=lambda:CoverageBinding(True,True,True,True,'fixture-owner','fixture-deploy'),finder_candidate_binding=self.binding)
  self.addCleanup(live.extensions['finder_composition_close_f9']);ld=live.extensions[m.KEY];self.assertEqual(live.test_client().get(ld.base+'snapshot.html',base_url=ORIGIN).headers['X-Finder-Device-Snapshot'],ld.digest)
 def test_raw_old_and_private_routes_still_denied(self):
  client=self.app().test_client()
  for n in ('index.html','sw.js','offline-sw.js','offline-control.js','offline-manifest.webmanifest','data.d6d1b417562b.js'):
   self.assertEqual(client.get('/workspace/finder/'+n,base_url=ORIGIN).status_code,403)
  self.assertEqual(client.get('/collect',base_url=ORIGIN).status_code,403)
 def test_drift_get_refused_head_does_not_read(self):
  app=self.app();d=app.extensions[m.KEY];client=app.test_client()
  with patch.object(m.Device,'verify',side_effect=m.Held('drift')):
   self.assertEqual(client.get(d.base+'snapshot.html',base_url=ORIGIN).status_code,503)
   self.assertEqual(client.head(d.base+'snapshot.html',base_url=ORIGIN).status_code,200)
 def test_install_requires_same_exact_selection_once(self):
  app=self.app();d=app.extensions[m.KEY]
  with self.assertRaises(m.Held):m.install(app,d)
  other=build_public_preview(SAMPLE)
  with self.assertRaises(m.Held):m.install(other,d)
 def test_wrong_render_and_size_refused(self):
  selection=f9.prepare(dict(SAMPLE,**{f9.FLAG:'true'}),self.binding)
  bad=f9.Selection(selection.binding,selection.rendered+'x',selection.editions)
  with self.assertRaises(m.Held):m.prepare({m.FLAG:'true'},bad)
  with self.assertRaises(m.Held):m.prepare({m.FLAG:'true'},f9.Selection(selection.binding,'',selection.editions))
 def test_no_worker_registration_on_snapshot(self):
  app=self.app();d=app.extensions[m.KEY];html=app.test_client().get(d.base+'snapshot.html',base_url=ORIGIN).text
  self.assertNotIn('serviceWorker.register',html);self.assertNotIn('localStorage',html);self.assertNotIn('public-ai-question-v1',html)
 def test_manifest_scope_edition_specific(self):
  app=self.app();d=app.extensions[m.KEY];r=app.test_client().get(d.base+'manifest.webmanifest',base_url=ORIGIN);self.assertEqual(r.json['scope'],d.base);self.assertEqual(r.json['start_url'],d.base+'snapshot.html')
 def test_snapshot_allowed_only_exact_method_and_paths(self):
  app=self.app();d=app.extensions[m.KEY];c=app.test_client()
  self.assertEqual(c.post(d.base+'snapshot.html',base_url=ORIGIN).status_code,403);self.assertEqual(c.get(d.base+'anything',base_url=ORIGIN).status_code,403)
 def test_asset_template_seam_closed(self):
  app=self.app();d=app.extensions[m.KEY]
  with patch.object(Path,'read_text',return_value='no config seam'),self.assertRaises(m.Held):m.script('worker.js',d)
 def test_workspace_manual_link_only_when_enabled(self):
  app=self.app();d=app.extensions[m.KEY];c=app.test_client();self.assertIn('href="'+d.base+'">Store public Finder',c.get('/workspace',base_url=ORIGIN).text)
  off=build_public_preview(dict(fixture_module.Tests.env,**{m.FLAG:'false'}),finder_candidate_binding=self.binding);self.addCleanup(off.extensions['finder_composition_close_f9']);self.assertNotIn('Store public Finder',off.test_client().get('/workspace',base_url=ORIGIN).text)
  path=Path(__file__).with_name('fixtures')/'f10_base_sample.txt';ns={};exec(compile(path.read_text(),str(path),'exec'),ns);before=ns['build_public_preview'](SAMPLE);after=build_public_preview(dict(SAMPLE,**{m.FLAG:'false'}))
  for route in ('/workspace','/workspace/finder/offline.html','/workspace/assets/workspace.js'):
   for method in ('get','head','post'):
    a=getattr(before.test_client(),method)(route,base_url=ORIGIN);b=getattr(after.test_client(),method)(route,base_url=ORIGIN);self.assertEqual((a.status_code,a.data,dict(a.headers)),(b.status_code,b.data,dict(b.headers)));a.close();b.close()
 def test_real_worker_js_adversarial_contract(self):
  import subprocess
  subprocess.run(['node',str(Path(__file__).with_name('finder_device_f10.mjs'))],check=True)
  subprocess.run(['node',str(Path(__file__).with_name('finder_device_f10_control.mjs'))],check=True)
 def test_size_bound_before_verify_empty_and_oversize(self):
  selection=f9.prepare(dict(SAMPLE,**{f9.FLAG:'true'}),self.binding)
  with patch.object(m.Device,'verify',side_effect=AssertionError('size first')):
   for raw in ('','x'*(24*1024*1024+1)):
    with self.subTest(size=len(raw)),self.assertRaisesRegex(m.Held,'Bounded public snapshot'):m.prepare({m.FLAG:'true'},f9.Selection(selection.binding,raw,selection.editions))
 def test_device_verify_checks_selection_root(self):
  app=self.app();d=app.extensions[m.KEY]
  with patch.object(f9.Selection,'verify',side_effect=m.Held('drifted root'))as verify:
   with self.assertRaisesRegex(m.Held,'drifted root'):d.verify()
   verify.assert_called_once_with()
   self.assertEqual(app.test_client().get(d.base+'snapshot.html',base_url=ORIGIN).status_code,503)
 def test_install_nondevice_rejected_before_any_selection_access(self):
  app=build_public_preview(SAMPLE)
  with self.assertRaisesRegex(m.Held,'One matching device selection'):m.install(app,object())
  self.assertNotIn(m.KEY,app.extensions)
 def test_all_device_route_policies_independently(self):
  # Remove generic no-store before the F10 hook so its own header assignment
  # is exercised rather than accidentally covered by the older generic hook.
  app=self.app();d=app.extensions[m.KEY]
  def strip(response):response.headers.pop('Cache-Control',None);return response
  hooks=app.after_request_funcs[None];index=next(i for i,hook in enumerate(hooks)if hook.__module__==m.__name__ and hook.__name__=='headers');hooks.insert(index+1,strip)
  c=app.test_client();policy="default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; connect-src 'self'; worker-src 'self'; manifest-src 'self'; frame-ancestors 'self'; base-uri 'none'; form-action 'none'"
  for name in ('','control.js','worker.js','snapshot.html','manifest.webmanifest'):
   with self.subTest(name=name):
    r=c.get(d.base+name,base_url=ORIGIN);self.assertEqual(r.status_code,200);self.assertEqual(r.headers['Cache-Control'],'no-store')
    self.assertEqual(c.post(d.base+name,base_url=ORIGIN).status_code,403)
    if name in ('','control.js','worker.js'):
     self.assertEqual(r.headers['Content-Security-Policy'],policy);self.assertNotIn("'unsafe-inline'",next(x for x in policy.split(';')if x.strip().startswith('script-src')))
 def test_workspace_nav_seam_drift_raises(self):
  app=self.app();app.testing=True
  app.view_functions['workspace']=lambda:'<html><body>missing navigation seam</body></html>'
  with self.assertRaisesRegex(m.Held,'Workspace device-link seam drift'):app.test_client().get('/workspace',base_url=ORIGIN)
if __name__=='__main__':unittest.main()
