import unittest,copy,hashlib,json,base64
from unittest.mock import patch
from integration.finder198_receipts import ProxyReceiptBudget,_v2
from integration.finder198_budget import BudgetRefused
from integration.finder198_transport import FixedProxyTransport,proxy_request,TransportRefused
from integration.finder198_connector import plan_ships
from tests.test_finder198ba import Collection,R
class Tests(unittest.TestCase):
 def setUp(self):
  self.c=Collection();self.c.doc.update(schema=2,receipts=[]);self.b=ProxyReceiptBudget(self.c,review=R);self.t=FixedProxyTransport({'FINDER_PROXY_BASE_URL':'https://hsn-ai-proxy.onrender.com','FINDER_PROXY_SECRET':'x'*48},enabled=True)
 def claim(self,nonce='n'*24):return self.b.claim(nonce,'a'*64,'b'*64,max(101,self.c.doc.get('last_clock',101)))
 def test_v1_refused_v2_claim_atomic(self):
  self.c.doc.pop('schema');self.c.doc.pop('receipts')
  with self.assertRaises(BudgetRefused):self.claim()
  self.setUp();r=self.claim();self.assertEqual(self.c.doc['calls'],1);self.assertEqual(self.c.doc['active']['key'],r['receipt']['nonce_hash']);self.assertEqual(len(self.c.doc['receipts']),1)
 def test_duplicate_claim_status_no_new_consumption_and_mismatch(self):
  self.claim();self.assertEqual(self.claim()['state'],'replay_status_only');self.assertEqual(self.c.doc['calls'],1)
  with self.assertRaises(BudgetRefused):self.b.claim('n'*24,'c'*64,'b'*64,102)
 def test_completed_replay_no_answer_no_transport(self):
  r=self.claim()['receipt'];r=self.b.start(r,102);done=self.b.finish(r,103,status=200,response_hash='c'*64,response_bytes=10)
  self.assertIsNone(self.c.doc['active']);again=self.claim();self.assertEqual(again['state'],'replay_status_only');self.assertEqual(again['receipt']['phase'],'complete');self.assertNotIn('body',again['receipt']);self.assertEqual(self.c.doc['calls'],1)
 def test_started_never_takeover_or_retry_and_unknown_held(self):
  r=self.b.start(self.claim()['receipt'],102)
  with self.assertRaises(BudgetRefused):self.b.start(r,103)
  self.b.hold(r,103)
  with self.assertRaises(BudgetRefused):self.b.claim('m'*24,'a'*64,'b'*64,1000)
  self.assertEqual(self.claim()['state'],'replay_status_only')
 def test_late_and_invalid_response_keep_hold(self):
  r=self.b.start(self.claim()['receipt'],102);out=self.b.finish(r,126,status=200,response_hash='c'*64,response_bytes=0);self.assertEqual(out['phase'],'unknown_held')
  self.setUp();r=self.b.start(self.claim()['receipt'],102)
  with self.assertRaises(BudgetRefused):self.b.finish(r,103,status=200,response_hash='c'*64,response_bytes=1048577)
  self.assertEqual(self.c.doc['receipts'][0]['phase'],'send_started')
 def test_unknown_cas_no_retry_receipt_persists(self):
  self.c.ack=False
  with self.assertRaises(BudgetRefused):self.claim()
  self.assertEqual(self.c.writes,1);self.assertEqual(self.c.doc['calls'],1)
 def test_full_receipts_no_reset_across_window(self):
  for i in range(64):
   r=self.b.claim(('n'+str(i)).ljust(24,'x'),'a'*64,'b'*64,100+i*601)['receipt'];r=self.b.start(r,101+i*601);self.b.finish(r,102+i*601,status=200,response_hash='c'*64,response_bytes=0)
  with self.assertRaises(BudgetRefused):self.b.claim('z'*24,'a'*64,'b'*64,50000)
 def test_off_and_ai_disabled_no_process_or_budget(self):
  off=FixedProxyTransport({},enabled=False)
  with self.assertRaises(TransportRefused):proxy_request(self.b,off,nonce='n'*24,operation='ships',port='INNSA',principal_hash='d'*64,clock=lambda:101)
  with self.assertRaises(ValueError):proxy_request(self.b,self.t,nonce='n'*24,operation='ai',provider='groq',model='invented',principal_hash='d'*64,clock=lambda:101)
  self.assertEqual(self.c.writes,0)
 def test_one_call_completed_and_replay_status_only(self):
  with patch.object(FixedProxyTransport,'execute',return_value={'status':200,'body':b'{"ok":true}'})as call:
   out=proxy_request(self.b,self.t,nonce='n'*24,operation='ships',port='INNSA',principal_hash='d'*64,clock=lambda:101)
   self.assertEqual(out['state'],'complete')
   out=proxy_request(self.b,self.t,nonce='n'*24,operation='ships',port='INNSA',principal_hash='d'*64,clock=lambda:101)
   self.assertEqual(out['state'],'replay_status_only');self.assertEqual(call.call_count,1)
 def test_timeout_exception_unknown_no_retry(self):
  with patch.object(FixedProxyTransport,'execute',side_effect=ValueError('SECRET'))as call:
   with self.assertRaises(TransportRefused)as e:proxy_request(self.b,self.t,nonce='n'*24,operation='ships',port='INNSA',principal_hash='d'*64,clock=lambda:101)
   self.assertNotIn('SECRET',str(e.exception));self.assertEqual(call.call_count,1)
  self.assertEqual(self.c.doc['receipts'][0]['phase'],'unknown_held')
 def test_malformed_state_no_secretdata(self):
  self.claim();self.c.doc['receipts'][0]['body']='prompt'
  with self.assertRaises(BudgetRefused):self.claim()
 def test_connector_drift_and_request_override_before_process(self):
  with patch('integration.finder198_transport.subprocess.Popen',side_effect=AssertionError):
   with self.assertRaises(ValueError):self.t.execute({**plan_ships('INNSA'),'path':'https://evil.example'},b'')
   with self.assertRaises(TransportRefused):self.t.execute(plan_ships('INNSA'),b'x')
 def test_cross_principal_nonce_refused(self):
  with patch.object(FixedProxyTransport,'execute',return_value={'status':200,'body':b'{}'})as call:
   proxy_request(self.b,self.t,nonce='n'*24,operation='ships',port='INNSA',principal_hash='d'*64,clock=lambda:101)
   with self.assertRaises(BudgetRefused):proxy_request(self.b,self.t,nonce='n'*24,operation='ships',port='INNSA',principal_hash='e'*64,clock=lambda:101)
   self.assertEqual(call.call_count,1)

