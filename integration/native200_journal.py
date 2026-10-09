"""Durable source guard before every native mutation; no leases/reclaim/TTL."""
import copy,secrets
from integration.native200_store import NativeStore
from integration.native200_transactions import NativeRefused
from integration.replay199_schema import FAMILIES,ishash,digest
MAX_OPERATIONS=4096
class OperationJournal:
 def __init__(self,provider,*,family):
  if family not in FAMILIES:raise NativeRefused('Exact journal family')
  self.family=family;self.provider=provider;self.g=NativeStore(provider,'native_guards200');self.o=NativeStore(provider,'native_operations200');self.m=NativeStore(provider,'native_outcomes200');self.key=family+':'+FAMILIES[family][2]
 def guard(self):
  d=self.g.find_one({'_id':self.key})
  if type(d)is not dict or set(d)!={'_id','schema','family','serial','operation','phase'}or d['_id']!=self.key or d['schema']!=1 or d['family']!=self.family or type(d['serial'])is not int or not 0<=d['serial']<=MAX_OPERATIONS or d['phase']not in ('idle','reserved','commit_attempt','acknowledged')or(d['phase']=='idle')!=(d['operation']is None)or d['operation']is not None and not ishash(d['operation']):raise NativeRefused('Preprovisioned exact guard required')
  return d
 def reserve(self,plan):
  # Fixed source-only metadata, no URI/secret/request body or caller-generated ID.
  if type(plan)is not dict or set(plan)!={'family','source','expected_revision','epoch','head','after_hash'}or plan['family']!=self.family or plan['source']!=FAMILIES[self.family][2]or type(plan['expected_revision'])is not int or not 0<=plan['expected_revision']<2**53 or type(plan['epoch'])is not int or not 0<=plan['epoch']<=1024 or not ishash(plan['head'])or not ishash(plan['after_hash']):raise NativeRefused('Exact immutable operation metadata')
  before=self.guard()
  if before['operation']is not None or before['serial']>=MAX_OPERATIONS:raise NativeRefused('Outstanding/capacity guard held; no reclaim')
  op=secrets.token_hex(32);after={**before,'serial':before['serial']+1,'operation':op,'phase':'reserved'}
  ack=self.g.replace_one(before,after,upsert=False)
  if ack.matched_count!=1 or self.guard()!=after:raise NativeRefused('Guard reservation held')
  intent={'_id':op,'schema':1,'guard':self.key,'serial':after['serial'],'plan':copy.deepcopy(plan)}
  self.o.insert_one(intent)
  if self.o.find_one({'_id':op})!=intent:raise NativeRefused('Intent readback held')
  return intent
 def phase(self,intent,name):
  if name not in ('commit_attempt','acknowledged'):raise NativeRefused('Exact journal phase')
  d=self.guard();expected='reserved'if name=='commit_attempt'else'commit_attempt'
  if d['operation']!=intent['_id']or d['serial']!=intent['serial']or d['phase']!=expected:raise NativeRefused('Exact outstanding journal phase')
  after={**d,'phase':name}
  if self.g.replace_one(d,after,upsert=False).matched_count!=1 or self.guard()!=after:raise NativeRefused('Journal phase held')
 def outcome(self,intent,*,session):
  marker={'_id':intent['_id'],'schema':1,'guard':self.key,'serial':intent['serial'],'plan_hash':digest(intent['plan']),'after_hash':intent['plan']['after_hash']}
  self.m.insert_one(marker,session=session)
  if self.m.find_one({'_id':marker['_id']},session=session)!=marker:raise NativeRefused('Outcome marker held')
  return marker
 def inspect_pending(self):
  d=self.guard();op=d['operation']
  if op is None:return {'state':'idle_observed','retry_safe':False,'holds_cleared':False}
  # Missing intent after reservation is a durable hold, never absence permission.
  intent=self.o.find_one({'_id':op});marker=self.m.find_one({'_id':op})
  return {'state':'outstanding_owner_review_required','guard':d,'intent':intent,'marker':marker,'retry_safe':False,'holds_cleared':False}
