"""Fixture-backed private staging API. Never imports a live legacy app."""
from flask import Flask,request,jsonify
from integration.news_view import views
from integration.relevance import match

def create_app(reader=None,authorize=None):
 app=Flask(__name__)
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
  records=views(reader())
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
