"""Unselected read-only v2 budget snapshot and classification. Never settles.
No DB client, active clears, refund, retry, pruning, migration or HTTP route.
"""
import copy,json,hashlib
from integration.finder198_receipts import ProxyReceiptBudget,_v2
from integration.finder198_budget import ID
from integration.collector197_archive import _bounded
class OpsRefused(ValueError):pass
SCHEMA='finder198-v2-retained-receipts-snapshot-v1'
MAX_BYTES=128*1024

def _raw(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8')
def pack(document):
 try:
  _bounded(document);_v2(document)
  body={'schema':SCHEMA,'scope':'all_retained_receipts_not_lifetime_history','budget':document}
  data=_raw({'body':body,'sha256':hashlib.sha256(_raw(body)).hexdigest()})
  if len(data)>MAX_BYTES:raise ValueError()
  unpack(data);return data
 except Exception:raise OpsRefused('Complete receipts snapshot refused; no state released')from None

def unpack(data):
 try:
  if type(data)is not bytes or not 0<len(data)<=MAX_BYTES:raise ValueError()
  def pairs(items):
   out={}
   for k,v in items:
    if k in out:raise ValueError()
    out[k]=v
   return out
  e=json.loads(data,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError()))
  if type(e)is not dict or set(e)!={'body','sha256'}or type(e['sha256'])is not str:raise ValueError()
  b=e['body'];_bounded(b)
  if type(b)is not dict or set(b)!={'schema','scope','budget'}or b['schema']!=SCHEMA or b['scope']!='all_retained_receipts_not_lifetime_history' or hashlib.sha256(_raw(b)).hexdigest()!=e['sha256']:raise ValueError()
  _v2(b['budget']);return copy.deepcopy(b)
 except Exception:raise OpsRefused('Receipts readback refused')from None

def capture(budget):
 try:
  if type(budget)is not ProxyReceiptBudget:raise ValueError()
  # Constructor already validates source mapping/concerns. Recheck read state;
  # observation is not owner permission or proof no other process is running.
  c=budget.c;w=c.write_concern.document;r=c.read_concern.document
  if c.name!='finder_budget198'or c.database.name!='geo_intel'or w.get('w')!='majority'or w.get('j')is not True or type(w.get('wtimeout'))is not int or not 1<=w['wtimeout']<=5000 or r.get('level')!='majority':raise ValueError()
  before=c.find_one({'_id':ID},max_time_ms=2000);data=pack(before)
  after=c.find_one({'_id':ID},max_time_ms=2000);_bounded(after);_v2(after)
  if before!=after:raise ValueError()
  return data
 except Exception:raise OpsRefused('Read-only receipts snapshot unavailable; no mutation/retry')from None

def classify(data,nonce_hash):
 body=unpack(data);d=body['budget']
 if type(nonce_hash)is not str or len(nonce_hash)!=64 or any(x not in '0123456789abcdef'for x in nonce_hash):raise OpsRefused('Exact retained nonce hash required')
 for r in d['receipts']:
  if r['nonce_hash']!=nonce_hash:continue
  labels={'reserved':'reserved_no_recorded_send_not_proof_unsent','send_started':'send_started_outcome_unverified','unknown_held':'unknown_outcome_owner_review_required','complete':'recorded_response_not_delivery_or_attempt_count_proof'}
  return {'nonce_hash':nonce_hash,'fence':r['fence'],'phase':r['phase'],'classification':labels[r['phase']],'status':r['status'],'response_bytes':r['response_bytes'],'response_hash':r['response_hash'],'answer_available':False,'retry_safe':False,'refund':False,'active_cleared':False,'capacity_released':False,'snapshot_only':True}
 raise OpsRefused('Nonce not retained; not proof of no earlier request')
