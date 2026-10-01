"""Fixture-backed private staging API. Never imports a live legacy app."""
from flask import Flask,request,jsonify,send_from_directory
from pathlib import Path
import re,hashlib,base64
from integration.news_view import views
from integration.relevance import match
from integration.story_links import groups
from integration.finder_links import finder_link
from integration.branding_meta import brand_head,valid_origin

def create_app(reader=None,authorize=None,finder_context_reader=None,finder_base=None,finder_index_verified=False,allowed_origin=None,branding_public_base=None):
 branding_public_base=valid_origin(branding_public_base)
 app=Flask(__name__)
 root=Path(__file__).resolve().parents[1]
 @app.after_request
 def private_response(response):
  response.headers['Cache-Control']='no-store'
  response.headers['X-Robots-Tag']='noindex, nofollow'
  if response.status_code==200 and response.mimetype=='text/html':
   response.direct_passthrough=False
   response.set_data(brand_head(response.get_data(as_text=True),branding_public_base))
  response.headers['X-Content-Type-Options']='nosniff'
  response.headers['Referrer-Policy']='same-origin'
  response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'self'; object-src 'none'; base-uri 'self'; form-action 'self'"
  if request.path.startswith('/workspace/finder/') and response.mimetype=='text/html' and response.status_code==200:
   response.direct_passthrough=False
   scripts=[body for attrs,body in re.findall(r'<script\b([^>]*)>(.*?)</script>',response.get_data(as_text=True),flags=re.S|re.I) if body.strip() and not re.search(r'\bsrc\s*=',attrs,re.I)]
   hashes=['\'sha256-'+base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()+'\'' for s in scripts]
   response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self' "+' '.join(hashes)+"; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'self'; object-src 'none'; base-uri 'self'; form-action 'self'"
  return response
 @app.get('/workspace')
 def workspace():return send_from_directory(root/'integration/ui','workspace.html')
 @app.get('/workspace/assets/<name>')
 def assets(name):
  if name not in ('workspace.js','workspace.css'):return jsonify(error='Not found'),404
  return send_from_directory(root/'integration/ui',name)
 @app.get('/workspace/branding/<name>')
 def branding(name):
  if name not in ('favicon.ico','icon-48.png','icon-192.png','icon-512.png','apple-touch-icon.png','og-image.png','logo.svg'):return jsonify(error='Not found'),404
  return send_from_directory(root/'integration/branding',name)
 @app.get('/workspace/manifest.webmanifest')
 def merged_manifest():return send_from_directory(root/'integration/branding','manifest.webmanifest')
 @app.get('/workspace/finder/<name>')
 def finder(name):
  import re
  if name not in ('index.html','offline.html','sw.js','manifest.webmanifest','icon-192.png','icon-512.png') and not re.fullmatch(r'data\.[0-9a-f]{12}\.js',name):return jsonify(error='Not found'),404
  return send_from_directory(root,name)
 source_reader=reader or (lambda:{'geo':[],'brics':[]})
 class ReadUnavailable(Exception):pass
 @app.errorhandler(ReadUnavailable)
 def read_unavailable(error):return jsonify(error='News storage temporarily unavailable'),503
 def reader():
  try:return source_reader()
  except Exception as error:
   app.logger.warning('Read-only news unavailable: %s',type(error).__name__)
   raise ReadUnavailable() from None
 authorize=authorize or (lambda req:False)
 @app.get('/health')
 def health():return jsonify(state='staging',collection=False,mail=False,scraper=False)
 @app.before_request
 def guard():
  if request.path=='/health':return None
  try:allowed=authorize(request)
  except Exception:allowed=False
  if not allowed:return jsonify(error='Private news unavailable until approved access control'),403
  if request.method=='POST' and request.headers.get('Origin')!=(allowed_origin or request.host_url.rstrip('/')):
   return jsonify(error='Same-origin request required'),403
 @app.get('/api/news')
 def news():
  q=request.args.get('q','')[:200].casefold()
  project=request.args.get('project','')
  if project and project not in ('geo','brics'):return jsonify(error='Invalid project'),400
  records=[r for r in views(reader()) if not project or r['project']==project]
  return jsonify(items=[r for r in records if not q or q in (r['title']+' '+r['summary']).casefold()][:100])
 @app.post('/api/related-news')
 def related():
  context=request.get_json(silent=True)
  if not isinstance(context,dict) or not isinstance(context.get('product_terms',[]),list) or len(context.get('product_terms',[]))>20 or any(not isinstance(t,str) or len(t)>200 for t in context.get('product_terms',[])):return jsonify(error='Invalid context'),400
  out=[]
  for row in views(reader()):
   evidence=match(context,row)
   if evidence['reasons']:out.append({'article':row,'match':evidence})
  return jsonify(items=out[:100])
 @app.get('/api/story-groups')
 def story_groups():return jsonify(items=groups(views(reader())))
 @app.post('/api/finder-context')
 def finder_context():
  data=request.get_json(silent=True)
  if not isinstance(data,dict) or data.get('project') not in ('geo','brics') or not isinstance(data.get('legacy_id'),str):return jsonify(error='Exact project and original ID required'),400
  articles=[r for r in views(reader()) if r['project']==data['project'] and r['legacy_id']==data['legacy_id']]
  if len(articles)!=1:return jsonify(error='Article identity not unique or unavailable'),404
  if finder_context_reader is None or not finder_base or not finder_index_verified:return jsonify(items=[],state='verified_finder_index_unwired')
  out=[]
  for context in finder_context_reader():
   evidence=match(context,articles[0])
   if not evidence['reasons']:continue
   link=finder_link(finder_base,context.get('system_index'),context.get('entry_index'),verified=True)
   out.append({'context':{k:context.get(k) for k in ('code','system','edition','country')},'finder_url':link,'match':evidence})
  return jsonify(items=out[:100])
 @app.get('/dashboard')
 def dashboard():return jsonify(state='Private dashboard UI requires Phase 2 login'),503
 return app
app=create_app()
