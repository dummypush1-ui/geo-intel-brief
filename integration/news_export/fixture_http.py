"""Dev/test-only offline fixture CSV app. Production modules never import this.

Payloads are inert; all request execution is concrete internal code. No DB, env,
client, network, persistent storage or production composition.
"""
import csv,io,json,hashlib,math
from threading import Lock
from bson import ObjectId
from flask import Flask,request,Response,jsonify,Request
from .keyset_plan import resume,ORDER
from .raw_pager import RawPager
from .original_stream import OriginalStream
from .original_contract import GEO_FIELDS,BRICS_FIELDS,original_snapshot

LABEL='supplied-offline-fixture'
_SLOT_LOCK=Lock()
_SLOT_BUSY=[False]
REASONS={'source exhausted':'source_exhausted','requested source limit':'requested_limit','hard source cap':'hard_cap','byte budget':'byte_budget','time budget':'time_budget','invalid source row':'invalid_row','source unavailable':'source_unavailable'}
KINDS={'source_exhausted':'EXPORT_COMPLETE','requested_limit':'EXPORT_COMPLETE','hard_cap':'EXPORT_TRUNCATED','byte_budget':'EXPORT_TRUNCATED','time_budget':'EXPORT_TRUNCATED','invalid_row':'EXPORT_INCOMPLETE','source_unavailable':'EXPORT_INCOMPLETE'}

def frozen_fixture(data):
 if type(data) is not dict or any(type(k) is not str for k in data) or not set(data)<=set(ORDER):raise ValueError('plain fixture')
 result={};total=0;count=0
 for project,rows in data.items():
  if type(project) is not str or type(rows) is not list:raise ValueError('plain fixture')
  count+=len(rows)
  if count>10000:raise ValueError('fixture rows')
  retained=[];last=None;fields=set(GEO_FIELDS if project=='geo' else BRICS_FIELDS)|{'_id','summary'}
  for row in rows:
   if type(row) is not dict or any(type(k) is not str or k not in fields for k in row):raise ValueError('plain row')
   copied={};frozen=[]
   for key,value in row.items():
    if key=='_id' and type(value) is ObjectId:v=ObjectId(value.binary)
    elif key=='corroborated_by' and type(value) is list:
     if len(value)>100 or any(type(x) is not str or len(x)>8000 or any(0xD800<=ord(c)<=0xDFFF for c in x) for x in value):raise ValueError('plain list')
     v=tuple(value)
    elif value is None or type(value) in (bool,str,int,float):
     if type(value) is str and (len(value)>32000 or any(0xD800<=ord(c)<=0xDFFF for c in value)):raise ValueError('plain string')
     if type(value) in (int,float) and (not math.isfinite(value) or abs(value)>10**12):raise ValueError('finite number')
     v=value
    else:raise ValueError('plain scalar')
    frozen.append((key,v));copied[key]=list(v) if type(v) is tuple else v
   current=resume(project,copied)
   if last is not None and not current.values<last:raise ValueError('source order')
   last=current.values
   encoded=json.dumps(copied,ensure_ascii=False,allow_nan=False,default=lambda x:str(x) if type(x) is ObjectId else None,separators=(',',':')).encode()
   total+=len(encoded)+1
   if len(encoded)>128*1024 or total>8*1024*1024:raise ValueError('fixture bytes')
   # Budget check precedes retention. Immutable tuples hold exact plain values.
   retained.append(tuple(frozen))
  result[project]=tuple(retained)
 return tuple(result.items())

def _pager(project,frozen):
 rows=dict(frozen).get(project,())
 def execute(plan):
  out=[]
  for values in rows:
   row={k:list(v) if type(v) is tuple else v for k,v in values}
   query=plan['query']
   if query and not any(all(row[k]<v['$lt'] if type(v) is dict else row[k]==v for k,v in t.items()) for t in query['$or']):continue
   out.append(row)
   if len(out)==plan['limit']:break
  return out
 return RawPager(project,execute,lambda p,o:True,page_size=15)

