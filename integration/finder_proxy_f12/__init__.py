"""Default-OFF feature broker over the existing fixed proxy. No new key/host.
No catalog entries, entitlement claims, privacy grants or live activation here.
"""
import json,re,hashlib
from dataclasses import dataclass
from pathlib import Path
from integration.public_ai_answers import Refused,decode,plain,validate,answer
from integration.finder198_server import _response
from integration.finder198_transport import FixedProxyTransport,proxy_request
from integration.finder198_receipts import ProxyReceiptBudget
from integration.finder198_connector import plan_ai
from integration.existing_proxy_codec import request_plan,decode_answer
from .evidence import Evidence,source_editions
FLAG='PUBLIC_FINDER_PROXY_FEATURES_ENABLED'
PATH='/api/finder-broker/features'
ASSET='/workspace/assets/finder-proxy-f12/workspace.js'
ASSETS=frozenset('/workspace/assets/finder-proxy-f12/'+n for n in ('workspace.js','client.mjs','panel.mjs','ships226.mjs','panel.css'))
ROOT=Path(__file__).resolve().parent
FEATURES=frozenset(('classification_context','plain_words','trade_brief','paperwork','code_comparison','report_context'))
QUESTIONS={'plain_words':'Explain this preserved wording simply.','trade_brief':'Summarize the supplied snapshot trade evidence.','paperwork':'Explain the named snapshot paperwork only.','code_comparison':'Compare the supplied preserved codes without a legal verdict.','report_context':'Write short source-bounded context for the existing report. No current research or unsupported sections.'}
def enabled(env):
 if type(env)is not dict or any(type(k)is not str or type(v)is not str for k,v in env.items()):raise Refused('Plain environment strings required')
 value=env.get(FLAG,'false')
 if value not in ('true','false'):raise Refused('Exact feature proxy flag required')
 if value=='true'and any(env.get(f)!='true'for f in ('PUBLIC_FINDER_CANDIDATE_COMPOSITION_ENABLED','PUBLIC_FINDER_DATA_REPORT_ENABLED')):raise Refused('Selected F11 required')
 return value=='true'
def validate_feature(v):
 if type(v)is not dict or set(v)!={'nonce','feature','question','candidates'}:raise Refused('Exact feature request required')
 if type(v['nonce'])is not str or not re.fullmatch(r'[A-Za-z0-9_-]{20,80}',v['nonce']):raise Refused('Exact nonce required')
 if type(v['feature'])is not str or v['feature']not in FEATURES:raise Refused('Exact feature required')
 validate(dict(mode='finder',question=v['question']or'Context',candidates=v['candidates']))
 count=len(v['candidates']);expected=(1,4)if v['feature']=='classification_context'else(2,2)if v['feature']=='code_comparison'else(1,1)
 if not expected[0]<=count<=expected[1]:raise Refused('Exact feature identity count required')
 if v['feature']!='classification_context'and v['question']!='':raise Refused('Server-owned feature question required')
 if v['feature']=='classification_context':plain(v['question'],1000)
 return v
@dataclass(frozen=True)
class FeaturePermission:
 # References must be recovered from the owner's authorized scope and current
 # proxy/vendor evidence. Fixture strings in tests are not a live grant.
 # Must cover selected source evidence AND typed classifier query <=1000chars.
 disclosure_reference:str
 spend_reference:str
 retention_reference:str
 no_paid_fallback_reference:str
 observed_at:int
 expires_at:int
 def validate(self,now):
  if type(now)is not int or type(self.observed_at)is not int or type(self.expires_at)is not int or not 0<=self.observed_at<=now<self.expires_at<=self.observed_at+3600:raise Refused('Fresh feature permission evidence required')
  for value in (self.disclosure_reference,self.spend_reference,self.retention_reference,self.no_paid_fallback_reference):
   if type(value)is not str or not 1<=len(value)<=200 or any(ord(c)<33 or ord(c)>126 for c in value):raise Refused('Source-grounded permission references required')
  return self
