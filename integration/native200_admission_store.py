"""New explicit admission store; old native preflight/gates remain unchanged."""
from types import SimpleNamespace
from integration.native200_store import NativeStore
from integration.native200_transactions import NativeRefused
class AdmissionStore(NativeStore):
 def insert_one(self,document,*,session=None):
  from integration.native200_admission_preflight import inspect_admission_existing
  inspect_admission_existing(self)
  if type(document)is not dict or '_id'not in document:raise NativeRefused('Exact native insert')
  out=self._command({'insert':self.name,'documents':[document],'ordered':True,'maxTimeMS':2000},session,True)
  if type(out.get('n'))is not int or out['n']!=1:raise NativeRefused('Insert acknowledgement held')
  return SimpleNamespace(acknowledged=True)
 def replace_one(self,query,document,*,upsert=False,session=None):
  from integration.native200_admission_preflight import inspect_admission_existing
  inspect_admission_existing(self)
  if type(query)is not dict or not query or type(document)is not dict or upsert is not False:raise NativeRefused('No native upsert')
  out=self._command({'update':self.name,'updates':[{'q':query,'u':document,'upsert':False,'multi':False}],'ordered':True,'maxTimeMS':2000},session,True)
  if type(out.get('n'))is not int or out['n']not in (0,1)or out.get('upserted'):raise NativeRefused('Update acknowledgement held')
  return SimpleNamespace(acknowledged=True,matched_count=out['n'])
