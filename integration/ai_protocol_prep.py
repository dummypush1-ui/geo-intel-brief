"""Pure protocol/fake-provider candidate. No sockets, routes, keys, env or logs."""
import json,hmac,re,html
class Refused(ValueError):pass
class Timeout(Exception):pass
MODEL='review-fixture-model'
def secret_equal(expected,received):
 return type(expected)is bytes and type(received)is bytes and bool(expected) and len(expected)==len(received) and hmac.compare_digest(expected,received)
def decode(chunks,content_type):
 if content_type!='application/json':raise Refused('content_type')
 data=bytearray()
 for chunk in chunks:
  if type(chunk)is not bytes:raise Refused('bytes')
  if len(data)+len(chunk)>16384:raise Refused('413')
  data.extend(chunk)
 try:
  def unique(pairs):
   out={}
   for k,v in pairs:
    if k in out:raise Refused('duplicate_field')
    out[k]=v
   return out
  obj=json.loads(data,object_pairs_hook=unique)
 except Refused:raise
 except (ValueError,UnicodeDecodeError):raise Refused('json')
 if type(obj)is not dict or set(obj)!={'question','evidence','model'} or obj['model']!=MODEL:raise Refused('schema')
 q=obj['question'];ev=obj['evidence']
 if type(q)is not str or not 1<=len(q)<=1000 or type(ev)is not list or len(ev)>4:raise Refused('bounded_question')
 for row in ev:
  if type(row)is not dict or set(row)!={'id','text'} or type(row['id'])is not str or not re.fullmatch('[a-f0-9]{64}',row['id']) or type(row['text'])is not str or len(row['text'])>2000:raise Refused('public_evidence')
 return obj
def response(chunks):
 data=bytearray()
 for chunk in chunks:
  if type(chunk)is not bytes or len(data)+len(chunk)>65536:raise Refused('response_cap')
  data.extend(chunk)
 try:s=data.decode('utf-8')
 except UnicodeError:raise Refused('response_encoding')
 if len(s)>4000:raise Refused('text_cap')
 # Plain displayed text only. No model-supplied links/HTML become links/actions.
 return re.sub(r'https?://\S+','[unverified link removed]',s)
def render(s):return html.escape(s,quote=True)
class Budget:
 """Fixture counter only, NOT durable production spend control."""
 def __init__(self,n=2):self.remaining=n
 def reserve(self):
  if self.remaining<=0:raise Refused('quota')
  self.remaining-=1
class Adapter:
 def __init__(self,provider,budget,*,enabled=False):self.provider=provider;self.budget=budget;self.enabled=enabled
 def routes(self):return ('/fixture-ai',) if self.enabled else ()
 def call(self,obj,*,origin=None):
  if not self.enabled:return {'state':'disabled'},403
  if origin is not None:return {'state':'browser_origin_refused'},403
  try:self.budget.reserve()
  except Refused:return {'state':'quota'},429
  try:
   # Exactly one fake/injected call, no key/model fallback or retry.
   raw=self.provider(obj)
   return {'state':'answer','text':response(raw),'headers':{}},200
  except Timeout:return {'state':'timeout_budget_spent'},503
  except Exception:return {'state':'provider_refused_budget_spent'},503
