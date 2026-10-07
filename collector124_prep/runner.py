"""Candidate bounded network-worker supervisor. No automatic fetch.
Fixed installation path, cleared env, -I Python, process-group kill/reap. This is
resource containment for trusted fixed code, NOT arbitrary-code sandboxing or
filesystem confidentiality. Parent enforces the WHOLE budget including DNS.
"""
import base64,hashlib,json,os,selectors,signal,subprocess,sys,time,math
from pathlib import Path
from collector113_prep.transport_policy import endpoint_plan
BASE=Path(__file__).resolve().parent
MAX_OUTPUT=2097152
FILE_PINS={'worker.py': 'a76a03022b899e5dd193a5603776677119a2bceb4a462d159990d5c24219e728', 'connector.py': 'a8713839ccb0b25b0f5e683451b2886f119f0e788b80b4493b0e647d92652f58'}
POLICY_PIN='f48111d937582161ffd7e52acb2ea8afaa1b26ed7198903cdb0a3506f1a9be7c'
class FetchRefused(ValueError):pass

def _command():
 return [sys.executable,'-I',str(BASE/'worker.py')]

def run_fetch(feeds,url,*,timeout=20):
 if type(timeout)not in (int,float) or not math.isfinite(timeout) or not 0<timeout<=30:
  raise FetchRefused('Timeout shape')
 for name, expected in FILE_PINS.items():
  if hashlib.sha256((BASE/name).read_bytes()).hexdigest()!=expected:raise FetchRefused('Worker source drift')
 if hashlib.sha256((BASE.parent/'collector113_prep/transport_policy.py').read_bytes()).hexdigest()!=POLICY_PIN:raise FetchRefused('Transport policy drift')
 endpoint_plan(feeds,url,('8.8.8.8',),'8.8.8.8')
 raw=json.dumps({'feeds':feeds,'url':url,'timeout':timeout},separators=(',',':')).encode()
 if len(raw)>131072:raise FetchRefused('Input budget')
 deadline=time.monotonic()+timeout
 p=None;sel=selectors.DefaultSelector();buffers={};sent=0;total=0
 try:
  p=subprocess.Popen(_command(),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                     env={'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC'},cwd=str(BASE),start_new_session=True)
  buffers={p.stdout:bytearray(),p.stderr:bytearray()}
  for f in (p.stdin,p.stdout,p.stderr):os.set_blocking(f.fileno(),False)
  sel.register(p.stdin,selectors.EVENT_WRITE)
  for f in buffers:sel.register(f,selectors.EVENT_READ)
  while sel.get_map():
   remaining=deadline-time.monotonic()
   if remaining<=0:raise FetchRefused('Whole-fetch wall budget')
   for key,_ in sel.select(min(remaining,.1)):
    f=key.fileobj
    if f is p.stdin:
     try:n=os.write(f.fileno(),raw[sent:sent+65536])
     except BrokenPipeError:n=0;sent=len(raw)
     sent+=n
     if sent>=len(raw):sel.unregister(f);f.close()
    else:
     data=os.read(f.fileno(),65536)
     if not data:sel.unregister(f);continue
     total+=len(data)
     if total>MAX_OUTPUT:raise FetchRefused('Combined worker output budget')
     buffers[f].extend(data)
  p.wait(timeout=max(.001,deadline-time.monotonic()))
  if p.returncode!=0 or buffers[p.stderr]:raise FetchRefused('Network worker refused')
  envelope=json.loads(buffers[p.stdout])
  if type(envelope)is not dict or set(envelope)!={'ok','result'} or envelope['ok']is not True:
   raise FetchRefused('Worker envelope')
  r=envelope['result']
  keys={'scope','url','body_b64','wire_bytes','decoded_bytes','hostname','peer','tls_hostname_verified','redirects','delivery'}
  if type(r)is not dict or set(r)!=keys or r['scope']!='inactive_https_connector_candidate' or r['url']!=url or r['tls_hostname_verified']is not True or r['redirects']is not False or r['delivery']is not False:
   raise FetchRefused('Worker protocol')
  if type(r['body_b64'])is not str or len(r['body_b64'])>1398104:raise FetchRefused('Encoded byte budget')
  blob=base64.b64decode(r['body_b64'],validate=True)
  if not 1<=len(blob)<=1048576 or type(r['decoded_bytes'])is not int or r['decoded_bytes']!=len(blob) or type(r['wire_bytes'])is not int or not 1<=r['wire_bytes']<=1048576:
   raise FetchRefused('Worker body/count protocol')
  plan=endpoint_plan(feeds,url,(r['peer'],),r['peer'])
  if r['hostname']!=plan['hostname']:raise FetchRefused('Worker hostname protocol')
  return {'bytes':blob,'input_sha256':hashlib.sha256(blob).hexdigest(),'wire_bytes':r['wire_bytes'],
          'url':url,'peer':r['peer'],'tls_hostname_verified':True,'delivery':False}
 except (OSError,ValueError,TypeError,subprocess.TimeoutExpired):
  raise FetchRefused('Network worker refused')from None
 finally:
  if p is not None:
   if p.poll()is None:
    try:os.killpg(p.pid,signal.SIGKILL)
    except ProcessLookupError:pass
   p.wait()
   for f in (p.stdin,p.stdout,p.stderr):
    if f is not None and not f.closed:f.close()
  sel.close()