class FeatureBroker:
 """Call only AFTER finder198_auth authenticated principal+session/CSRF gates.
 No ambient env/client/model selection or request-provided URLs/prompts/models.
 """
 def __init__(self,evidence,budget,transport,clock,*,provider,model,permission=None):
  if type(evidence)is not Evidence or type(budget)is not ProxyReceiptBudget or type(transport)is not FixedProxyTransport or not callable(clock):raise Refused('Exact existing broker collaborators required')
  self.evidence=evidence;self.budget=budget;self.transport=transport;self.clock=clock;self.provider=provider;self.model=model;self.permission=permission
 def __call__(self,req,principal_hash):
  if req.path!=PATH or req.method!='POST':return _response({'ok':False,'error':'not_found'},404)
  try:
   if req.query_string or req.mimetype!='application/json'or req.content_length is None or not 1<=req.content_length<=16384:raise Refused('Bounded JSON required')
   if 'HTTP_TRANSFER_ENCODING'in req.environ:raise Refused('Framing refused')
   raw=req.stream.read(16385 if req.environ.get('wsgi.input_terminated')is True else req.content_length)
   if len(raw)!=req.content_length:raise Refused('Length mismatch')
   v=validate_feature(decode(raw,16384));feature=v['feature']
   if type(principal_hash)is not str or not re.fullmatch('[a-f0-9]{64}',principal_hash):raise Refused('Authenticated principal required')
   if type(self.permission)is not FeaturePermission:raise Refused('Feature disclosures and spend held')
   self.permission.validate(self.clock())
   # Refuse BEFORE receipts/provider dispatch without reviewed existing catalog.
   plan_ai(self.provider,self.model,now=self.clock())
   evidence=self.evidence.project(v['candidates'],feature)
   question=v['question']if feature=='classification_context'else QUESTIONS[feature]
   plan=request_plan(feature,question,[{'id':r['id'],'text':r['text']}for r in evidence],provider=self.provider,model=self.model)
   out=proxy_request(self.budget,self.transport,nonce=v['nonce'],operation='ai',provider=self.provider,model=self.model,body=plan['body'],principal_hash=principal_hash,clock=self.clock)
   if out['state']=='replay_status_only':return _response({'ok':False,'state':'replay_status_only','cached_answer':False},409)
   if out['state']!='complete':raise Refused('Proxy outcome held')
   checked=answer(decode_answer(self.provider,out['status'],'application/json',out['body']),evidence)
   return _response(dict(ok=True,feature=feature,**checked))
  except Exception:return _response({'ok':False,'error':'finder_proxy_feature_held','message':'AI unavailable or outcome held. No automatic retry. Data-only Finder/report remains available.'},409)

