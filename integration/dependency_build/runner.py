"""Bounded local subprocess capture. No production launcher."""
import os,resource,selectors,signal,subprocess,time
class StageBlocked(RuntimeError):pass
def capture(argv,*,env,cwd=None,stdin=b'',wall=120,cpu=60,cap=1048576):
 def limits():
  resource.setrlimit(resource.RLIMIT_CPU,(cpu,cpu));resource.setrlimit(resource.RLIMIT_AS,(1073741824,1073741824));resource.setrlimit(resource.RLIMIT_FSIZE,(67108864,67108864))
 p=None;sel=None;out=bytearray();reason=None;start=time.monotonic();code=None
 try:
  p=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=env,cwd=cwd,preexec_fn=limits,start_new_session=True);start=time.monotonic()
  sel=selectors.DefaultSelector();os.set_blocking(p.stdout.fileno(),False);os.set_blocking(p.stdin.fileno(),False);sel.register(p.stdout,selectors.EVENT_READ,'out');pending=memoryview(stdin)
  if pending:sel.register(p.stdin,selectors.EVENT_WRITE,'in')
  else:p.stdin.close()
  while sel.get_map() or p.poll() is None:
   remaining=wall-(time.monotonic()-start)
   if remaining<=0:reason='wall_deadline';break
   for key,mask in sel.select(min(.05,remaining)):
    if key.data=='out':
     b=os.read(key.fd,min(65536,cap+1-len(out)))
     if b:out.extend(b)
     else:sel.unregister(key.fileobj);key.fileobj.close()
     if len(out)>cap:reason='output_cap';break
    else:
     n=os.write(key.fd,pending[:65536]);pending=pending[n:]
     if not pending:sel.unregister(key.fileobj);key.fileobj.close()
   if reason:break
  if not reason:
   code=p.poll()
   if code!=0:reason='nonzero_exit'
 except Exception as e:reason='capture_error:'+type(e).__name__
 finally:
  if p is not None:
   # Kill group even after leader exit, so descendants cannot outlive the stage.
   try:os.killpg(p.pid,signal.SIGKILL)
   except ProcessLookupError:pass
   try:code=p.wait(timeout=5)
   except subprocess.TimeoutExpired:
    p.kill();code=p.wait();reason=reason or 'reap_timeout'
   for f in (p.stdin,p.stdout):
    if f and not f.closed:f.close()
  if sel:sel.close()
 return {'status':'passed' if reason is None and code==0 else 'blocked','exit_code':code,'stop_reason':reason,'output':bytes(out[:cap]),'output_bytes':min(len(out),cap),'wall_seconds':round(time.monotonic()-start,3)}
