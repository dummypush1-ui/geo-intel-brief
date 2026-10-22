"""Default-OFF comparison of two exact supplied F8 public snapshots.
No source acquisition, saved-user watch storage, provider, currentness or advice.
"""
import base64,gzip,io,json,re,hashlib
from pathlib import Path
from bisect import bisect_left
from flask import request,Response,jsonify
from integration.finder_binding_f8 import Binding
from integration.finder_composition_f9 import Selection
from integration.finder_proxy_f12.evidence import Evidence
from integration.public_ai_answers import SYSTEMS,Refused,plain
FLAG='PUBLIC_FINDER_SNAPSHOT_CHANGES_ENABLED'
PAGE='/workspace/finder-changes';API='/api/finder-snapshot-changes'
BASE='/workspace/assets/finder-changes-f13/'
PATHS=frozenset((PAGE,API,BASE+'view.js',BASE+'view.css'))
ROOT=Path(__file__).resolve().parent
NOTICE='Two preserved snapshots only. A difference is not proof of a current legal change; absence is not deletion, delisting or clearance. Verify official sources. Data, not advice.'
def enabled(env):
 if type(env)is not dict or any(type(k)is not str or type(v)is not str for k,v in env.items()):raise Refused('Plain environment strings required')
 value=env.get(FLAG,'false')
 if value not in ('true','false'):raise Refused('Exact snapshot change flag required')
 if value=='true'and env.get('PUBLIC_FINDER_CANDIDATE_COMPOSITION_ENABLED')!='true':raise Refused('Selected Finder required')
 return value=='true'
def snapshot_meta(binding,source=None):
 # Binding integrity is checked by the caller. Metadata-only missing-baseline
 # state must not decompress or index the full code dataset.
 build=Evidence.literal((binding.root/'offline.html').read_text()if source is None else source,'DATA_BUILD');plain(build,100)
 return {'dataset_build_label':build,'source_revision':binding.source_revision,'package_sha256':binding.package_sha256,'offline_sha256':next(pin for name,size,pin in binding.files if name=='offline.html'),'proof':'supplied_F8_artifact_integrity_not_official_freshness'}
class Snapshot:
 def __init__(self,binding):
  if type(binding)is not Binding:raise Refused('Exact reviewed public snapshot binding required')
  binding.verify();self.binding=binding;s=(binding.root/'offline.html').read_text()
  payload=re.findall(r'var DATA_B64 = "([A-Za-z0-9+/=]+)";',s)
  if len(payload)!=1:raise Refused('One bounded source dataset required')
  with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(payload[0],validate=True)))as stream:raw=stream.read(100_000_001)
  if len(raw)>100_000_000:raise Refused('Dataset cap')
  rows=json.loads(raw);supp=Evidence.literal(s,'US_CH97_SUPPLEMENT');seen={r[1]for r in rows if type(r)is list and r and r[0]==2};rows.extend(r for r in supp if r[1]not in seen)
  self.rows={};self.duplicates=set()
  for r in rows:
   if type(r)is not list or len(r)!=6 or type(r[0])is not int or not 0<=r[0]<len(SYSTEMS)or type(r[1])is not str or type(r[2])is not str or type(r[5])is not str:raise Refused('Snapshot row schema')
   if not re.fullmatch('[0-9]{2,12}',r[1]):continue
   key=(SYSTEMS[r[0]],r[1])
   if key in self.rows:self.duplicates.add(key)
   self.rows[key]=tuple(r)
  self.sorted={tag:sorted(code for system,code in self.rows if system==tag)for tag in SYSTEMS}
  self.gst=Evidence.literal(s,'GST_MAP');self.meta=snapshot_meta(binding,s)
 def value(self,system,code):
  key=(system,code);r=self.rows.get(key)
  if r is None:return {'state':'not_present_in_snapshot','wording':None,'listed_duty':None,'gst':None,'duplicate_identity':False}
  gst=None
  if system=='IN':gst=next((self.gst[code[:n]]for n in (8,6,4,2)if code[:n]in self.gst),self.gst.get('*'))
  return {'state':'present','wording':r[2],'listed_duty':r[5]or'Not listed','gst':gst,'duplicate_identity':key in self.duplicates}
 def links(self,system,code):
  # Exact preserved Finder linkage targets and at most8 extension samples per
  # system. No assertion that shared prefixes mean equivalent national goods.
  out=[];base6=code[:6]if len(code)>=6 else code
  for tag in SYSTEMS:
   target=code if tag==system else base6;arr=self.sorted[tag];at=bisect_left(arr,target);sample=[];count=0;digest=hashlib.sha256()
   while at<len(arr)and arr[at].startswith(target):
    if len(arr[at])>len(target):
     count+=1;digest.update(arr[at].encode()+b'\n')
     if len(sample)<8:sample.append(arr[at])
    at+=1
   chain=[target[:n]for n in (2,4,6,8)if n<=len(target)and(tag,target[:n])in self.rows]
   out.append({'system':tag,'target':target,'target_present':(tag,target)in self.rows,'chain':chain,'extension_count':count,'extension_sample':sample,'extension_membership_sha256':digest.hexdigest(),'sample_complete':count<=8})
  return out

