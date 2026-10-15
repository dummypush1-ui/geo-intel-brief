"""Default-OFF original-column Geo snapshot CSV HTTP bridge.

Explicit injected source review only. No Mongo client creation, environment URI,
latest100 fallback, collector/mail action, browser activation or source proof.
"""
import hashlib,json,re
from dataclasses import dataclass
from pathlib import Path
from threading import BoundedSemaphore,Lock
from urllib.parse import urlsplit
from flask import Response,jsonify,request
from integration.news_export.original_contract import original_snapshot,GEO_FIELDS
from integration.news_export.export import ExportRequestError
from integration.news_export.geo_snapshot import create_geo_original_stream
ROOT=Path(__file__).resolve().parents[2]
FLAG='PUBLIC_GEO_ORIGINAL_EXPORT_ENABLED'
PATH='/api/geo-original-export.csv'
DEPENDENCIES=('PREVIEW_PUBLIC_SAMPLE_ENABLED','PUBLIC_NEWS_READ_ENABLED',
 'NEWS_STORE_MAPPING_VERIFIED','PUBLIC_NEWS_DISCLOSURE_VERIFIED','GEO_READONLY_CREDENTIAL_VERIFIED')
FIELDS={'mapping','read_only','snapshot_supported','index','index_explain_verified'}
# Process-wide admission shared by independently built apps. Not distributed.
_SLOT=BoundedSemaphore(1)
_CLEANUP='geo_original_export_e2_cleanup'

@dataclass(frozen=True)
class SourceBinding:
 """Trusted application input, NOT evidence of actual review by itself.

 The operator must independently verify this source's public original-field
 disclosure, read-only credential, stable snapshot support, binary collation,
 and complete original-order index/explain. No environment strings create it.
 Client lifetime belongs to the caller; each request owns only its session.
 """
 client:object
 review:dict
 public_fields_reviewed:tuple

def checked(binding):
 if type(binding)is not SourceBinding:raise ValueError('Explicit original-export source binding required')
 if type(binding.public_fields_reviewed)is not tuple or binding.public_fields_reviewed!=GEO_FIELDS:raise ValueError('Exact original public-field disclosure review required')
 r=binding.review
 if type(r)is not dict or any(type(k)is not str for k in r)or set(r)!=FIELDS or type(r.get('mapping'))is not tuple or r.get('mapping')!=('geo_intel','articles') or any(r.get(k)is not True for k in ('read_only','snapshot_supported','index_explain_verified')):raise ValueError('Exact original-export source review required')
 index=r.get('index')
 if type(index)is not str or not re.fullmatch('[A-Za-z0-9_-]{1,128}',index,re.ASCII)or binding.client is None:raise ValueError('Explicit original-export source review required')
 return SourceBinding(binding.client,dict(r),binding.public_fields_reviewed)

def prepare(env,binding=None):
 value=env.get(FLAG,'false')
 if value not in ('true','false'):raise ValueError('Exact original-export flag required')
 if value=='false':
  if binding is not None:raise ValueError('Disabled original-export cannot accept binding')
  return None
 if any(env.get(k)!='true'for k in DEPENDENCIES):raise ValueError('Reviewed public original-export composition required')
 b=checked(binding)
 pins=json.loads((ROOT/'integration/news_export_e2/pins.json').read_text())
 if set(pins)!={'integration/news_export/'+n for n in ('geo_snapshot.py','original_contract.py','original_stream.py','raw_pager.py','keyset_plan.py','export.py')}:raise ValueError('Exact export source pins required')
 if any(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=h for n,h in pins.items()):raise ValueError('Original-export source drift')
 return b

class Lease:
 def __init__(self,stream,release):self.stream=stream;self.release=release;self.lock=Lock();self.closed=False
 def __iter__(self):return self
 def __next__(self):
  if self.closed:raise StopIteration
  try:return next(self.stream)
  except BaseException:self.close();raise
 def close(self):
  with self.lock:
   if self.closed:return
   self.closed=True
  try:self.stream.close()
  finally:self.release()

