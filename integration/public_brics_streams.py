"""Public supplied-video wall. No public mutation or availability lookup.
Fixed startup pins are not continuous drift monitoring. Owner management unwired.
"""
from pathlib import Path
import hashlib
from flask import request, Response, jsonify
from integration.brics_streams import video_id, label

ROOT=Path(__file__).resolve().parents[1]
FLAG='PUBLIC_BRICS_STREAMS_ENABLED'
API='/api/brics/streams'
PAGE='/workspace/brics-streams'
PATHS=frozenset((API,PAGE,'/workspace/assets/brics_streams.js','/workspace/assets/brics_streams.css'))
SEEDS=(('Republic','jndNegut8RY'),('Al Jazeera English','gCNeDWCI0vo'),
       ('France24 English','HvZt-nh9sGg'),('DW News','LuKwFajn37U'),('ANI News','nOuWVqeUGt4'))
PINS={'integration/news_api.py': '77137ebf1d8debef70bc49bdc0a253c9b4845429135431af9e8e46328217dff7', 'integration/brics_streams.py': '0add85dfd3b541b2d681daad0d21af4a6320dea89d8c9254baf9a308d9a89b10', 'integration/youtube_links.py': 'd725d910b08cae5317c82f7b9742b0e499396cd9a9d8dfe7be4a7b3e4d958503', 'intelligence/brics/config/streams.yaml': '65c676f7112813ac6196e859ecf88dd0a866118b9ad5801dd8982b2ea9afc0dd', 'integration/ui/live_channels.js': '3d3dd9ac5ae6849679caddaafdda0276002ca929b35287d77e5d98825e2a171b', 'integration/ui/public_brics_streams.html': 'a509bc1dbcfe91213550ad38a793b7b31032b083bba40eaa16a6dbd0400adcf5', 'integration/ui/public_brics_streams.js': 'e8e2fe52fed120a76c570bd7dab65cf7a9ebe2bc5338142df8dd8ed5a254c0a6', 'integration/ui/public_brics_streams.css': '03012562682905040f92a2f297f90c98d9ecca57202638d7ab05b2412a38f0fe'}

def seed_rows():
 if type(SEEDS)is not tuple or len(SEEDS)!=5:raise ValueError('Fixed seed unavailable')
 rows=[]
 for name,vid in SEEDS:
  if type(name)is not str or type(vid)is not str or label(name)!=name or video_id(vid)!=vid:raise ValueError('Fixed seed unavailable')
  rows.append(dict(name=name,video=vid,watch_url='https://www.youtube.com/watch?v='+vid,compulsory=name=='Republic'))
 if len({r['video']for r in rows})!=5 or len({r['name'].casefold()for r in rows})!=5 or sum(r['compulsory']for r in rows)!=1:raise ValueError('Fixed seed unavailable')
 return rows

def prepare(env):
 value=env.get(FLAG,'false')
 if value not in ('true','false'):raise ValueError('Exact public BRICS flag required')
 if value=='false':return False
 if env.get('PREVIEW_PUBLIC_SAMPLE_ENABLED')!='true':raise ValueError('BRICS requires public composition')
 try:
  for name,expected in PINS.items():
   h=hashlib.sha256()
   with (ROOT/name).open('rb')as f:
    while chunk:=f.read(65536):h.update(chunk)
   if h.hexdigest()!=expected:raise ValueError()
  seed_rows()
 except Exception:raise ValueError('Public BRICS pins/seed unavailable')from None
 return True

def install(app):
 from integration.news_api import create_app
 import json
 for endpoint,path in [('brics_stream_workspace',PAGE),('brics_stream_get',API)]:
  old=app.view_functions.get(endpoint)
  code=next((c for c in create_app.__code__.co_consts if hasattr(c,'co_name')and c.co_name==endpoint),None)
  rules=[r for r in app.url_map.iter_rules()if r.endpoint==endpoint]
  if old is None or getattr(old,'__code__',None)is not code or len(rules)!=1 or rules[0].rule!=path or rules[0].methods!={'GET','HEAD','OPTIONS'}or not rules[0].provide_automatic_options:raise ValueError('Public BRICS mount unavailable')
 html=(ROOT/'integration/ui/public_brics_streams.html').read_text()
 if html.count('data-public-brics="true"')!=1:raise ValueError('Public BRICS shell seam unavailable')
 payload=json.dumps(dict(streams=seed_rows(),scope='supplied_video_ids',persistence='browser_extras_only',availability_verified=False),ensure_ascii=True,separators=(',',':')).encode()
 if len(payload)>32768:raise ValueError('Public BRICS response bound')
 def shell():return Response(''if request.method=='HEAD'else html,mimetype='text/html')
 def listing():return Response(b''if request.method=='HEAD'else payload,mimetype='application/json')
 app.view_functions['brics_stream_workspace']=shell
 app.view_functions['brics_stream_get']=listing
 old_assets=app.view_functions['assets']
 def assets(name):
  if name in ('brics_streams.js','brics_streams.css'):
   kind='application/javascript'if name.endswith('.js')else'text/css'
   data=''if request.method=='HEAD'else(ROOT/('integration/ui/public_'+name)).read_text()
   return Response(data,mimetype=kind)
  return old_assets(name)
 app.view_functions['assets']=assets
 @app.before_request
 def brics_query():
  if request.path in PATHS and request.query_string:return jsonify(error='No query parameters accepted'),400
 @app.after_request
 def brics_headers(response):
  if request.path in PATHS:
   response.headers['Cache-Control']='no-store'
   response.headers['Referrer-Policy']='no-referrer'
   response.headers['X-Content-Type-Options']='nosniff'
   response.headers['Content-Security-Policy']=("default-src 'none'; frame-ancestors 'none'"if request.path==API else"default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-src https://www.youtube-nocookie.com; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
  return response
 hooks=app.after_request_funcs[None];hooks.remove(brics_headers);hooks.insert(0,brics_headers)
 app.extensions['public_brics_streams']=True
