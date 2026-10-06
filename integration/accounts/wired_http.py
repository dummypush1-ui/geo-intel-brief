"""Explicit unselected account/news wiring. No client, provisioning or activation."""
import re,json,hashlib
from urllib.parse import urlsplit
from werkzeug.wrappers import Request,Response
from .service import AccountService,COOKIE_NAME,PREAUTH_NAME
from .passwords import Hasher
from .limiter import Limiter,MAX_USER_FAILS,MAX_CLIENT_FAILS
from .store import MemoryStore
from .mongo_store import MongoAccountStore
from .settings import SettingsPolicy,REPUBLIC
from . import csrf
from .validators import channel_validator,watch_validator
PRIVATE_NEWS_GET=frozenset(['/workspace','/workspace/weekly','/api/weekly-report.pdf','/api/export.csv','/api/export-full.csv','/digest-data','/critical','/weekly','/workspace/brics-streams','/api/brics/streams','/workspace/tariffs','/workspace/countries','/workspace/map','/api/map-data','/api/tariff-evidence','/api/country-signals','/api/country-page','/api/news','/api/news-export.csv','/api/sample-volume','/api/source-health','/api/critical-stories','/api/news-stats','/api/dashboard-snapshots','/api/dashboard-signals','/api/story-groups','/dashboard','/workspace/manifest.webmanifest'])
PRIVATE_NEWS_POST=frozenset(['/api/related-news','/api/finder-context'])
PUBLIC_ACCOUNT_GET=frozenset(['/account/preauth'])
PRIVATE_ACCOUNT_GET=frozenset(['/account/whoami','/account/settings'])
ACCOUNT_POST=frozenset('/account/'+x for x in ['login','signup','logout','save-settings','export','change-password','delete'])
def validate(service,origin,client_identity):
 try:
  u=urlsplit(origin)
  if type(origin) is not str or origin!=origin.lower() or u.scheme!='https' or u.port is not None or u.netloc!=u.hostname or u.path or u.query or u.fragment or not re.fullmatch(r'[a-z0-9]+(?:[.-][a-z0-9]+)*',u.hostname or ''):raise ValueError()
 except (ValueError,TypeError):raise ValueError('Exact HTTPS origin without explicit port required') from None
 if type(service) is not AccountService or type(service.store) not in (MemoryStore,MongoAccountStore) or type(service.hasher) is not Hasher or type(service.limiter) is not Limiter or type(service.policy) is not SettingsPolicy or service.mode!='closed' or service.require_origin is not True or service.origins!=frozenset([origin]) or not callable(client_identity):raise ValueError('Exact reviewed account collaborators required')
 h=service.hasher;l=service.limiter;p=service.policy
 if h.n!=32768 or h.r!=8 or h.p!=1 or h.iters!=600000 or l.store is not service.store or l.secret!=service.secret or l.clock is not service.clock or l.max_user!=MAX_USER_FAILS or l.max_client!=MAX_CLIENT_FAILS or p.compulsory!=(REPUBLIC,) or p.channel_validator is not channel_validator or p.watch_validator is not watch_validator or len(service.secret)<32 or not callable(service.clock):raise ValueError('Reviewed account policy required')
 return True