def validate_file(data,project):
 """Validate protocol, exact original bytes hashed, proper multiline CSV parser."""
 if type(data) is not bytes or data.startswith(b'\xef\xbb\xbf') or project not in ORDER:raise ValueError('file')
 stream=io.StringIO(data.decode('utf-8'),newline='');reader=csv.reader(stream,strict=True);records=[];starts=[]
 while True:
  start=stream.tell()
  try:r=next(reader)
  except StopIteration:break
  if not stream.getvalue()[start:stream.tell()].endswith('\r\n'):raise ValueError('record ending')
  records.append(r);starts.append(start)
 fields=GEO_FIELDS if project=='geo' else BRICS_FIELDS
 if len(records)<2 or tuple(records[0])!=fields or any(len(r)!=len(fields) for r in records):raise ValueError('records')
 footers=[i for i,r in enumerate(records) if r[0] in set(KINDS.values())]
 if footers!=[len(records)-1] or any(cell.startswith('EXPORT_') for r in records[1:-1] for cell in r):raise ValueError('footer')
 f=records[-1];reason=f[1].removeprefix('fixture:')
 if f[1]!='fixture:'+reason or KINDS.get(reason)!=f[0]:raise ValueError('status')
 cap=10000 if project=='geo' else 5000
 if any(len(f[i])>5 for i in (2,3)):raise ValueError('count bound')
 if not f[2].isascii() or not f[2].isdigit() or int(f[2])!=len(records)-2:raise ValueError('rows')
 if not f[3].isascii() or not f[3].isdigit() or not int(f[2])<=int(f[3])<=cap:raise ValueError('read')
 if f[5] not in ('0','1') or any(f[6:]):raise ValueError('metadata')
 prefix=stream.getvalue()[:starts[-1]].encode('utf-8')
 if f[4]!=hashlib.sha256(prefix).hexdigest():raise ValueError('digest')
 return {'kind':f[0],'reason':reason,'scope':LABEL,'rows':int(f[2]),'read':int(f[3])}