def compare_values(before,after):
 return {'wording_changed':before['wording']!=after['wording'],'listed_duty_changed':before['listed_duty']!=after['listed_duty'],'gst_changed':before['gst']!=after['gst'],'presence_changed':before['state']!=after['state']}
def compare(before,after,system,code):
 if type(before)is not Snapshot or type(after)is not Snapshot or system not in SYSTEMS or type(code)is not str or not re.fullmatch('[0-9]{2,12}',code):raise Refused('Exact snapshot comparison identity required')
 before.binding.verify();after.binding.verify();a=before.value(system,code);b=after.value(system,code)
 links_a=before.links(system,code)if a['state']=='present'else[];links_b=after.links(system,code)if b['state']=='present'else[]
 # Bounded22system rows show additions/removals as snapshot observations only.
 la={x['system']:x for x in links_a};lb={x['system']:x for x in links_b};link_changes=[]
 for tag in SYSTEMS:
  x=la.get(tag);y=lb.get(tag)
  if x!=y:link_changes.append({'system':tag,'before':x,'after':y})
 return {'snapshot_relationship':'identical_artifact'if before.meta['package_sha256']==after.meta['package_sha256']and before.meta['offline_sha256']==after.meta['offline_sha256']else'distinct_supplied_artifacts_chronology_unverified','baseline_chronology_verified':False,'state':'compared','system':system,'code':code,'before_snapshot':dict(before.meta),'after_snapshot':dict(after.meta),'before':a,'after':b,'changes':compare_values(a,b),'link_changes':link_changes,'link_scope':'Original Finder prefix/target/chain and first 8 extension samples per system, not legal equivalence. Full extension membership is digest-compared; display shows only the first 8 codes, not a complete added/removed-code list.','notice':NOTICE,'currentness_verified':False,'official_refreshes':0}
class Comparison:
 def __init__(self,selection,baseline=None):
  if type(selection)is not Selection:raise Refused('Selected Finder required')
  selection.verify();self.selection=selection
  # No baseline means no comparison: avoid allocating an unused full index.
  # Reuse only the exact same immutable Binding object, never a matching hash
  # from another root whose drift must remain independently detectable.
  self.after=Snapshot(selection.binding)if baseline is not None else None
  self.before=(self.after if baseline is selection.binding else Snapshot(baseline))if baseline is not None else None
 def read(self,system,code):
  if type(system)is not str or system not in SYSTEMS or type(code)is not str or not re.fullmatch('[0-9]{2,12}',code):raise Refused('Exact identity required')
  self.selection.verify()
  if self.before is None:return {'state':'baseline_unavailable','notice':'A second verified public snapshot has not been supplied. No comparison or change claim is made. '+NOTICE,'after_snapshot':dict(self.after.meta)if self.after is not None else snapshot_meta(self.selection.binding)}
  return compare(self.before,self.after,system,code)
def prepare(env,selection,baseline=None):
 if not enabled(env):
  if baseline is not None:raise Refused('Baseline supplied while changes disabled')
  return None
 return Comparison(selection,baseline)
def install(app,comparison):
 if type(comparison)is not Comparison:raise Refused('Exact comparison service required')
 @app.get(PAGE)
 def f13_page():return Response((ROOT/'view.html').read_text(),mimetype='text/html')
 @app.get(BASE+'<name>')
 def f13_asset(name):
  if request.path not in PATHS:return Response(status=404)
  return Response((ROOT/name).read_text(),mimetype='text/css'if name.endswith('.css')else'application/javascript')
 @app.get(API)
 def f13_data():
  if request.method=='HEAD':return Response(status=200)
  if set(request.args)!={'system','code'}or any(len(request.args.getlist(k))!=1 for k in request.args)or len(request.query_string)>80:return jsonify(state='invalid_identity'),400
  try:return jsonify(comparison.read(request.args['system'],request.args['code']))
  except Exception:return jsonify(state='unavailable',notice='Snapshot integrity or identity unavailable. No change claim is made.'),503
 @app.after_request
 def headers(response):
  if request.path=='/workspace'and response.status_code==200:
   response.direct_passthrough=False;s=response.get_data(as_text=True)
   if s.count('</nav>')!=1:raise Refused('Workspace navigation seam drift')
   response.set_data(s.replace('</nav>','<a href="'+PAGE+'">Snapshot changes</a></nav>'))
  if request.path in PATHS:
   response.headers['Cache-Control']='no-store';response.headers['Referrer-Policy']='no-referrer';response.headers['Content-Security-Policy']="default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'self'; base-uri 'none'; form-action 'none'"
  return response
 app.extensions['finder_changes_f13']=comparison