def install(app,origin,binding):
 b=checked(binding);p=urlsplit(origin)
 if p.scheme not in ('http','https')or not p.netloc or p.username or p.password or p.path or p.query or p.fragment:raise ValueError('Exact export origin required')
 if any(r.rule==PATH for r in app.url_map.iter_rules()):raise ValueError('Original-export route collision')
 active=set();lock=Lock();stopped=[False]
 def close():
  with lock:stopped[0]=True;leases=list(active)
  for lease in leases:lease.close()
 @app.before_request
 def guard():
  if request.path!=PATH:return
  if request.host_url.rstrip('/')!=origin or request.method not in ('GET','HEAD'):return jsonify(error='Export unavailable'),403
  if request.headers.get('X-HTTP-Method-Override')or '_method'in request.args:return jsonify(error='Invalid export arguments'),400
 @app.get(PATH)
 def export():
  args={k:v[0]if len(v)==1 else v for k,v in request.args.lists()}
  try:_,headers,_=original_snapshot([],'geo',args)
  except ExportRequestError:return jsonify(error='Invalid export arguments'),400
  headers.pop('X-Export-Truncated',None)
  headers['X-Export-Scope']='injected_reviewed_geo_snapshot_original_columns_capped'
  headers['X-Export-Trailer']='final EXPORT_COMPLETE/EXPORT_TRUNCATED/EXPORT_INCOMPLETE with SHA256 of preceding bytes'
  if request.method=='HEAD':
   headers['X-Export-Readiness']='metadata-only-not-source-readiness'
   return Response(status=200,headers=headers)
  with lock:
   if stopped[0]:return jsonify(error='Export unavailable'),503
  if not _SLOT.acquire(False):return jsonify(error='Export busy'),429,{'Retry-After':'5'}
  stream=None;lease=None;transferred=False
  def release():
   with lock:
    if lease is not None:active.discard(lease)
   _SLOT.release()
  try:
   stream=create_geo_original_stream(b.client,review=b.review,args=args)
   lease=Lease(stream,release)
   with lock:
    if stopped[0]:raise ValueError()
    active.add(lease)
   request.environ[_CLEANUP]=lease.close
   response=Response(lease,headers=headers)
   response.call_on_close(lease.close);transferred=True;return response
  except Exception:return jsonify(error='Export unavailable'),503
  finally:
   if not transferred:
    if lease is not None:lease.close()
    else:
     try:
      if stream is not None:stream.close()
     finally:release()
 @app.after_request
 def headers(r):
  if request.path==PATH:
   r.headers.update({'Cache-Control':'private, no-store, max-age=0','Pragma':'no-cache','Expires':'0','Referrer-Policy':'no-referrer','X-Content-Type-Options':'nosniff','X-Robots-Tag':'noindex, nofollow','Content-Security-Policy':"default-src 'none'; frame-ancestors 'none'"})
   for k in ('ETag','Last-Modified','Accept-Ranges'):r.headers.pop(k,None)
   if request.method=='HEAD':r.automatically_set_content_length=False;r.headers.pop('Content-Length',None)
  return r
 hooks=app.after_request_funcs[None];hooks.remove(headers);hooks.insert(0,headers)
 original=app.wsgi_app
 def wsgi(environ,start_response):
  def start(status,headers,exc_info=None):
   # Flask may swallow a failing after_request hook and replace the response.
   # Such an error still owns a prepared stream which must not strand a slot.
   meta=dict(headers)
   if environ.get(_CLEANUP) is not None and (not status.startswith('200 ')or meta.get('X-Export-Scope')!='injected_reviewed_geo_snapshot_original_columns_capped'):
    environ[_CLEANUP]()
   return start_response(status,headers,exc_info)
  try:return original(environ,start)
  except BaseException:
   cleanup=environ.pop(_CLEANUP,None)
   if cleanup is not None:cleanup()
   raise
 app.wsgi_app=wsgi
 import atexit
 atexit.register(close)
 app.extensions['geo_original_export_close']=close
 app.extensions['geo_original_export']={'scope':'injected_snapshot','server_client_created':False,'source_verified_by_this_module':False}
