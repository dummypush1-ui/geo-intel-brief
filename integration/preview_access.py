"""Optional single-worker private preview access. Not public account login.

No credentials or session key are created here. A reviewed operator configures
PREVIEW_ACCESS_ENABLED, PREVIEW_ORIGIN, PREVIEW_PASSWORD_HASH and a strong
PREVIEW_SESSION_KEY. The in-memory limiter is for a single-worker preview only;
production multi-user login requires a shared limiter and account lifecycle.
"""
import hmac,secrets,time,threading
from datetime import timedelta
from urllib.parse import urlsplit
from flask import session,request,redirect,render_template_string
from werkzeug.security import check_password_hash
from integration.news_api import create_app

FORM='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Private preview sign in</title></head><body><h1>Private preview</h1><p>This preview is private. Collection and mail are off.</p>{% if error %}<p>{{ error }}</p>{% endif %}<form method="post"><input type="hidden" name="csrf" value="{{ csrf }}"><label>Password <input name="password" type="password" required autocomplete="current-password" maxlength="1024"></label><button type="submit">Sign in</button></form></body></html>'''

class PreviewAccess:
 def __init__(self,origin,password_hash,clock=time.monotonic):
  p=urlsplit(origin)
  if p.scheme!='https' or not p.hostname or p.username or p.password or p.query or p.fragment or p.path not in ('','/'):
   raise ValueError('Explicit HTTPS preview origin required')
  parts=password_hash.split('$')
  if len(parts)!=3 or not parts[0].startswith(('scrypt:','pbkdf2:')) or not parts[1] or len(parts[2])<64 or any(c not in '0123456789abcdef' for c in parts[2]):raise ValueError('Supported complete password hash required')
  self.origin=origin.rstrip('/');self.password_hash=password_hash;self.clock=clock
  self.lock=threading.Lock();self.attempts=[]
 def authorize(self,req):
  if req.host_url.rstrip('/')!=self.origin:return False
  # Only these two access-control routes are available without a login.
  if req.path in ('/login','/logout'):return True
  issued=session.get('preview_issued_at')
  return session.get('preview_authenticated') is True and isinstance(issued,(int,float)) and 0<=time.time()-issued<7200
 def limited(self,record=False):
  with self.lock:
   now=self.clock();self.attempts=[t for t in self.attempts if now-t<300]
   if len(self.attempts)>=10:return True
   if record:self.attempts.append(now)
   return False
 def install(self,app):
  @app.route('/login',methods=['GET','POST'])
  def login():
   if request.host_url.rstrip('/')!=self.origin:return 'Invalid preview host',400
   if request.method=='GET':
    session['preview_csrf']=secrets.token_urlsafe(32)
    return render_template_string(FORM,csrf=session['preview_csrf'],error=None)
   token=request.form.get('csrf','');expected=session.get('preview_csrf','')
   if not expected or not hmac.compare_digest(token,expected):return 'Invalid sign-in token',403
   if self.limited():return 'Too many attempts. Try again later.',429
   password=request.form.get('password','')
   if len(password)>1024 or not check_password_hash(self.password_hash,password):
    if self.limited(record=True):return 'Too many attempts. Try again later.',429
    return render_template_string(FORM,csrf=expected,error='Password not accepted'),401
   session.clear();session.permanent=True;session['preview_authenticated']=True;session['preview_issued_at']=time.time()
   return redirect('/workspace',303)
  @app.post('/logout')
  def logout():
   session.clear();return redirect('/login',303)

 def build(self,session_key,reader=None,**kwargs):
  if len(session_key)<48:raise ValueError('Strong preview session key required')
  app=create_app(reader=reader,authorize=self.authorize,allowed_origin=self.origin,**kwargs)
  app.config.update(SECRET_KEY=session_key,SESSION_COOKIE_NAME='__Host-merged-preview',SESSION_COOKIE_SECURE=True,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Strict',PERMANENT_SESSION_LIFETIME=timedelta(hours=2),SESSION_REFRESH_EACH_REQUEST=False,MAX_CONTENT_LENGTH=16384)
  self.install(app);return app

def create_preview_from_env(environ,reader=None,**kwargs):
 if environ.get('PREVIEW_ACCESS_ENABLED','false').lower()!='true':return create_app(**kwargs)
 access=PreviewAccess(environ.get('PREVIEW_ORIGIN',''),environ.get('PREVIEW_PASSWORD_HASH',''))
 app=access.build(environ.get('PREVIEW_SESSION_KEY',''),reader=reader,**kwargs)
 # Configure only after confirming exactly one trusted TLS-terminating proxy.
 if environ.get('PREVIEW_TRUST_ONE_PROXY','false').lower()=='true':
  from werkzeug.middleware.proxy_fix import ProxyFix
  app.wsgi_app=ProxyFix(app.wsgi_app,x_for=0,x_proto=1,x_host=0,x_port=0,x_prefix=0)
 return app
