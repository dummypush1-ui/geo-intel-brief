"""Default-OFF public title/source context for bounded reported-code coverage.
No new lookup/source request, vocabulary, inferred meaning or classification.
"""
import hashlib,json,re
from pathlib import Path
from urllib.parse import urlsplit
from integration.code_news_coverage_broker_prep import CoverageBroker
from integration.code_news_coverage_route_prep import validate as base_validate,Invalid
ROOT=Path(__file__).resolve().parents[2]
FLAG='PUBLIC_CODE_NEWS_SOURCE_CONTEXT_ENABLED'
FIELDS={'state','project','title','source','url'}

def plain(v,cap):return type(v)is str and len(v)<=cap and not any(ord(c)<32 or ord(c)==127 for c in v)
def safe_url(v):
 if not plain(v,2048)or not v or any(c.isspace()for c in v)or '\\'in v:return False
 try:
  p=urlsplit(v)
  return p.scheme=='https'and bool(p.hostname)and not p.username and not p.password and p.port in (None,443)
 except ValueError:return False

def article_context(row):
 unavailable={'state':'unavailable','project':'geo','title':'','source':'','url':None}
 if type(row)is not dict or row.get('project')!='geo' or not plain(row.get('title'),2000)or not row['title'].strip()or not plain(row.get('source',''),200)or not safe_url(row.get('url')):return unavailable
 return {'state':'source_context','project':'geo','title':row['title'],'source':row.get('source',''),'url':row['url']}

def check_context(x):
 if type(x)is not dict or set(x)!=FIELDS or x['project']!='geo':raise Invalid()
 if x['state']=='unavailable':
  if x!={'state':'unavailable','project':'geo','title':'','source':'','url':None}:raise Invalid()
 elif x['state']=='source_context':
  if not plain(x['title'],2000)or not x['title'].strip()or not plain(x['source'],200)or not safe_url(x['url']):raise Invalid()
 else:raise Invalid()
 return dict(x)

class ContextBroker(CoverageBroker):
 def _finish_locked(self,active,reply):
  # The same parent page already admitted by the coverage broker. Do not fetch
  # by hash, disclose raw IDs, retain an unbounded historical title cache or
  # bind another client's context to an article merely sharing a title.
  rows=reply['items']if reply is not None and type(reply)is dict and type(reply.get('items'))is list else self.contexts[active]['carry']
  sources={};ambiguous=set()
  for row in rows[:100]:
   if type(row)is not dict or type(row.get('article_key'))is not str:continue
   key=row['article_key'];context=article_context(row)
   if key in sources and sources[key]!=context:ambiguous.add(key)
   sources[key]=context
  body,done=super()._finish_locked(active,reply)
  for item in body['items']:
   key=item['article_key'];item['article_context']=article_context({})if key in ambiguous else sources.get(key,article_context({}))
  if len(json.dumps(body,ensure_ascii=False).encode())>520000:raise ValueError('Context reply byte cap')
  return body,done

def validate(body,status):
 if status!=200 or type(body)is not dict or body.get('state')=='target_unavailable':return base_validate(body,status)
 if type(body.get('items'))is not list:raise Invalid()
 stripped=[];contexts=[]
 for item in body['items']:
  if type(item)is not dict or set(item)!={'article_key','relationships','article_context'}:raise Invalid()
  contexts.append(check_context(item['article_context']));stripped.append({k:v for k,v in item.items()if k!='article_context'})
 clean,status=base_validate({**body,'items':stripped},status)
 clean={**clean,'items':[{**item,'article_context':context}for item,context in zip(clean['items'],contexts)]}
 return clean,status

def prepare(env):
 flag=env.get(FLAG,'false')
 if flag not in ('true','false'):raise ValueError('Exact source-context flag required')
 if flag=='false':return False
 if any(env.get(k)!='true'for k in ('PUBLIC_NEWS_READ_ENABLED','PUBLIC_NEWS_FULL_PAGES_ENABLED','PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED','PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED')):raise ValueError('Source context requires reviewed coverage API/UI')
 pins=json.loads((ROOT/'integration/code_news_context_d4/pins.json').read_text())
 if set(pins)!={'integration/'+n for n in ('code_news_coverage_broker_prep.py','code_news_parent_prep.py','news_pages.py','ui/code_news_coverage.js','ui/code_news_finder_navigation.js')}:raise ValueError('Exact source-context pins required')
 if any(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=h for n,h in pins.items()):raise ValueError('Source-context drift')
 return True

CHECK="""const c=item.article_context;if(!c||Object.keys(c).sort().join()!=='project,source,state,title,url'||c.project!=='geo')throw Error('invalid');
   if(c.state==='unavailable'){if(c.title!==''||c.source!==''||c.url!==null)throw Error('invalid');}
   else if(c.state==='source_context'){if(!plain(c.title,2000)||!c.title.trim()||!plain(c.source,200)||typeof c.url!=='string'||c.url.length>2048||/[\\s\\\\]/.test(c.url))throw Error('invalid');let u;try{u=new URL(c.url);}catch{throw Error('invalid');}if(u.protocol!=='https:'||!u.hostname||u.username||u.password||u.port&&u.port!=='443')throw Error('invalid');}else throw Error('invalid');"""
RENDER="""const context=item.article_context;if(context.state==='source_context'){const h=node('h3',''),a=node('a',context.title);a.href=context.url;a.target='_blank';a.rel='noopener noreferrer';h.append(a);article.append(h,node('p',context.source||'Source label unavailable'));}else article.append(node('h3','Source context unavailable'));article.append(node('p','Article key: '+item.article_key));"""
def transform(source):
 a="for(const item of r.items){if(!plain(item.article_key,100)"
 b="article.append(node('h3','Article key: '+item.article_key));"
 if source.count(a)!=1 or source.count(b)!=1:raise ValueError('Context UI seam drift')
 source=source.replace(a,'for(const item of r.items){'+CHECK+'if(!plain(item.article_key,100)',1).replace(b,RENDER,1)
 return source.replace('Manual coverage fixture available','Manual reported-mention coverage available')

def install_ui(app):
 from flask import request
 if type(app.extensions.get('code_news_coverage_broker'))is not ContextBroker:raise ValueError('Mounted context broker required')
 @app.after_request
 def served(r):
  if request.path=='/workspace/assets/code_news_coverage.js'and r.status_code==200 and request.method!='HEAD':
   r.direct_passthrough=False;r.set_data(transform(r.get_data(as_text=True)))
   for key in ('ETag','Last-Modified','Accept-Ranges'):r.headers.pop(key,None)
   r.headers['Cache-Control']='no-store'
  return r
 app.extensions['code_news_source_context']='same_admitted_page_not_extra_lookup'
