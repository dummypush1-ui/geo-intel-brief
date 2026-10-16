"""D3b dormant injected-broker adapter. No builder/source/model construction.
Route fault after broker success retains reservation to normal TTL. Headers are
browser cross-site controls, not auth or abuse protection. Single worker required.
"""
import json,re
from urllib.parse import urlsplit
from integration.code_news_coverage_contract_prep import RESOLUTIONS,serialize
PATH='/api/code-news-coverage'
ERRORS={429:('resolve_busy','shared_capacity','busy','quota_wait'),400:('target_unavailable',),410:('expired_restart','binding_changed_restart','target_mismatch'),503:('source_unavailable','admission_fault')}
SUCCESS=('continue_scan','complete_mutable_read','budget_stopped_incomplete')
FIELDS={'state','items','scan_complete','evidence_complete','evidence_scope','coverage_gap','articles_checked','articles_refused_mentions_limit','articles_unreadable','articles_checked_this_page','articles_refused_this_page','articles_unreadable_this_page','rows_consumed_this_page','parent_pages','public_rows_received','total_count','coverage_message','consistency','scope','next_cursor','manifest','matcher_version'}
class Invalid(ValueError):pass
def enabled(env):
 flag=env.get('PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED','false')
 if flag not in ('true','false'):raise ValueError('Exact coverage API flag')
 return flag=='true'
def origin_value(value):
 if type(value)is not str:raise ValueError('Explicit origin required')
 p=urlsplit(value)
 if p.scheme not in ('http','https')or not p.hostname or p.username or p.password or p.path or p.query or p.fragment or p.netloc!=p.hostname+((':'+str(p.port))if p.port else ''):raise ValueError('Canonical origin required')
 return value
def matches(value,pattern):return type(value)is str and re.fullmatch(pattern,value)is not None
def parse(raw):
 if raw.startswith(b'\xef\xbb\xbf'):raise Invalid()
 def unique(pairs):
  out={}
  for k,v in pairs:
   if k in out:raise Invalid()
   out[k]=v
  return out
 def constant(_):raise Invalid()
 try:body=json.loads(raw.decode('utf-8',errors='strict'),object_pairs_hook=unique,parse_constant=constant)
 except (ValueError,UnicodeError,RecursionError):raise Invalid()from None
 if type(body)is not dict:raise Invalid()
 start={'system':r'[A-Z]{2,3}','edition':r'[A-Za-z0-9:_.-]{1,100}','code':r'[0-9]{2,12}'}
 resume={'scope':r'[A-Za-z0-9_-]{43}','manifest':r'[a-f0-9]{64}','matcher_version':r'[A-Za-z0-9_.-]{1,40}'}
 shape=start if set(body)==set(start)else resume if set(body)==set(resume)else None
 if shape is None or any(not matches(body[k],pattern)for k,pattern in shape.items()):raise Invalid()
 return body

def plain(value,cap):return type(value)is str and len(value)<=cap and not any(ord(c)<32 and c not in '\n\t'for c in value)

