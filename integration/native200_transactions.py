"""200a unselected pinned private PyMongo primitive, NOT live readiness.
No core wiring, DB creation, journal, retry, activation or implicit client.
"""
import hashlib,inspect,json
from pathlib import Path
import pymongo
from pymongo.synchronous.mongo_client import MongoClient
from pymongo.synchronous.client_session import ClientSession,_TxnState
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern
from pymongo.read_preferences import ReadPreference
from pymongo import _csot
class NativeRefused(ValueError):pass

def verify_native_pins():
 import importlib
 p=json.loads(Path(__file__).with_name('native200a-pins.json').read_text())
 if pymongo.version!=p['version']:raise NativeRefused('Pinned native version required')
 for row in p['modules']:
  m=importlib.import_module(row['module'])
  if hashlib.sha256(Path(inspect.getfile(m)).read_bytes()).hexdigest()!=row['sha256']:raise NativeRefused('Pinned native source changed')
 return p['version']

class NativeNoRetryProvider:
 """Explicit raw session lifecycle. OFF cannot begin. One lifetime transaction.
 Raw ClientSession is passed to existing Collection APIs, never a fake wrapper.
 200b durable operation guard is REQUIRED before any production use.
 """
 def __init__(self,client,*,enabled=False):
  if type(enabled)is not bool:raise NativeRefused('Exact native selection')
  self.enabled=enabled;self.client=client;self.session=None;self.started=False;self.commit_attempted=False;self.abort_attempted=False;self.closed=False;self.uncertain=False
  if not enabled:return
  verify_native_pins()
  if type(client)is not MongoClient:raise NativeRefused('Exact synchronous native client')
  if client.options.retry_writes or client.options.retry_reads or client.options.load_balanced or client._encrypter is not None or client.options.timeout is not None:raise NativeRefused('Nonretry replica-set client only')
  credentials=client.options.pool_options._credentials
  if credentials is not None and credentials.mechanism=='MONGODB-OIDC':raise NativeRefused('OIDC reauthentication route refused')
 def _check(self):
  if not self.enabled or self.closed:raise NativeRefused('Native provider disabled or closed')
  verify_native_pins()
 def _topology(self):
  # Observed topology, not URI assertions. Selection may discover/handshake but
  # never submits a commit. Reject mongos/loadbalancer even if supplied RS text.
  if self.client.topology_description.topology_type_name!='ReplicaSetWithPrimary':raise NativeRefused('Observed replica-set primary required')
 def begin(self):
  self._check()
  if self.session is not None:raise NativeRefused('One session only')
  self._topology();self.session=self.client.start_session(causal_consistency=False);return self.session
 def start(self):
  self._check();self._topology()
  if type(self.session)is not ClientSession or self.started or self.commit_attempted or self.abort_attempted:raise NativeRefused('One exact transaction only')
  self.session.start_transaction(read_concern=ReadConcern('snapshot'),write_concern=WriteConcern(w='majority',j=True,wtimeout=5000),read_preference=ReadPreference.PRIMARY,max_commit_time_ms=5000);self.started=True
  return self.session
 def commit_once(self):
  self._check()
  if not self.started or self.commit_attempted or self.abort_attempted or type(self.session)is not ClientSession:raise NativeRefused('Commit lifecycle refused')
  self.commit_attempted=True # BEFORE topology check/checkout, never retry later.
  s=self.session
  try:
   self._topology()
   if _csot.get_timeout()is not None:raise NativeRefused('Ambient timeout would alter pinned commit semantics')
   if s._transaction.state is _TxnState.STARTING:
    s._transaction.state=_TxnState.COMMITTED_EMPTY;return {'state':'empty_committed','native_ready':False}
   if s._transaction.state is not _TxnState.IN_PROGRESS:raise NativeRefused('Exact transaction state')
   with self.client._conn_for_writes(s,'commitTransaction')as conn:
    if conn.is_mongos or conn.service_id is not None:raise NativeRefused('Replica-set connection required')
    # Preserve native lsid/txnNumber/autocommit and explicit writeConcern/recoveryToken; suppress reauth replay.
    result=self._finish_once(conn,'commitTransaction')
   if result.get('ok')!=1 or result.get('writeConcernError')or result.get('errorLabels'):raise NativeRefused('Commit reply not verified')
   return {'state':'acknowledged','native_ready':False}
  except BaseException:
   self.uncertain=True;raise
  finally:
   # Mirror driver's terminal lifecycle, even on unknown. end_session MUST NOT
   # call the public auto-retrying abort helper after a commit attempt.
   if s._transaction.state is not _TxnState.COMMITTED_EMPTY:s._transaction.state=_TxnState.COMMITTED
 def _finish_once(self,conn,command_name):
  # Pinned equivalent of _finish_transaction command construction. Do not call
  # Database._command: Connection.command's reauth decorator otherwise replays
  # code391. Explicit no_reauth consumes that replay path and re-raises.
  s=self.session;s._transaction.attempt+=1;opts=s._transaction.opts
  if opts is None or s._transaction.attempt!=1:raise NativeRefused('One transaction finish attempt')
  wc=opts.write_concern;cmd={command_name:1}
  if command_name=='commitTransaction'and opts.max_commit_time_ms:cmd['maxTimeMS']=opts.max_commit_time_ms
  if s._transaction.recovery_token:cmd['recoveryToken']=s._transaction.recovery_token
  return conn.command('admin',cmd,read_preference=ReadPreference.PRIMARY,write_concern=wc,parse_write_concern_error=True,session=s,client=self.client,no_reauth=True)
 def abort_once(self):
  self._check()
  if not self.started or self.commit_attempted or self.abort_attempted:raise NativeRefused('Abort lifecycle refused')
  self.abort_attempted=True;s=self.session
  try:
   self._topology()
   if s._transaction.state is _TxnState.STARTING:return
   if s._transaction.state is not _TxnState.IN_PROGRESS:raise NativeRefused('Exact transaction state')
   with self.client._conn_for_writes(s,'abortTransaction')as conn:
    if conn.is_mongos or conn.service_id is not None:raise NativeRefused('Replica-set connection required')
    self._finish_once(conn,'abortTransaction')
  except BaseException:self.uncertain=True;raise
  finally:s._transaction.state=_TxnState.ABORTED
 def close(self):
  if self.closed:return
  try:
   if self.session is not None:
    # No implicit abort retries on cleanup. A started, unattempted transaction
    # needs explicit abort_once; close alone quarantines state without network.
    if self.started and not self.commit_attempted and not self.abort_attempted:
     self.uncertain=True;self.session._transaction.state=_TxnState.ABORTED
    self.session.end_session()
  finally:self.closed=True
