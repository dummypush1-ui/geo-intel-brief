"""New unselected native archive core. 199 exact types/gates remain unchanged."""
import copy,time,math,threading
from integration.replay199_core import ArchiveCore
from integration.replay199_schema import FAMILIES,source,record,manifest,canonical,digest,ishash,MAX_EPOCHS,MAX_RECORDS,LIMIT_BYTES,ReplayRefused
from integration.native200_transactions import NativeNoRetryProvider,NativeRefused
from integration.native200_store import NativeStore
from integration.native200_journal import OperationJournal
class NativeArchiveCore(ArchiveCore):
 def __init__(self,client,*,family,fingerprint=None,enabled=False,clock=time.monotonic):
  if type(enabled)is not bool or family not in FAMILIES or not callable(clock):raise NativeRefused('Exact native core selection')
  self.enabled=enabled;self.client=client;self.family=family;self.fp=fingerprint;self.clock=clock;self.uncertain=False;self.last_operation=None;self.pending_plan=None;self.lock=threading.Lock()
  if not enabled:return
  if family=='collector'and not ishash(fingerprint)or family=='broker'and fingerprint is not None:raise NativeRefused('Exact family fingerprint')
  self.provider=NativeNoRetryProvider(client,enabled=True);sn,an,_,_=FAMILIES[family];self.s=NativeStore(self.provider,sn);self.a=NativeStore(self.provider,an);self.journal=OperationJournal(self.provider,family=family)
  from integration.native200_store import NAMES
  from integration.native200_preflight import inspect_existing
  for name in sorted(NAMES):inspect_existing(NativeStore(self.provider,name))
 def _session(self,write,work):
  if not self.enabled or write and(self.uncertain or self.pending_plan is None):raise NativeRefused('Native mutation guard required')
  intent=None;p=None;start=self.clock()
  if type(start)not in(int,float)or not math.isfinite(start)or start<0:raise NativeRefused('Native exact transaction clock')
  def deadline():
   now=self.clock()
   if type(now)not in(int,float)or not math.isfinite(now)or not start<=now<start+20:raise NativeRefused('Native transaction deadline')
  try:
   if write:intent=self.journal.reserve(self.pending_plan)
   p=NativeNoRetryProvider(self.client,enabled=True);s=p.begin();p.start();out=work(s,deadline);deadline()
   if write:
    saved=self.s.find_one({'_id':FAMILIES[self.family][2]},session=s)
    if digest(saved)!=intent['plan']['after_hash']:raise NativeRefused('Native outcome source hash mismatch')
    self.journal.outcome(intent,session=s);self.journal.phase(intent,'commit_attempt');deadline()
   p.commit_once()
   if write:
    self.journal.phase(intent,'acknowledged')
    # No automatic guard release EVEN AFTER ACK. Closure is separate review.
   return out
  except BaseException:
   if write:self.uncertain=True
   if p is not None and p.started and not p.commit_attempted:
    try:p.abort_once()
    except BaseException:pass
   raise NativeRefused('Native operation held; no retry/reclaim/guard release')from None
  finally:
   if write:self.pending_plan=None
   if p is not None:p.close()
 def rollover(self,*,expected_revision,checkpoints=None):
  if not self.lock.acquire(blocking=False):raise NativeRefused('One native operation at a time')
  try:return self._rollover(expected_revision=expected_revision,checkpoints=checkpoints)
  finally:self.lock.release()
 def _rollover(self,*,expected_revision,checkpoints=None):
  if not self.enabled:raise NativeRefused('Native core disabled')
  if self.family=='collector':
   if type(checkpoints)is not NativeStore or checkpoints.name!='collector_checkpoints197'or checkpoints.database.client is not self.client:raise NativeRefused('Exact native checkpoints')
  elif checkpoints is not None:raise NativeRefused('No broker checkpoint')
  def plan_work(session,deadline):
   d,archive,workload=self.verified_view(session,deadline)
   if type(expected_revision)is not int or d['revision']!=expected_revision or d['active']is not None or d['archive_epoch']>=MAX_EPOCHS:raise NativeRefused('Exact quiescent native revision')
   rows=d['history'if self.family=='collector'else'receipts'];refs=[];total=0;epoch=d['archive_epoch']+1
   for row in rows:
    deadline()
    if len(refs)>=64 or len(archive)+len(refs)>=MAX_RECORDS:break
    cp=checkpoints.find_one({'_id':row['key']},session=session)if self.family=='collector'else None
    r=record(self.family,row,epoch=epoch,source_revision=d['revision'],fingerprint=self.fp,checkpoint=cp);candidate=refs+[{'id':r['_id'],'sha256':r['sha256']}];m=manifest(self.family,epoch,d['chain_head'],candidate);size=len(canonical(r))
    if total+size+len(canonical(m))>LIMIT_BYTES or workload+total+size+len(canonical(m))>LIMIT_BYTES:break
    refs=candidate;total+=size
   if not refs:raise NativeRefused('Native safe prefix unavailable')
   after=copy.deepcopy(d);after['history'if self.family=='collector'else'receipts']=copy.deepcopy(rows[len(refs):]);after.update(revision=d['revision']+1,archive_epoch=epoch,archived_count=d['archived_count']+len(refs),chain_head=m['sha256']);source(self.family,after,self.fp)
   return {'family':self.family,'source':FAMILIES[self.family][2],'expected_revision':d['revision'],'epoch':d['archive_epoch'],'head':d['chain_head'],'after_hash':digest(after)}
  plan=self._session(False,plan_work);self.pending_plan=plan
  # Inherited bounded archive algorithm revalidates complete snapshot/CAS and
  # planned final source hash under the SAME native transaction as outcomemarker.
  return super().rollover(expected_revision=expected_revision,checkpoints=checkpoints)
 def reconcile_pending(self):
  if not self.enabled:raise NativeRefused('Native core disabled')
  pending=self.journal.inspect_pending()
  def inspect(session,deadline):
   d,archive,_=self.verified_view(session,deadline);intent=pending.get('intent');marker=pending.get('marker');proven=False
   if type(intent)is dict and type(marker)is dict and set(intent)=={'_id','schema','guard','serial','plan'} and intent['_id']==pending['guard']['operation'] and intent['guard']==self.journal.key and intent['serial']==pending['guard']['serial']:
    expected={'_id':intent['_id'],'schema':1,'guard':self.journal.key,'serial':intent['serial'],'plan_hash':digest(intent['plan']),'after_hash':intent['plan']['after_hash']}
    same=self.journal.m.find_one({'_id':intent['_id']},session=session)
    proven=marker==expected and same==expected and digest(d)==expected['after_hash']
   return {'state':'committed_observed_guard_still_held'if proven else'not_proven_owner_review_required','retry_safe':False,'holds_cleared':False,'capacity_claim':False}
  return self._session(False,inspect)
