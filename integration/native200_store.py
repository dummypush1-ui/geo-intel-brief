"""Fixed-mapping single-command native bridge. No creation or reauth replay."""
import copy
from types import SimpleNamespace
from bson import BSON
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern
from pymongo.read_preferences import ReadPreference
from pymongo.synchronous.client_session import ClientSession
from integration.native200_transactions import NativeNoRetryProvider,NativeRefused
NAMES=frozenset(('collector_jobs197','collector_replay199','collector_checkpoints197','finder_budget198','finder_replay199','native_operations200','native_guards200','native_outcomes200'))
CAP=8*1024*1024
class NativeStore:
 def __init__(self,provider,name):
  if type(provider)is not NativeNoRetryProvider or provider.enabled is not True or name not in NAMES:raise NativeRefused('Exact fixed native store')
  self.provider=provider;self.name=name;self.database=SimpleNamespace(name='geo_intel',client=provider.client);self.write_concern=WriteConcern(w='majority',j=True,wtimeout=5000);self.read_concern=ReadConcern('majority')
 def _command(self,cmd,session=None,write=False):
  if type(cmd)is not dict or not cmd:raise NativeRefused('Exact fixed raw command')
  action=next(iter(cmd))
  if action not in ('find','insert','update','listCollections','listIndexes'):raise NativeRefused('No provisioning or other command')
  if action=='listCollections':
   if set(cmd)!={'listCollections','filter','cursor','maxTimeMS'} or cmd['listCollections']!=1 or cmd['filter']!={'name':self.name} or cmd['cursor']!={'batchSize':2}:raise NativeRefused('Fixed collection inspection')
  elif cmd[action]!=self.name:raise NativeRefused('Fixed command mapping')
  if cmd.get('maxTimeMS')!=2000:raise NativeRefused('Bounded command timeout')
  if write!=(action in ('insert','update')):raise NativeRefused('Exact write concern classification')
  if action in ('listCollections','listIndexes')and session is not None:raise NativeRefused('Inspection outside transaction only')
  self.provider._check();self.provider._topology()
  if session is not None and(type(session)is not ClientSession or session.client is not self.database.client or not session.in_transaction):raise NativeRefused('Exact active native session')
  if len(BSON.encode(cmd))>CAP:raise NativeRefused('Native command byte cap')
  cmd=copy.deepcopy(cmd)
  if session is None and not write and next(iter(cmd))=='find':cmd['readConcern']={'level':'majority'}
  with self.database.client._conn_for_writes(session,next(iter(cmd)))as conn:
   if conn.is_mongos or conn.service_id is not None:raise NativeRefused('Native replica-set connection only')
   out=conn.command('geo_intel',cmd,read_preference=ReadPreference.PRIMARY,session=session,client=self.database.client,write_concern=self.write_concern if write and session is None else None,parse_write_concern_error=True,no_reauth=True)
  if type(out)is not dict or out.get('ok')!=1 or out.get('writeErrors')or out.get('writeConcernError')or out.get('errorLabels')or len(BSON.encode(out))>CAP:raise NativeRefused('Native command reply held')
  return out
 def find_one(self,query,*,session=None,max_time_ms=2000):
  if type(query)is not dict or not query or max_time_ms!=2000:raise NativeRefused('Exact bounded find')
  out=self._command({'find':self.name,'filter':query,'limit':2,'batchSize':2,'singleBatch':True,'maxTimeMS':2000},session)
  cursor=out.get('cursor')
  if type(cursor)is not dict or cursor.get('id')!=0 or cursor.get('ns')!='geo_intel.'+self.name or type(cursor.get('firstBatch'))is not list or len(cursor['firstBatch'])>1:raise NativeRefused('Exact exhausted one-row cursor')
  rows=cursor['firstBatch']
  if rows and type(rows[0])is not dict:raise NativeRefused('Exact returned document')
  return copy.deepcopy(rows[0])if rows else None
 def insert_one(self,document,*,session=None):
  from integration.native200_preflight import inspect_existing
  inspect_existing(self)
  if type(document)is not dict or '_id'not in document:raise NativeRefused('Exact native insert')
  out=self._command({'insert':self.name,'documents':[document],'ordered':True,'maxTimeMS':2000},session,True)
  if type(out.get('n'))is not int or out['n']!=1:raise NativeRefused('Insert acknowledgement held')
  return SimpleNamespace(acknowledged=True)
 def replace_one(self,query,document,*,upsert=False,session=None):
  from integration.native200_preflight import inspect_existing
  inspect_existing(self)
  if type(query)is not dict or not query or type(document)is not dict or upsert is not False:raise NativeRefused('No native upsert')
  out=self._command({'update':self.name,'updates':[{'q':query,'u':document,'upsert':False,'multi':False}],'ordered':True,'maxTimeMS':2000},session,True)
  if type(out.get('n'))is not int or out['n']not in (0,1)or out.get('upserted'):raise NativeRefused('Update acknowledgement held')
  return SimpleNamespace(acknowledged=True,matched_count=out['n'])