def transform(html,selection):
 """Noncached F9 served copy only. F10 stays exact F11 offline snapshot."""
 from integration.finder_report_f11 import once,head_insert
 selection.verify()
 if not selection.report_enabled:raise Refused('F11 data fallback required')
 bridge=(ROOT/'finder.js').read_text().replace('/*F12_EDITIONS*/',json.dumps(source_editions(selection),separators=(',',':')))
 html=once(html,'async function classifyRun() {','async function classifyRun() {\n  if(window.__f12Classify) { window.__f12Classify(); return; }')
 a=html.index('async function assistRun(cands) {');b=html.index('\nfunction paintResults() {',a)
 html=html[:a]+"async function assistRun(cands) { if(window.__f12Classify)window.__f12Classify(); }\n"+html[b:]
 html=once(html,'Tip: add a free Gemini or Groq key on any detail page and this box also gives AI best-code picks. Without a key it shows closest text matches.','Optional existing-proxy context explains preserved candidates after sign-in and review gates. No personal AI key is needed. Offline search still works.')
 html=once(html,'Compare verdict - which code for what','Compare preserved snapshot context')
 html=head_insert(html,'<style>#f12-status,#plain-slot,#brief-slot,#doc-slot,#cmpv-slot{overflow-wrap:anywhere}</style>')
 # Source template remains intact. Optional proxy context is a separate labeled
 # appendix, never passed as authoritative replacement for the source sections.
 html=once(html,"    secs +\n    '<div class=\"tpl-foot\">", "    secs +\n    (opts.f12Context ? '<section class=\"tpl-sec\"><h2>Optional AI snapshot context</h2><p>'+esc(opts.f12Context)+'</p><p class=\"muted\">Not verified. Supplied snapshot only. Check the source data and current official sources.</p></section>' : '') +\n    '<div class=\"tpl-foot\">")
 # Append before the real closing body, not a quoted report body in app JS.
 at=html.rfind('</body>');html=html[:at]+'<script>'+bridge+'</script>'+html[at:]
 import base64
 html=re.sub(r'<meta http-equiv="Content-Security-Policy"[^>]*>','',html,count=1)
 hashes=' '.join("'sha256-"+base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()+"'"for s in re.findall(r'<script>(.*?)</script>',html,re.S|re.I))
 return head_insert(html,'<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src '+hashes+'; style-src \'unsafe-inline\'; img-src data:; connect-src \'none\'; form-action \'none\'; base-uri \'none\'">')

def install(app,selection,origin):
 from flask import request,Response,jsonify
 from integration.finder_composition_f9 import selected
 if selected(app)is not selection:raise Refused('Same selected app required')
 selection.verify();html=transform(selection.rendered,selection)
 @app.get('/workspace/assets/finder-proxy-f12/<name>')
 def workspace_script(name):
  if request.path not in ASSETS:return Response(status=404)
  return Response((ROOT/name).read_text(),mimetype='text/css'if name.endswith('.css')else'application/javascript')
 @app.post(PATH)
 def held():return jsonify(ok=False,error='finder_proxy_feature_held',message='Existing authenticated proxy is not activated. Data-only features remain available.'),409
 @app.after_request
 def compose(response):
  if request.path=='/workspace/finder/offline.html'and response.status_code==200:
   selection.verify();response.set_data(html)
  if request.path=='/workspace/finder/live.html'and response.status_code==200:
   response.direct_passthrough=False;response.set_data(response.get_data(as_text=True).replace('title="Local trade-code Finder"','id="finder-frame" title="Local trade-code Finder"'))
  if request.path=='/workspace'and response.status_code==200:
   response.direct_passthrough=False;s=response.get_data(as_text=True)
   if s.count('</body>')!=1:raise Refused('Workspace script seam drift')
   response.set_data(s.replace('</body>','<link rel="stylesheet" href="/workspace/assets/finder-proxy-f12/panel.css"><script type="module" src="'+ASSET+'"></script></body>'))
  return response
 app.extensions['finder_proxy_f12']={'state':'held','selection':selection}

def activate(app,*,handler=None,service=None,origin=None,client_identity=None,worker_evidence=None,clock=None):
 """Unselected explicit integration point. Existing auth invariant is kept;
 no environment value can construct accounts, budgets, transport or catalog.
 """
 from integration.finder198_auth import create_finder_auth
 if 'finder_proxy_f12'not in app.extensions or type(handler)is not FeatureBroker:raise Refused('Exact reviewed feature handler required')
 if handler.evidence.selection is not app.extensions['finder_proxy_f12']['selection']:raise Refused('Exact feature evidence selection required')
 app.wsgi_app=create_finder_auth(app.wsgi_app,enabled=True,service=service,origin=origin,client_identity=client_identity,worker_evidence=worker_evidence,clock=clock,broker_handler=handler)
 # State means auth wiring, never cost/privacy/model approval or successful AI.
 app.extensions['finder_proxy_f12']['state']='authenticated_catalog_gated'
