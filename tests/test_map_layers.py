import unittest,copy,hashlib
from integration.map_layers import build_layers
NOW='2026-10-06T00:00:00Z';BOX={'south':-90,'north':90,'west':-180,'east':180,'antimeridian':False}
def port(**kw):return dict({'id':'port1','name':'Fixture','lat':0,'lon':0,'source_url':'https://example.com/data?token=x','country':'India','dataset':'fixture','version':'v1','licence':'unverified','provenance':'unverified_fixture'},**kw)
def envelope(points=None):return {'bbox':dict(BOX),'layers':{k:{'status':'available' if k=='ports' else 'empty','observed_at':NOW,'points':points if k=='ports' and points is not None else [port()] if k=='ports' else []} for k in ('ports','vessels','news')}}
class Tests(unittest.TestCase):
 def test_mixed_empty_invalid_atomic(self):
  e=envelope();r=build_layers(e,now=NOW);self.assertEqual(r['layers']['ports']['status'],'available');self.assertEqual(r['layers']['news']['status'],'empty');self.assertNotIn('?',r['layers']['ports']['points'][0]['source_url']);e['layers']['ports']['points']=[port(lat=True)];r=build_layers(e,now=NOW);self.assertEqual(r['layers']['ports']['status'],'invalid');self.assertEqual(r['layers']['news']['status'],'empty')
 def test_coords_caps_duplicates_private(self):
  for points in [[port(lat=v)] for v in [True,float('nan'),float('inf'),10**100,'1']]+[[port()]*101,[port(),port(name='conflict')],[dict(port(),private='x')]]:self.assertEqual(build_layers(envelope(points),now=NOW)['layers'].get('ports',{'status':'invalid'})['status'],'invalid')
  self.assertEqual(len(build_layers(envelope([port(),port()]),now=NOW)['layers']['ports']['points']),1)
 def test_clock_boundaries_future_stale(self):
  for stamp in ['1970-01-01T00:00:00+01:00','2100-12-31T23:30:00-01:00']:
   e=envelope();e['layers']['ports']['observed_at']=stamp;self.assertEqual(build_layers(e,now=NOW)['layers']['ports']['status'],'invalid')
  e=envelope();e['layers']['ports']['observed_at']='2026-10-07T00:00:00Z';self.assertEqual(build_layers(e,now=NOW)['layers']['ports']['age'],'future')
 def test_bbox_antimeridian_and_half(self):
  e=envelope([port(lon=179)]);e['bbox'].update(west=170,east=-170,antimeridian=True);self.assertEqual(build_layers(e,now=NOW)['layers']['ports']['status'],'available');e['layers']['ports']['points']=[port(lon=0)];self.assertEqual(build_layers(e,now=NOW)['layers']['ports']['status'],'invalid');e['bbox']['antimeridian']=False;self.assertEqual(build_layers(e,now=NOW)['status'],'invalid')
 def test_vessel_news_crosskind_and_age(self):
  e=envelope();v={'id':'port1','name':'Shipfixture','lat':0,'lon':0,'source_url':'https://example.com','imo':'1234567','mmsi':'123456789','reported_at':None};e['layers']['vessels']={'status':'available','observed_at':NOW,'points':[v]};r=build_layers(e,now=NOW);self.assertEqual(r['layers']['vessels']['points'][0]['freshness'],'unknown');self.assertEqual(len(r['layers']['ports']['points']),1)
  url='https://example.com/a';n={'id':'n1','name':'Newsfixture','lat':0,'lon':0,'source_url':url,'url':url,'project':'geo','article_key':hashlib.sha256(('geo\n'+url).encode()).hexdigest(),'published_at':'2000-01-01T00:00:00Z','located_at':NOW};e['layers']['news']={'status':'available','observed_at':NOW,'points':[n]};self.assertEqual(build_layers(e,now=NOW)['layers']['news']['points'][0]['freshness'],'fresh')
 def test_url_controls_unknown_status_aliasing(self):
  for v in ['https://exa mple.com/a','https://user:pass@example.com','https://example.com/a b','https://example.com\\a']:
   self.assertEqual(build_layers(envelope([port(source_url=v)]),now=NOW)['layers']['ports']['status'],'invalid')
  self.assertEqual(build_layers(envelope([port(name='bad\u200b')]),now=NOW)['layers']['ports']['status'],'invalid')
  e=envelope();old=copy.deepcopy(e);r=build_layers(e,now=NOW);r['layers']['ports']['points'][0]['name']='changed';self.assertEqual(e,old);e['layers']['ports']['status']='bogus';self.assertEqual(build_layers(e,now=NOW)['layers']['ports']['status'],'invalid')

 def test_unavailable_malformed_half_stale_and_identifiers(self):
  e=envelope();e['layers']['ports']={'status':'unavailable','observed_at':None,'points':[]};self.assertEqual(build_layers(e,now=NOW)['layers']['ports']['status'],'unavailable')
  e['layers']['ports']['points']=[port()];self.assertEqual(build_layers(e,now=NOW)['layers']['ports']['status'],'invalid')
  p=port();p.pop('lon');self.assertEqual(build_layers(envelope([p]),now=NOW)['layers']['ports']['status'],'invalid')
  v={'id':'v','name':'Fixture','lat':0,'lon':0,'source_url':'https://example.com','imo':'１２３４５６７','mmsi':'','reported_at':'2026-10-01T00:00:00Z'}
  e=envelope();e['layers']['vessels']={'status':'available','observed_at':NOW,'points':[v]};self.assertEqual(build_layers(e,now=NOW)['layers']['vessels']['status'],'invalid')
  v['imo']='1234567';self.assertEqual(build_layers(e,now=NOW)['layers']['vessels']['points'][0]['freshness'],'stale')
  v['reported_at']='2026-10-07T00:00:00Z';self.assertEqual(build_layers(e,now=NOW)['layers']['vessels']['points'][0]['freshness'],'future')

 def test_news_identity_not_opaque_and_vessel_identifier_collision(self):
  e=envelope();u='https://example.com/a';n={'id':'n1','name':'News','lat':0,'lon':0,'source_url':u,'url':u,'project':'geo','article_key':hashlib.sha256(('geo\n'+u).encode()).hexdigest(),'published_at':None,'located_at':NOW}
  e['layers']['news']={'status':'available','observed_at':NOW,'points':[n,dict(n,id='n2')]}
  self.assertEqual(len(build_layers(e,now=NOW)['layers']['news']['points']),1)
  e['layers']['news']['points'][1]['lat']=45;self.assertEqual(build_layers(e,now=NOW)['layers']['news']['status'],'invalid')
  v={'id':'v1','name':'Ship','lat':0,'lon':0,'source_url':u,'imo':'1234567','mmsi':'','reported_at':NOW};e['layers']['vessels']={'status':'available','observed_at':NOW,'points':[v,dict(v,id='v2')]}
  self.assertEqual(build_layers(e,now=NOW)['layers']['vessels']['status'],'invalid')
 def test_input_node_key_and_overall_byte_bound(self):
  e=envelope([dict(port(),**{'k'+str(i):'x' for i in range(10000)})]);self.assertEqual(build_layers(e,now=NOW)['status'],'invalid')
  e=envelope();e[1]='bad';self.assertEqual(build_layers(e,now=NOW)['status'],'invalid')
  e=envelope();e['layers']['ports']['points']=[port(id=str(i),source_url='https://example.com/'+'x'*1900) for i in range(100)]
  # Bound wellformed layers without silently truncating; large envelope refused.
  e['layers']['ports']['extra']='x'*3000;self.assertEqual(build_layers(e,now=NOW)['status'],'invalid')
 def test_multibyte_overall_and_layer_byte_budgets(self):
  e=envelope([port(id=str(i),name='界'*100,source_url='https://example.com/'+'界'*1900) for i in range(100)])
  # Per-layer512KiB result refused, nottruncated, whileinertinput<1MiB.
  self.assertEqual(build_layers(e,now=NOW)['layers']['ports']['status'],'invalid')
  e=envelope();u='https://example.com/'+'界'*1900
  e['layers']['ports']['points']=[port(id=str(i),name='界'*100,source_url=u) for i in range(100)]
  e['layers']['vessels']={'status':'available','observed_at':NOW,'points':[{'id':str(i),'name':'界'*100,'lat':0,'lon':0,'source_url':u,'imo':'','mmsi':'','reported_at':NOW} for i in range(100)]}
  e['layers']['news']={'status':'available','observed_at':NOW,'points':[{'id':str(i),'name':'界'*100,'lat':0,'lon':0,'source_url':u,'project':'geo','article_key':hashlib.sha256(('geo\n'+u+str(i)).encode()).hexdigest(),'url':u+str(i),'published_at':NOW,'located_at':NOW} for i in range(100)]}
  self.assertEqual(build_layers(e,now=NOW)['status'],'invalid')
