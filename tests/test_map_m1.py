import unittest,sys,json,hashlib
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]
BASE=Path(os.environ.get('MAP_BASE_ROOT',ROOT))
if (ROOT/'source').is_dir():sys.path[:0]=[str(ROOT/'source'),str(BASE)]
else:sys.path.insert(0,str(ROOT))
from integration import public_map_prep as m
from integration.news_api import create_app
from integration.public_preview_builder import build_public_preview
from integration.public_live_builder import build_public_live_preview
from tests.test_code_news_coverage_binding_prep import SAMPLE,LIVE,ORIGIN,Client
from unittest.mock import Mock,patch
RAW={'geo':[{'title':'<img src=x onerror=alert(1)>','url':'https://news.example.com/a','country':'India','source':'Fixture','summary':'secret summary','private':'secret','created_at':'2026-10-12T00:00:00Z'}]}
def make(raw=RAW):
 app=create_app(authorize=lambda r:True);from integration.api_v1 import install as alias_install;alias_install(app);f=m.FakeMap(lambda:raw);m.install(app,'http://localhost',f);return app,f
class Tests(unittest.TestCase):
 def test_alias_no_old_payload(self):
  a,f=make();r=a.test_client().get(m.ALIAS);self.assertTrue(r.json['fixture_only']);self.assertEqual(r.headers['Referrer-Policy'],'no-referrer');self.assertEqual(a.test_client().get(m.ALIAS+'?x=1').status_code,400)
 def test_pins(self):self.assertTrue(m.prepare(dict(SAMPLE,PUBLIC_MAP_ENABLED='true')))
 def test_OFF_differential(self):
  for name,builder in [('sample',build_public_preview),('live',build_public_live_preview)]:
   src=Path(__file__).parent/'fixtures'/('map_m1_base_'+name+'.txt');n={};exec(compile(src.read_text(),str(src),'exec'),n)
   env=SAMPLE if name=='sample'else dict(LIVE,PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED='false',PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED='false',PUBLIC_NEWS_FULL_PAGES_ENABLED='false')
   kw={}if name=='sample'else{'client_factory':lambda *a,**k:Client()}
   a=n[builder.__name__](env,**kw);b=builder(env,**kw)
   for p in ['/workspace/map','/api/map-data','/workspace','/workspace/assets/map.js']:
    for method in ['GET','HEAD','POST']:
     with patch('integration.news_api.datetime') as dt:
      from datetime import datetime,timezone
      dt.now.return_value=datetime(2026,10,12,tzinfo=timezone.utc)
      x=a.test_client().open(p,method=method,base_url=ORIGIN);y=b.test_client().open(p,method=method,base_url=ORIGIN)
     self.assertEqual((x.status_code,x.data,dict(x.headers)),(y.status_code,y.data,dict(y.headers)))
 def test_env_cannot_enable_real(self):
  for e in [dict(SAMPLE,PUBLIC_MAP_ENABLED='true'),dict(SAMPLE,PUBLIC_MAP_ENABLED='true',PUBLIC_MAP_BASE_TILES_ENABLED='true',PUBLIC_MAP_NEWS_ENABLED='true',PUBLIC_MAP_DATASETS_VERIFIED='true',PUBLIC_MAP_OSM_POLICY_VERIFIED='true')]:
   a=build_public_preview(e);r=a.test_client().get(m.API,base_url=ORIGIN);self.assertEqual(r.status_code,503);self.assertTrue(r.json['live_on_blocked'])
 def test_flags(self):
  for v in ['yes','TRUE','1',' false','']:
   with self.assertRaises(ValueError):m.prepare(dict(SAMPLE,PUBLIC_MAP_ENABLED=v))
  with self.assertRaises(ValueError):m.prepare(dict(SAMPLE,PUBLIC_MAP_NEWS_ENABLED='true'))
 def test_only_local_fake(self):
  a=create_app(authorize=lambda r:True)
  with self.assertRaises(ValueError):m.install(a,ORIGIN,m.FakeMap(lambda:RAW))
 def test_news_closed_projection(self):
  x=m.news(RAW,{'India':'FX-A'});self.assertEqual(x['rows_seen'],1);self.assertEqual(x['rows'][0]['feature_id'],'FX-A');self.assertNotIn('summary',json.dumps(x));self.assertNotIn('private',json.dumps(x));self.assertIn('<img',x['rows'][0]['title'])
 def test_bounds_unmapped(self):
  r=dict(RAW['geo'][0],country='Congo');x=m.news({'geo':[r]},{});self.assertEqual(x['rows_unmapped'],1)
  with self.assertRaises(ValueError):m.news({'geo':[r]*101},{})
  self.assertEqual(m.news({'geo':[],'brics':[]},{})['rows'],[])
  with self.assertRaises(ValueError):m.news({'geo':[],'private':[]},{})
 def test_headers_HEAD_methods(self):
  a,f=make();f.reader=Mock(side_effect=AssertionError('read'));c=a.test_client()
  for p in [m.PAGE,m.API,'/workspace/map-fixture/map.js']:
   r=c.head(p);self.assertEqual(r.status_code,200);self.assertEqual(r.data,b'')
  f.reader.assert_not_called()
  r=c.get(m.PAGE);self.assertEqual(r.headers['Referrer-Policy'],'strict-origin-when-cross-origin');self.assertIn("style-src 'self'",r.headers['Content-Security-Policy']);self.assertNotIn('unsafe-inline',r.headers['Content-Security-Policy'])
  self.assertEqual(c.get(m.API).headers['Referrer-Policy'],'no-referrer')
  self.assertEqual(c.get('/workspace').headers['Referrer-Policy'],'same-origin')
  for p in [m.PAGE,m.API]:
   self.assertEqual(c.get(p+'?x=1').status_code,400);self.assertEqual(c.post(p).status_code,403)
 def test_failure_no_fabrication(self):
  a,f=make();f.reader=lambda:(_ for _ in()).throw(ValueError('private secret'));r=a.test_client().get(m.API);self.assertEqual(r.status_code,503);self.assertNotIn('secret',r.text)
 def test_busy(self):
  a,f=make();f.slots.acquire();f.slots.acquire();self.assertEqual(a.test_client().get(m.API).status_code,429);f.slots.release();f.slots.release()
 def test_shapes(self):
  a,f=make();r=a.test_client().get(m.API);self.assertEqual(r.status_code,200);self.assertTrue(r.json['fixture_only']);self.assertFalse(r.json['ports']['available']);self.assertIn('approved free',r.json['ships']['note'])
 def test_real_base_fixture_hashes(self):
  expected={'sample':'be448f3cd92a7b0305233de3161d5fd0df21ca278affb81c9ca9ca7cbfbe38ff','live':'d05bcba1be7fc00164dae14cdc053d92c8bd8fe65ff38049ced6090c45043eca'}
  for name,h in expected.items():self.assertEqual(hashlib.sha256((Path(__file__).parent/'fixtures'/('map_m1_base_'+name+'.txt')).read_bytes()).hexdigest(),h)
 def test_duplicate_and_project(self):
  x=m.news({'geo':[RAW['geo'][0],RAW['geo'][0]]},{});self.assertEqual(len(x['rows']),1);self.assertEqual(x['rows_rejected'],1)
  # views normally choosesproject; direct poison verifiesboundaryindependently.
  with patch.object(m,'views',return_value=[dict(article_key='a',project='brics',title='x',url='https://n.test/a',source='',original_country='')]):self.assertEqual(m.news({'geo':[]},{})['rows'],[])
 def test_https_only(self):
  for u in ['http://news.example.com/a','javascript:alert(1)','https://user:pass@news.example.com/a','https://news.example.com:444/a']:
   self.assertIsNone(m.url(u))
 def test_payload_cap_direct(self):
  f=m.FakeMap(lambda:RAW);f.country={'type':'FeatureCollection','features':[{'padding':'x'*262144}]}
  with self.assertRaises(ValueError):f.payload()
 def test_startup_pins_and_dependency(self):
  env=dict(SAMPLE,PUBLIC_MAP_ENABLED='true')
  with patch.object(m,'PINS',{'map.js':'0'*64}):
   with self.assertRaises(ValueError):m.prepare(env)
  with patch.object(m,'BASE_PIN','0'*64):
   with self.assertRaises(ValueError):m.prepare(env)
  with self.assertRaises(ValueError):m.prepare(dict(env,PREVIEW_PUBLIC_SAMPLE_ENABLED='false'))
 def test_route_rule_shape(self):
  a=create_app(authorize=lambda r:True);a.add_url_rule(m.PAGE,endpoint='map_workspace',view_func=a.view_functions['map_workspace'])
  with self.assertRaises(ValueError):m.install(a,'http://localhost',m.FakeMap(lambda:RAW))
 def test_asset_allowlist_and_method(self):
  a,f=make();f.reader=Mock(side_effect=AssertionError('read'));c=a.test_client()
  self.assertEqual(c.get('/workspace/map-fixture/LICENSE').status_code,404)
  self.assertEqual(c.post(m.API).status_code,403);self.assertEqual(c.options(m.API).status_code,403);f.reader.assert_not_called()
 def test_loopback_same_scheme_wrong_host(self):
  for origin in ['http://example.test','http://127.0.0.2','https://localhost']:
   a=create_app(authorize=lambda r:True)
   with self.assertRaises(ValueError):m.install(a,origin,m.FakeMap(lambda:RAW))
if __name__=='__main__':unittest.main()
