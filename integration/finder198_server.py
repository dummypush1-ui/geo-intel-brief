"""Default-OFF unselected authenticated broker HTTP composition. No client/UI.
Exact injected AccountService/budget/transport/evidence only; no live provider.
"""
import json
from werkzeug.wrappers import Response
from integration.broker_json211 import parse,BodyRefused
from integration.finder198_auth import create_finder_auth
from integration.finder198_receipts import ProxyReceiptBudget
from integration.finder198_transport import FixedProxyTransport,proxy_request
class ServerRefused(ValueError):pass

def _response(data,status=200):
 return Response(json.dumps(data,separators=(',',':')),status=status,mimetype='application/json',headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','X-Robots-Tag':'noindex, nofollow'})

class BrokerHandler:
 def __init__(self,budget,transport,clock):
  if type(budget)is not ProxyReceiptBudget or type(transport)is not FixedProxyTransport or transport.enabled is not True or not callable(clock):raise ServerRefused('Exact enabled injected broker collaborators required')
  self.budget=budget;self.transport=transport;self.clock=clock
 def __call__(self,req,principal_hash):
  if req.method!='POST'or req.path not in ('/api/finder-broker/ships','/api/finder-broker/ai'):return _response({'ok':False,'error':'not_found'},404)
  try:
   d=parse(req,'ships'if req.path.endswith('/ships')else'ai')
  except BodyRefused as error:return _response({'ok':False,'error':error.error},error.status)
  except Exception:return _response({'ok':False,'error':'broker_unavailable'},503)
  try:
   if req.path.endswith('/ships'):
    out=proxy_request(self.budget,self.transport,nonce=d['nonce'],operation='ships',port=d['port'],principal_hash=principal_hash,clock=self.clock)
   else:
    # Narrow generic prompt interface; provider adapter schemas selected by us,
    # never caller-supplied messages/tools/URLs/headers/arbitraryproviderpayload.
    if d['provider']=='gemini':payload={'contents':[{'role':'user','parts':[{'text':d['prompt']}]}],'generationConfig':{'temperature':0.2,'maxOutputTokens':2048}}
    elif d['provider']in ('groq','mistral'):payload={'model':d['model'],'messages':[{'role':'user','content':d['prompt']}],'temperature':0.2,'max_tokens':2048}
    else:raise ValueError()
    body=json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode('utf-8')
    out=proxy_request(self.budget,self.transport,nonce=d['nonce'],operation='ai',provider=d['provider'],model=d['model'],body=body,principal_hash=principal_hash,clock=self.clock)
  except (ValueError,UnicodeError,RecursionError):return _response({'ok':False,'error':'broker_request_held'},409)
  except Exception:return _response({'ok':False,'error':'broker_unavailable'},503)
  if out['state']=='replay_status_only':
   r=out['receipt']
   # Never disclose receipt hashes/fence/nonce/principal/otherinternalmetadata.
   return _response({'ok':False,'state':'replay_status_only','phase':r['phase'],'status':r['status'],'response_bytes':r['response_bytes'],'cached_answer':False},409)
  if out['state']!='complete':return _response({'ok':False,'error':'broker_request_held'},409)
  return Response(out['body'],status=out['status'],mimetype='application/json',headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','X-Robots-Tag':'noindex, nofollow'})

def create_broker_server(public,*,enabled=False,service=None,origin=None,client_identity=None,worker_evidence=None,clock=None,budget=None,transport=None):
 if type(enabled)is not bool:raise ServerRefused('Exact broker selection required')
 if not enabled:return create_finder_auth(public)
 handler=BrokerHandler(budget,transport,clock)
 return create_finder_auth(public,enabled=True,service=service,origin=origin,client_identity=client_identity,worker_evidence=worker_evidence,clock=clock,broker_handler=handler)
