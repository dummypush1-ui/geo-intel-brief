"""Inactive Linux bubblewrap runner. Supplied bytes only; no network fetch.
Fixed read-only system/Python code mounts, empty private home/tmp, cleared env,
all namespaces incl. network. No fallback to unisolated execution. Deployment
must separately validate bubblewrap kernel capability and mounted dependency
paths. This scratch preparation uses explicitly configured fixed local paths.
"""
import sys,json,os,selectors,subprocess,time,hashlib,math,signal
from pathlib import Path
BASE=Path(__file__).resolve().parent
ENV=Path(sys.executable).parent.parent
BWRAP='/usr/bin/bwrap'
FILE_PINS={'parser_child.py': 'c1a8218c5775193aa24572e9e83c46c7b69e0bcf08410dbc072187b7390c271c', 'sdk-pins.json': '9ba077de033c7f86ab15f4608e93f8a012b89a30500c91b64b5dbdc92d71ea58'}
class ParserRefused(ValueError):pass

def parse_supplied_bytes(blob,*,timeout=10,projection_limit=100):
 if type(timeout)not in (int,float) or not math.isfinite(timeout) or not 0<timeout<=10:raise ParserRefused('Bounded parser timeout')
 if type(projection_limit)is not int or not 1<=projection_limit<=200:raise ParserRefused('Fixed bounded projection')
 if type(blob)is not bytes or not 1<=len(blob)<=1048576:raise ParserRefused('Bounded supplied bytes required')
 for name,h in FILE_PINS.items():
  if hashlib.sha256((BASE/name).read_bytes()).hexdigest()!=h:raise ParserRefused('Parser source drift')
 # Path/config is installation-owned, never accepted from request/data.
 cmd=[BWRAP,'--unshare-all','--die-with-parent','--new-session','--clearenv','--ro-bind','/usr','/usr','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64','--tmpfs','/tmp','--ro-bind',str(ENV),str(ENV),'--ro-bind',str(BASE),'/app','--proc','/proc','--dev','/dev','--dir','/home','--dir','/etc','--setenv','LANG','C.UTF-8','--setenv','LC_ALL','C.UTF-8','--setenv','TZ','UTC','--setenv','PATH','/usr/bin','--setenv','PYTHONPATH','/app/vendor','--chdir','/app','--',sys.executable,'/app/parser_child.py',str(projection_limit)]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={},start_new_session=True)
 sel=selectors.DefaultSelector();buffers={p.stdout:bytearray(),p.stderr:bytearray()};deadline=time.monotonic()+timeout;sent=0;total=0
 try:
  for f in (p.stdin,p.stdout,p.stderr):os.set_blocking(f.fileno(),False)
  sel.register(p.stdin,selectors.EVENT_WRITE)
  for f in buffers:sel.register(f,selectors.EVENT_READ)
  while sel.get_map():
   remaining=deadline-time.monotonic()
   if remaining<=0:raise ParserRefused('Parser wall budget')
   for k,_ in sel.select(min(remaining,.1)):
    f=k.fileobj
    if f is p.stdin:
     try:n=os.write(f.fileno(),blob[sent:sent+65536])
     except BrokenPipeError:n=0;sent=len(blob)
     sent+=n
     if sent>=len(blob):sel.unregister(f);f.close()
    else:
     data=os.read(f.fileno(),65536)
     if not data:sel.unregister(f);continue
     total+=len(data)
     if total>1048576:raise ParserRefused('Parser output budget')
     buffers[f].extend(data)
  p.wait(timeout=max(.001,deadline-time.monotonic()))
  if p.returncode!=0 or buffers[p.stderr]:raise ParserRefused('Isolated parser refused')
  out=json.loads(buffers[p.stdout])
  expected={'scope','entries','entry_count','bozo','input_sha256','network_namespace','delivery'}
  if type(out)is not dict or set(out)!=expected or out['scope']!='inactive_arbitrary_utf8_bytes_parser' or out['input_sha256']!=hashlib.sha256(blob).hexdigest() or type(out['entry_count'])is not int or not 0<=out['entry_count']<=1000 or type(out['bozo'])is not bool or out['network_namespace']!='loopback_only' or out['delivery']is not False or type(out['entries'])is not list or len(out['entries'])!=min(projection_limit,out['entry_count']):raise ParserRefused('Parser protocol refused')
  for row in out['entries']:
   if type(row)is not dict or set(row)-{'title','link','summary','description','published','updated'} or any(type(v)is not str or len(v)>10000 for v in row.values()):raise ParserRefused('Entry protocol refused')
  return out
 except (OSError,ValueError,subprocess.TimeoutExpired):raise ParserRefused('Parser refused')from None
 finally:
  if p.poll()is None:
   try:os.killpg(p.pid,signal.SIGKILL)
   except ProcessLookupError:pass
  p.wait();sel.close()
  for f in (p.stdin,p.stdout,p.stderr):
   if not f.closed:f.close()
