"""Additive native archive adapters. Unselected; no closure or transport wiring."""
import copy
from integration.native200_core import NativeArchiveCore
from integration.native200_transactions import NativeRefused
from integration.native200_store import NativeStore
from integration.replay199_adapters import ArchivedCollectorLedger,ArchivedProxyReceiptBudget
from integration.replay199_schema import source,digest,FAMILIES

class _NativeChange:
 def _init_native(self,core,family):
  if type(core)is not NativeArchiveCore or core.family!=family or core.enabled is not True or type(core.s)is not NativeStore:raise NativeRefused('Exact enabled native archive core')
  self.core=core
 def _change(self,mutate):
  core=self.core
  if not core.lock.acquire(blocking=False):raise NativeRefused('One native mutation at a time')
  try:
   def transform(session,deadline):
    before,archive,_=core.verified_view(session,deadline);after=copy.deepcopy(before);out=mutate(after,archive);deadline()
    if after!=before:
     after['revision']=before['revision']+1;source(core.family,after,core.fp)
    return before,after,out
   def planning(session,deadline):return transform(session,deadline)
   before,after,out=core._session(False,planning)
   # Replay/status-only paths never reserve a journal or mutate the source.
   if after==before:return out
   core.pending_plan={'family':core.family,'source':FAMILIES[core.family][2],'expected_revision':before['revision'],'epoch':before['archive_epoch'],'head':before['chain_head'],'after_hash':digest(after)}
   def work(session,deadline):
    fresh,changed,result=transform(session,deadline)
    if fresh!=before or changed!=after:raise NativeRefused('Native mutation snapshot changed; hold, no retry')
    query={k:fresh[k]for k in ('_id','schema','revision','archive_epoch','chain_head')}
    ack=core.s.replace_one(query,changed,upsert=False,session=session)
    if ack.acknowledged is not True or ack.matched_count!=1:raise NativeRefused('Native source CAS held')
    if core.s.find_one({'_id':changed['_id']},session=session)!=changed:raise NativeRefused('Native source readback held')
    return result
   return core._session(True,work)
  finally:core.lock.release()

class NativeArchivedCollectorLedger(_NativeChange,ArchivedCollectorLedger):
 def __init__(self,core):self._init_native(core,'collector');self.profile='geo108';self.fp=core.fp

class NativeArchivedProxyReceiptBudget(_NativeChange,ArchivedProxyReceiptBudget):
 def __init__(self,core):self._init_native(core,'broker')