def create_wired_http(service,*,origin,client_identity,reader):
 """Construction does not touch store/client. Serving may read/write injected store.

One exact service/Limiter per store/process is required, not enforced globally.
Unselected by launcher. No UI is added; existing fixture pages remain unchanged.
 """
 validate(service,origin,client_identity)
 if not callable(reader):raise ValueError('Explicit selected-news reader required')
 account=_account_app(service,origin,client_identity)
 from integration.news_api import create_app
 def authenticated(req):
  try:validate(service,origin,client_identity);return service.whoami(req.cookies.get(COOKIE_NAME,'')).get('ok') is True
  except Exception:return False
 workspace=create_app(reader=reader,authorize=authenticated,allowed_origin=origin)
 def refuse(status=403):return Response(json.dumps({'ok':False,'error':'private_access_required'}),status=status,mimetype='application/json',headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer'})
 def dispatch(environ,start_response):
  req=Request(environ);path=req.path;raw=environ.get('RAW_URI',environ.get('REQUEST_URI',path)).split('?',1)[0]
  try:validate(service,origin,client_identity)
  except Exception:return refuse()(environ,start_response)
  # No proxy trust. Ignore forwarded values; only direct configured authority accepted.
  if req.host_url.rstrip('/')!=origin or '%' in raw or '\\' in path or '//' in path or any(x in ('.','..') for x in path.split('/')):return refuse()(environ,start_response)
  if req.method not in ('GET','POST'):return refuse(405)(environ,start_response)
  if req.method=='POST' and req.headers.get('Origin')!=origin:return refuse()(environ,start_response)
  if path in PUBLIC_ACCOUNT_GET and req.method=='GET' or path in ACCOUNT_POST and req.method=='POST':return account(environ,start_response)
  if path in PRIVATE_ACCOUNT_GET and req.method=='GET':
   if not authenticated(req):return refuse()(environ,start_response)
   return account(environ,start_response)
  # Static news assets still require a live session; account UI/assets intentionally absent.
  static=any(rule.rule==path or ('<' in rule.rule and rule.rule.startswith('/workspace/') and req.path.startswith(rule.rule.split('<')[0])) for rule in workspace.url_map.iter_rules() if 'GET' in rule.methods and rule.rule.startswith('/workspace/'))
  if not (req.method=='GET' and (path in PRIVATE_NEWS_GET or static) or req.method=='POST' and path in PRIVATE_NEWS_POST):return refuse(404)(environ,start_response)
  if not authenticated(req):return refuse()(environ,start_response)
  if req.method=='POST':
   token=req.cookies.get(COOKIE_NAME,'')
   if not csrf.verify_session_token(service.secret,hashlib.sha256(token.encode('utf-8')).hexdigest(),req.headers.get('X-CSRF-Token')):return refuse()(environ,start_response)
  return workspace(environ,start_response)
 dispatch.route_contract={'public_get':sorted(PUBLIC_ACCOUNT_GET),'private_account_get':sorted(PRIVATE_ACCOUNT_GET),'account_mutations':sorted(ACCOUNT_POST),'private_news_get':sorted(PRIVATE_NEWS_GET),'private_news_post_readonly':sorted(PRIVATE_NEWS_POST),'private_static_rules':sorted(rule.rule for rule in workspace.url_map.iter_rules() if rule.rule.startswith('/workspace/') and '<' in rule.rule),'denied_mutations':['/mark-emailed','POST /critical','POST /weekly','POST/DELETE /api/brics/streams'],'account_ui':'absent; no fixture UI promoted'}
 return dispatch

from flask import Flask,request,jsonify
from .service import clear_cookie_header
def _account_app(service,origin,client_identity):
 app=Flask(__name__);app.logger.disabled=True;app.config.update(MAX_CONTENT_LENGTH=16384,DEBUG=False,PROPAGATE_EXCEPTIONS=False)
 @app.before_request
 def host_guard():
  if request.host_url.rstrip('/')!=origin:return jsonify(ok=False,error='forbidden'),403
  if request.method!='GET' and request.headers.get('Origin')!=origin:return jsonify(ok=False,error='forbidden'),403
 @app.after_request
 def security(r):
  r.headers['Cache-Control']='no-store';r.headers['X-Content-Type-Options']='nosniff';r.headers['X-Robots-Tag']='noindex, nofollow';r.headers['Referrer-Policy']='no-referrer';r.headers['Content-Security-Policy']="default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'";return r
 @app.errorhandler(500)
 def internal_error(e):return jsonify(ok=False,error='internal_error'),500
 @app.errorhandler(404)
 def not_found(e):return jsonify(ok=False,error='not_found'),404
 @app.errorhandler(405)
 def method_not_allowed(e):return jsonify(ok=False,error='method_not_allowed'),405
 @app.errorhandler(413)
 def too_large(e):return jsonify(ok=False,error='request_too_large'),413
 def body(fields):
  if request.mimetype!='application/json':return None,(jsonify(ok=False,error='json_required'),415)
  n=request.content_length
  if n is None or not 0<n<=16384:return None,(jsonify(ok=False,error='request_too_large'),413)
  raw=request.stream.read(16385)
  if len(raw)>16384:return None,(jsonify(ok=False,error='request_too_large'),413)
  if len(raw)!=n:return None,(jsonify(ok=False,error='invalid_request'),400)
  def pairs(items):
   out={}
   for k,v in items:
    if k in out:raise ValueError('duplicate')
    out[k]=v
   return out
  try:
   value=json.loads(raw,object_pairs_hook=pairs)
   if type(value) is not dict or set(value)!=set(fields):raise ValueError('fields')
  except (ValueError,UnicodeError,RecursionError):return None,(jsonify(ok=False,error='invalid_request'),400)
  return value,None
 def client():
  # Resolver reads no caller-supplied JSON or forwarded header by default.
  value=client_identity(request)
  if not service._client_ok(value):raise ValueError('Trusted client missing')
  return value
 def result(data):
  data=dict(data);cookie=data.pop('set_cookie',None);data.pop('session_token',None)
  status=200 if data.get('ok') else {'forbidden':403,'unauthenticated':401,'invalid_credentials':401,'too_many_attempts':429,'busy':503,'version_conflict':409}.get(data.get('error'),400)
  response=jsonify(data);response.status_code=status
  if cookie:response.headers.add('Set-Cookie',cookie)
  if data.get('retry_after'):response.headers['Retry-After']=str(data['retry_after'])
  return response
 @app.get('/account/preauth')
 def preauth():
  data=service.issue_preauth();r=jsonify(csrf=data['csrf'],state='explicit_wiring_unselected',signup_mode=service.mode);r.headers.add('Set-Cookie',data['set_cookie']);return r
 @app.post('/account/<action>')
 def dispatch(action):
  schemas={'login':('username','password','csrf'),'signup':('username','password','invite','csrf'),'logout':('csrf',),'save-settings':('csrf','channels','watchlist','version'),'export':('csrf',),'change-password':('csrf','old','new'),'delete':('csrf','password')}
  if action not in schemas:return jsonify(ok=False,error='not_found'),404
  d,error=body(schemas[action])
  if error:return error
  token=request.cookies.get(COOKIE_NAME,'');nonce=request.cookies.get(PREAUTH_NAME,'');csrf=d['csrf']
  try:
   if action=='login':out=service.login(d['username'],d['password'],csrf,nonce,client(),origin)
   elif action=='signup':out=service.signup(d['username'],d['password'],d['invite'],csrf,nonce,client(),origin)
   elif action=='logout':out=service.logout(token,csrf,origin)
   elif action=='save-settings':out=service.save_settings(token,csrf,d['channels'],d['watchlist'],d['version'],origin)
   elif action=='export':out=service.export(token,csrf,origin)
   elif action=='change-password':out=service.change_password(token,csrf,d['old'],d['new'],client(),origin)
   else:out=service.delete_account(token,csrf,d['password'],client(),origin)
  except ValueError:return jsonify(ok=False,error='invalid_request'),400
  except Exception:return jsonify(ok=False,error='account_unavailable'),503
  response=result(out)
  if action in ('login','signup') and out.get('ok'):response.headers.add('Set-Cookie',clear_cookie_header(PREAUTH_NAME))
  if action=='logout':response.headers.add('Set-Cookie',clear_cookie_header(COOKIE_NAME))
  return response
 @app.get('/account/whoami')
 def whoami():return result(service.whoami(request.cookies.get(COOKIE_NAME,'')))
 @app.get('/account/settings')
 def settings():return result(service.get_settings(request.cookies.get(COOKIE_NAME,'')))
 return app
