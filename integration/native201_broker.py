"""201b unselected admission-native broker composition, default OFF.
No production entry/runtime/env/client/activation change.
"""
import json,hashlib
from integration.native200_admission_adapters import AdmissionProxyReceiptBudget
from integration.finder198_transport import FixedProxyTransport,TransportRefused,_plan
from integration.finder198_connector import MAX_REQUEST_BYTES

def proxy_request_native(budget,transport,*,nonce,operation,provider=None,model=None,port=None,body=b'',principal_hash=None,clock):
 if type(budget)is not AdmissionProxyReceiptBudget or type(transport)is not FixedProxyTransport or not callable(clock):raise TransportRefused('Exact archive-aware broker adapters required')
 if not transport.enabled:raise TransportRefused('Transport disabled')
 if type(principal_hash)is not str or len(principal_hash)!=64 or any(c not in '0123456789abcdef'for c in principal_hash):raise TransportRefused('Authenticated principal scope required')
 if type(body)is not bytes or len(body)>MAX_REQUEST_BYTES:raise TransportRefused('Bounded request bytes required')
 plan=_plan(operation,provider,model,port,clock())
 if operation=='ships'and body:raise TransportRefused('No ships body')
 if operation=='ai':json.loads(body)
 identity=hashlib.sha256(json.dumps({'principal_hash':principal_hash,'operation':operation,'provider':provider,'model':model,'port':port},sort_keys=True,separators=(',',':')).encode()).hexdigest()
 # Both current v2 and new v3 claim use {state,receipt}; never v1 reserve shape.
 claim=budget.claim(nonce,hashlib.sha256(body).hexdigest(),identity,clock())
 if claim['state']=='replay_status_only':return claim
 if claim['state']!='claimed':raise TransportRefused('Unverified claim')
 # No transport unless claim and send-start transaction ACKs both returned.
 ticket=budget.start(claim['receipt'],clock())
 try:
  out=transport.execute(plan,body)
  receipt=budget.finish(ticket,clock(),status=out['status'],response_hash=hashlib.sha256(out['body']).hexdigest(),response_bytes=len(out['body']))
  if receipt['phase']!='complete':raise TransportRefused('Late proxy outcome held')
  return {'state':'complete','status':out['status'],'body':out['body']}
 except Exception:
  try:budget.hold(ticket,clock())
  except Exception:pass
  raise TransportRefused('Proxy request held; no automatic retry')from None

from werkzeug.wrappers import Response
from integration.broker_json211 import parse,BodyRefused
from integration.finder198_auth import create_finder_auth
class ServerRefused(ValueError):pass

def _response(data,status=200):
 return Response(json.dumps(data,separators=(',',':')),status=status,mimetype='application/json',headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','X-Robots-Tag':'noindex, nofollow'})

class NativeBrokerHandler:
 def __init__(self,budget,transport,clock):
  if type(budget)is not AdmissionProxyReceiptBudget or type(transport)is not FixedProxyTransport or transport.enabled is not True or not callable(clock):raise ServerRefused('Exact enabled injected broker collaborators required')
  self.budget=budget;self.transport=transport;self.clock=clock
 def __call__(self,req,principal_hash):
  if req.method!='POST'or req.path not in ('/api/finder-broker/ships','/api/finder-broker/ai'):return _response({'ok':False,'error':'not_found'},404)
  try:
   d=parse(req,'ships'if req.path.endswith('/ships')else'ai')
  except BodyRefused as error:return _response({'ok':False,'error':error.error},error.status)
  except Exception:return _response({'ok':False,'error':'broker_unavailable'},503)
  try:
   if req.path.endswith('/ships'):
    out=proxy_request_native(self.budget,self.transport,nonce=d['nonce'],operation='ships',port=d['port'],principal_hash=principal_hash,clock=self.clock)
   else:
    # Narrow generic prompt interface; provider adapter schemas selected by us,
    # never caller-supplied messages/tools/URLs/headers/arbitraryproviderpayload.
    if d['provider']=='gemini':payload={'contents':[{'role':'user','parts':[{'text':d['prompt']}]}],'generationConfig':{'temperature':0.2,'maxOutputTokens':2048}}
    elif d['provider']in ('groq','mistral'):payload={'model':d['model'],'messages':[{'role':'user','content':d['prompt']}],'temperature':0.2,'max_tokens':2048}
    else:raise ValueError()
    body=json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode('utf-8')
    out=proxy_request_native(self.budget,self.transport,nonce=d['nonce'],operation='ai',provider=d['provider'],model=d['model'],body=body,principal_hash=principal_hash,clock=self.clock)
  except (ValueError,UnicodeError,RecursionError):return _response({'ok':False,'error':'broker_request_held'},409)
  except Exception:return _response({'ok':False,'error':'broker_unavailable'},503)
  if out['state']=='replay_status_only':
   r=out['receipt']
   # Never disclose receipt hashes/fence/nonce/principal/otherinternalmetadata.
   return _response({'ok':False,'state':'replay_status_only','phase':r['phase'],'status':r['status'],'response_bytes':r['response_bytes'],'cached_answer':False},409)
  if out['state']!='complete':return _response({'ok':False,'error':'broker_request_held'},409)
  return Response(out['body'],status=out['status'],mimetype='application/json',headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','X-Robots-Tag':'noindex, nofollow'})

def create_native_broker_server(public,*,enabled=False,service=None,origin=None,client_identity=None,worker_evidence=None,clock=None,budget=None,transport=None):
 if type(enabled)is not bool:raise ServerRefused('Exact broker selection required')
 if not enabled:return create_finder_auth(public)
 handler=NativeBrokerHandler(budget,transport,clock)
 return create_finder_auth(public,enabled=True,service=service,origin=origin,client_identity=client_identity,worker_evidence=worker_evidence,clock=clock,broker_handler=handler)
