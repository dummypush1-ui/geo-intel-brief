"""Inactive fixture HTTP wiring. No production mount, fetch or background worker.
Full run inputs are registered server-side by explicit fixture setup, never
accepted over HTTP. This process-local registry is not restart recovery.
"""
import copy,hmac,json
from flask import Flask,request,jsonify
from collector108_prep.durable_ledger import DurableLedger,LedgerRefused
from collector109_prep.drive import drive_collection,DriveRefused
from collector109_prep.checkpoint import FixtureCheckpoints,run_inputs

class FixtureService:
 def __init__(self,ledger,checkpoints,clock):
  if type(ledger)is not DurableLedger or type(checkpoints)is not FixtureCheckpoints or not callable(clock):raise ValueError('Explicit fixtures required')
  self.ledger=ledger;self.checkpoints=checkpoints;self.clock=clock;self._runs={}
 def register(self,key,fence,candidates,categories,threshold):
  bound=run_inputs(candidates,categories,threshold)
  if type(fence)is not int or fence<1:raise ValueError('Exact fence required')
  self.ledger.heartbeat(key,fence,self.clock())
  self.checkpoints.put(key,fence,bound)
  # Checkpoint enforces full identity immutability, including fence.
  self._runs[key]={'fence':fence,'inputs':copy.deepcopy(bound)}
 def drive(self,key):
  if key not in self._runs:raise DriveRefused('Server-side inputs unwired')
  run=self._runs[key];b=run['inputs']
  # Deliberately no writer/store: HTTP cannot authorize article writes.
  return drive_collection(self.ledger,key,run['fence'],candidates=b['candidates'],active_categories=b['active_categories'],threshold=b['threshold'],clock=self.clock,checkpoints=self.checkpoints)

def create_drive_fixture_app(service,secret):
 if type(service)is not FixtureService or type(secret)is not str or len(secret)<48 or any(not 33<=ord(c)<=126 for c in secret):raise ValueError('Fixture service/header secret required')
 app=Flask(__name__);app.config['MAX_CONTENT_LENGTH']=4096
 def auth():return hmac.compare_digest(request.headers.get('Authorization','').encode(),('Bearer '+secret).encode())
 def valid_key(key):return type(key)is str and len(key)==64 and all(c in '0123456789abcdef' for c in key)
 @app.post('/internal/collector109/jobs/<key>/drive')
 def drive(key):
  if not auth():return jsonify(error='unauthorized'),401
  if request.query_string or not valid_key(key) or request.mimetype!='application/json' or request.content_length is None:return jsonify(error='invalid_request'),400
  if request.content_length>4096:return jsonify(error='request_too_large'),413
  try:
   # Empty object is the only request. No remote inputs, fence or writer flags.
   pairs=json.loads(request.get_data(),object_pairs_hook=lambda p:p)
   if pairs!=[] or not request.get_data().strip().startswith(b'{'):raise ValueError()
  except Exception:return jsonify(error='invalid_request'),400
  try:out=service.drive(key)
  except (DriveRefused,LedgerRefused):return jsonify(error='drive_refused'),409
  except Exception:return jsonify(error='drive_unavailable'),503
  return jsonify(job=out['job'],state=out['state'],phase=out.get('phase')),200
 @app.get('/internal/collector109/jobs/<key>')
 def status(key):
  if not auth():return jsonify(error='unauthorized'),401
  if request.query_string or not valid_key(key):return jsonify(error='invalid_request'),400
  try:return jsonify(service.ledger.status(key)),200
  except LedgerRefused:return jsonify(error='status_unavailable'),503
 @app.errorhandler(413)
 def too_large(_):return jsonify(error='request_too_large'),413
 return app