def validate(body,status):
 if type(body)is not dict or type(status)is not int:raise Invalid()
 state=body.get('state')
 if status!=200:
  if state not in ERRORS.get(status,()):raise Invalid()
  return {'state':'invalid_request'if status==400 else state},status
 if state=='target_unavailable':
  if set(body)!={'state','target','resolution'}or body['target']is not None or body['resolution']not in RESOLUTIONS:return {'state':'invalid_request'},400
  return dict(body),200
 if state not in SUCCESS or set(body)!=FIELDS:raise Invalid()
 if type(body['scan_complete'])is not bool or body['scan_complete']!=(state=='complete_mutable_read')or body['evidence_complete']is not False or body['coverage_gap']not in (True,False)or type(body['coverage_gap'])is not bool or body['total_count']is not None or body['consistency']!='mutable_read_not_snapshot'or body['evidence_scope']!='bounded_explicit_mentions_only_not_all_commodity_news':raise Invalid()
 if not matches(body['manifest'],r'[a-f0-9]{64}')or not matches(body['matcher_version'],r'[A-Za-z0-9_.-]{1,40}')or body['scope']!=body['next_cursor']:raise Invalid()
 if state=='continue_scan':
  if not matches(body['next_cursor'],r'[A-Za-z0-9_-]{43}'):raise Invalid()
 elif body['next_cursor']is not None:raise Invalid()
 for key in ('articles_checked','articles_refused_mentions_limit','articles_unreadable','articles_checked_this_page','articles_refused_this_page','articles_unreadable_this_page','rows_consumed_this_page','parent_pages','public_rows_received'):
  if type(body[key])is not int or not 0<=body[key]<=2000:raise Invalid()
 if body['rows_consumed_this_page']>100 or not 1<=body['parent_pages']<=20 or not plain(body['coverage_message'],300):raise Invalid()
 if body['articles_checked_this_page']+body['articles_refused_this_page']+body['articles_unreadable_this_page']!=body['rows_consumed_this_page']or body['articles_checked']+body['articles_refused_mentions_limit']+body['articles_unreadable']>body['public_rows_received']or body['coverage_gap']!=(body['articles_refused_mentions_limit']+body['articles_unreadable']>0)or any(body[total]<body[page]for total,page in [('articles_checked','articles_checked_this_page'),('articles_refused_mentions_limit','articles_refused_this_page'),('articles_unreadable','articles_unreadable_this_page')]):raise Invalid()
 if type(body['items'])is not list or len(body['items'])>25:raise Invalid()
 for item in body['items']:
  if type(item)is not dict or set(item)!={'article_key','relationships'}or not plain(item['article_key'],100)or not item['article_key'] or type(item['relationships'])is not list or not 1<=len(item['relationships'])<=32:raise Invalid()
  for link in item['relationships']:
   if type(link)is not dict or set(link)!={'article_key','kind','target','evidence','legal_classification_verified'}or link['article_key']!=item['article_key']or link['kind']!='reported_code_mention'or link['legal_classification_verified']is not False or not plain(link['evidence'],18001):raise Invalid()
   t=link['target']
   if type(t)is not dict or set(t)-{'system','edition','code','description','state'}or not {'system','edition','code','description'}<=set(t)or not matches(t['system'],r'[A-Z]{2,3}')or not matches(t['edition'],r'[A-Za-z0-9:_.-]{1,100}')or not matches(t['code'],r'[0-9]{2,12}')or not plain(t['description'],4000)or not t['description'] or 'state'in t and t['state']!='resolved':raise Invalid()
 return body,200

def install(app,origin,broker,env=None,*,response_validator=None):
 if not enabled(env or {}):return False
 from integration.news_finder_navigation_prep import enabled as navigation_enabled
 navigation_on=navigation_enabled(env or {})
 canonical=origin_value(origin)
 from flask import request,Response
 def response(body,status,extra=None):
  raw=serialize(body)
  if len(raw)>524288:raise Invalid()
  return Response(raw,status=status,mimetype='application/json',headers=extra)
 @app.route(PATH,methods=['POST','HEAD','OPTIONS'],provide_automatic_options=False)
 def coverage():
  if request.method in ('HEAD','OPTIONS'):
   broker.head();return Response(status=200 if request.method=='HEAD'else 204,headers={'Allow':'POST, HEAD, OPTIONS'})
  if request.headers.get('Origin')!=canonical or request.headers.get('Sec-Fetch-Site')!='same-origin'or request.headers.get('Sec-Fetch-Mode')not in ('cors','same-origin')or request.headers.get('Sec-Fetch-Dest')!='empty':return response({'state':'request_refused'},403)
  if request.query_string or request.headers.get('Content-Encoding')is not None or request.mimetype!='application/json'or set(request.mimetype_params)-{'charset'}or request.mimetype_params.get('charset','utf-8').lower()!='utf-8':return response({'state':'invalid_request'},400)
  try:
   raw=request.stream.read(1025)
   if len(raw)>1024:return response({'state':'request_too_large'},413)
   body=parse(raw)
  except Exception:return response({'state':'invalid_request'},400)
  try:
   if 'scope'in body:out,status=broker.page(**body)
   else:out,status=broker.page(body)
   evidence=None
   if navigation_on and status==200 and type(out)is dict and out.get('state')in SUCCESS:
    from integration.news_finder_navigation_prep import valid_evidence
    out=dict(out);evidence=out.pop('finder_navigation',None)
    from integration.finder_composition_f9 import selected
    selection=selected(app)
    if not valid_evidence(evidence,dict(selection.editions)if selection else None):raise Invalid()
   clean,status=(response_validator or validate)(out,status)
   if evidence is not None:
    from integration.news_finder_navigation_prep import decorate
    clean=dict(clean,finder_navigation=decorate(app,evidence))
   headers={'Retry-After':'60'}if status==429 and clean['state']in ('quota_wait','resolve_busy')else None
   return response(clean,status,headers)
  except Exception:return response({'state':'source_unavailable'},503)
 @app.after_request
 def coverage_headers(out):
  if request.path==PATH:
   out.headers['Cache-Control']='no-store';out.headers['X-Content-Type-Options']='nosniff';out.headers['Referrer-Policy']='no-referrer';out.headers['Content-Security-Policy']="default-src 'none'; frame-ancestors 'none'";out.headers['Vary']='Origin'
  return out
 hooks=app.after_request_funcs[None];hooks.remove(coverage_headers);hooks.insert(0,coverage_headers)
 return True