def create_original_export_fixture_app(data,*,authorize):
 """Tests/dev only. authorize is trusted auth, never a fixture-data callback."""
 if not callable(authorize):raise ValueError('private auth required')
 frozen=frozen_fixture(data);app=Flask(__name__,static_folder=None);app.debug=False
 lock=_SLOT_LOCK;busy=_SLOT_BUSY
 @app.before_request
 def auth():
  allowed=request.environ.get('fixture_authorized') is True
  if not allowed:return jsonify(error='Private fixture unavailable'),403
 @app.after_request
 def headers(r):
  r.headers.update({'Cache-Control':'private, no-store, max-age=0','Pragma':'no-cache','Expires':'0','Vary':'Authorization, Cookie','X-Content-Type-Options':'nosniff','X-Robots-Tag':'noindex, nofollow','X-Export-Fixture':LABEL})
  for name in ('ETag','Last-Modified','Accept-Ranges'):r.headers.pop(name,None)
  if request.method=='HEAD':
   r.automatically_set_content_length=False;r.headers.pop('Content-Length',None);r.headers['X-Export-Readiness']='metadata-only'
  return r
 @app.errorhandler(Exception)
 def error(exc):
  from werkzeug.exceptions import HTTPException
  return jsonify(error='Fixture unavailable'),exc.code if isinstance(exc,HTTPException) else 500
 @app.route('/api/original-export/<project>.csv',methods=['GET','HEAD','OPTIONS'],strict_slashes=True)
 def export(project):
  if request.headers.get('X-HTTP-Method-Override') or '_method' in request.args:return jsonify(error='Method override unavailable'),400
  if request.method=='OPTIONS':return Response(status=204,headers={'Allow':'GET, HEAD, OPTIONS'})
  if project not in ORDER:return jsonify(error='Project unavailable'),404
  if project not in dict(frozen):return jsonify(error='Fixture unavailable'),503
  args={k:(v[0] if len(v)==1 else v) for k,v in request.args.lists()}
  try:_,meta,_=original_snapshot([],project,args)
  except Exception:return jsonify(error='Invalid export arguments'),400
  meta.pop('X-Export-Truncated',None);meta['X-Export-Scope']=LABEL
  meta['X-Export-Trailer']='final fixture status, SHA256 preceding UTF-8 CSV bytes'
  if request.method=='HEAD':return Response(status=200,headers=meta)
  with lock:
   if busy[0]:return jsonify(error='Fixture export busy'),429
   busy[0]=True
  transferred=False;closed=[False];stream=None;pager=None
  def release():
   with lock:
    if not closed[0]:closed[0]=True;busy[0]=False
  def cleanup():
   try:
    if stream is not None:stream.close()
    elif pager is not None:RawPager._shutdown(pager)
   finally:release()
  try:
   pager=_pager(project,frozen);stream=OriginalStream(pager,project,args)
   def body():
    try:
     for part in stream:
      # Footer is its own chunk. Preserve payload digest, replace reason only.
      parsed=list(csv.reader(io.StringIO(part.decode(),newline='')))
      if len(parsed)==1 and parsed[0][0] in set(KINDS.values()):
       r=parsed[0];r[1]='fixture:'+REASONS[r[1]]
       buf=io.StringIO(newline='');csv.writer(buf).writerow(r);part=buf.getvalue().encode()
      yield part
    finally:cleanup()
   response=Response(body(),headers=meta);response.call_on_close(cleanup)
   request.environ['fixture_cleanup']=cleanup
   transferred=True;return response
  except Exception:return jsonify(error='Fixture unavailable'),503
  finally:
   if not transferred:cleanup()
 original_wsgi=app.wsgi_app
 def outer_wsgi(environ,start_response):
  # Request without app URL binding: auth precedes malformed routing paths.
  try:allowed=authorize(Request(environ)) is True
  except Exception:allowed=False
  if not allowed:
   r=Response(b'{"error":"Private fixture unavailable"}\n',status=403,mimetype='application/json')
   r.headers.update({'Cache-Control':'private, no-store, max-age=0','Pragma':'no-cache','Expires':'0','Vary':'Authorization, Cookie','X-Content-Type-Options':'nosniff','X-Robots-Tag':'noindex, nofollow','X-Export-Fixture':LABEL})
   if environ.get('REQUEST_METHOD')=='HEAD':
    r.automatically_set_content_length=False;r.headers.pop('Content-Length',None);r.headers['X-Export-Readiness']='metadata-only'
   return r(environ,start_response)
  try:environ.get('PATH_INFO','').encode('latin-1').decode('utf-8','replace')
  except (UnicodeError,AttributeError):
   r=Response(b'{"error":"Fixture unavailable"}\n',status=400,mimetype='application/json')
   r.headers.update({'Cache-Control':'private, no-store, max-age=0','Pragma':'no-cache','Expires':'0','Vary':'Authorization, Cookie','X-Content-Type-Options':'nosniff','X-Robots-Tag':'noindex, nofollow','X-Export-Fixture':LABEL})
   if environ.get('REQUEST_METHOD')=='HEAD':
    r.automatically_set_content_length=False;r.headers.pop('Content-Length',None);r.headers['X-Export-Readiness']='metadata-only'
   return r(environ,start_response)
  environ['fixture_authorized']=True
  try:return original_wsgi(environ,start_response)
  except BaseException:
   # A failed start_response happens after view ownership transfer, before
   # server receives the iterable. Close this request's stream without relying
   # on the server or garbage collection.
   cleanup=environ.pop('fixture_cleanup',None)
   if cleanup is not None:cleanup()
   raise
 app.wsgi_app=outer_wsgi
 return app
