import os
import sys,unittest,json,copy,hashlib,html
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,os.environ.get('M2_BASE',str(ROOT)));import integration;integration.__path__.insert(0,str(ROOT/'integration'))
from integration import public_map_m2 as m
from integration.news_api import create_app
class Tests(unittest.TestCase):
 def test_reference(self):
  c=m.load_json('countries.json',524288);self.assertEqual(len(m.validate_countries(c)),177);self.assertEqual(len(m.validate_ports(m.load_json('ports.json',524288))),3630);self.assertNotIn('Congo',m.references())
 def test_polygons_refuse(self):
  c=m.load_json('countries.json',524288)
  for val in [True,float('nan'),181,'0']:
   d=copy.deepcopy(c);g=d['features'][0]['geometry'];ps=[g['coordinates']]if g['type']=='Polygon'else g['coordinates'];ps[0][0][0][0]=val
   with self.assertRaises(m.Refused):m.validate_countries(d)
  d=copy.deepcopy(c);d['features'].append(d['features'][0])
  with self.assertRaises(m.Refused):m.validate_countries(d)
 def test_disclaimer(self):
  raw=(m.ROOT/'nga-disclaimer-official.txt').read_text();ui=(m.ROOT/'nga-disclaimer-ui.txt').read_text();self.assertEqual(ui.replace('and Mapping','andMapping'),raw);self.assertEqual(ui.count('and Mapping'),1);self.assertEqual(hashlib.sha256(raw.encode()).hexdigest(),'130cbe259489eee233f460359915cc94c636d1001f1d5e2c66422c2b81afbcdf');self.assertEqual((m.ROOT/'map.html').read_text().count(html.escape(ui.rstrip('\n'))),2)
 def test_flags(self):
  self.assertFalse(m.prepare({}))
  with self.assertRaises(m.Refused):m.prepare({'PUBLIC_MAP_M2_ENABLED':'true','PUBLIC_MAP_BASE_TILES_ENABLED':'true'})
  with self.assertRaises(m.Refused):m.prepare({'PUBLIC_MAP_M2_ENABLED':'true'})
 def test_http_latest100(self):
  raw={'geo':[{'country':'India','title':'a','url':'https://news.example.com/a'},{'country':'Congo','title':'b','url':'https://news.example.com/b'}]};app=create_app(authorize=lambda _:True);m.install(app,'https://app.example.com',lambda:raw);c=app.test_client();x=c.get('/api/map-data',base_url='https://app.example.com');self.assertEqual(x.status_code,200);d=x.json;self.assertEqual(d['rows_unmapped'],1);self.assertFalse(d['tile_provider']['enabled']);self.assertEqual(d['rows'][0]['feature_id'],'IND');self.assertEqual(c.get('/api/map-data?a=1',base_url='https://app.example.com').status_code,400);self.assertNotIn('openstreetmap.org',c.get('/workspace/map',base_url='https://app.example.com').headers['Content-Security-Policy'])
 def test_asset_allowlist(self):
  app=create_app(authorize=lambda _:True);m.install(app,'https://app.example.com',lambda:{'geo':[]});c=app.test_client()
  for name in ['__init__.py','pins.json','crosswalk.json','nga-disclaimer-official.txt','provenance.json','reference_converter.py','LICENSE']:
   for method in ['get','head']:self.assertEqual(getattr(c,method)('/workspace/map-fixture/'+name,base_url='https://app.example.com').status_code,404,name)
 def test_headers_last_hook(self):
  app=create_app(authorize=lambda _:True)
  def poison(r):r.headers['Referrer-Policy']='unsafe-url';r.headers['Cache-Control']='public,max-age=999';r.headers['Content-Security-Policy']='bad';return r
  app.after_request_funcs.setdefault(None,[]).insert(0,poison);m.install(app,'https://app.example.com',lambda:{'geo':[]});app.after_request(poison);c=app.test_client()
  self.assertEqual(app.after_request_funcs[None][0].__name__,'headers')
  for path in [m.API,m.ALIAS]+['/workspace/map-fixture/'+x for x in m.ASSETS]+['/workspace/map-fixture/pins.json']:
   for verb in ['get','head']:
    r=getattr(c,verb)(path,base_url='https://app.example.com');self.assertEqual(r.headers['Referrer-Policy'],'no-referrer');self.assertEqual(r.headers['Cache-Control'],'no-store')
  r=c.get(m.PAGE,base_url='https://app.example.com');self.assertEqual(r.headers['Referrer-Policy'],'strict-origin-when-cross-origin');self.assertIn("img-src 'self'",r.headers['Content-Security-Policy'])
 def test_alias_identity(self):
  app=create_app(authorize=lambda _:True);app.view_functions['v1_read_10']=lambda:'changed'
  with self.assertRaises(m.Refused):m.install(app,'https://app.example.com',lambda:{'geo':[]})
 def test_duplicate_alias(self):
  app=create_app(authorize=lambda _:True);app.add_url_rule(m.ALIAS,endpoint='duplicate_alias',view_func=app.view_functions['map_data'],methods=['GET'])
  with self.assertRaises(m.Refused):m.install(app,'https://app.example.com',lambda:{'geo':[]})
 def test_fixture_no_promotion(self):
  with self.assertRaises(m.Refused):m.install(create_app(authorize=lambda _:True),'https://app.example.com',lambda:{'geo':[]},local_provider=m.LocalProvider())
if __name__=='__main__':unittest.main()
