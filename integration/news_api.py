"""Fixture-backed private staging API. Never imports a live legacy app."""
from flask import Flask,request,jsonify,send_from_directory
from pathlib import Path
from integration.news_view import views
from integration.relevance import match

def create_app(reader=None,authorize=None):
 app=Flask(__name__)
 root=Path(__file__).resolve().parents[1]
 @app.after_request
 def private_response(response):
  response.headers['Cache-Control']='no-store'
  response.headers['X-Content-Type-Options']='nosniff'
  response.headers['Referrer-Policy']='no-referrer'
  response.headers['Content-Security-Policy']="frame-ancestors 'self'; object-src 'none'; base-uri 'self'"
  return response
 @app.get('/workspace')
 def workspace():return send_from_directory(root/'integration/ui','workspace.html')
 @app.get('/workspace/assets/<name>')
 def assets(name):
  if name not in ('workspace.js','workspace.css'):return jsonify(error='Not found'),404
  return send_from_directory(root/'integration/ui',name)
 @app.get('/workspace/finder/<name>')
 def finder(name):
  import re
  if name not in ('index.html','offline.html','sw.js','manifest.webmanifest','icon-192.png','icon-512.png') and not re.fullmatch(r'data\.[0-9a-f]{12}\.js',name):return jsonify(error='Not found'),404
  return send_from_directory(root,name)
 reader=reader or (lambda:{'geo':[],'brics':[]})
 authorize=authorize or (lambda req:False)
 @app.get('/health')
 def health():return jsonify(state='staging',collection=False,mail=False,scraper=False)
 @app.before_request
 def guard():
  if request.path!='/health' and not authorize(request):return jsonify(error='Private news unavailable until approved access control'),403
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
  if not isinstance(context,dict) or not isinstance(context.get('product_terms',[]),list):return jsonify(error='Invalid context'),400
  out=[]
  for row in views(reader()):
   evidence=match(context,row)
   if evidence['reasons']:out.append({'article':row,'match':evidence})
  return jsonify(items=out[:100])
 @app.get('/dashboard')
 def dashboard():return jsonify(state='Private dashboard UI requires Phase 2 login'),503
 return app
app=create_app()
