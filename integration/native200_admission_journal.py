"""New write-ahead successor admission. No idle release or restart permission."""
import copy,secrets
from integration.native200_journal import OperationJournal,MAX_OPERATIONS
from integration.native200_admission_store import AdmissionStore
from integration.native200_transactions import NativeNoRetryProvider,NativeRefused
from integration.replay199_schema import FAMILIES,digest,ishash
class AdmissionJournal(OperationJournal):
 def __init__(self,provider,*,family,core):
  self.family=family;self.provider=provider;self.core=core;self.g=AdmissionStore(provider,'native_guards200');self.o=AdmissionStore(provider,'native_operations200');self.m=AdmissionStore(provider,'native_outcomes200');self.key=family+':'+FAMILIES[family][2]
 def guard(self):
  d=self.g.find_one({'_id':self.key})
  if type(d)is not dict or set(d)!={'_id','schema','family','serial','operation','phase'}or d['_id']!=self.key or d['schema']!=1 or d['family']!=self.family or type(d['serial'])is not int or not 0<=d['serial']<=MAX_OPERATIONS or d['phase']not in ('idle','reserved','commit_attempt','acknowledged','admission_attempt')or(d['phase']=='idle')!=(d['operation']is None)or d['operation']is not None and not ishash(d['operation']):raise NativeRefused('Exact admission guard')
  return d
 def _proof(self,d,session,deadline):
  before,archive,_=self.core.verified_view(session,deadline)
  intent=self.o.find_one({'_id':d['operation']},session=session);marker=self.m.find_one({'_id':d['operation']},session=session)
  if type(intent)is not dict or set(intent)!={'_id','schema','guard','serial','plan'}or intent['_id']!=d['operation']or intent['schema']!=1 or intent['guard']!=self.key or intent['serial']!=d['serial']:raise NativeRefused('Exact previous intent required')
  plan=intent['plan']
  if type(plan)is not dict or set(plan)!={'family','source','expected_revision','epoch','head','after_hash'}or plan['family']!=self.family or plan['source']!=FAMILIES[self.family][2]or type(plan['expected_revision'])is not int or not 0<=plan['expected_revision']<2**53 or type(plan['epoch'])is not int or not 0<=plan['epoch']<=1024 or not ishash(plan['head'])or not ishash(plan['after_hash'])or before['revision']!=plan['expected_revision']+1:raise NativeRefused('Exact prior immutable plan')
  expected={'_id':intent['_id'],'schema':1,'guard':self.key,'serial':intent['serial'],'plan_hash':digest(plan),'after_hash':plan['after_hash']}
  if marker!=expected or digest(before)!=plan['after_hash']:raise NativeRefused('Previous complete outcome not proven')
  deadline();return before
 def reserve(self,plan):
  if type(plan)is not dict or set(plan)!={'family','source','expected_revision','epoch','head','after_hash'}or plan['family']!=self.family or plan['source']!=FAMILIES[self.family][2]or type(plan['expected_revision'])is not int or not 0<=plan['expected_revision']<2**53 or type(plan['epoch'])is not int or not 0<=plan['epoch']<=1024 or not ishash(plan['head'])or not ishash(plan['after_hash']):raise NativeRefused('Exact successor plan')
  old=self.guard()
  if old['phase']=='idle':return super().reserve(plan)
  if old['phase']!='acknowledged'or old['serial']>=MAX_OPERATIONS:raise NativeRefused('No admission of held phase/capacity')
  # Read-only complete-chain proof before permanent write-ahead latch.
  before=self.core._session(False,lambda s,deadline:self._proof(old,s,deadline))
  if before['revision']!=plan['expected_revision']or before['archive_epoch']!=plan['epoch']or before['chain_head']!=plan['head']:raise NativeRefused('Successor plan scope mismatch')
  latch={**old,'phase':'admission_attempt'}
  if self.g.replace_one(old,latch,upsert=False).matched_count!=1 or self.guard()!=latch:raise NativeRefused('Admission latch held')
  op=secrets.token_hex(32);new={**latch,'serial':old['serial']+1,'operation':op,'phase':'reserved'}
  intent={'_id':op,'schema':1,'guard':self.key,'serial':new['serial'],'plan':copy.deepcopy(plan)}
  closure={'_id':'admission:'+op,'kind':'admission','schema':1,'guard':self.key,'old_operation':old['operation'],'old_serial':old['serial'],'new_operation':op,'new_serial':new['serial'],'source_hash':digest(before)}
  p=NativeNoRetryProvider(self.provider.client,enabled=True)
  try:
   session=p.begin();p.start();deadline=self.core._admission_deadline()
   fresh=self._proof(latch,session,deadline)
   if fresh!=before or self.g.find_one({'_id':self.key},session=session)!=latch:raise NativeRefused('Admission snapshot changed')
   if self.g.replace_one(latch,new,upsert=False,session=session).matched_count!=1:raise NativeRefused('Admission CAS held')
   self.o.insert_one(intent,session=session);self.m.insert_one(closure,session=session)
   if self.g.find_one({'_id':self.key},session=session)!=new or self.o.find_one({'_id':op},session=session)!=intent or self.m.find_one({'_id':closure['_id']},session=session)!=closure:raise NativeRefused('Admission transaction readback held')
   deadline();p.commit_once()
   # ONLY this known same-process ACK yields an executable successor intent.
   return intent
  except BaseException:
   if p.started and not p.commit_attempted:
    try:p.abort_once()
    except BaseException:pass
   raise NativeRefused('Admission held; no restart execution permission')from None
  finally:p.close()
 def inspect_pending(self):
  d=self.guard();out={'guard':d,'retry_safe':False,'holds_cleared':False,'capacity_claim':False}
  if d['phase']=='admission_attempt':return {**out,'state':'admission_attempt_held_owner_review_required'}
  if d['phase']=='reserved':
   closure=self.m.find_one({'_id':'admission:'+d['operation']})
   if closure is not None:
    fields={'_id','kind','schema','guard','old_operation','old_serial','new_operation','new_serial','source_hash'}
    if type(closure)is not dict or set(closure)!=fields or closure['_id']!='admission:'+d['operation']or closure['kind']!='admission'or closure['schema']!=1 or closure['guard']!=self.key or closure['new_operation']!=d['operation']or closure['new_serial']!=d['serial']or type(closure['old_serial'])is not int or closure['old_serial']!=d['serial']-1 or not ishash(closure['old_operation'])or not ishash(closure['source_hash']):return {**out,'state':'malformed_admission_record_held_owner_review_required'}
    return {**out,'state':'admitted_but_never_executed_owner_review_required'}
  return {**super().inspect_pending(),**out}
