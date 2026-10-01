"""Offline Apps Script receipt contract. No mail sender or live routes."""
from dataclasses import dataclass
from copy import deepcopy
from contextlib import contextmanager
from hashlib import sha256
from threading import RLock
import json
from integration.project_reports import original_ids
PROJECTS=('finder','geo','brics')
@dataclass(frozen=True)
class MailSettings:
 path:str='apps_script'
 enabled:bool=False
 @classmethod
 def from_env(cls,e):
  if e.get('MERGED_MAIL_PATH','apps_script')!='apps_script':raise ValueError('Apps Script only')
  return cls(enabled=e.get('MERGED_MAIL_ENABLED','false').lower()=='true')

class FixtureLedger:
 """Thread-safe fixture ledger, NOT durable. Never use in a live sender.

A production ledger must persist content/hash/send identity/status/project claims
atomically, with cross-process locking and crash-safe idempotency keys.
"""
 def __init__(self):self.rows={};self.lock=RLock()
 @contextmanager
 def transaction(self):
  with self.lock:yield
 def get(self,k):return deepcopy(self.rows.get(k))
 def put(self,k,v):self.rows[k]=deepcopy(v)

class ReceiptBridge:
 def __init__(self,ledger,markers,verify_send):
  if set(markers)!=set(PROJECTS):raise ValueError('Three project markers required')
  self.ledger=ledger;self.markers=markers;self.verify_send=verify_send
 def prepare(self,receipt_id,payload):
  # payload comes from combined_reports: original builder HTML, not generic rows.
  if not isinstance(receipt_id,str) or not receipt_id:raise ValueError('Receipt required')
  if not isinstance(payload,dict) or set(payload.get('project_ids',{}))!=set(PROJECTS) or not isinstance(payload.get('html'),str) or payload.get('delivery_path')!='apps_script':raise ValueError('Composed report required')
  if any(not isinstance(v,list) or any(not isinstance(i,str) or not i for i in v) for v in payload['project_ids'].values()):raise ValueError('Original string IDs required')
  for project in PROJECTS:original_ids(payload,project)
  canonical=json.dumps(payload,sort_keys=True,separators=(',',':'));digest=sha256(canonical.encode()).hexdigest()
  with self.ledger.transaction():
   old=self.ledger.get(receipt_id)
   if old is not None:
    if old['hash']!=digest:raise ValueError('Receipt content changed')
   else:self.ledger.put(receipt_id,{'payload':deepcopy(payload),'hash':digest,'status':'prepared','send_id':None,'done':[]})
   return deepcopy(self.ledger.get(receipt_id)['payload'])
 def stored_payload(self,receipt_id):
  with self.ledger.transaction():
   state=self.ledger.get(receipt_id)
   if state is None:raise ValueError('Unknown receipt')
   return deepcopy(state['payload'])
 def acknowledge(self,receipt_id,send_id):
  if not isinstance(send_id,str) or not send_id:raise ValueError('Verified send ID required')
  with self.ledger.transaction():
   state=self.ledger.get(receipt_id)
   if state is None:raise ValueError('Unknown receipt')
   if not self.verify_send(receipt_id,send_id,state['hash']):raise ValueError('Send proof rejected')
   if state['send_id'] not in (None,send_id):raise ValueError('Conflicting send identity')
   if state['status']=='done':return {'status':'acknowledged'}
   state.update(status='acking',send_id=send_id);self.ledger.put(receipt_id,state)
   for project in PROJECTS:
    if project in state['done']:continue
    # Marker MUST persist this idempotency key atomically with its project write.
    # A crash after marker return but before ledger commit safely retries the key.
    self.markers[project](original_ids(state['payload'],project),receipt_id+':'+project)
    state['done'].append(project);self.ledger.put(receipt_id,state)
   state['status']='done';self.ledger.put(receipt_id,state)
   return {'status':'acknowledged'}
