"""Default-OFF fixed bounded transport and one-shot receipt composition.
No clients/providers/catalog enabling/mount. Fixtures only until owner live grant.
"""
import sys,json,base64,subprocess,time,hashlib,selectors,os,signal
from pathlib import Path
from integration.finder198_connector import validate_backend,plan_ai,plan_ships,ConnectorRefused,MAX_REQUEST_BYTES,MAX_RESPONSE_BYTES,FIXED_BASE
from integration.finder198_receipts import ProxyReceiptBudget
ROOT=Path(__file__).resolve().parents[1]
class TransportRefused(ValueError):pass
CHILD_PIN='f0033e40c26ea4c787e0a465cab32f26881244d8916d4226e737abf2f0f2e918'
def _plan(op,provider,model,port,now):
 if op=='ai'and port is None:return plan_ai(provider,model,now=now)
 if op=='ships'and provider is None and model is None:return plan_ships(port)
 raise TransportRefused('Closed operation required')
class FixedProxyTransport:
 def __init__(self,values,*,enabled=False):
  if type(enabled)is not bool:raise TransportRefused('Exact transport switch required')
  self.enabled=enabled;self._secret=None
  if enabled:validate_backend(values);self._secret=values['FINDER_PROXY_SECRET']
 def execute(self,plan,body):
  if not self.enabled:raise TransportRefused('Transport disabled')
  if type(plan)is not dict or plan.get('base')!=FIXED_BASE or plan.get('redirects')is not False or plan.get('retries')!=0 or plan.get('timeout_seconds')!=20:raise TransportRefused('Exact fixed plan required')
  # Reconstruct permitted path from reviewed catalog/closed port constants.
  if plan.get('method')=='GET':expected=plan_ships(plan.get('path','').removeprefix('/ships?port='))
  else:expected=plan_ai(plan.get('provider'),plan.get('model'),now=int(time.time()))
  if plan!=expected or type(body)is not bytes or len(body)>MAX_REQUEST_BYTES or (plan['method']=='GET'and body):raise TransportRefused('Closed request bytes required')
  child=ROOT/'integration/finder198_transport_child.py'
  if hashlib.sha256(child.read_bytes()).hexdigest()!=CHILD_PIN:raise TransportRefused('Transport installation drift')
  raw=json.dumps({'path':plan['path'],'method':plan['method'],'body_b64':base64.b64encode(body).decode('ascii'),'secret':self._secret},separators=(',',':')).encode()
  p=None;sel=selectors.DefaultSelector();end=time.monotonic()+20;buffers={};sent=0
  try:
   p=subprocess.Popen([sys.executable,'-I',str(child)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={},cwd=str(ROOT),start_new_session=True)
   buffers={p.stdout:bytearray(),p.stderr:bytearray()}
   for f in (p.stdin,p.stdout,p.stderr):os.set_blocking(f.fileno(),False)
   sel.register(p.stdin,selectors.EVENT_WRITE)
   for f in buffers:sel.register(f,selectors.EVENT_READ)
   while sel.get_map():
    if time.monotonic()>=end:raise ValueError()
    for key,_ in sel.select(.05):
     f=key.fileobj
     if f is p.stdin:
      try:n=os.write(f.fileno(),raw[sent:])
      except BrokenPipeError:raise ValueError()
      sent+=n
      if sent>=len(raw):sel.unregister(f);f.close()
     else:
      chunk=os.read(f.fileno(),65536)
      if not chunk:sel.unregister(f)
      else:buffers[f].extend(chunk)
      if len(buffers[f])>(1500000 if f is p.stdout else 4096):raise ValueError()
   p.wait(timeout=max(.001,end-time.monotonic()))
   if p.returncode!=0 or buffers[p.stderr]or time.monotonic()>=end:raise ValueError()
   out=json.loads(buffers[p.stdout])
   if type(out)is not dict or set(out)!={'status','body_b64'}or type(out['status'])is not int or not 200<=out['status']<=599 or 300<=out['status']<=399:raise ValueError()
   wire=base64.b64decode(out['body_b64'],validate=True)
   if len(wire)>MAX_RESPONSE_BYTES or self._secret in wire.decode('utf-8')or self._secret in json.dumps(json.loads(wire),ensure_ascii=False):raise ValueError()
   return {'status':out['status'],'body':wire}
  except Exception:raise TransportRefused('Proxy outcome unknown; no retry')from None
  finally:
   if p is not None:
    if p.poll()is None:
     try:os.killpg(p.pid,signal.SIGKILL)
     except ProcessLookupError:pass
    p.wait()
    for f in (p.stdin,p.stdout,p.stderr):
     if not f.closed:f.close()
   sel.close()

def proxy_request(budget,transport,*,nonce,operation,provider=None,model=None,port=None,body=b'',principal_hash=None,clock):
 if type(budget)is not ProxyReceiptBudget or type(transport)is not FixedProxyTransport or not callable(clock):raise TransportRefused('Exact injected broker adapters required')
 if not transport.enabled:raise TransportRefused('Transport disabled')
 if type(principal_hash)is not str or len(principal_hash)!=64 or any(c not in '0123456789abcdef'for c in principal_hash):raise TransportRefused('Authenticated principal scope required')
 if type(body)is not bytes or len(body)>MAX_REQUEST_BYTES:raise TransportRefused('Bounded request bytes required')
 plan=_plan(operation,provider,model,port,clock())
 if operation=='ships'and body:raise TransportRefused('No ships request body')
 if operation=='ai':json.loads(body) # structural/provider schema validation remains later mount work
 identity=hashlib.sha256(json.dumps({'principal_hash':principal_hash,'operation':operation,'provider':provider,'model':model,'port':port},sort_keys=True,separators=(',',':')).encode()).hexdigest()
 claim=budget.claim(nonce,hashlib.sha256(body).hexdigest(),identity,clock())
 if claim['state']=='replay_status_only':return claim
 ticket=budget.start(claim['receipt'],clock())
 try:
  out=transport.execute(plan,body)
  receipt=budget.finish(ticket,clock(),status=out['status'],response_hash=hashlib.sha256(out['body']).hexdigest(),response_bytes=len(out['body']))
  if receipt['phase']!='complete':raise TransportRefused('Late proxy outcome held')
  return {'state':'complete','status':out['status'],'body':out['body']}
 except Exception:
  try:budget.hold(ticket,clock())
  except Exception:pass
  raise TransportRefused('Proxy request held; no automatic retry')from None
