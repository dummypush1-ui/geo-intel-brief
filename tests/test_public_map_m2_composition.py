import os
import sys,unittest,json,copy,resource,importlib.util
from pathlib import Path
from unittest.mock import patch,Mock
ROOT=Path(__file__).resolve().parents[1];BASE=Path(os.environ.get('M2_BASE',str(ROOT)));sys.path.insert(0,str(BASE));import integration;integration.__path__.insert(0,str(ROOT/'integration'))
from integration import public_map_m2 as m
from integration.public_preview_builder import build_public_preview
from integration.public_live_builder import build_public_live_preview
from tests.test_code_news_coverage_binding_prep import SAMPLE,LIVE,ORIGIN,Client
LIVE={**LIVE,'PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED':'false','PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED':'false','PUBLIC_NEWS_FULL_PAGES_ENABLED':'false'}
def old(name):
 ns={'__file__':str(BASE/'integration'/('public_'+name+'_builder.py'))};exec(compile((ROOT/'tests/fixtures'/('map_m2_base_'+name+'.txt')).read_text(),ns['__file__'],'exec'),ns);return ns['build_public_preview'if name=='preview'else'build_public_live_preview']
class Tests(unittest.TestCase):
 def test_off_byte_equal(self):
  for name,builder,env in [('preview',build_public_preview,SAMPLE),('live',build_public_live_preview,LIVE)]:
   def make(b,e):return b(e)if name=='preview'else b(e,client_factory=lambda *a,**k:Client())
   for flags in [{},{'PUBLIC_MAP_ENABLED':'false'},{'PUBLIC_MAP_ENABLED':'true'},{'PUBLIC_MAP_ENABLED':'true','PUBLIC_MAP_M2_ENABLED':'false'},{'PUBLIC_MAP_ENABLED':'true','PUBLIC_MAP_BASE_TILES_ENABLED':'true'}]:
    x,y=make(old(name),dict(env,**flags)),make(builder,dict(env,**flags))
    for path in ['/workspace','/workspace/map','/api/map-data','/api/v1/map-data','/workspace/map-fixture/map.js','/workspace/map-fixture/countries.json']:
     for verb in ['get','head','post','options']:
      from datetime import datetime,timezone
     with patch('integration.news_api.datetime')as dt:
      dt.now.return_value=datetime(2026,10,12,tzinfo=timezone.utc);a,b=getattr(x.test_client(),verb)(path,base_url=ORIGIN),getattr(y.test_client(),verb)(path,base_url=ORIGIN)
     self.assertEqual((a.status_code,a.data,dict(a.headers)),(b.status_code,b.data,dict(b.headers)))
 def test_on_sample_and_live_existing_reader(self):
  raw={'geo':[{'title':'India','country':'India','url':'https://news.example.com/a','secret':'PRIVATE'},{'title':'Ambiguous','country':'Congo','url':'https://news.example.com/b'}]}
  for builder,env in [(build_public_preview,SAMPLE),(build_public_live_preview,LIVE)]:
   e=dict(env,PUBLIC_MAP_ENABLED='true',PUBLIC_MAP_M2_ENABLED='true');calls=[]
   def read():calls.append(1);return raw
   with patch('integration.public_live_builder.ReadOnlyNewsReader',return_value=read):
    app=builder(e)if builder is build_public_preview else builder(e,client_factory=lambda *a,**k:Client())
   c=app.test_client();self.assertEqual(c.head(m.API,base_url=ORIGIN).status_code,200);self.assertFalse(calls)
   r=c.get(m.API,base_url=ORIGIN);self.assertEqual(r.status_code,200);self.assertFalse(r.json['tile_provider']['enabled']);self.assertNotIn('PRIVATE',r.text)
   self.assertEqual(len(r.json['rows']),0 if builder is build_public_preview else 2)
   if builder is build_public_live_preview:
    self.assertEqual(len(calls),1);self.assertEqual(r.json['rows'][0]['feature_id'],'IND');c.get('/api/news',base_url=ORIGIN);self.assertEqual(len(calls),1,'same cached reader')
   self.assertIn('Trade reference map',c.get(m.PAGE,base_url=ORIGIN).text)
   for path in m.PATHS:
    self.assertEqual(c.get(path,base_url=ORIGIN).status_code,200,path)
    self.assertEqual(c.get(path+'?bad=1',base_url=ORIGIN).status_code,400,path)
    self.assertEqual(c.get(path,base_url='https://evil.test').status_code,403,path)
    for verb in ['post','options','delete']:self.assertEqual(getattr(c,verb)(path,base_url=ORIGIN).status_code,403,path)
   self.assertEqual(c.get('/workspace/map-fixture/tiles/2/1/1.png',base_url=ORIGIN).status_code,403)
 def test_M1_base_flag_OFF_preserved(self):
  app=build_public_preview(dict(SAMPLE,PUBLIC_MAP_ENABLED='true',PUBLIC_MAP_BASE_TILES_ENABLED='true'));r=app.test_client().get(m.API,base_url=ORIGIN);self.assertEqual(r.status_code,503);self.assertTrue(r.json['live_on_blocked'])
 def test_flags_before_client(self):
  for e in [{m.FLAG:'true'},dict(LIVE,PUBLIC_MAP_ENABLED='true',PUBLIC_MAP_M2_ENABLED='bad'),dict(LIVE,PUBLIC_MAP_ENABLED='true',PUBLIC_MAP_M2_ENABLED='true',PUBLIC_MAP_BASE_TILES_ENABLED='true')]:
   factory=Mock()
   with self.assertRaises(ValueError):build_public_live_preview(e,client_factory=factory)
   factory.assert_not_called()
 def test_boundaries(self):
  def feat(id='AAA',ring=None):return {'type':'Feature','id':id,'properties':{'id':id,'name':id},'geometry':{'type':'Polygon','coordinates':[ring or [[0,0],[1,0],[1,1],[0,0]]]}}
  def coll(f=None):return {'type':'FeatureCollection','features':f or [feat()]}
  self.assertEqual(m.validate_countries(coll()),{'AAA'})
  cases=[coll([feat(),feat()]),coll([feat(ring=[[i%2,i%3]for i in range(1024)]+[[0,0]])]),coll([feat(ring=[[0,0],[1,0],[1,1],[2,2]])]),coll([feat(ring=[[0,0],[1,0],[0,0],[0,0]])])]
  for case in cases:
   with self.assertRaises(m.Refused):m.validate_countries(case)
  for mutation in ['features','polygons','rings','total']:
   x=coll()
   if mutation=='features':x['features']=[feat(str(i))for i in range(257)]
   elif mutation=='polygons':x['features'][0]['geometry']={'type':'MultiPolygon','coordinates':[[[[0,0],[1,0],[1,1],[0,0]]]]*33}
   elif mutation=='rings':x['features'][0]['geometry']['coordinates']*=9
   else:x['features']=[feat(str(i),[[j%2,j%3]for j in range(999)]+[[0,0]])for i in range(13)]
   with self.assertRaises(m.Refused):m.validate_countries(x)
  ports=m.load_json('ports.json',524288)
  for x in [ports+[ports[0]],ports*2,[dict(ports[0],lat=True)],[dict(ports[0],lon=181)],[dict(ports[0],id='catalogue-code')],[dict(ports[0],extra=1)]]:
   with self.assertRaises(m.Refused):m.validate_ports(x)
  original=m.load_json
  for aliases in [{'Congo':'COG'},{'India':'NOPE'},{'India':'IND',' India ':'IND'}]:
   with patch.object(m,'load_json',side_effect=lambda n,c:aliases if n=='crosswalk.json'else original(n,c)):
    with self.assertRaises(m.Refused):m.references()
if __name__=='__main__':unittest.main()
