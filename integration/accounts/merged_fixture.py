"""Separate memory-only merged account fixture. Never production launcher."""
import json,re
from urllib.parse import urlsplit
from werkzeug.wrappers import Request,Response
from .service import AccountService,COOKIE_NAME
from .store import MemoryStore
from .http_fixture import create_fixture_app

class FixtureNews:
 """Exact bounded inert supplied test rows, not a production reader hook."""
 def __init__(self,rows):
  if type(rows) is not list or len(rows)>100:raise ValueError('Fixture rows required')
  for row in rows:
   if type(row) is not dict or len(row)>30 or any(type(k) is not str or len(k)>100 or type(v) not in (str,int,float,bool,type(None)) for k,v in row.items()):raise ValueError('Inert fixture rows required')
  raw=json.dumps(rows,allow_nan=False,separators=(',',':'))
  if len(raw)>100000:raise ValueError('Bounded fixture rows required')
  self._raw=raw
 def __call__(self):return {'geo':json.loads(self._raw)}

ACCOUNT_GET={'/account/preview','/account/preauth','/account/whoami','/account/settings','/account/assets/account.js','/account/assets/account.css'}
ACCOUNT_POST={'/account/login','/account/signup','/account/logout','/account/save-settings','/account/export','/account/change-password','/account/delete'}
WORKSPACE={'/workspace','/workspace/weekly','/workspace/tariffs','/workspace/countries','/workspace/map','/workspace/brics-streams','/api/brics/streams','/workspace/manifest.webmanifest','/api/news','/api/news-export.csv','/api/news-stats','/api/critical-stories','/api/country-page','/api/country-signals','/api/map-data','/api/tariff-evidence','/api/sample-volume','/api/source-health','/api/dashboard-snapshots','/api/dashboard-signals','/api/story-groups','/api/weekly-report.pdf','/api/export.csv','/digest-data','/critical','/weekly'}

