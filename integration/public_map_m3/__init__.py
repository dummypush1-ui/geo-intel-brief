"""Default-OFF hosted OpenFreeMap street layer over preserved M2 references.
No server source fetch, proxy, tile cache, private data or automatic activation.
"""
import hashlib,json
from pathlib import Path
from flask import Response,jsonify,request
from integration.public_map_prep import flag,Refused
ROOT=Path(__file__).resolve().parent
FLAG='PUBLIC_MAP_M3_ENABLED'
PREFIX='/workspace/map-streets/'
ASSETS={'maplibre.js','maplibre-worker.js','maplibre.css','leaflet-maplibre.js','streets.js','streets.css','liberty.json','OPENFREEMAP-STYLES-LICENSE.txt','LIBERTY-LICENSE.txt','MAPLIBRE-LICENSE.txt','LEAFLET-MAPLIBRE-LICENSE.txt'}
PATHS={PREFIX+n for n in ASSETS}
CSP="default-src 'none'; script-src 'self'; worker-src 'self'; style-src 'self'; img-src 'self' data: https://tiles.openfreemap.org; connect-src 'self' https://tiles.openfreemap.org; frame-ancestors 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"
CREDIT='''<p id="m3-credit" aria-label="Street map data credit"><a href="https://openfreemap.org/" target="_blank" rel="noopener noreferrer">OpenFreeMap</a> | <a href="https://www.openmaptiles.org/" target="_blank" rel="noopener noreferrer">© OpenMapTiles</a> | Data from <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">© OpenStreetMap contributors</a></p>'''

def prepare(env):
 on=flag(env,FLAG)
 if not on:return False
 if any(env.get(k)!='true' for k in ('PREVIEW_PUBLIC_SAMPLE_ENABLED','PUBLIC_MAP_ENABLED','PUBLIC_MAP_M2_ENABLED')):raise Refused('M3 requires public M2 composition')
 pins=json.loads((ROOT/'pins.json').read_text())
 if set(pins)!=ASSETS:raise Refused('M3 exact assets required')
 for n,h in pins.items():
  if hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=h:raise Refused('M3 asset drift')
 from integration import public_map_m2 as m2
 if hashlib.sha256((m2.ROOT/'map.html').read_bytes()).hexdigest()!='e683a88f437a2ca0c34ccb5337cba14ce9d93ca0fc2875c25f5204bb4f0e9e2b':raise Refused('M3 M2 shell drift')
 return True

def transform(body):
 if body.count('</head>')!=1 or body.count('</body>')!=1 or body.count('<div id="map" aria-label="Reference map"></div>')!=1:raise Refused('M3 exact served shell required')
 controls='''<section id="m3-controls"><h2>Online street map (optional)</h2><p>Hosted OpenFreeMap needs internet. Clicking sends map-view requests to OpenFreeMap/Cloudflare, not your news or search text. Free/as-is, no uptime guarantee; not navigation or legal boundaries. <a href="https://openfreemap.org/tos/" target="_blank" rel="noopener noreferrer">Terms</a> / <a href="https://openfreemap.org/privacy/" target="_blank" rel="noopener noreferrer">Privacy</a>. Countries and historical ports remain usable without it.</p><button id="m3-start" type="button">Show online streets</button><button id="m3-stop" type="button">Use country map only</button><p id="m3-status" role="status">Streets not requested. Load the reference map first, then choose streets.</p><details><summary>Map software and style notices</summary><p>Unmodified Liberty style by OpenFreeMap / OSM Liberty / OSM Bright, with OpenMapTiles design. <a href="https://github.com/hyperknot/openfreemap-styles/blob/main/LICENSE.md" target="_blank" rel="noopener noreferrer">Style attribution and licenses</a>. Bundled notices: <a href="/workspace/map-streets/OPENFREEMAP-STYLES-LICENSE.txt">OpenFreeMap styles</a>, <a href="/workspace/map-streets/LIBERTY-LICENSE.txt">Liberty</a>, <a href="/workspace/map-streets/MAPLIBRE-LICENSE.txt">MapLibre</a>, <a href="/workspace/map-streets/LEAFLET-MAPLIBRE-LICENSE.txt">Leaflet adapter</a>. Design: CC BY 4.0 / upstream CC BY 3.0, see linked license notices.</p></details></section>'''
 body=body.replace('<div id="map" aria-label="Reference map"></div>',controls+'<div id="m3-map-wrap"><div id="map" aria-label="Reference map"></div>'+CREDIT+'</div>')
 body=body.replace('Historical reference vectors. Street tiles unavailable.','Historical reference vectors with optional online streets.').replace('<button id="tiles" disabled>Street tiles unavailable</button>','<button id="tiles" disabled hidden>Local raster fixture disabled</button>').replace('Street tiles hard-disabled. Vectors work without them.','Country vectors work without online streets.')
 body=body.replace('</head>','<link rel="stylesheet" href="'+PREFIX+'maplibre.css"><link rel="stylesheet" href="'+PREFIX+'streets.css"></head>')
 body=body.replace('</body>',''.join('<script src="'+PREFIX+n+'" defer></script>'for n in ['maplibre.js','leaflet-maplibre.js','streets.js'])+'</body>')
 return body

def install(app,origin):
 from integration import public_map_m2 as m2
 rules=[r for r in app.url_map.iter_rules()if r.endpoint=='map_workspace']
 expected=next(c for c in m2.install.__code__.co_consts if hasattr(c,'co_name')and c.co_name=='shell')
 previous=app.view_functions.get('map_workspace')
 if len(rules)!=1 or rules[0].rule!=m2.PAGE or getattr(previous,'__code__',None)is not expected:raise Refused('M3 requires mounted M2')
 def shell():
  r=previous()
  if request.method=='HEAD':return r
  r.direct_passthrough=False;r.set_data(transform(r.get_data(as_text=True)));return r
 app.view_functions['map_workspace']=shell
 @app.get(PREFIX+'<name>')
 def m3_assets(name):
  if name not in ASSETS:return jsonify(state='unavailable'),404
  mime='application/json'if name.endswith('.json')else'application/javascript'if name.endswith('.js')else'text/css'if name.endswith('.css')else'text/plain'
  return Response(b''if request.method=='HEAD'else(ROOT/name).read_bytes(),mimetype=mime)
 @app.before_request
 def guard():
  if not request.path.startswith(PREFIX):return
  if request.host_url.rstrip('/')!=origin or request.method not in ('GET','HEAD'):return jsonify(state='unavailable'),403
  if request.query_string:return jsonify(state='invalid_query'),400
 @app.after_request
 def headers(r):
  if request.path==m2.PAGE:
   r.headers['Content-Security-Policy']=CSP;r.headers['Referrer-Policy']='no-referrer';r.headers['Cache-Control']='no-store'
  if request.path.startswith(PREFIX):
   r.headers['Cache-Control']='no-store';r.headers['Referrer-Policy']='no-referrer';r.headers['X-Content-Type-Options']='nosniff'
   if request.path.endswith('maplibre-worker.js'):r.headers['Content-Security-Policy']="default-src 'none'; script-src 'self'; connect-src https://tiles.openfreemap.org;"
  return r
 # Flask after_request runs in reverse; M3 must set the final page CSP after M2.
 hooks=app.after_request_funcs[None];hooks.remove(headers);hooks.insert(0,headers)
 app.extensions['public_map_m3']={'state':'manual_online_streets_available','provider':'OpenFreeMap','offline':False,'server_network':False}
