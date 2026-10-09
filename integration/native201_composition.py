"""201b explicit unselected native source helper. No production selection.
Default OFF returns public unchanged; no environment/clients/mount/activation.
"""
import hmac,json
from werkzeug.wrappers import Request,Response
from integration.native201_broker import create_native_broker_server
from integration.native201_ledger import NativeCheckpointCollectorLedger
from integration.native201_coverage import NativeCoverageCheckpoints
from integration.collector197_job_runtime import require_job_provider
from integration.native201_collector import native_collector_status
from integration.replay199_schema import ishash
class CompositionRefused(ValueError):pass

def _response(body,status):
 return Response(json.dumps(body,separators=(',',':')),status=status,mimetype='application/json',headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','X-Robots-Tag':'noindex, nofollow'})

def build_native_composition(public,*,enabled=False,ledger=None,checkpoints=None,status_secret=None,job_evidence=None,clock=None,service=None,origin=None,client_identity=None,worker_evidence=None,budget=None,transport=None):
 if type(enabled)is not bool:raise CompositionRefused('Exact source selection required')
 if not enabled:return public
 if (not callable(public)or type(ledger)is not NativeCheckpointCollectorLedger or type(checkpoints)is not NativeCoverageCheckpoints or checkpoints.c.database.client is not ledger.core.client or not callable(job_evidence)or not callable(clock)or type(status_secret)is not str or not 48<=len(status_secret)<=256 or any(ord(c)<33 or ord(c)>126 for c in status_secret)):
  raise CompositionRefused('Exact injected source collaborators required')
 # Existing auth+broker gates remain mandatory. This helper opens no client and
 # neither constructs nor replaces JobRuntimeEvidence/transaction providers.
 broker=create_native_broker_server(public,enabled=True,service=service,origin=origin,client_identity=client_identity,worker_evidence=worker_evidence,clock=clock,budget=budget,transport=transport)
 def app(environ,start_response):
  req=Request(environ)
  if not(req.path=='/api/collect'or req.path.startswith('/api/collect/')):return broker(environ,start_response)
  # Auth before key validation, archive/checkpoint access or evidence callbacks.
  supplied=req.headers.get('Authorization','')
  if len(supplied)>300 or not hmac.compare_digest(supplied.encode(),('Bearer '+status_secret).encode()):return _response({'error':'unauthorized'},401)(environ,start_response)
  if req.headers.get('Origin')is not None or req.query_string or req.content_length not in (None,0)or req.headers.get('Transfer-Encoding')is not None:return _response({'error':'invalid_request'},400)(environ,start_response)
  prefix='/api/collect/status/'
  key=req.path[len(prefix):]if req.path.startswith(prefix)else''
  if req.method!='GET'or not ishash(key):return _response({'error':'route_unavailable'},404)(environ,start_response)
  try:
   # Read-only status must not imply capacity-ready or permission to retry.
   require_job_provider(job_evidence,clock)
   out=native_collector_status(ledger,checkpoints,key)
   return _response(out,200)(environ,start_response)
  except Exception:return _response({'error':'status_unavailable'},503)(environ,start_response)
 return app
