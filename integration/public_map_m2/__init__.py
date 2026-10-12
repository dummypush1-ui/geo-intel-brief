"""OFF-default vector reference candidate. OSM hard-disabled. No new DB client."""
import hashlib,json,math,unicodedata
from pathlib import Path
from threading import BoundedSemaphore
from urllib.parse import urlsplit
from flask import Response,jsonify,request
from integration.public_map_prep import news,Refused,flag,text
ROOT=Path(__file__).resolve().parent
FLAG='PUBLIC_MAP_M2_ENABLED';PAGE='/workspace/map';API='/api/map-data';ALIAS='/api/v1/map-data'
ASSETS={'map.js','map.css','leaflet.js','leaflet.css','countries.json','ports.json'}
PATHS={PAGE,API,ALIAS}|{'/workspace/map-fixture/'+x for x in ASSETS}
OSM_DESCRIPTOR={'url':'https://tile.openstreetmap.org/{z}/{x}/{y}.png','enabled':False,'admission':'separate owner decision required'}
BASE_PIN='77137ebf1d8debef70bc49bdc0a253c9b4845429135431af9e8e46328217dff7'
def finite(v):return type(v)in(int,float)and math.isfinite(v)
def validate_countries(x):
 if type(x)is not dict or set(x)!={'type','features'}or x['type']!='FeatureCollection' or type(x['features'])is not list or not 1<=len(x['features'])<=256:raise Refused('Country schema')
 count=0;seen=set()
 for f in x['features']:
  if type(f)is not dict or set(f)!={'type','id','properties','geometry'}or f['type']!='Feature':raise Refused('Feature schema')
  ident=text(f['id'],16);p=f['properties'];g=f['geometry']
  if not ident.isascii()or not ident.isalnum()or ident in seen or type(p)is not dict or set(p)!={'id','name'}or p['id']!=ident:raise Refused('Country identity')
  seen.add(ident);text(p['name'],100)
  if type(g)is not dict or set(g)!={'type','coordinates'}or g['type']not in('Polygon','MultiPolygon'):raise Refused('Geometry schema')
  polys=[g['coordinates']]if g['type']=='Polygon'else g['coordinates']
  if type(polys)is not list or not 1<=len(polys)<=32:raise Refused('Polygon cap')
  for poly in polys:
   if type(poly)is not list or not 1<=len(poly)<=8:raise Refused('Ring cap')
   for ring in poly:
    if type(ring)is not list or not 4<=len(ring)<=1024 or ring[0]!=ring[-1]:raise Refused('Ring bound')
    count+=len(ring)
    if count>12000:raise Refused('Coordinate cap')
    for xy in ring:
     if type(xy)is not list or len(xy)!=2 or not all(finite(v)for v in xy)or not -180<=xy[0]<=180 or not -90<=xy[1]<=90:raise Refused('Coordinate bound')
    if len({tuple(xy)for xy in ring})<3:raise Refused('Degenerate ring')
 return seen

def validate_ports(x):
 if type(x)is not list or len(x)>4000:raise Refused('Port bound')
 seen=set()
 for p in x:
  if type(p)is not dict or set(p)!={'id','name','country_code','lat','lon'}:raise Refused('Port schema')
  ident=text(p['id'],32)
  if not ident.startswith('WPI2019-')or not ident[8:].isdigit()or ident in seen:raise Refused('Port identity')
  seen.add(ident);text(p['name'],100);text(p['country_code'],8)
  if not finite(p['lat'])or not finite(p['lon'])or not -90<=p['lat']<=90 or not -180<=p['lon']<=180:raise Refused('Port coordinate')
 return seen

def load_json(name,cap):
 raw=(ROOT/name).read_bytes()
 if len(raw)>cap:raise Refused('Artifact bytes')
 def pairs(items):
  out={}
  for k,v in items:
   if k in out:raise Refused('Duplicate JSON key')
   out[k]=v
  return out
 return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in()).throw(Refused('Nonfinite JSON')))

def references():
 pins=json.loads((ROOT/'pins.json').read_text())
 for name,h in pins.items():
  if '/'in name or name=='pins.json' or hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=h:raise Refused('M2 artifact drift')
 countries=load_json('countries.json',524288);ports=load_json('ports.json',524288);aliases=load_json('crosswalk.json',32768);ids=validate_countries(countries);validate_ports(ports)
 if type(aliases)is not dict or len(aliases)>512 or 'Congo'in aliases:raise Refused('Crosswalk ambiguity')
 normal={}
 for alias,ident in aliases.items():
  text(alias,100);text(ident,16);key=unicodedata.normalize('NFC',alias.strip())
  if ident not in ids or key in normal:raise Refused('Alias collision')
  normal[key]=ident
 return normal

