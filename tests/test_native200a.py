import unittest,copy
from unittest.mock import patch
from pymongo import MongoClient
from pymongo.synchronous.client_session import ClientSession,_TxnState
from integration.native200_transactions import NativeNoRetryProvider,verify_native_pins
from tests.native200_wire_fixture import WireServer
class Tests(unittest.TestCase):
 def connected(self,server):
  c=MongoClient('mongodb://127.0.0.1:'+str(server.port)+'/?replicaSet=fixture',retryWrites=False,retryReads=False,serverSelectionTimeoutMS=600,connectTimeoutMS=600,socketTimeoutMS=600,maxPoolSize=2,heartbeatFrequencyMS=500);c.admin.command('ping');self.addCleanup(c.close);return c
 def transaction(self,s):
  c=self.connected(s);p=NativeNoRetryProvider(c,enabled=True);raw=p.begin();self.assertIs(type(raw),ClientSession);p.start();c.geo_intel.fixture.find_one({},session=raw);return c,p,raw
 def test_pins_off_exact_flags(self):
  self.assertEqual(verify_native_pins(),'4.18.2');p=NativeNoRetryProvider(None)
  with self.assertRaises(ValueError):p.begin()
  with self.assertRaises(ValueError):NativeNoRetryProvider(None,enabled=1)
 def test_actual_wire_commit_once_native_session_fields(self):
  s=WireServer();self.addCleanup(s.close);c,p,raw=self.transaction(s)
  with patch.object(ClientSession,'commit_transaction',side_effect=AssertionError),patch.object(ClientSession,'_finish_transaction_with_retry',side_effect=AssertionError),patch.object(MongoClient,'_retry_internal',side_effect=AssertionError):self.assertEqual(p.commit_once()['state'],'acknowledged');p.close()
  cmds=[d for d in s.commands if 'commitTransaction'in d];self.assertEqual(len(cmds),1);d=cmds[0];find=next(d for d in s.commands if'find'in d)
  for k in ('lsid','txnNumber','autocommit'):self.assertEqual(d[k],find[k])
  self.assertFalse(d['autocommit']);self.assertEqual(d['writeConcern'],{'w':'majority','j':True,'wtimeout':5000});self.assertEqual(d['maxTimeMS'],5000);self.assertEqual(d['$db'],'admin');self.assertNotIn('startTransaction',d);self.assertFalse(any('abortTransaction'in x for x in s.commands))
  with self.assertRaises(ValueError):p.commit_once()
 def test_real_wire_unknowns_no_retry_no_abort(self):
  for mode,reply in [('drop',None),('ok',{'ok':0,'code':91,'errmsg':'stepdown','errorLabels':['RetryableWriteError','UnknownTransactionCommitResult']}),('ok',{'ok':1,'writeConcernError':{'code':64,'errmsg':'timedout','errInfo':{'wtimeout':True}}})]:
   with self.subTest(mode=mode,reply=reply):
    s=WireServer(mode=mode,commit_reply=reply);self.addCleanup(s.close);c,p,raw=self.transaction(s)
    with self.assertRaises(Exception):p.commit_once()
    self.assertTrue(p.uncertain);self.assertIs(raw._transaction.state,_TxnState.COMMITTED);p.close();p.close();self.assertEqual(sum('commitTransaction'in d for d in s.commands),1);self.assertEqual(sum('abortTransaction'in d for d in s.commands),0)
    with self.assertRaises(ValueError):p.commit_once()
 def test_checkout_failure_latches_before_attempt_no_commit_or_abort(self):
  s=WireServer();self.addCleanup(s.close);c,p,raw=self.transaction(s)
  def check(*args):self.assertTrue(p.commit_attempted);raise RuntimeError()
  with patch.object(c,'_conn_for_writes',side_effect=check):
   with self.assertRaises(RuntimeError):p.commit_once()
  p.close();self.assertTrue(p.uncertain);self.assertFalse(any('commitTransaction'in d or 'abortTransaction'in d for d in s.commands))
 def test_empty_session_no_commit_network(self):
  s=WireServer();self.addCleanup(s.close);c=self.connected(s);p=NativeNoRetryProvider(c,enabled=True);p.begin();p.start();self.assertEqual(p.commit_once()['state'],'empty_committed');p.close();self.assertFalse(any('commitTransaction'in d or'abortTransaction'in d for d in s.commands))
 def test_abort_one_direct_command_and_close_no_implicit_retry(self):
  s=WireServer();self.addCleanup(s.close);c,p,raw=self.transaction(s)
  with patch.object(ClientSession,'abort_transaction',side_effect=AssertionError),patch.object(ClientSession,'_finish_transaction_with_retry',side_effect=AssertionError):p.abort_once();p.close()
  self.assertEqual(sum('abortTransaction'in d for d in s.commands),1);self.assertEqual(sum('commitTransaction'in d for d in s.commands),0)
 def test_close_unattempted_quarantines_no_autoabort(self):
  s=WireServer();self.addCleanup(s.close);c,p,raw=self.transaction(s);p.close();self.assertTrue(p.uncertain);self.assertFalse(any('abortTransaction'in d for d in s.commands))
 def test_real_mongos_rejected_even_client_native(self):
  s=WireServer(hello_mode='mongos');self.addCleanup(s.close);c=MongoClient('mongodb://127.0.0.1:'+str(s.port),retryWrites=False,retryReads=False,serverSelectionTimeoutMS=600);self.addCleanup(c.close);c.admin.command('ping');p=NativeNoRetryProvider(c,enabled=True)
  with self.assertRaises(ValueError):p.begin()
  self.assertFalse(any('commitTransaction'in d for d in s.commands))
 def test_retry_client_rejected(self):
  c=MongoClient(connect=False);self.addCleanup(c.close)
  with self.assertRaises(ValueError):NativeNoRetryProvider(c,enabled=True)

 def test_standalone_and_loadbalanced_rejected(self):
  server=WireServer(hello_mode='standalone');self.addCleanup(server.close);c=MongoClient('mongodb://127.0.0.1:'+str(server.port),retryWrites=False,retryReads=False,serverSelectionTimeoutMS=600);self.addCleanup(c.close);c.admin.command('ping');p=NativeNoRetryProvider(c,enabled=True)
  with self.assertRaises(ValueError):p.begin()
  lb=MongoClient('mongodb://127.0.0.1:1/?loadBalanced=true',connect=False,retryWrites=False,retryReads=False);self.addCleanup(lb.close)
  with self.assertRaises(ValueError):NativeNoRetryProvider(lb,enabled=True)
 def test_ambient_timeout_unknown_nocommit(self):
  import pymongo
  server=WireServer();self.addCleanup(server.close);c,p,raw=self.transaction(server)
  with pymongo.timeout(1):
   with self.assertRaises(ValueError):p.commit_once()
  p.close();self.assertTrue(p.uncertain);self.assertFalse(any('commitTransaction'in d or 'abortTransaction'in d for d in server.commands))
 def test_topology_change_before_checkout_no_retry(self):
  server=WireServer();self.addCleanup(server.close);c,p,raw=self.transaction(server)
  with patch.object(p,'_topology',side_effect=ValueError):
   with self.assertRaises(ValueError):p.commit_once()
  self.assertTrue(p.commit_attempted);p.close();self.assertTrue(p.uncertain);self.assertFalse(any('commitTransaction'in d or 'abortTransaction'in d for d in server.commands))

 def test_391_commit_and_abort_each_one_wireframe(self):
  for command in ('commitTransaction','abortTransaction'):
   with self.subTest(command=command):
    server=WireServer(commit_reply={'ok':0,'code':391,'errmsg':'ReauthenticationRequired'});self.addCleanup(server.close);c,p,raw=self.transaction(server)
    with patch.object(ClientSession,'_finish_transaction',side_effect=AssertionError),patch.object(ClientSession,'_finish_transaction_with_retry',side_effect=AssertionError),patch.object(MongoClient,'_retry_internal',side_effect=AssertionError):
     with self.assertRaises(Exception)as caught:(p.commit_once if command=='commitTransaction'else p.abort_once)()
     self.assertEqual(caught.exception.code,391);p.close()
    self.assertTrue(p.uncertain);self.assertEqual(sum(command in d for d in server.commands),1);self.assertEqual(sum(('abortTransaction'if command=='commitTransaction'else'commitTransaction')in d for d in server.commands),0)
 def test_oidc_client_refused_without_authentication(self):
  client=MongoClient('mongodb://127.0.0.1:1/?authMechanism=MONGODB-OIDC',connect=False,retryWrites=False,retryReads=False,authMechanismProperties={'ENVIRONMENT':'gcp','TOKEN_RESOURCE':'test'});self.addCleanup(client.close)
  with self.assertRaises(ValueError):NativeNoRetryProvider(client,enabled=True)
