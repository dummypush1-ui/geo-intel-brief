"""INACTIVE factory; never imported by live entrypoint. Submission only.
No worker/fetch/write wiring yet. Fixture/local review usage only.
"""
import hmac,json,time
from flask import Flask,request,jsonify
if __package__:
 from .durable_ledger import LedgerRefused
else:
 from durable_ledger import LedgerRefused

def create_fixture_app(ledger,secret,clock):
 if type(secret)is not str or len(secret)<48 or any(ord(c)<33 or ord(c)>126 for c in secret):raise ValueError('Header secret required')
 app=Flask(__name__);app.config['MAX_CONTENT_LENGTH']=4096
 @app.get('/health')
 def health():return jsonify(component='collector108_inactive_submission',collection=False,writes=False,mail=False),200
 @app.post('/internal/collector108/jobs')
 def submit():
  # Authenticate before JSON parsing or any ledger access.
  supplied=request.headers.get('Authorization','')
  if not hmac.compare_digest(supplied.encode(),('Bearer '+secret).encode()):return jsonify(error='unauthorized'),401
  if request.content_length is not None and request.content_length>4096:return jsonify(error='request_too_large'),413
  if request.query_string or request.mimetype!='application/json' or request.content_length is None:return jsonify(error='invalid_request'),400
  try:
   def object_pairs(pairs):
    d={}
    for k,v in pairs:
     if k in d:raise ValueError()
     d[k]=v
    return d
   b=json.loads(request.get_data(),object_pairs_hook=object_pairs)
   now=clock()
   if type(b)is not dict or set(b)!={'profile','nonce','created_at'} or b['profile']!='geo108' or type(b['created_at'])is not int or type(now)is not int or abs(now-b['created_at'])>300:raise ValueError()
   out=ledger.submit(b['nonce'],now)
  except LedgerRefused:return jsonify(error='ledger_refused'),409
  except Exception:return jsonify(error='invalid_request'),400
  return jsonify(job=out['key'],phase=out['phase'],counts=out['counts']),202
 @app.errorhandler(413)
 def too_big(_):return jsonify(error='request_too_large'),413
 @app.get('/internal/collector108/jobs/<key>')
 def status(key):
  supplied=request.headers.get('Authorization','')
  if not hmac.compare_digest(supplied.encode(),('Bearer '+secret).encode()):return jsonify(error='unauthorized'),401
  if request.query_string:return jsonify(error='invalid_request'),400
  try:return jsonify(ledger.status(key)),200
  except LedgerRefused:return jsonify(error='status_unavailable'),503
 return app