def create_merged_fixture(service,*,origin,client_identity,reader):
 """Explicit closed/test only. Full whoami for every protected request.

No second cookie parser, source/client/env creation, settings sync or old gate
replacement. Caller seeds fixture users before construction; sessions remain
original AccountService-owned. No production readiness inferred.
 """
 try:
  u=urlsplit(origin)
  if type(origin) is not str or u.port is not None or u.scheme!='https' or u.netloc!=u.hostname or not re.fullmatch(r'[a-z0-9]+(?:[.-][a-z0-9]+)*',u.hostname or '') or origin!=origin.lower() or u.path or u.query or u.fragment:raise ValueError()
 except (ValueError,TypeError):raise ValueError('Canonical fixture origin required') from None
 if type(service) is not AccountService or type(service.store) is not MemoryStore or service.mode!='closed' or not service.store.users or service.origins!=frozenset([origin]) or not service.require_origin or type(reader) is not FixtureNews or not callable(client_identity):raise ValueError('Closed memory fixture with seeded users required')
 account=create_fixture_app(service,origin,client_identity)
 from integration.news_api import create_app
 def auth(req):return service.whoami(req.cookies.get(COOKIE_NAME,'' )).get('ok') is True
 workspace=create_app(reader=reader,authorize=auth,allowed_origin=origin)
 # Exact asset route expansion, no arbitrary prefix catch-all.
 from pathlib import Path
 root=Path(__file__).resolve().parents[2]
 assets={'/workspace/assets/'+p.name for p in (root/'integration/ui').glob('*') if p.is_file() and p.suffix in ('.js','.css')}
 branding={'/workspace/branding/'+p.name for p in (root/'integration/branding').glob('*') if p.is_file()}
 finder={'/workspace/finder/'+name for name in ['index.html','icon-192.png','icon-512.png']}
 finder|={'/workspace/finder/'+p.name for p in root.glob('data.*.js') if re.fullmatch(r'data\.[0-9a-f]{12}\.js',p.name)}
 # Existing source owning route enforces narrower file names; unknown stays404.
 allowed=WORKSPACE|assets|branding|finder|{'/fixture-navigation'}
 post_paths={'/api/related-news','/api/finder-context'}
 hardened={'Cache-Control':'no-store','X-Robots-Tag':'noindex, nofollow','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Content-Security-Policy':"default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"}
 def refuse(status=403):return Response('Private memory fixture required',status=status,headers={'Cache-Control':'no-store','X-Robots-Tag':'noindex, nofollow','X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'none'; frame-ancestors 'none'"})
 def dispatch(environ,start_response):
  req=Request(environ);path=req.path
  # Deny malformed/encoded normalized aliases even if WSGI server decodes PATH.
  raw=environ.get('RAW_URI',environ.get('REQUEST_URI',path)).split('?',1)[0]
  if '%' in raw or '\\' in path or '//' in path or any(x in ('.','..') for x in path.split('/')) or req.host_url.rstrip('/')!=origin:return refuse()(environ,start_response)
  if type(service.store) is not MemoryStore or service.mode!='closed':return refuse()(environ,start_response)
  if path in ('/merged-login','/account/preview') and req.method=='GET':
   body=(root/'integration/accounts/ui/account.html').read_text()
   body=body.replace('This page does not unlock the merged app.','This login unlocks only this merged memory fixture, not the live app.')
   body=body.replace('<body>','<body><p>MERGED MEMORY-ONLY FIXTURE. No persistent settings sync.</p><p><a href="/fixture-navigation">Open fixture workspace navigation</a></p>')
   return Response(body,mimetype='text/html',headers=hardened)(environ,start_response)
  if path in ACCOUNT_GET and req.method=='GET' or path in ACCOUNT_POST and req.method=='POST':return account(environ,start_response)
  if not (path in allowed and req.method=='GET' or path in post_paths and req.method=='POST'):return refuse()(environ,start_response)
  try:permitted=auth(req)
  except Exception:permitted=False
  if not permitted:return refuse()(environ,start_response)
  if req.method=='POST':
   if req.headers.get('Origin')!=origin or req.mimetype!='application/json' or req.content_length is None or not 0<req.content_length<=16384:return refuse()(environ,start_response)
   rawbody=req.stream.read(16385)
   try:
    def pairs(items):
     out={}
     for k,v in items:
      if k in out:raise ValueError()
      out[k]=v
     return out
    data=json.loads(rawbody,object_pairs_hook=pairs)
    if len(rawbody)!=req.content_length or type(data) is not dict:raise ValueError()
    if path=='/api/related-news':
     if not set(data)<={'code','system','edition','country','system_name','product_terms'} or any(type(v) is not str or len(v)>200 for k,v in data.items() if k!='product_terms') or type(data.get('product_terms',[])) is not list or len(data.get('product_terms',[]))>20 or any(type(x) is not str or len(x)>200 for x in data.get('product_terms',[])):raise ValueError()
    elif set(data)!={'project','article_key'} or data['project'] not in ('geo','brics') or type(data['article_key']) is not str or len(data['article_key'])>200:raise ValueError()
   except (ValueError,TypeError,RecursionError,UnicodeError):return refuse(400)(environ,start_response)
   import io
   environ=dict(environ);environ['wsgi.input']=io.BytesIO(rawbody)
  if path=='/fixture-navigation':
   return Response('<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Memory fixture navigation</title></head><body><h1>Memory-only merged fixture</h1><p>No persistent settings sync or live account activation.</p><p><a href="/workspace">Workspace</a></p><p><a href="/account/preview">Account fixture settings and logout</a></p></body></html>',mimetype='text/html',headers={'Cache-Control':'no-store','X-Robots-Tag':'noindex, nofollow','Content-Security-Policy':"default-src 'none'; frame-ancestors 'none'"})(environ,start_response)
  if path in ('/workspace','/workspace/finder/index.html','/workspace/brics-streams'):
   response=Response.from_app(workspace,environ,buffered=True)
   if response.status_code==200 and response.mimetype=='text/html':
    body=response.get_data(as_text=True)
    warning='<p><strong>MEMORY FIXTURE: offline installation / Store public snapshot is disabled here. BRICS add/remove writes are disabled and streams are unwired. Controls for those features cannot save in this fixture.</strong> <a href="/account/preview">Account settings / sign out</a></p>'
    body=body.replace('<body>', '<body>'+warning,1)
    response.set_data(body)
   return response(environ,start_response)
  return workspace(environ,start_response)
 return dispatch
