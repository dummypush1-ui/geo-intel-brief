"""Explicit fixture HTTP factory, not production auth or merged access gate.

No env/client/store discovery. Memory-only. Caller supplies reviewed HTTPS origin,
service and trusted fixture client resolver. No forwarded headers are trusted.
"""
import json
from urllib.parse import urlsplit
from flask import Flask,request,jsonify,send_from_directory
from pathlib import Path
from .service import AccountService,COOKIE_NAME,PREAUTH_NAME,clear_cookie_header
from .store import MemoryStore

def create_fixture_app(service,origin,client_identity):
 u=urlsplit(origin)
 if u.scheme!='https' or not u.hostname or u.username or u.password or u.path or u.query or u.fragment or origin=='null' or any(c.isspace() for c in origin):raise ValueError('Canonical HTTPS fixture origin required')
 if type(service) is not AccountService or type(service.store) is not MemoryStore or service.origins!=frozenset([origin]) or not service.require_origin:raise ValueError('Exact fixture service required')
 if not callable(client_identity):raise ValueError('Explicit trusted fixture client resolver required')
 app=Flask(__name__);app.config.update(MAX_CONTENT_LENGTH=16384,DEBUG=False,PROPAGATE_EXCEPTIONS=False)
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
 @app.get('/account/preview')
 def preview():return send_from_directory(Path(__file__).parent/'ui','account.html')
 @app.get('/account/assets/<name>')
 def asset(name):
  if name not in ('account.js','account.css'):return jsonify(ok=False,error='not_found'),404
  return send_from_directory(Path(__file__).parent/'ui',name)
 @app.get('/account/preauth')
 def preauth():
  data=service.issue_preauth();r=jsonify(csrf=data['csrf'],state='fixture_only',signup_mode=service.mode);r.headers.add('Set-Cookie',data['set_cookie']);return r
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
  response=result(out)
  if action in ('login','signup') and out.get('ok'):response.headers.add('Set-Cookie',clear_cookie_header(PREAUTH_NAME))
  if action=='logout':response.headers.add('Set-Cookie',clear_cookie_header(COOKIE_NAME))
  return response
 @app.get('/account/whoami')
 def whoami():return result(service.whoami(request.cookies.get(COOKIE_NAME,'')))
 @app.get('/account/settings')
 def settings():return result(service.get_settings(request.cookies.get(COOKIE_NAME,'')))
 return app
