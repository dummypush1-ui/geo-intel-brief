"""Default-OFF passive tariff page, no source connection or duty inference.
Fixture snapshots are explicit Python inputs only; no env/path/DB discovery.
"""
from pathlib import Path
from datetime import datetime,timezone
from collections import deque
from threading import Lock
import hashlib,json,time
from flask import Response,request,jsonify
from integration.tariff_evidence import TariffEvidenceSnapshot
ROOT=Path(__file__).resolve().parents[1]
FLAG='PUBLIC_TARIFF_EVIDENCE_ENABLED'
PAGE='/workspace/tariffs';API='/api/tariff-evidence';ASSET='/workspace/assets/public_tariff_evidence.js'
PATHS=frozenset((PAGE,API,ASSET));NOT_CONNECTED='Evidence source not connected: no conclusion about tariffs.'
PINS={'integration/news_api.py': '77137ebf1d8debef70bc49bdc0a253c9b4845429135431af9e8e46328217dff7', 'integration/tariff_evidence.py': 'cac8e46fade3005839a6a4f179a11675d35b855bbe11b8712b77e3431454b69c', 'integration/ui/public_tariff_evidence.html': '39103445416a9e5e1ac010186d96d0ac61b8d186122a629e830b1d5588d1ddd4', 'integration/ui/public_tariff_evidence.js': 'c1b60846723de0ef513929fabc4b7075a74261eae6ba623843da85d41f572200', 'integration/ui/workspace.html': 'f0947e8b67b2c579f105ce3f24752d96e1d7633718a7ba0972be41b455a8324f', 'integration/ui/weekly.html': '18a7dac2b8854d3bd51146d9ac6ed55c9146d0ae6bc7b7d39c557c7519eb2faa'}

def prepare(env):
 value=env.get(FLAG,'false')
 if value not in ('true','false'):raise ValueError('Exact tariff evidence flag required')
 if value=='false':return False
 if env.get('PREVIEW_PUBLIC_SAMPLE_ENABLED')!='true':raise ValueError('Public tariff composition required')
 try:
  for name,pin in PINS.items():
   if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=pin:raise ValueError()
  for name in ['integration/ui/workspace.html','integration/ui/weekly.html']:
   if (ROOT/name).read_text().count('</nav>')!=1:raise ValueError()
 except Exception:raise ValueError('Tariff source unavailable')from None
 return True

class Service:
 def __init__(self,snapshot=None,clock=time.monotonic,now=lambda:datetime.now(timezone.utc)):
  if snapshot is not None and type(snapshot)is not TariffEvidenceSnapshot:raise ValueError('Exact tariff snapshot required')
  self.snapshot=None if snapshot is None else TariffEvidenceSnapshot(snapshot._observed_at,snapshot._items)
  self.clock=clock;self.now=now;self.lock=Lock();self.starts=deque()
 def run(self,jurisdiction):
  if not self.lock.acquire(False):return {'state':'busy'},429
  try:
   tick=self.clock()
   while self.starts and tick-self.starts[0]>=60:self.starts.popleft()
   if len(self.starts)>=10:return {'state':'rate_limited'},429
   self.starts.append(tick)
   if self.snapshot is None:return {'state':'evidence_source_not_connected','message':NOT_CONNECTED,'current_rates_verified':False,'legal_effect_independently_verified':False,'network':False,'polling':False},200
   # Revalidate content at each admitted GET, not only exact type at startup.
   snap=TariffEvidenceSnapshot(self.snapshot._observed_at,self.snapshot._items)
   return snap.view(self.now(),jurisdiction),200
  except Exception:return {'state':'evidence_unavailable'},503
  finally:self.lock.release()

def install(app,origin,snapshot=None):
 from integration.news_api import create_app
 for endpoint,path in [('tariff_workspace',PAGE),('tariff_evidence_view',API)]:
  expected=next(c for c in create_app.__code__.co_consts if getattr(c,'co_name',None)==endpoint)
  rules=[r for r in app.url_map.iter_rules()if r.endpoint==endpoint]
  if getattr(app.view_functions.get(endpoint),'__code__',None)is not expected or len(rules)!=1 or rules[0].rule!=path or rules[0].methods!={'GET','HEAD','OPTIONS'}:raise ValueError('Tariff mount unavailable')
 html=(ROOT/'integration/ui/public_tariff_evidence.html').read_text();js=(ROOT/'integration/ui/public_tariff_evidence.js').read_text();service=Service(snapshot)
 def shell():return Response(html if any(r.rule=='/api/weekly-report.pdf'for r in app.url_map.iter_rules())and app.extensions.get('public_weekly_pdf')else html.replace('<a href="/workspace/weekly">Weekly PDF</a>',''),mimetype='text/html')
 def evidence():
  if request.method=='HEAD':return Response(status=200,mimetype='application/json')
  body,status=service.run(request.args.get('jurisdiction',''))
  encoded=json.dumps(body,ensure_ascii=False,separators=(',',':')).encode('utf-8')
  if len(encoded)>250000:return jsonify(state='evidence_unavailable'),503
  return Response(encoded,status=status,mimetype='application/json')
 app.view_functions['tariff_workspace']=shell;app.view_functions['tariff_evidence_view']=evidence
 @app.get(ASSET)
 def public_tariff_js():return Response(js,mimetype='application/javascript')
 @app.before_request
 def guard():
  if request.path not in PATHS:return
  if request.host_url.rstrip('/')!=origin or request.method not in ('GET','HEAD'):return jsonify(state='unavailable'),403
  if request.path!=API:
   if request.query_string:return jsonify(state='invalid_query'),400
  else:
   if len(request.query_string)>32 or b'%' in request.query_string or set(request.args)-{'jurisdiction'} or any(len(request.args.getlist(k))!=1 for k in request.args)or request.args.get('jurisdiction','')not in ('','IN','US','EU'):return jsonify(state='invalid_query'),400
 @app.after_request
 def headers(r):
  if request.path in ('/workspace','/workspace/weekly')and r.status_code==200 and mounted(app):
   if request.method=='HEAD':r.headers.pop('Content-Length',None);r.automatically_set_content_length=False
   else:
    r.direct_passthrough=False;text=r.get_data(as_text=True)
    if text.count('</nav>')!=1:raise ValueError('Tariff navigation seam drift')
    r.set_data(text.replace('</nav>','<a href="/workspace/tariffs">Supplied tariff documents</a></nav>',1))
  if request.path in PATHS:
   r.headers['Cache-Control']='no-store';r.headers['Referrer-Policy']='no-referrer';r.headers['X-Content-Type-Options']='nosniff'
   r.headers['Content-Security-Policy']="default-src 'none'; frame-ancestors 'none'"if request.path==API else "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; object-src 'none'; form-action 'none'; frame-ancestors 'none'"
  return r
 hooks=app.after_request_funcs[None];hooks.remove(headers);hooks.insert(0,headers)
 app.extensions['public_tariff_evidence']=service
 app.extensions['public_tariff_view']=shell

def mounted(app):
 return type(app.extensions.get('public_tariff_evidence'))is Service and app.view_functions.get('tariff_workspace') is app.extensions.get('public_tariff_view') and any(r.rule==PAGE and r.endpoint=='tariff_workspace'for r in app.url_map.iter_rules())
