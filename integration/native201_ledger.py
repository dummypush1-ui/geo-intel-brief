"""New atomic native checkpoint + source transition. Old gates unchanged."""
import copy
from integration.native200_admission_adapters import AdmissionCollectorLedger
from integration.native200_admission_store import AdmissionStore
from integration.native200_transactions import NativeRefused
from integration.native201_coverage import NativeCoverageCheckpoints,checkpoint_row
from integration.replay199_adapters import _clock
from integration.replay199_schema import source,digest,FAMILIES,ishash
class NativeCheckpointCollectorLedger(AdmissionCollectorLedger):
 def checkpoint_and_advance(self,checkpoints,key,fence,now,inputs,source_coverage):
  core=self.core
  if type(checkpoints)is not NativeCoverageCheckpoints or checkpoints.c.database.client is not core.client or not ishash(key)or type(fence)is not int or fence<1:raise NativeRefused('Exact atomic checkpoint collaborators')
  _clock(now);inputs=copy.deepcopy(inputs);source_coverage=copy.deepcopy(source_coverage);row=checkpoint_row(key,fence,inputs,source_coverage)
  if not core.lock.acquire(blocking=False):raise NativeRefused('One native mutation at a time')
  try:
   def transform(session,deadline):
    before,archive,_=core.verified_view(session,deadline);after=copy.deepcopy(before);j=after['active']
    if key in archive or not j or j['key']!=key or j['fence']!=fence or j['phase']!='running'or now<j['updated_at']or now>=j['lease_until']:raise NativeRefused('Exact running source checkpoint ticket')
    saved=checkpoints.c.find_one({'_id':key},session=session)
    if saved is not None and saved!=row:raise NativeRefused('Immutable checkpoint scope mismatch')
    count=len(inputs['candidates'])
    if type(count)is not int or count>1000:raise NativeRefused('Bounded checkpoint count')
    j.update(phase='fetch_complete',counts={'fetched':count},updated_at=now,lease_until=now+120);after['revision']=before['revision']+1;source(core.family,after,core.fp);deadline()
    return before,after,copy.deepcopy(j)
   before,after,result=core._session(False,transform)
   core.pending_plan={'family':core.family,'source':FAMILIES[core.family][2],'expected_revision':before['revision'],'epoch':before['archive_epoch'],'head':before['chain_head'],'after_hash':digest(after)}
   def work(session,deadline):
    fresh,changed,out=transform(session,deadline)
    if fresh!=before or changed!=after:raise NativeRefused('Atomic checkpoint source changed')
    existing=checkpoints.c.find_one({'_id':key},session=session)
    if existing is None:checkpoints.c.insert_one(row,session=session)
    if checkpoints.c.find_one({'_id':key},session=session)!=row:raise NativeRefused('Immutable checkpoint readback held')
    query={k:fresh[k]for k in ('_id','schema','revision','archive_epoch','chain_head')}
    ack=core.s.replace_one(query,changed,upsert=False,session=session)
    if ack.acknowledged is not True or ack.matched_count!=1 or core.s.find_one({'_id':changed['_id']},session=session)!=changed:raise NativeRefused('Atomic checkpoint source CAS/readback held')
    deadline();return out
   return core._session(True,work)
  finally:core.lock.release()
