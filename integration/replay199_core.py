"""Unselected explicit-session archive core. Exactly one commit attempt.
No with_transaction callback/commit retry, no clients/env/migration/HTTP routes.
New submit/claim/status adapters must use this same transaction view in 199b.
"""
import copy,time,math
from integration.replay199_transactions import NoRetryTransactionProvider
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern
from pymongo.read_preferences import ReadPreference
from integration.replay199_schema import (ReplayRefused,FAMILIES,LIMIT_BYTES,MAX_EPOCHS,MAX_RECORDS,source,manifest,validate_manifest,record,validate_record,bounded,canonical,ishash)

class ArchiveCore:
 def __init__(self,client,source_collection,archive_collection,*,family,fingerprint=None,enabled=False,clock=time.monotonic,transaction_provider=None):
  if type(enabled)is not bool or family not in FAMILIES or not callable(clock):raise ReplayRefused('Exact archive core selection')
  self.enabled=enabled;self.client=client;self.s=source_collection;self.a=archive_collection;self.family=family;self.fp=fingerprint;self.clock=clock;self.uncertain=False;self.last_operation=None;self.provider=transaction_provider
  if not enabled:return
  if type(transaction_provider)is not NoRetryTransactionProvider or transaction_provider.client is not client or transaction_provider.synthetic_only is not True:raise ReplayRefused('Exact synthetic-only no-retry provider required; native unavailable')
  sn,an,_,_=FAMILIES[family]
  if family=='collector'and not ishash(fingerprint)or family=='broker'and fingerprint is not None:raise ReplayRefused('Exact family fingerprint')
  for c,name in ((self.s,sn),(self.a,an)):
   if c.name!=name or c.database.name!='geo_intel'or c.database.client is not client:raise ReplayRefused('Fixed same-client mappings')
   w=c.write_concern.document;r=c.read_concern.document
   if w.get('w')!='majority'or w.get('j')is not True or type(w.get('wtimeout'))is not int or not 1<=w['wtimeout']<=5000 or r.get('level')!='majority':raise ReplayRefused('Fixed durable concerns')
 def _session(self,write,work):
  if not self.enabled:raise ReplayRefused('Archive core disabled')
  if write and self.uncertain:raise ReplayRefused('Prior write uncertain; no new operation')
  session=None;started=False;commit_started=False;start=self.clock()
  if type(start)not in (int,float)or not math.isfinite(start)or start<0:raise ReplayRefused('Exact bounded transaction clock')
  def deadline():
   now=self.clock()
   if type(now)not in (int,float)or not math.isfinite(now)or not start<=now<start+20:raise ReplayRefused('Archive transaction workload deadline')
  try:
   session=self.provider.begin()
   session.start_transaction(read_concern=ReadConcern('snapshot'),write_concern=WriteConcern(w='majority',j=True,wtimeout=5000),read_preference=ReadPreference.PRIMARY,max_commit_time_ms=5000);started=True
   result=work(session,deadline);deadline();commit_started=True;session.commit_transaction()
   return result
  except Exception:
   if write:self.uncertain=True
   # Commit acknowledgement is uncertain: do not retry or abort after commit
   # began. Read-only reconciliation on the exact operation is separate.
   if session is not None and started and not commit_started:
    try:session.abort_transaction()
    except Exception:pass
   raise ReplayRefused('Archive operation uncertain/held; no automatic transaction or commit retry')from None
  finally:
   if session is not None:
    try:session.end_session()
    except Exception:pass
 def _state(self,session):
  d=self.s.find_one({'_id':FAMILIES[self.family][2]},session=session,max_time_ms=2000)
  return source(self.family,d,self.fp)
 def verified_view(self,session,deadline):
  """199b uses this inside the same session BEFORE any new nonce mutation.
  No absence from a lone per-key find is trusted. Validate the whole boundedchain.
  """
  d=self._state(session);previous='0'*64;all_records={};total=0;last_fence=0
  for epoch in range(d['archive_epoch']+1):
   deadline();m=self.a.find_one({'_id':'batch:'+str(epoch)},session=session,max_time_ms=2000);validate_manifest(self.family,m)
   if m['epoch']!=epoch or m['previous']!=previous:raise ReplayRefused('Archive chain broken')
   total+=len(canonical(m));previous=m['sha256']
   for ref in m['records']:
    deadline()
    if ref['id']in all_records or len(all_records)>=MAX_RECORDS:raise ReplayRefused('Archive identity/workload cap')
    r=self.a.find_one({'_id':ref['id']},session=session,max_time_ms=2000);validate_record(r)
    if r['family']!=self.family or r['epoch']!=epoch or r['sha256']!=ref['sha256']or self.family=='collector'and r['fingerprint']!=self.fp:raise ReplayRefused('Archive record chain mismatch')
    if r['row']['fence']<=last_fence or r['source_revision']>=d['revision']:raise ReplayRefused('Archive chronology/revision inconsistent')
    last_fence=r['row']['fence']
    total+=len(canonical(r))
    if total>LIMIT_BYTES:raise ReplayRefused('Archive completeness byte cap reached')
    all_records[ref['id']]=r
   if total>LIMIT_BYTES:raise ReplayRefused('Archive completeness byte cap reached')
  if previous!=d['chain_head']or len(all_records)!=d['archived_count']:raise ReplayRefused('Archive completeness mismatch')
  # Current source and immutable archive must never share identity or fence.
  rows=([d['active']]if d['active']is not None else[])+d['history']if self.family=='collector'else d['receipts']
  archived_fences={r['row']['fence']for r in all_records.values()}
  if len(archived_fences)!=len(all_records)or any(r['row']['fence']>d['fence']for r in all_records.values()):raise ReplayRefused('Archive fences inconsistent')
  for row in rows:
   key=row['key']if self.family=='collector'else row['nonce_hash']
   if key in all_records or row['fence']in archived_fences or row['fence']<=last_fence:raise ReplayRefused('Archive/source identity collision')
  return d,all_records,total
 def lookup(self,key,*,body_hash=None,identity_hash=None):
  if not ishash(key):raise ReplayRefused('Exact replay identity')
  if self.family=='broker'and(not ishash(body_hash)or not ishash(identity_hash)):raise ReplayRefused('Exact broker request scope')
  def work(session,deadline):
   d,archive,_=self.verified_view(session,deadline)
   rows=([d['active']]if d['active']is not None else[])+d['history']if self.family=='collector'else d['receipts']
   found=next((r for r in rows if r['key'if self.family=='collector'else'nonce_hash']==key),None)
   archived=key in archive
   if found is None and archived:found=archive[key]['row']
   if found is None:return {'state':'verified_absent','source_revision':d['revision'],'archive_epoch':d['archive_epoch'],'capacity_released':False}
   if self.family=='broker'and(found['body_hash']!=body_hash or found['identity_hash']!=identity_hash):raise ReplayRefused('Nonce scope mismatch; no status disclosure')
   return {'state':'status_only','archived':archived,'row':copy.deepcopy(found),'capacity_released':False}
  return self._session(False,work)
 def rollover(self,*,expected_revision,checkpoints=None):
  if type(expected_revision)is not int or expected_revision<0:raise ReplayRefused('Exact source revision')
  if self.family=='collector':
   if checkpoints is None or checkpoints.name!='collector_checkpoints197'or checkpoints.database.name!='geo_intel'or checkpoints.database.client is not self.client:raise ReplayRefused('Fixed immutable checkpoint mapping')
   w=checkpoints.write_concern.document;r=checkpoints.read_concern.document
   if w.get('w')!='majority'or w.get('j')is not True or type(w.get('wtimeout'))is not int or not 1<=w['wtimeout']<=5000 or r.get('level')!='majority':raise ReplayRefused('Durable checkpoint concerns')
  elif checkpoints is not None:raise ReplayRefused('No broker checkpoint')
  def work(session,deadline):
   d,archived,workload=self.verified_view(session,deadline)
   if d['revision']!=expected_revision or d['active']is not None or d['archive_epoch']>=MAX_EPOCHS:raise ReplayRefused('Exact quiescent source revision required')
   rows=d['history']if self.family=='collector'else d['receipts'];selected=[];refs=[];bytes_used=0;epoch=d['archive_epoch']+1
   for row in rows:
    deadline()
    if len(selected)>=64:break
    if len(archived)+len(selected)>=MAX_RECORDS:break
    cp=checkpoints.find_one({'_id':row['key']},session=session,max_time_ms=2000)if self.family=='collector'else None
    r=record(self.family,row,epoch=epoch,source_revision=d['revision'],fingerprint=self.fp,checkpoint=cp);size=len(canonical(r))
    candidate_refs=refs+[{'id':r['_id'],'sha256':r['sha256']}];m=manifest(self.family,epoch,d['chain_head'],candidate_refs)
    if bytes_used+size+len(canonical(m))>LIMIT_BYTES or workload+bytes_used+size+len(canonical(m))>LIMIT_BYTES:break
    selected.append(r);refs=candidate_refs;bytes_used+=size
   if not selected:raise ReplayRefused('No safe archive prefix within workload cap')
   m=manifest(self.family,epoch,d['chain_head'],refs)
   # All immutable inserts and serialized readbacks remain inside one txn.
   for r in selected+[m]:
    deadline();ack=self.a.insert_one(r,session=session)
    if ack.acknowledged is not True:raise ReplayRefused('Archive insert uncertain')
    saved=self.a.find_one({'_id':r['_id']},session=session,max_time_ms=2000)
    if saved!=r:raise ReplayRefused('Archive full readback mismatch')
    (validate_manifest(self.family,saved)if r['kind']=='manifest'else validate_record(saved))
   after=copy.deepcopy(d);after['history'if self.family=='collector'else'receipts']=copy.deepcopy(rows[len(selected):]);after.update(revision=d['revision']+1,archive_epoch=epoch,archived_count=d['archived_count']+len(selected),chain_head=m['sha256']);source(self.family,after,self.fp)
   self.last_operation={'family':self.family,'epoch':epoch,'expected_revision':d['revision'],'source_revision':after['revision'],'previous_head':d['chain_head'],'chain_head':m['sha256'],'ids':[r['_id']for r in selected]}
   query={'_id':d['_id'],'schema':d['schema'],'revision':d['revision'],'archive_epoch':d['archive_epoch'],'chain_head':d['chain_head']}
   ack=self.s.replace_one(query,after,upsert=False,session=session)
   if ack.acknowledged is not True or ack.matched_count!=1:raise ReplayRefused('Archive source CAS uncertain/conflicted')
   if self.s.find_one({'_id':d['_id']},session=session,max_time_ms=2000)!=after:raise ReplayRefused('Source readback mismatch')
   return {'state':'rollover_committed','epoch':epoch,'records':len(selected),'source_revision':after['revision'],'chain_head':m['sha256'],'runtime_wired':False,'cadence_ready':False}
  return self._session(True,work)

 def reconcile(self,operation):
  """Exact read-only status of supplied operation; never clears local or durable
  holds, retries a commit, or converts unknown to complete transport response.
  Caller must retain exact operation metadata after errors. Recreated clients
  do not turn this observation into permission to run the operation again.
  """
  if type(operation)is not dict or set(operation)!={'family','epoch','expected_revision','source_revision','previous_head','chain_head','ids'}or operation['family']!=self.family or any(type(operation[k])is not int for k in ('epoch','expected_revision','source_revision'))or not 1<=operation['epoch']<=MAX_EPOCHS or not 0<=operation['expected_revision']<2**53 or operation['source_revision']!=operation['expected_revision']+1 or not ishash(operation['previous_head'])or not ishash(operation['chain_head'])or type(operation['ids'])is not list or not 1<=len(operation['ids'])<=64 or any(not ishash(k)for k in operation['ids'])or len(set(operation['ids']))!=len(operation['ids']):raise ReplayRefused('Exact operation identity required')
  op=copy.deepcopy(operation)
  def work(session,deadline):
   d,archive,_=self.verified_view(session,deadline)
   if d['archive_epoch']>=op['epoch']:
    m=self.a.find_one({'_id':'batch:'+str(op['epoch'])},session=session,max_time_ms=2000);validate_manifest(self.family,m)
    if m['sha256']!=op['chain_head']or m['previous']!=op['previous_head']or [r['id']for r in m['records']]!=op['ids']:raise ReplayRefused('Committed operation identity mismatch')
    if any(archive[k]['source_revision']!=op['expected_revision']for k in op['ids']):raise ReplayRefused('Committed source revision mismatch')
    state='verified_committed_archive_only'
   elif d['archive_epoch']==op['epoch']-1 and d['revision']==op['expected_revision']and d['chain_head']==op['previous_head']:
    state='not_visible_in_snapshot_not_retry_permission'
   else:state='unknown_owner_review_required'
   return {'state':state,'operation':op,'retry_safe':False,'holds_cleared':False,'capacity_claim':False}
  return self._session(False,work)
