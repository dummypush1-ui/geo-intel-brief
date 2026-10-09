import unittest,copy
from types import SimpleNamespace
from unittest.mock import patch,PropertyMock
from bson import Int64
from pymongo import MongoClient
from integration.native200_owner_package import owner_package
from integration.native200_readonly_measurement import measure,_plain,_read
from integration.native200_admission_preflight import VALIDATORS
from integration.native200_store import NAMES

class Tests(unittest.TestCase):
 def data(self):
  d={n:{}for n in NAMES}
  for row in owner_package(fingerprint='a'*64,clock=1791552000)['empty_new_genesis_templates']:
   doc=row['empty_new_install_only'];d[row['collection']][doc['_id']]=doc
  return d
 def run_measure(self,change=None):
  data=self.data();calls=[];client=MongoClient(connect=False,retryReads=False,retryWrites=False);self.addCleanup(client.close)
  def read(c,cmd):
   self.assertIs(c,client);name=next(iter(cmd));calls.append(name)
   if change:change(data,cmd,calls)
   if name=='hello':return {'ok':1,'setName':'PRIVATE-CLUSTER','hosts':['secret-host'],'isWritablePrimary':True,'maxWireVersion':25,'logicalSessionTimeoutMinutes':30}
   if name=='buildInfo':return {'ok':1,'version':'8.0.1','private':'SECRET'}
   if name=='count':return {'ok':1,'n':len(data[cmd[name]])}
   if name=='listCollections':
    n=cmd['filter']['name'];rows=[{'name':n,'type':'collection','options':{'validator':copy.deepcopy(VALIDATORS[n]),'validationLevel':'strict','validationAction':'error'}}];ns='geo_intel.$cmd.listCollections'
   elif name=='listIndexes':rows=[{'name':'_id_','key':{'_id':1}}];ns='geo_intel.'+cmd[name]
   elif name=='find':rows=list(copy.deepcopy(data[cmd[name]]).values());ns='geo_intel.'+cmd[name]
   else:raise AssertionError('Forbidden command '+name)
   out={'ok':1,'cursor':{'id':Int64(0),'ns':ns,'firstBatch':rows}}
   if change:change(out,cmd,calls)
   return out
  with patch('integration.native200_readonly_measurement.verify_native_pins',return_value='4.18.2'),patch('integration.native200_readonly_measurement._read',side_effect=read),patch.object(MongoClient,'topology_description',new_callable=PropertyMock,return_value=SimpleNamespace(topology_type_name='ReplicaSetWithPrimary')):
   result=measure(client,enabled=True,fingerprint='a'*64)
  return result,calls
 def test_default_off_no_access(self):
  with patch('integration.native200_readonly_measurement._read',side_effect=AssertionError):self.assertEqual(measure()['state'],'disabled')
  with self.assertRaises(ValueError):measure(enabled=1)
  with self.assertRaises(ValueError):measure(enabled=True,fingerprint='a'*64)
 def test_genesis_all_eight_readonly_sanitized(self):
  out,calls=self.run_measure();self.assertEqual(len(out['collections']),8);self.assertFalse(out['ready']);self.assertFalse(out['role_verified']);self.assertFalse(out['atomic_snapshot']);self.assertEqual(out['guard_phases'],{'collector':'idle','broker':'idle'})
  self.assertEqual(set(calls),{'hello','buildInfo','listCollections','listIndexes','find','count'});self.assertNotIn('SECRET',str(out));self.assertNotIn('PRIVATE',str(out));self.assertNotIn('secret-host',str(out))
 def test_complete_count_truncation_stop(self):
  def change(d,cmd,calls):
   if 'cursor'in d and 'find'in cmd and cmd['find']=='collector_jobs197':d['cursor']['firstBatch']=[]
  with self.assertRaises(ValueError):self.run_measure(change)
 def test_numeric_validator_double_drift_stop(self):
  def change(d,cmd,calls):
   if 'cursor'in d and 'listCollections'in cmd:d['cursor']['firstBatch'][0]['options']['validator']={'$jsonSchema':{'minimum':1.0}}
  with self.assertRaises(ValueError):self.run_measure(change)
 def test_archive_orphan_stop(self):
  def change(d,cmd,calls):
   if 'collector_replay199'in d:d['collector_replay199']['orphan']={'_id':'orphan'}
  with self.assertRaises(ValueError):self.run_measure(change)
 def test_unknown_checkpoint_stop(self):
  def change(d,cmd,calls):
   if 'collector_checkpoints197'in d:d['collector_checkpoints197']['unknown']={'_id':'unknown'}
  with self.assertRaises(ValueError):self.run_measure(change)
 def test_source_change_stop(self):
  def change(d,cmd,calls):
   if 'collector_jobs197'in d and calls.count('find')>8:d['collector_jobs197']['geo108']['revision']=1
  with self.assertRaises(ValueError):self.run_measure(change)
 def test_cursor_not_exhausted_stop(self):
  def change(d,cmd,calls):
   if 'cursor'in d:d['cursor']['id']=1
  with self.assertRaises(ValueError):self.run_measure(change)
 def test_read_boundary_rejects_writes_before_client(self):
  for name in ('insert','update','create','collMod','drop','commitTransaction','abortTransaction','getMore'):
   with self.assertRaises(ValueError):_read(None,{name:1,'maxTimeMS':2000})
 def test_int64_lossless_only_double_unchanged(self):
  self.assertIs(type(_plain(Int64(2**53-1))),int);self.assertEqual(_plain(Int64(2**53-1)),2**53-1);self.assertIs(type(_plain(1.0)),float)
 def test_real_pinned_wire_readonly_no_sessions_or_mutations(self):
  from tests.native200cb_read_fixture import ReadServer
  from integration.native200_transactions import verify_native_pins
  self.assertEqual(verify_native_pins(),'4.18.2');s=ReadServer(self.data());self.addCleanup(s.close)
  c=MongoClient('mongodb://127.0.0.1:'+str(s.port)+'/?replicaSet=fixture',retryReads=False,retryWrites=False,serverSelectionTimeoutMS=600,connectTimeoutMS=600,socketTimeoutMS=600);self.addCleanup(c.close)
  c.admin.command({'hello':1})
  before=copy.deepcopy(s.data)
  with patch.object(MongoClient,'start_session',side_effect=AssertionError),patch.object(MongoClient,'_retry_internal',side_effect=AssertionError):out=measure(c,enabled=True,fingerprint='a'*64)
  self.assertEqual(out['state'],'readonly_observed');self.assertEqual(s.data,before)
  self.assertTrue(set(next(iter(x))for x in s.commands)<={'ismaster','hello','buildInfo','listCollections','listIndexes','find','count'})
  self.assertFalse(any('autocommit'in x or 'txnNumber'in x for x in s.commands))
 def test_real_wire_391_never_reauth_or_retry(self):
  from tests.native200cb_read_fixture import ReadServer
  s=ReadServer(self.data(),fail=lambda d:'find'in d);self.addCleanup(s.close)
  c=MongoClient('mongodb://127.0.0.1:'+str(s.port)+'/?replicaSet=fixture',retryReads=False,retryWrites=False,serverSelectionTimeoutMS=600,connectTimeoutMS=600,socketTimeoutMS=600);self.addCleanup(c.close);c.admin.command({'hello':1})
  with self.assertRaises(ValueError):measure(c,enabled=True,fingerprint='a'*64)
  self.assertEqual(sum('find'in x for x in s.commands),1)
 def test_historical_complete_chains_both_families(self):
  from tests.test_replay199a import Client
  from integration.native200_readonly_measurement import _chains
  data=self.data()
  for family in ('collector','broker'):
   c=Client(family);c.provision();c.core().rollover(expected_revision=0,checkpoints=c.cp if family=='collector'else None);data[c.sn]=c.data[c.sn];data[c.an]=c.data[c.an]
  out,_=_chains(data,'a'*64,lambda:None);self.assertEqual(out['collector']['archive_records'],2);self.assertEqual(out['broker']['archive_records'],2)
  data['collector_replay199']['batch:1']['sha256']='f'*64
  with self.assertRaises(ValueError):_chains(data,'a'*64,lambda:None)
