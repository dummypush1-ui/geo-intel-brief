"""Separate private manual probe app. No standard route/launcher activation."""
import hmac,secrets,threading,time,math
from datetime import timedelta
from flask import Flask,request,session,jsonify,render_template_string
from werkzeug.wrappers import Request
from integration.preview_access import PreviewAccess
from integration.geo_probe_process import execute_probe,validate_result
from integration.geo_sample_probe import _result
_LOCK=threading.Lock()
_LAST=None
_FORM='''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Private sample check</title></head><body><h1>Private sample check</h1><p>Read operations under a write-capable credential. No verified read-only access. Sample only.</p><form method="post"><input type="hidden" name="csrf" value="{{ token }}"><button type="submit">Run one sample check</button></form><form method="post" action="/logout"><input type="hidden" name="csrf" value="{{ logout_token }}"><button type="submit">Sign out</button></form></body></html>'''
def create_probe_app(*,origin,password_hash,session_key,uri,executor=execute_probe,clock=time.monotonic):
 """Trusted explicit arguments only. Caller handles secure env and proxy review.

No automatic env read, startup query, public status, retry or DB role grant.
Single worker; cooldown/busy state is perprocess and resets on restart.
 """
 if type(uri) is not str or not uri or len(uri)>8192 or not callable(executor) or not callable(clock):raise ValueError('Explicit probe configuration required')
 if type(session_key) is not str or len(session_key)<48:raise ValueError('Strong private key required')
 access=PreviewAccess(origin,password_hash);app=Flask(__name__,static_folder=None)
 app.config.update(SECRET_KEY=session_key,SESSION_COOKIE_NAME='__Host-merged-preview',SESSION_COOKIE_SECURE=True,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Strict',MAX_CONTENT_LENGTH=1024,SESSION_REFRESH_EACH_REQUEST=False,PERMANENT_SESSION_LIFETIME=timedelta(hours=2))
 access.install(app)
 @app.after_request
 def headers(response):
  response.headers.update({'Cache-Control':'no-store, max-age=0','Pragma':'no-cache','X-Robots-Tag':'noindex, nofollow','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Content-Security-Policy':"default-src 'none'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"})
  return response
 @app.get('/workspace')
 def landing():return '',303,{'Location':'/db-check'}
 @app.route('/db-check',methods=['GET','POST'],provide_automatic_options=False)
 def check():
  global _LAST
  if request.query_string:return 'Invalid check request',400
  if request.method=='GET':
   session['probe_csrf']=secrets.token_urlsafe(32)
   return render_template_string(_FORM,token=session['probe_csrf'],logout_token=session.get('logout_csrf',''))
  if request.headers.get('Origin')!=access.origin or request.mimetype!='application/x-www-form-urlencoded':return 'Invalid check request',403
  if set(request.form)!= {'csrf'} or len(request.form.getlist('csrf'))!=1:return 'Invalid check request',403
  expected=session.get('probe_csrf','');actual=request.form.get('csrf','')
  if not expected or not hmac.compare_digest(expected.encode('utf-8'),actual.encode('utf-8')):return 'Invalid check request',403
  if not _LOCK.acquire(blocking=False):return 'Check busy',429,{'Retry-After':'600'}
  try:
   now=clock()
   if type(now) not in (int,float) or not math.isfinite(now):return 'Check unavailable',503
   if _LAST is not None and not now-_LAST>=600:return 'Check cooldown',429,{'Retry-After':'600'}
   _LAST=now
   try:result=validate_result(executor(uri))
   except Exception:result=_result('unavailable',reason='source_unavailable')
   return jsonify(result),503 if result['state']=='unavailable' else 200
  finally:_LOCK.release()
 # Before dispatch, auth also covers unknown paths/methods. Never expose config.
 inner=app.wsgi_app
 def gate(environ,start_response):
  permitted=False
  try:
   with app.request_context(environ):
    permitted=access.authorize(Request(environ))
  except Exception:pass
  if not permitted:
   body=b'Private preview required'
   start_response('403 FORBIDDEN',[('Content-Type','text/plain'),('Cache-Control','no-store, max-age=0'),('X-Robots-Tag','noindex, nofollow'),('X-Content-Type-Options','nosniff'),('Content-Security-Policy',"default-src 'none'; frame-ancestors 'none'")]);return [body]
  return inner(environ,start_response)
 app.wsgi_app=gate
 return app
