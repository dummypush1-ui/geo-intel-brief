"""New explicitly selected admission core; old native core byte-unchanged."""
import copy,time,math,threading
from integration.native200_core import NativeArchiveCore
from integration.replay199_core import ArchiveCore
from integration.native200_admission_store import AdmissionStore
from integration.native200_admission_journal import AdmissionJournal
from integration.native200_transactions import NativeNoRetryProvider,NativeRefused
from integration.replay199_schema import FAMILIES,ishash,record,manifest,canonical,digest,source,MAX_EPOCHS,MAX_RECORDS,LIMIT_BYTES
class AdmissionArchiveCore(NativeArchiveCore):
 def __init__(self,client,*,family,fingerprint=None,enabled=False,clock=time.monotonic):
  if type(enabled)is not bool or family not in FAMILIES or not callable(clock):raise NativeRefused('Exact native core selection')
  self.enabled=enabled;self.client=client;self.family=family;self.fp=fingerprint;self.clock=clock;self.uncertain=False;self.last_operation=None;self.pending_plan=None;self.lock=threading.Lock()
  if not enabled:return
  if family=='collector'and not ishash(fingerprint)or family=='broker'and fingerprint is not None:raise NativeRefused('Exact family fingerprint')
  self.provider=NativeNoRetryProvider(client,enabled=True);sn,an,_,_=FAMILIES[family];self.s=AdmissionStore(self.provider,sn);self.a=AdmissionStore(self.provider,an);self.journal=AdmissionJournal(self.provider,family=family,core=self)
  from integration.native200_store import NAMES
  from integration.native200_admission_preflight import inspect_admission_existing
  for name in sorted(NAMES):inspect_admission_existing(AdmissionStore(self.provider,name))
 def _admission_deadline(self):
  start=self.clock()
  if type(start)not in(int,float)or not math.isfinite(start)or start<0:raise NativeRefused('Exact admission clock')
  def deadline():
   now=self.clock()
   if type(now)not in(int,float)or not math.isfinite(now)or not start<=now<start+20:raise NativeRefused('Admission deadline held')
  return deadline
 def reconcile_pending(self):
  pending=self.journal.inspect_pending()
  if pending.get('state')in ('admission_attempt_held_owner_review_required','admitted_but_never_executed_owner_review_required','malformed_admission_record_held_owner_review_required'):return pending
  return super().reconcile_pending()
 def _rollover(self,*,expected_revision,checkpoints=None):
  if not self.enabled:raise NativeRefused('Native core disabled')
  if self.family=='collector':
   if type(checkpoints)is not AdmissionStore or checkpoints.name!='collector_checkpoints197'or checkpoints.database.client is not self.client:raise NativeRefused('Exact native checkpoints')
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
  return ArchiveCore.rollover(self,expected_revision=expected_revision,checkpoints=checkpoints)
