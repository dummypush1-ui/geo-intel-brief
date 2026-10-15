import unittest,sys,json,hashlib,subprocess,tempfile,shutil
from pathlib import Path
from unittest.mock import patch,Mock
from integration import public_map_m3 as m
from integration.public_preview_builder import build_public_preview
from integration.public_live_builder import build_public_live_preview
from tests.test_code_news_coverage_binding_prep import SAMPLE,LIVE,ORIGIN,Client
LIVE={**LIVE,'PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED':'false','PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED':'false','PUBLIC_NEWS_FULL_PAGES_ENABLED':'false'}
ENV={'PUBLIC_MAP_ENABLED':'true','PUBLIC_MAP_M2_ENABLED':'true',m.FLAG:'true'}
class Tests(unittest.TestCase):
 def test_flags(self):
  self.assertFalse(m.prepare({}));self.assertFalse(m.prepare({m.FLAG:'false'}));self.assertTrue(m.prepare(dict(SAMPLE,**ENV)))
  for missing in ('PREVIEW_PUBLIC_SAMPLE_ENABLED','PUBLIC_MAP_M2_ENABLED'):
   with self.assertRaises(ValueError):m.prepare({**SAMPLE,**ENV,missing:'false'})
  for x in [{m.FLAG:'x'},{m.FLAG:'TRUE'},{m.FLAG:'true'},{**SAMPLE,**ENV,'PUBLIC_MAP_M2_ENABLED':'false'}]:
   f=Mock()
   with self.assertRaises(ValueError):build_public_live_preview(x,client_factory=f)
   f.assert_not_called()
 def test_off_parity(self):
  root=Path(__file__).resolve().parents[1]
  for name,new,env in [('preview',build_public_preview,SAMPLE),('live',build_public_live_preview,LIVE)]:
   source=(root/'tests/fixtures'/('map_m3_base_'+name+'.txt')).read_text()
   ns={'__file__':str(root/'integration'/('public_'+name+'_builder.py'))};exec(compile(source,ns['__file__'],'exec'),ns);old=ns['build_public_preview'if name=='preview'else'build_public_live_preview']
   for extra in [{},{'PUBLIC_MAP_ENABLED':'true'},{'PUBLIC_MAP_ENABLED':'true','PUBLIC_MAP_M2_ENABLED':'true'}]:
    e=dict(env,**extra);make=lambda b:b(e)if name=='preview'else b(e,client_factory=lambda *a,**k:Client())
    a,b=make(old).test_client(),make(new).test_client()
    for path in ['/workspace','/workspace/map','/api/map-data','/workspace/map-fixture/countries.json','/workspace/map-streets/streets.js']:
     for verb in ['get','head','options','post']:
      from datetime import datetime,timezone
      with patch('integration.news_api.datetime')as dt:
       dt.now.return_value=datetime(2026,10,15,tzinfo=timezone.utc);x,y=getattr(a,verb)(path,base_url=ORIGIN),getattr(b,verb)(path,base_url=ORIGIN)
      self.assertEqual((x.status_code,x.data,dict(x.headers)),(y.status_code,y.data,dict(y.headers)))
 def test_composition_and_assets(self):
  for builder,env in [(build_public_preview,SAMPLE),(build_public_live_preview,LIVE)]:
   with patch('integration.public_live_builder.ReadOnlyNewsReader',return_value=lambda:{'geo':[]}):
    app=builder(dict(env,**ENV))if builder is build_public_preview else builder(dict(env,**ENV),client_factory=lambda *a,**k:Client())
   c=app.test_client()
   r=c.get('/workspace/map',base_url=ORIGIN);self.assertEqual(r.status_code,200);s=r.text
   self.assertIn('m3-start',s);self.assertEqual(s.count('</head>'),1);self.assertEqual(c.head('/workspace/map',base_url=ORIGIN).data,b'');self.assertFalse(app.extensions['public_map_m3']['server_network']);self.assertIn('Clicking sends map-view requests to OpenFreeMap/Cloudflare, not your news or search text.',s);self.assertIn('© OpenMapTiles',s);self.assertIn('© OpenStreetMap contributors',s);self.assertEqual(s.count('This reproduction, partial or complete'),2);self.assertNotIn('Street tiles unavailable',s)
   self.assertEqual(r.headers['Content-Security-Policy'],"default-src 'none'; script-src 'self'; worker-src 'self'; style-src 'self'; img-src 'self' data: https://tiles.openfreemap.org; connect-src 'self' https://tiles.openfreemap.org; frame-ancestors 'none'; object-src 'none'; base-uri 'none'; form-action 'none'");self.assertEqual(r.headers['Referrer-Policy'],'no-referrer')
   for path in m.PATHS:
    a=c.get(path,base_url=ORIGIN);self.assertEqual(a.status_code,200,path);self.assertEqual(c.head(path,base_url=ORIGIN).data,b'')
    self.assertEqual(a.headers['Cache-Control'],'no-store');self.assertEqual(a.headers['Referrer-Policy'],'no-referrer');self.assertEqual(a.headers['X-Content-Type-Options'],'nosniff')
    self.assertEqual(c.get(path+'?x=1',base_url=ORIGIN).status_code,400)
    self.assertEqual(c.get(path,base_url='https://evil.test').status_code,403)
    for verb in ['post','options','delete']:self.assertEqual(getattr(c,verb)(path,base_url=ORIGIN).status_code,403)
   self.assertEqual(c.get('/api/map-data',base_url=ORIGIN).status_code,200)
   self.assertEqual(c.get(m.PREFIX+'maplibre-worker.js',base_url=ORIGIN).headers['Content-Security-Policy'],"default-src 'none'; script-src 'self'; connect-src https://tiles.openfreemap.org;")
   self.assertEqual(c.get(m.PREFIX+'not-an-asset.js',base_url=ORIGIN).status_code,403) # outer public authorization denies non-allowlisted paths
   from integration.news_api import create_app
   from integration import public_map_m2 as m2
   standalone=create_app(authorize=lambda _:True);m2.install(standalone,ORIGIN,lambda:{'geo':[]});m.install(standalone,ORIGIN);direct=standalone.test_client()
   self.assertEqual(direct.get(m.PREFIX+'not-an-asset.js',base_url=ORIGIN).status_code,404)
   self.assertEqual(direct.get(m.PREFIX+'not-an-asset.js',base_url='https://evil.test').status_code,403)
 def test_pins_style_and_no_server_network(self):
  x=json.loads((m.ROOT/'pins.json').read_text());self.assertEqual(set(x),m.ASSETS)
  for n,h in x.items():self.assertEqual(hashlib.sha256((m.ROOT/n).read_bytes()).hexdigest(),h)
  style=json.loads((m.ROOT/'liberty.json').read_text());self.assertEqual(style['sources']['openmaptiles']['url'],'https://tiles.openfreemap.org/planet')
  with patch('socket.socket.connect',side_effect=AssertionError('network')):
   app=build_public_preview(dict(SAMPLE,**ENV));self.assertEqual(app.test_client().get('/workspace/map',base_url=ORIGIN).status_code,200)
 def test_mount_and_pin_fail_closed(self):
  from integration.news_api import create_app
  with self.assertRaises(ValueError):m.install(create_app(authorize=lambda _:True),ORIGIN)
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp)
   for n in m.ASSETS:shutil.copyfile(m.ROOT/n,root/n)
   (root/'pins.json').write_text((m.ROOT/'pins.json').read_text())
   with patch.object(m,'ROOT',root):
    self.assertTrue(m.prepare(dict(SAMPLE,**ENV)))
    x=json.loads((root/'pins.json').read_text());x['extra.js']='0'*64;(root/'pins.json').write_text(json.dumps(x))
    with self.assertRaises(ValueError):m.prepare(dict(SAMPLE,**ENV))
    del x['extra.js'];(root/'pins.json').write_text(json.dumps(x));(root/'streets.css').write_text('asset drift')
    with self.assertRaises(ValueError):m.prepare(dict(SAMPLE,**ENV))
  from integration import public_map_m2 as m2
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);(root/'map.html').write_text('unexpected M2 shell')
   with patch.object(m2,'ROOT',root):
    with self.assertRaises(ValueError):m.prepare(dict(SAMPLE,**ENV))
 def test_source_guard_independent_of_csp(self):
  p=Path(__file__).resolve().with_name('public_map_m3_sources.cjs')
  result=subprocess.run(['node',str(p)],capture_output=True,text=True,timeout=10)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)
 def test_shell_rejects_unknown(self):
  with self.assertRaises(ValueError):m.transform('<head></head><body></body>')
  body='<html><head></head></head><body><div id="map" aria-label="Reference map"></div></body></html>'
  with self.assertRaises(ValueError):m.transform(body)
if __name__=='__main__':unittest.main()
