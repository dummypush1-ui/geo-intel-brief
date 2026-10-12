"""M1 default-OFF local-fixture candidate. No admitted real ports/countries/tiles.
Environment cannot enable OSM or a dataset. FakeMap is an explicit test input.
"""
import hashlib,json,math,re
from pathlib import Path
from threading import BoundedSemaphore
from urllib.parse import urlsplit
from flask import Response,jsonify,request
from integration.news_view import views
from integration.public_news import public_news_row
ROOT=Path(__file__).resolve().parent
FLAG='PUBLIC_MAP_ENABLED'
PAGE='/workspace/map';API='/api/map-data';ALIAS='/api/v1/map-data'
ASSETS={'map.js','map.css','leaflet.js','leaflet.css'}
PATHS={PAGE,API,ALIAS}|{'/workspace/map-fixture/'+x for x in ASSETS}
BASE_PIN='77137ebf1d8debef70bc49bdc0a253c9b4845429135431af9e8e46328217dff7'
PINS={'leaflet.js': 'db49d009c841f5ca34a888c96511ae936fd9f5533e90d8b2c4d57596f4e5641a', 'leaflet.css': 'a7837102824184820dfa198d1ebcd109ff6d0ff9a2672a074b9a1b4d147d04c6', 'LICENSE': '53e8dc25862014e4324741ca18fbe3611e11d42ef69f59f86ea8c5389647d4cb', 'map.css': '46710624cd8e582c15d666883c97700f43b8f09a22701ffa39f112120d86e6df', 'map.html': '121260e7aef529bcecbd6acaf646e7e682c25755b18c7975563779b5515db603', 'map.js': '442f35d803aca1199bb2aff22db8a3e83524d515ad694e2b166ef2711368eb0a'}
class Refused(ValueError):pass

def flag(env,key):
 v=env.get(key,'false')
 if v not in ('true','false'):raise Refused('Exact map flag required')
 return v=='true'
def prepare(env):
 on=flag(env,FLAG)
 for key in ('PUBLIC_MAP_BASE_TILES_ENABLED','PUBLIC_MAP_NEWS_ENABLED'):
  if flag(env,key) and not on:raise Refused('Map dependency required')
 if not on:return False
 if env.get('PREVIEW_PUBLIC_SAMPLE_ENABLED')!='true':raise Refused('Public composition required')
 # No environment-only live admission. Verify code pins, not data assertions.
 for p,h in PINS.items():
  if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h:raise Refused('Map asset drift')
 from integration.news_api import __file__ as source
 if hashlib.sha256(Path(source).read_bytes()).hexdigest()!=BASE_PIN:raise Refused('Map base drift')
 return True

def text(v,cap,empty=False):
 if type(v)is not str or len(v)>cap or (not empty and not v.strip()) or any(ord(c)<32 or ord(c)==127 for c in v):raise Refused('Bounded text')
 try:v.encode('utf-8')
 except UnicodeError:raise Refused('Invalid UTF8')from None
 return v

def url(v):
 try:
  text(v,2048);p=urlsplit(v)
  if p.scheme!='https' or not p.hostname or p.username or p.password or p.port not in (None,443) or any(c.isspace() for c in v) or '\\' in v:return None
  return v
 except (Refused,ValueError):return None

def news(raw,crosswalk):
 if type(raw)is not dict or set(raw)-{'geo','brics'} or 'geo'not in raw or type(raw['geo'])is not list or len(raw['geo'])>100 or ('brics'in raw and raw['brics']!=[]):raise Refused('Latest100 Geo required')
 clean=[];reject=0;seen=set();unmapped=0
 # raw input cap before normalization, independent of caller/store.
 for r in views({'geo':raw['geo']}):
  r=public_news_row(r)
  try:
   t=text(r.get('title'),2048);u=url(r.get('url'))
   if not u or r.get('project')!='geo':raise Refused('Unsafe source')
   key=text(r.get('article_key'),100);country=text(r.get('original_country',''),100,True)
   source=text(r.get('source',''),100,True)
   if key in seen:raise Refused('Duplicate article')
   seen.add(key);fid=crosswalk.get(country)
   if fid is None:unmapped+=1
   clean.append({'title':t,'url':u,'source':source,'article_key':key,'project':'geo','country':country,'feature_id':fid})
  except Refused:reject+=1
 return {'rows':clean,'rows_seen':len(raw['geo']),'rows_unmapped':unmapped,'rows_rejected':reject,'scope':'country-level latest-100 Geo view only; not full-store or precise event locations'}

