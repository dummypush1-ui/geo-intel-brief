"""Inactive injected drive. Never replay write_started. No network/client setup.
A full immutable checkpoint is mandatory. Only the invocation which wins the
prepare_complete -> write_started CAS may call the writer, once. An interrupted
write_started job requires reconciliation, not retry. Fixture persistence does
not provide process-restart recovery; production checkpoint wiring remains OFF.
"""
import copy
from datetime import datetime,timezone
from collector108_prep.durable_ledger import DurableLedger,LedgerRefused
from integration.geo_collector_contract import prepare_geo_documents,run_geo_fixture_cycle
if __package__:
 from .checkpoint import FixtureCheckpoints,CheckpointRefused,run_inputs,digest
else:
 from checkpoint import FixtureCheckpoints,CheckpointRefused,run_inputs,digest

class DriveRefused(ValueError):pass

def _now(clock):
 n=clock()
 if type(n)is not int or n<0:raise DriveRefused('Exact integer clock required')
 return n

def _receipt(out,n):
 fields={'state','attempted','inserted_count','duplicate_count','failed_count','uncertain_count','retry_safe'}
 if type(out)is not dict or set(out)!=fields or type(out['state'])is not str or out['state']not in ('empty','inserted','duplicates','partial','uncertain') or type(out['attempted'])is not int or out['attempted']!=n or type(out['retry_safe'])is not bool:raise DriveRefused('Receipt shape')
 if out['state']=='uncertain':
  if any(out[k] is not None for k in ('inserted_count','duplicate_count','failed_count')) or type(out['uncertain_count'])is not int or out['uncertain_count']!=n or out['retry_safe']is not False:raise DriveRefused('Uncertain receipt')
  return None
 vals=[out[k] for k in ('inserted_count','duplicate_count','failed_count','uncertain_count')]
 if any(type(v)is not int or not 0<=v<=n for v in vals) or sum(vals)!=n or vals[3]!=0:raise DriveRefused('Receipt accounting')
 i,d,f,_=vals
 if (out['state']=='empty' and (n!=0 or out['retry_safe']is not True)) or (out['state']!='empty' and (n==0 or out['retry_safe']is not False)) or (out['state']=='inserted' and i!=n) or (out['state']=='duplicates' and (d==0 or f!=0)) or (out['state']=='partial' and f==0):raise DriveRefused('Receipt state mismatch')
 return {'attempted':n,'inserted':i,'duplicate':d,'failed':f,'uncertain':0}

def _uncertain(ledger,key,fence,clock,n):
 try:ledger.advance(key,fence,'uncertain_after_write',_now(clock),{'attempted':n,'uncertain':n})
 except (LedgerRefused,DriveRefused):
  # Expired lease/store outage cannot be bypassed. write_started stays locked.
  return {'state':'reconciliation_required','job':key,'phase':'write_started','network':False,'live_writes':False}
 return {'state':'uncertain_after_write','job':key,'network':False,'live_writes':False}

def drive_collection(ledger,key,fence,*,candidates,active_categories,threshold,clock,checkpoints,writer=None,store=None):
 if type(ledger)is not DurableLedger or type(key)is not str or type(fence)is not int or type(checkpoints)is not FixtureCheckpoints or (writer is not None and store is not None):raise DriveRefused('Exact fixture drive configuration required')
 job=ledger.status(key)
 if job['phase']=='write_started':
  # No mutation ever resumes here, including wrong fence and expired callers.
  raise DriveRefused('write_started requires reconciled proof; replay refused')
 if job['phase']not in ('accepted','running','fetch_complete','prepare_complete'):raise DriveRefused('Job not drivable')
 # Ownership/lease verified even before checkpoint reads/writes or preparation.
 ledger.heartbeat(key,fence,_now(clock))
 try:
  proposed=run_inputs(candidates,active_categories,threshold)
  if job['phase']=='accepted':checkpoints.put(key,fence,proposed)
  bound=checkpoints.get(key,fence)
  if digest(key,fence,bound)!=digest(key,fence,proposed):raise CheckpointRefused('Run input mismatch')
 except CheckpointRefused:raise DriveRefused('Immutable run checkpoint refused')from None
 candidates=bound['candidates'];active_categories=bound['active_categories'];threshold=bound['threshold']
 if job['phase']=='accepted':
  ledger.advance(key,fence,'running',_now(clock),{})
  job=ledger.status(key)
 if job['phase']=='running':
  ledger.advance(key,fence,'fetch_complete',_now(clock),{'fetched':len(candidates)})
  job=ledger.status(key)
 try:docs=prepare_geo_documents(candidates,active_categories,threshold)['documents']
 except Exception:
  # A preparation failure is known to precede article writes. Fail closed.
  try:ledger.advance(key,fence,'failed_before_write',_now(clock),{'fetched':len(candidates)})
  except (LedgerRefused,DriveRefused):pass
  raise DriveRefused('Prepare failed before write; inspect ledger status')from None
 counts={'fetched':len(candidates),'prepared':len(docs),'attempted':len(docs)}
 if job['phase']=='fetch_complete':
  ledger.advance(key,fence,'prepare_complete',_now(clock),{'fetched':len(candidates),'prepared':len(docs)})
  job=ledger.status(key)
 if job['phase']!='prepare_complete':raise DriveRefused('Phase changed; no writer called')
 if writer is None and store is None:return {'state':'held_before_write','job':key,'phase':'prepare_complete','network':False,'live_writes':False}
 # Atomic transition is the write ticket. A second driver cannot win it.
 ledger.advance(key,fence,'write_started',_now(clock),counts)
 try:
  write_now=_now(clock)
  ledger.heartbeat(key,fence,write_now)
  stamp=datetime.fromtimestamp(write_now,timezone.utc)
  if store is not None:
   out=run_geo_fixture_cycle(candidates,active_categories,threshold,stamp,store)
   n=len(docs)
   receipt={'state':'empty' if n==0 else 'partial' if out['failed_count'] else 'duplicates' if out['duplicate_count'] else 'inserted','attempted':n,'inserted_count':out['inserted_count'],'duplicate_count':out['duplicate_count'],'failed_count':out['failed_count'],'uncertain_count':0,'retry_safe':n==0}
  else:receipt=writer.write(copy.deepcopy(docs),stamp)
  checked=_receipt(receipt,len(docs))
  if checked is None:return _uncertain(ledger,key,fence,clock,len(docs))
 except Exception:return _uncertain(ledger,key,fence,clock,len(docs))
 counts.update(checked)
 try:ledger.advance(key,fence,'completed',_now(clock),counts)
 except (LedgerRefused,DriveRefused):return _uncertain(ledger,key,fence,clock,len(docs))
 return {'state':'completed','job':key,'counts':counts,'network':False,'live_writes':False}