def prepare(env):
 on=flag(env,FLAG)
 if not on:return False
 if flag(env,'PUBLIC_MAP_BASE_TILES_ENABLED'):raise Refused('OSM hard-disabled in M2')
 if env.get('PUBLIC_MAP_ENABLED')!='true' or env.get('PREVIEW_PUBLIC_SAMPLE_ENABLED')!='true':raise Refused('Public map composition required')
 references()
 from integration.news_api import __file__ as source
 if hashlib.sha256(Path(source).read_bytes()).hexdigest()!=BASE_PIN:raise Refused('M2 base drift')
 return True

class LocalProvider:
 """Exact loopback fixture route only, never an environment/provider URL."""
 pass

def install(app,origin,reader,*,local_provider=None):
 if not callable(reader):raise Refused('Existing public reader required')
 if local_provider is not None:
  p=urlsplit(origin)
  if type(local_provider)is not LocalProvider or p.scheme!='http' or p.hostname not in('127.0.0.1','localhost'):raise Refused('Local provider only')
 aliases=references();slots=BoundedSemaphore(2)
 from integration.news_api import create_app
 for endpoint,path in [('map_workspace',PAGE),('map_data',API)]:
  original=next(c for c in create_app.__code__.co_consts if hasattr(c,'co_name')and c.co_name==endpoint)
  rules=[r for r in app.url_map.iter_rules()if r.endpoint==endpoint]
  if getattr(app.view_functions.get(endpoint),'__code__',None)is not original or len(rules)!=1 or rules[0].rule!=path:raise Refused('Exact M2 seam')
 alias_rules=[r for r in app.url_map.iter_rules()if r.rule==ALIAS]
 if len(alias_rules)!=1 or alias_rules[0].endpoint!='v1_read_10' or app.view_functions.get('v1_read_10')is not app.view_functions['map_data']:raise Refused('Exact M2 alias seam')
 def shell():
  body=(ROOT/'map.html').read_text();body=body.replace('data-local="false"','data-local="true"')if local_provider else body
  return Response(''if request.method=='HEAD'else body,mimetype='text/html')
 def data():
  if request.method=='HEAD':return Response(status=200)
  if not slots.acquire(False):return jsonify(state='busy'),429
  try:
   raw=reader()
   if type(raw)is not dict or type(raw.get('geo'))is not list or len(raw['geo'])>100:raise Refused('Latest100 required')
   # Normalize labels only for lookup; preserve original row labels in output.
   dynamic={}
   for r in raw['geo']:
    if type(r)is not dict:raise Refused('Plain raw row')
    label=r.get('country','')
    if type(label)is str:dynamic[label]=aliases.get(unicodedata.normalize('NFC',label.strip()))
   out=news(raw,{k:v for k,v in dynamic.items()if v is not None});out['rows_rejected']=len(raw['geo'])-len(out['rows']);out.update(reference='Historical WPI 2019 reference, not navigation/port availability',tile_provider=OSM_DESCRIPTOR,ships='no approved free public feed')
   encoded=json.dumps(out,ensure_ascii=True,separators=(',',':')).encode()
   if len(encoded)>262144:raise Refused('News response cap')
   return Response(encoded,mimetype='application/json')
  except Exception:return jsonify(state='news_unavailable',news_available=False),503
  finally:slots.release()
 app.view_functions['map_workspace']=shell;app.view_functions['map_data']=data
 for rule in list(app.url_map.iter_rules()):
  if rule.rule==ALIAS:app.view_functions[rule.endpoint]=data
 @app.get('/workspace/map-fixture/<name>')
 def m2_assets(name):
  if name not in ASSETS:return jsonify(state='unavailable'),404
  mime='application/json'if name.endswith('.json')else'application/javascript'if name.endswith('.js')else'text/css'
  return Response(b''if request.method=='HEAD'else(ROOT/name).read_bytes(),mimetype=mime)
 @app.before_request
 def guard():
  if request.path.startswith('/workspace/map-fixture/')or request.path in(PAGE,API,ALIAS):
   if request.query_string:return jsonify(state='invalid_query'),400
   if request.host_url.rstrip('/')!=origin or request.method not in('GET','HEAD'):return jsonify(state='unavailable'),403
 @app.after_request
 def headers(response):
  if request.path==PAGE:
   response.headers['Referrer-Policy']='strict-origin-when-cross-origin';response.headers['Content-Security-Policy']="default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"
  if request.path in(API,ALIAS)or request.path.startswith('/workspace/map-fixture/'):
   response.headers['Referrer-Policy']='no-referrer'
   response.headers['Cache-Control']='no-store'
  return response
 hooks=app.after_request_funcs[None];hooks.remove(headers);hooks.insert(0,headers)
