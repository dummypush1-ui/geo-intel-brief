import hashlib,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
from integration import brics_recovery_b4 as m,public_brics_streams as base
from integration.public_preview_builder import build_public_preview
from integration.public_live_builder import build_public_live_preview
from tests.test_code_news_coverage_binding_prep import SAMPLE,LIVE,ORIGIN,Client
class Tests(unittest.TestCase):
 def app(self):return build_public_preview(dict(SAMPLE,**{base.FLAG:'true',m.FLAG:'true'}))
 def test_off_before_io_invalid_and_required_wall(self):
  with patch.object(Path,'read_text',side_effect=AssertionError):self.assertFalse(m.prepare({}));self.assertFalse(m.prepare({m.FLAG:'false'}))
  for env in ({m.FLAG:'TRUE'},{m.FLAG:'true'},{m.FLAG:'true',base.FLAG:'true'}):
   factory=Mock()
   with self.assertRaises(ValueError):build_public_live_preview(env,client_factory=factory)
   factory.assert_not_called()
 def test_transform_exact_hashes_and_no_polling(self):
  source=(m.ROOT/'integration/ui/public_brics_streams.js').read_text();recovery=(m.ROOT/'integration/brics_recovery_b4/recovery.js').read_text();result=m.transform(source,recovery)
  for a,b in ((source+' ',recovery),(source,recovery+' ')):
   with self.assertRaises(m.Held):m.transform(a,b)
  self.assertIn('enablejsapi=1&origin=',result);self.assertIn("tile.dataset.recoveryHeld==='true'",result);self.assertNotIn('setInterval',recovery);self.assertNotIn('setTimeout',recovery);self.assertNotIn("postMessage(JSON.stringify({event:'listening'}), '*'",recovery)
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp)/'fixture.mjs';p.write_text(result);subprocess.run(['node','--check',str(p)],check=True)
 def test_on_asset_HEAD_noIO_boundaries_unchanged(self):
  app=self.app();client=app.test_client()
  for path in base.PATHS:
   a=client.get(path,base_url=ORIGIN);self.assertEqual(a.status_code,200);self.assertEqual(a.headers['Cache-Control'],'no-store')
   for method in ('post','delete','options'):self.assertEqual(getattr(client,method)(path,base_url=ORIGIN).status_code,403)
   self.assertEqual(client.get(path+'?x=1',base_url=ORIGIN).status_code,400);self.assertEqual(client.get(path,base_url='https://evil.test').status_code,403)
   with patch.object(Path,'read_text',side_effect=AssertionError):self.assertEqual(client.head(path,base_url=ORIGIN).data,b'')
  js=client.get('/workspace/assets/brics_streams.js',base_url=ORIGIN).text;self.assertIn('installRecovery(document,window);',js);self.assertIn("frame-src https://www.youtube-nocookie.com;",client.get(base.PAGE,base_url=ORIGIN).headers['Content-Security-Policy'])
  self.assertNotIn('installRecovery',client.get(base.PAGE,base_url=ORIGIN).text)
 def test_exact_off_differential_sample_and_live(self):
  for name,builder,env in [('sample',build_public_preview,dict(SAMPLE,**{base.FLAG:'true'})),('live',build_public_live_preview,dict(LIVE,**{base.FLAG:'true','PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED':'false','PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED':'false','PUBLIC_NEWS_FULL_PAGES_ENABLED':'false'}))]:
   ns={};path=Path(__file__).parent/'fixtures'/('recovery_b4_base_'+name+'.txt');exec(compile(path.read_text(),str(path),'exec'),ns);old=ns['build_public_preview'if name=='sample'else'build_public_live_preview'];kw={}if name=='sample'else{'client_factory':lambda *a,**k:Client()}
   a=old(env,**kw);b=builder(dict(env,**{m.FLAG:'false'}),**kw)
   for route in [*base.PATHS,'/workspace']:
    for method in ('get','head','post','delete','options'):
     x=getattr(a.test_client(),method)(route,base_url=ORIGIN);y=getattr(b.test_client(),method)(route,base_url=ORIGIN);self.assertEqual((x.status_code,x.data,dict(x.headers)),(y.status_code,y.data,dict(y.headers)))
   self.assertNotIn('brics_recovery_b4',b.extensions)
 def test_install_requires_mount_and_is_single(self):
  from integration.news_api import create_app
  with self.assertRaises(m.Held):m.install(create_app())
  app=self.app()
  with self.assertRaises(m.Held):m.install(app)
 def test_bounded_provider_parser_node(self):
  subprocess.run(['node','tests/brics_recovery_b4.mjs'],cwd=m.ROOT,check=True)
 def test_actual_browser_recovery_controls(self):
  import sys
  with tempfile.TemporaryDirectory()as tmp:subprocess.run([sys.executable,'tests/browser_brics_recovery_b4.py',tmp],cwd=m.ROOT,check=True,stdout=subprocess.DEVNULL,timeout=45)
 def test_live_builder_on_and_base_routes_preserved(self):
  env=dict(LIVE,**{base.FLAG:'true',m.FLAG:'true','PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED':'false','PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED':'false','PUBLIC_NEWS_FULL_PAGES_ENABLED':'false'})
  app=build_public_live_preview(env,client_factory=lambda *a,**k:Client());off=build_public_live_preview(dict(env,**{m.FLAG:'false'}),client_factory=lambda *a,**k:Client())
  self.assertTrue(app.extensions['brics_recovery_b4']);asset='/workspace/assets/brics_streams.js';response=app.test_client().get(asset,base_url=ORIGIN);self.assertIn('installRecovery(document,window);',response.text)
  for path in base.PATHS-{asset}:
   x=app.test_client().get(path,base_url=ORIGIN);y=off.test_client().get(path,base_url=ORIGIN);self.assertEqual((x.status_code,x.data,dict(x.headers)),(y.status_code,y.data,dict(y.headers)))
 def test_exact_flags_with_other_prerequisites_valid(self):
  env=dict(SAMPLE,**{base.FLAG:'true',m.FLAG:'true'})
  with self.assertRaises(m.Held):m.prepare(dict(env,**{m.FLAG:'TRUE'}))
  for key in ('PREVIEW_PUBLIC_SAMPLE_ENABLED',base.FLAG):
   missing=dict(env);del missing[key]
   with self.subTest(missing=key),self.assertRaises(m.Held):m.prepare(missing)
 def test_prepare_own_pin_checks_and_each_seam_boundary(self):
  env=dict(SAMPLE,**{base.FLAG:'true',m.FLAG:'true'});source=(m.ROOT/'integration/ui/public_brics_streams.js').read_text();recovery=(m.ROOT/'integration/brics_recovery_b4/recovery.js').read_text()
  with patch.object(m,'BASE_SHA','0'*64),self.assertRaises(m.Held):m.prepare(env)
  with patch.object(Path,'read_text',side_effect=[source+' ',recovery]),self.assertRaises(m.Held):m.prepare(env)
  for seam in ("'?autoplay=1&mute=1&playsinline=1&rel=0';",'function mini(tile,c){',"function selectedPlayer(){const target=el('selected'),"):
   for altered in (source.replace(seam,''),source+seam):
    with self.subTest(seam=seam,count=altered.count(seam)),patch.object(m,'BASE_SHA',hashlib.sha256(altered.encode()).hexdigest()),self.assertRaisesRegex(m.Held,'seam drift'):m.transform(altered,recovery)
 def test_served_module_selected_reset_type_and_HEAD_policy_headers(self):
  app=self.app();path='/workspace/assets/brics_streams.js';client=app.test_client();get=client.get(path,base_url=ORIGIN)
  with patch.object(Path,'read_text',side_effect=AssertionError):head=client.head(path,base_url=ORIGIN)
  self.assertEqual(get.mimetype,'application/javascript');self.assertEqual(head.mimetype,'application/javascript');self.assertEqual(head.data,b'')
  self.assertEqual({k:v for k,v in get.headers.items()if k!='Content-Length'},{k:v for k,v in head.headers.items()if k!='Content-Length'})
  self.assertEqual(int(get.headers['Content-Length']),len(get.data));self.assertEqual(head.headers['Content-Length'],'0')
  self.assertIn("function selectedPlayer(){const target=el('selected');target.removeAttribute('data-recovery-held');const ",get.text)
  self.assertEqual(get.text.count('installRecovery(document,window);'),1);self.assertIn('export const PROVIDER_ORIGIN=',get.text)
if __name__=='__main__':unittest.main()
