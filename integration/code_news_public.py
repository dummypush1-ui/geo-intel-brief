"""Dormant public supplied-page code relationships. No full-store/provider route."""
from pathlib import Path
import json,re,time
from threading import Lock
from flask import request,Response,jsonify
from integration.code_news_disk import DiskLinks
from integration.code_news_links import Links,Refused
from integration.code_news_query import query_plan
from integration.news_view import views
from integration.public_news import public_news_row
PATHS=frozenset(('/workspace/code-news','/workspace/assets/code_news.js','/api/code-news-context','/api/news-code-context'))

def enabled(env):
 flag=env.get('PUBLIC_CODE_NEWS_ENABLED','false')
 if flag not in ('true','false'):raise ValueError('Exact code-news flag')
 if flag=='true'and env.get('PUBLIC_CODE_NEWS_SCOPE_REVIEWED')!='true':raise ValueError('Supplied-page public code-news scope review required')
 return flag=='true'

class Service:
 def __init__(self,root,reader,model=None,clock=time.monotonic):
  self.root=Path(root);self.reader=reader;self.model=model;self.lock=Lock();self.clock=clock;self.window=None;self.calls=0;self.failed=False
 def run(self,operation):
  now=int(self.clock()//60)
  # Global conservative cap, no client-forwarding identity assumptions.
  if not self.lock.acquire(False):return {'state':'busy'},429
  try:
   if self.window!=now:self.window=now;self.calls=0
   self.calls+=1
   if self.calls>10:return {'state':'rate_limited'},429
   if self.failed:return {'state':'index_load_held_until_restart'},503
   if self.model is None:
    try:self.model=DiskLinks(self.root/'integration/code_news_index')
    except Exception:
     self.failed=True;return {'state':'index_load_held_until_restart'},503
   return operation(self.model)
  finally:self.lock.release()
 def rows(self):
  supplied=self.reader()
  if type(supplied)is not dict or set(supplied)-{'geo','brics'}or any(type(v)is not list or len(v)>100 for v in supplied.values()):raise Refused('Bounded supplied page')
  rows=views(supplied)
  if len(rows)>100:raise Refused('Only100supplied articles')
  return [{**public_news_row(r),'article_key':r['article_key'],'project':r['project']}for r in rows]

def install(app,origin,reader,service=None):
 root=Path(__file__).resolve().parents[1];service=service or Service(root,reader)
 @app.get('/workspace/code-news')
 def code_news_shell():return Response((root/'integration/ui/code_news.html').read_text(),mimetype='text/html')
 @app.get('/workspace/assets/code_news.js')
 def code_news_js():return Response((root/'integration/ui/code_news.js').read_text(),mimetype='application/javascript')
 def query(shape):
  if len(request.query_string)>512 or set(request.args)-set(shape)or any(len(request.args.getlist(k))!=1 or len(request.args[k])>shape[k]for k in request.args):raise Refused('Exact bounded parameters')
 @app.get('/api/code-news-context')
 def code_context():
  if request.method=='HEAD':return Response(status=200)
  try:
   query({'query':200,'system':3,'edition':100})
   q=request.args.get('query','');system=request.args.get('system')or None;edition=request.args.get('edition')or None
   def op(model):
    plan=query_plan(model,q,system=system,edition=edition)
    if plan['mode']!='code':return {'state':'keywords_not_code','generic_news_search_not_called':True},400
    if plan['state']in ('invalid_code','mixed_or_malformed_code','label_system_conflict'):return plan,400
    if plan['state']!='resolved':return dict(plan,scope='supplied_page_only',not_full_store_search=True),200
    target=plan['items'][0];rows=service.rows();result=model.for_code(target['code'],rows,target['system'],target['edition'])
    by_id={r['article_key']:r for r in rows}
    for link in result['relationships']:link['article']=by_id[link['article_key']]
    return dict(result,scope='latest100_supplied_page_only',vocabulary_state='draft_not_enabled',no_matches_not_no_related_news=True),200
   body,status=service.run(op);return jsonify(body),status
  except Refused:return jsonify(state='invalid_query'),400
  except Exception:return jsonify(state='relationships_unavailable'),503
 @app.get('/api/news-code-context')
 def news_context():
  if request.method=='HEAD':return Response(status=200)
  try:
   query({'project':5,'article_key':64});project=request.args.get('project');key=request.args.get('article_key','')
   if project not in ('geo','brics')or not re.fullmatch('[a-f0-9]{64}',key):raise Refused('Exact article identity')
   def op(model):
    rows=[r for r in service.rows()if r['project']==project and r['article_key']==key]
    if len(rows)!=1:return {'state':'article_unavailable_in_supplied_page','scope':'latest100_supplied_page_only'},404
    return dict(model.for_news(rows[0]),vocabulary_state='draft_not_enabled',no_matches_not_no_related_news=True),200
   body,status=service.run(op);return jsonify(body),status
  except Refused:return jsonify(state='invalid_query'),400
  except Exception:return jsonify(state='relationships_unavailable'),503
 @app.after_request
 def public_link_headers(response):
  if request.path in PATHS:
   response.headers['Cache-Control']='no-store';response.headers['Referrer-Policy']='no-referrer';response.headers['X-Content-Type-Options']='nosniff'
   response.headers['Content-Security-Policy']="default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'; object-src 'none'"
  return response
 hooks=app.after_request_funcs[None];hooks.remove(public_link_headers);hooks.insert(0,public_link_headers)
 app.extensions['code_news_public']=service
