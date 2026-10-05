"""Local Werkzeug fixture evidence only, not Render or write-timeout proof."""
import contextlib,http.client,socket,struct,threading,time,unittest,sys
from unittest.mock import patch
from werkzeug.serving import ThreadedWSGIServer,WSGIRequestHandler
from integration.news_export import fixture_http as F
from tests.news_export.test_fixture_http import row,URL

class QuietHandler(WSGIRequestHandler):
 protocol_version="HTTP/1.0"
 def log(self,*args,**kwargs):pass

class BoundedServer(ThreadedWSGIServer):
 daemon_threads=False
 def __init__(self,app):
  self.capacity=threading.BoundedSemaphore(2);self.errors=[];self.workers=[]
  super().__init__('127.0.0.1',0,app,QuietHandler)
 def get_request(self):
  sock,addr=super().get_request();sock.settimeout(min(2,max(.001,self.app.deadline-time.monotonic())));sock.setsockopt(socket.SOL_SOCKET,socket.SO_SNDBUF,4096)
  return sock,addr
 def process_request(self,request,address):
  if not self.capacity.acquire(blocking=False):
   self.errors.append(RuntimeError('worker cap exceeded'));self.shutdown_request(request);return
  def worker():
   try:self.process_request_thread(request,address)
   except BaseException as exc:self.errors.append(exc)
   finally:self.capacity.release()
  t=threading.Thread(target=worker)
  try:t.start()
  except BaseException:
   self.capacity.release();self.shutdown_request(request);raise
  self.workers.append(t)
 def handle_error(self,*args):
  import sys
  self.errors.append(sys.exc_info()[1] or RuntimeError("handle_error without active exception"))

class Probe:
 def __init__(self,app,deadline,gate=False):
  self.deadline=deadline
  self.app=app;self.started=threading.Event();self.waiting=threading.Event();self.release=threading.Event();self.closed=threading.Event()
  self.complete=False;self.bytes=0;self.gate=gate;self.remaining=False
 def __call__(self,env,start):
  iterable=self.app(env,start)
  if env['REQUEST_METHOD']!='GET' or env.get('HTTP_AUTHORIZATION')!='yes':return iterable
  def body():
   try:
    self.started.set()
    for n,chunk in enumerate(iterable):
     if self.gate and n==1:
      # Header yielded, next known data chunk pending, producer unfinished.
      self.remaining=True;self.waiting.set()
      if not self.release.wait(min(4,max(0,self.deadline-time.monotonic()))):raise TimeoutError('fixture producer gate budget')
     self.bytes+=len(chunk);yield chunk
    self.complete=True
   finally:
    iterable.close();self.closed.set()
  return body()