class FakeMap:
 def __init__(self,reader,*,clock=lambda:0):
  if not callable(reader):raise Refused('Fixture reader required')
  self.reader=reader;self.clock=clock;self.slots=BoundedSemaphore(2)
  self.country={'type':'FeatureCollection','features':[{'type':'Feature','properties':{'id':'FX-A','name':'SIMULATED India'},'geometry':{'type':'Polygon','coordinates':[[[65,5],[95,5],[95,35],[65,35],[65,5]]]}}]}
  self.crosswalk={'India':'FX-A'}
 def payload(self):
  out=news(self.reader(),self.crosswalk);out.update(fixture_only=True,news_available=True,news_empty=not out['rows'],countries=self.country,ports={'available':False,'note':'Ports unavailable: official archive and country dataset not admitted.'},ships={'available':False,'note':'Live ship positions unavailable: no approved free public feed.'},tile_url='/workspace/map-fixture/tiles/{z}/{x}/{y}.png',generated_at='SIMULATED time')
  raw=json.dumps(out,ensure_ascii=True,separators=(',',':')).encode()
  if len(raw)>262144:raise Refused('Map JSON bound')
  return raw

def install(app,origin,fixture=None):
 if fixture is not None and type(fixture)is not FakeMap:raise Refused('Exact fixture required')
 if fixture is not None:
  p=urlsplit(origin)
  if p.scheme!='http' or p.hostname not in ('127.0.0.1','localhost'):raise Refused('Local fixture only')
 from integration.news_api import create_app
 for endpoint,path in [('map_workspace',PAGE),('map_data',API)]:
  original=next(c for c in create_app.__code__.co_consts if hasattr(c,'co_name')and c.co_name==endpoint)
  rules=[r for r in app.url_map.iter_rules()if r.endpoint==endpoint]
  if getattr(app.view_functions.get(endpoint),'__code__',None)is not original or len(rules)!=1 or rules[0].rule!=path or rules[0].methods!={'GET','HEAD','OPTIONS'}:raise Refused('Exact map seam required')
 def shell():return Response(''if request.method=='HEAD'else(ROOT/'map.html').read_text(),mimetype='text/html')
 def data():
  if request.method=='HEAD':return Response(status=200)
  if fixture is None:return jsonify(state='held',news_available=False,fixture_only=False,live_on_blocked=True,note='Public map held: datasets and tile policy not admitted.'),503
  if not fixture.slots.acquire(blocking=False):return jsonify(state='busy'),429
  try:return Response(fixture.payload(),mimetype='application/json')
  except Exception:return jsonify(state='news_unavailable',news_available=False),503
  finally:fixture.slots.release()
 app.view_functions['map_workspace']=shell;app.view_functions['map_data']=data
 for rule in list(app.url_map.iter_rules()):
  if rule.rule==ALIAS:app.view_functions[rule.endpoint]=data
 @app.get('/workspace/map-fixture/<name>')
 def map_asset(name):
  if name not in ASSETS:return jsonify(state='unavailable'),404
  return Response(b''if request.method=='HEAD'else(ROOT/name).read_bytes(),mimetype='application/javascript'if name.endswith('.js')else'text/css')
 # Deliberately no server tiles route; browser test owns local tile responses.
 @app.before_request
 def map_guard():
  if request.path.startswith('/workspace/map-fixture/')or request.path in (PAGE,API,ALIAS):
   if request.query_string:return jsonify(state='invalid_query'),400
   if request.host_url.rstrip('/')!=origin or request.method not in ('GET','HEAD'):return jsonify(state='unavailable'),403
   if request.method=='HEAD':return Response(status=200)
 @app.after_request
 def map_headers(response):
  if request.path==PAGE:
   response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
   response.headers['Content-Security-Policy']="default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"
  elif request.path in (API,ALIAS) or request.path.startswith('/workspace/map-fixture/'):
   response.headers['Referrer-Policy']='no-referrer'
  return response
 # Flask executes in reverse registration order; first hook runs LAST.
 hooks=app.after_request_funcs[None];hooks.remove(map_headers);hooks.insert(0,map_headers)
 app.extensions['public_map_fixture']=fixture