class ChildFixtures(unittest.TestCase):
 def test_dns_mixed_rejected_before_socket(self):
  from integration.finder198_transport_child import perform
  import socket,time
  rows=[(socket.AF_INET,socket.SOCK_STREAM,socket.IPPROTO_TCP,'',('8.8.8.8',443)),(socket.AF_INET,socket.SOCK_STREAM,socket.IPPROTO_TCP,'',('127.0.0.1',443))]
  with patch('socket.getaddrinfo',return_value=rows),patch('socket.socket',side_effect=AssertionError):
   with self.assertRaises(ValueError):perform('/ships?port=ALL','GET',b'','x'*48,deadline=time.monotonic()+1)
 def test_closed_paths_before_dns(self):
  from integration.finder198_transport_child import perform
  import time
  with patch('socket.getaddrinfo',side_effect=AssertionError):
   for path in ('/ships?port=BAD','https://evil.example','/nvidia/v1/chat/completions'):
    with self.assertRaises(ValueError):perform(path,'GET',b'','x'*48,deadline=time.monotonic()+1)
 def test_mock_tls_json_response_echo_redirect_length(self):
  from integration.finder198_transport_child import perform
  import socket,time,ssl
  from types import SimpleNamespace
  class TLS:
   def settimeout(self,n):pass
   def connect(self,t):pass
   def getpeername(self):return ('8.8.8.8',443)
   def sendall(self,b):self.sent=b
   def close(self):pass
  class Up:
   def __init__(self,*a):self.status=200;self.headers=SimpleNamespace(defects=[]);self.chunked=False;self.read_count=0
   def begin(self):pass
   def getheaders(self):return self.pairs
   def read(self,n):self.read_count+=1;out=self.blob[:n];self.blob=self.blob[n:];return out
   def close(self):pass
  tls=TLS();ctx=SimpleNamespace(check_hostname=True,verify_mode=ssl.CERT_REQUIRED,wrap_socket=lambda *a,**kw:tls)
  rows=[(socket.AF_INET,socket.SOCK_STREAM,socket.IPPROTO_TCP,'',('8.8.8.8',443))]
  for blob,status,length,success in ((b'{"ok":true}',200,'11',True),(b'{"x":"'+b'x'*48+b'"}',200,'56',False),(b'{}',302,'2',False),(b'{}',200,'1048577',False),(b'{}',200,'3',False)):
   up=Up();up.status=status;up.blob=blob;up.pairs=[('Content-Type','application/json'),('Content-Length',length)]
   with patch('socket.getaddrinfo',return_value=rows),patch('socket.socket',return_value=tls),patch('ssl.create_default_context',return_value=ctx),patch('http.client.HTTPResponse',return_value=up):
    if success:self.assertEqual(perform('/ships?port=ALL','GET',b'','x'*48,deadline=time.monotonic()+1)['status'],200)
    else:
     with self.assertRaises(ValueError):perform('/ships?port=ALL','GET',b'','x'*48,deadline=time.monotonic()+1)
   if length=='1048577':self.assertEqual(up.read_count,0)
 def test_real_child_empty_environment_closed_invalid_protocol(self):
  import subprocess,sys
  from pathlib import Path
  child=Path(__file__).resolve().parents[1]/'integration/finder198_transport_child.py'
  p=subprocess.run([sys.executable,'-I',str(child)],input=b'{}',capture_output=True,env={},timeout=3)
  self.assertEqual(p.returncode,70);self.assertEqual(p.stdout,b'');self.assertEqual(p.stderr,b'')
 def test_parent_forced_timeout_real_child_kill_reap_no_secret_args(self):
  import subprocess,sys,time
  real=subprocess.Popen;children=[];times=iter([0,21])
  def launch(argv,**kw):
   self.assertNotIn('x'*48,str(argv));self.assertEqual(kw['env'],{})
   p=real([sys.executable,'-I','-c','import time;time.sleep(10)'],**kw);children.append(p);return p
  transport=FixedProxyTransport({'FINDER_PROXY_BASE_URL':'https://hsn-ai-proxy.onrender.com','FINDER_PROXY_SECRET':'x'*48},enabled=True)
  with patch('integration.finder198_transport.subprocess.Popen',side_effect=launch),patch('integration.finder198_transport.time.monotonic',side_effect=lambda:next(times)):
   with self.assertRaises(TransportRefused):transport.execute(plan_ships('INNSA'),b'')
  self.assertEqual(len(children),1);self.assertIsNotNone(children[0].returncode);self.assertLess(children[0].returncode,0)