class ServingTests(unittest.TestCase):
 def remaining(self,deadline,cap=2):
  remaining=deadline-time.monotonic()
  if remaining<=0:raise TimeoutError('absolute harness deadline')
  return min(cap,remaining)
 def wait(self,event,deadline,cap=2):return event.wait(self.remaining(deadline,cap))
 def reset_client(self,s,p,connections,deadline):
  sock=socket.create_connection(('127.0.0.1',s.server_port),timeout=self.remaining(deadline));connections.append(sock)
  sock.sendall(b'GET '+URL.encode()+b' HTTP/1.0\r\nHost: localhost\r\nAuthorization: yes\r\n\r\n')
  self.assertTrue(self.wait(p.waiting,deadline));received=b''
  # Read actual wire header and the one yielded CSV header chunk. No data yet.
  while b'\r\n\r\n' not in received:
   sock.settimeout(self.remaining(deadline));received+=sock.recv(1)
  header,body=received.split(b'\r\n\r\n',1)
  self.assertTrue(header.startswith(b'HTTP/1.0 '));self.assertNotIn(b'transfer-encoding:',header.lower());self.assertNotIn(b'content-length:',header.lower())
  while len(body)<p.bytes:
   sock.settimeout(self.remaining(deadline));body+=sock.recv(p.bytes-len(body))
  # Cannot export expected while actual slot busy; use header/payload size
  # captured before this request in the server context instead.
  self.assertEqual(body,p.expected[:len(body)]);self.assertEqual(len(body),74)
  self.assertGreater(len(p.expected)-len(body),0);self.assertFalse(p.complete);self.assertTrue(F._SLOT_BUSY[0])
  return sock,header,body

 @contextlib.contextmanager
 def server(self,gate=False):
  deadline=time.monotonic()+9
  app=F.create_original_export_fixture_app({'brics':[row(n=1,title='fixture'*2000)]},authorize=lambda r:r.headers.get('Authorization')=='yes')
  expected=app.test_client().get(URL,headers={'Authorization':'yes'}).data
  probe=Probe(app,deadline,gate);probe.expected=expected;server=None;thread=None;connections=[]
  counts={'pager':0,'stream':0};probe.counts=counts
  original_pager=F._pager;original_stream=F.OriginalStream
  def pager(*args,**kw):counts['pager']+=1;return original_pager(*args,**kw)
  def stream(*args,**kw):counts['stream']+=1;return original_stream(*args,**kw)
  patches=contextlib.ExitStack();patches.enter_context(patch.object(F,'_pager',pager));patches.enter_context(patch.object(F,'OriginalStream',stream))
  started=threading.Event()

  try:
   server=BoundedServer(probe)
   def serve():
    started.set();server.serve_forever(poll_interval=.01)
   thread=threading.Thread(target=serve);thread.start();self.assertTrue(self.wait(started,deadline))
   yield server,probe,connections,deadline
  finally:
   original_failure=sys.exc_info()[0] is not None;cleanup_errors=[]
   probe.release.set()
   for connection in connections:
    try:connection.close()
    except OSError:pass
   if server is not None:
    if thread is not None and thread.ident is not None and started.is_set():
     stopper=threading.Thread(target=server.shutdown);stopper.start();stopper.join(max(0,deadline-time.monotonic()))
     if stopper.is_alive():cleanup_errors.append('shutdown survived deadline')
    for worker in server.workers:worker.join(max(0,deadline-time.monotonic()))
    if any(worker.is_alive() for worker in server.workers):cleanup_errors.append('request worker survived')
    # Never unbounded ThreadingMixIn.server_close join.
    socket.socket.close(server.socket)
    check=socket.socket()
    try:
     check.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);check.bind(('127.0.0.1',server.server_port))
    except OSError:cleanup_errors.append('port not released')
    finally:check.close()
   if thread is not None and thread.ident is not None:
    thread.join(max(0,deadline-time.monotonic()))
    if thread.is_alive():cleanup_errors.append('server survived')
   if server is not None and server.errors:cleanup_errors.extend(str(e) for e in server.errors)
   if F._SLOT_BUSY[0]:cleanup_errors.append('slot leaked')
   if time.monotonic()>=deadline:cleanup_errors.append('absolute deadline exceeded')
   patches.close()
   if cleanup_errors:
    if original_failure:print('CLEANUP_ERRORS_WITH_ORIGINAL',cleanup_errors)
    else:self.fail(str(cleanup_errors))
 def request(self,server,connections,method='GET',authorized=True):
  c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=self.remaining(server.app.deadline));connections.append(c)
  c.request(method,URL,headers={'Authorization':'yes'} if authorized else {});r=c.getresponse();c.sock and c.sock.settimeout(self.remaining(server.app.deadline));data=r.read()
  # EOF precedes server thread final cleanup. Synchronize before next request.
  for worker in list(server.workers):
   worker.join(self.remaining(server.app.deadline))
   self.assertFalse(worker.is_alive(),'response worker unfinished')
  return r,data
 def test_complete_head_unauthorized_real_http(self):
  with self.server() as (s,p,connections,deadline):
   r,data=self.request(s,connections,authorized=False);self.assertEqual(r.status,403);self.assertFalse(p.started.is_set());self.assertEqual(p.counts,{'pager':0,'stream':0});self.assertFalse(F._SLOT_BUSY[0])
   r,data=self.request(s,connections,method='HEAD');self.assertEqual(r.status,200);self.assertEqual(data,b'');self.assertFalse(p.started.is_set());self.assertEqual(p.counts,{'pager':0,'stream':0});self.assertFalse(F._SLOT_BUSY[0])
   r,data=self.request(s,connections);self.assertEqual(r.status,200)
   self.assertEqual(r.getheader('X-Export-Fixture'),F.LABEL);self.assertIn('no-store',r.getheader('Cache-Control'))
   self.assertEqual(F.validate_file(data,'brics')['rows'],1)
   expected=p.expected
   self.assertEqual(data,expected);self.assertTrue(self.wait(p.closed,deadline));self.assertTrue(p.complete);self.assertFalse(F._SLOT_BUSY[0])
 def test_reset_pending_data_releases_actual_slot(self):
  with self.server(gate=True) as (s,p,connections,deadline):
   sock,headers,body=self.reset_client(s,p,connections,deadline)
   sock.setsockopt(socket.SOL_SOCKET,socket.SO_LINGER,struct.pack('ii',1,0));sock.close();p.release.set()
   self.assertTrue(self.wait(p.closed,deadline,3));self.assertFalse(p.complete);self.assertFalse(F._SLOT_BUSY[0])
   p.gate=False;r,data=self.request(s,connections);self.assertEqual(r.status,200);self.assertEqual(F.validate_file(data,'brics')['rows'],1)
 def test_slow_reader_observation_and_forced_cleanup(self):
  with self.server(gate=True) as (s,p,connections,deadline):
   sock,headers,received=self.reset_client(s,p,connections,deadline)
   observation={'received_bytes_at_least':len(received),'producer_bytes':p.bytes,'producer_finished':p.complete,'slot_busy':F._SLOT_BUSY[0],'socket_deadline_seconds':2,'forced_cleanup':True,'producer_gate':True}
   print('LOCAL_WERKZEUG_SLOW_READER',observation)
   self.assertGreater(len(received),0);self.assertFalse(p.complete);self.assertTrue(F._SLOT_BUSY[0])
   sock.setsockopt(socket.SOL_SOCKET,socket.SO_LINGER,struct.pack('ii',1,0));sock.close();p.release.set();self.assertTrue(self.wait(p.closed,deadline,3));self.assertFalse(F._SLOT_BUSY[0])
 def test_assertion_failure_still_tears_down(self):
  with self.assertRaisesRegex(AssertionError,'intentional teardown'):
   with self.server(gate=True) as (s,p,connections,deadline):
    self.reset_client(s,p,connections,deadline);raise AssertionError('intentional teardown')
  self.assertFalse(F._SLOT_BUSY[0])
