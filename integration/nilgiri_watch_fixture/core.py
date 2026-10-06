"""Trusted injected offline fixture ONLY. No HTTP transport, persistence or activation."""
import copy,datetime as dt,re,threading
from integration.page_watch import snapshot,validate_snapshot,compare
HOME='https://nilgiried.com/'
ROBOTS=HOME+'robots.txt'
POLICY='nilgiri92v1'
UTC=dt.timezone.utc
class Refusal(ValueError):pass
def clock(x):
 if type(x)is not dt.datetime or type(x.tzinfo)is not dt.timezone or x.utcoffset()!=dt.timedelta(0)or not 1970<=x.year<=2100:raise Refusal('clock')
 return x
def opaque(x):
 if type(x)is not str or len(x.encode('utf-8'))>1024 or any(ord(c)<32 or ord(c)==127 for c in x):raise Refusal('validator')
 return x
def response(r):
 if type(r)is not dict or set(r)!={'status','headers','body'}:raise Refusal('response_schema')
 s,h,b=r['status'],r['headers'],r['body']
 if type(s)is not int or not 100<=s<=599 or type(h)is not dict or len(h)>32 or type(b)is not bytes or len(b)>131072:raise Refusal('response_bounds')
 headers={};size=0
 for k,v in h.items():
  if type(k)is not str or not re.fullmatch(r"[A-Za-z0-9!#$%&'*+.^_`|~-]{1,64}",k):raise Refusal('header_name')
  v=opaque(v);size+=len(k.encode())+len(v.encode());key=k.lower()
  if key in headers or size>8192:raise Refusal('header_bounds')
  headers[key]=v
 if headers.get('content-encoding','identity').lower()!='identity':raise Refusal('compression_unsupported')
 if 'content-length'in headers:
  n=headers['content-length']
  if not n.isdecimal()or len(n)>8 or int(n)!=len(b):raise Refusal('content_length')
 try:text=b.decode('utf-8','strict')
 except UnicodeError:raise Refusal('utf8')
 return s,headers,text

def baseline(b,now):
 if type(b)is not dict or set(b)!={'source','policy','revision','snapshot','validators','checked_at'}:raise Refusal('baseline_schema')
 if b['source']!=HOME or b['policy']!=POLICY or type(b['revision'])is not int or not 1<=b['revision']<=2**53:raise Refusal('baseline_identity')
 raw=b['snapshot']
 if type(raw)is not dict or set(raw)!={'url','observed_at','text','sha256','method'}:raise Refusal('snapshot_schema')
 if any(type(raw[k])is not str for k in raw):raise Refusal('snapshot_type')
 # Limits checked before generic validation, hashing, copying or comparison.
 if len(raw['text'])>131072 or len(raw['text'].encode('utf-8'))>131072:raise Refusal('retained_text_bounds')
 if any(len(raw[k])>2048 for k in raw if k!='text'):raise Refusal('retained_field_bounds')
 sn=validate_snapshot(raw)
 if sn!=b['snapshot'] or sn['url']!=HOME:raise Refusal('baseline_canonical')
 observed=dt.datetime.fromisoformat(sn['observed_at']);checked=clock(b['checked_at'])
 if observed>now or checked>now or checked<observed:raise Refusal('baseline_clock')
 v=b['validators']
 if type(v)is not dict or not set(v)<= {'etag','last-modified'}:raise Refusal('baseline_validators')
 for value in v.values():opaque(value)
 total=sum(len(x.encode('utf-8'))for x in raw.values())+len(HOME.encode())+len(POLICY.encode())+len(str(b['revision']))+sum(len(k.encode())+len(value.encode())for k,value in v.items())+len(checked.isoformat())
 if total>131072:raise Refusal('retained_aggregate_bounds')
 return copy.deepcopy(b)

class MemoryFixtureStore:
 """Atomic trusted fake only. No DB/files/network."""
 def __init__(self):
  self.lock=threading.Lock();self.minimum_interval=3600;self.version=0;self.active=None;self.last=None;self.content=None;self.state='requested-on-not-running';self.reason='transport_not_wired'
 def begin(self,now,interval):
  with self.lock:
   clock(now)
   interval=max(interval,self.minimum_interval);self.minimum_interval=interval
   if self.last is not None:
    clock(self.last)
    if now<self.last:raise Refusal('clock_rollback')
   if self.state in ('paused','stopped'):return None,self.state,self.reason
   if self.active is not None:return None,'paused','active_attempt'
   if self.last is not None and (now-self.last).total_seconds()<interval:return None,'eligible','cadence'
   if self.content is not None:baseline(self.content,now)
   self.version+=1;token=self.version;self.active=token;self.last=now
   return (token,copy.deepcopy(self.content)),'eligible','reserved'
 def finish(self,token,content,state,reason):
  with self.lock:
   if self.active!=token or self.version!=token:return False
   # CAS atomically updates latest revision + state. Source cadence stays consumed.
   self.content=copy.deepcopy(content);self.state=state;self.reason=reason;self.active=None;self.version+=1;return True
 def inspect(self):
  with self.lock:return copy.deepcopy({'version':self.version,'active':self.active,'last':self.last,'content':self.content,'state':self.state,'reason':self.reason})

def cycle(store,fetch,now,*,enabled=False,fixture_wired=False,interval=3600):
 """fetch fixedURL, closed generatedconditionalheaders -> trusted fake response."""
 if type(enabled)is not bool or type(fixture_wired)is not bool:raise Refusal('flags')
 if not enabled:return {'state':'disabled','reason':'off','outcome':'refusal','alert':None}
 if not fixture_wired:return {'state':'requested-on-not-running','reason':'transport_not_wired','outcome':'refusal','alert':None}
 if type(interval)is not int or not 3600<=interval<=604800:raise Refusal('interval')
 clock(now)
 try:reserved,state,reason=store.begin(now,interval)
 except Exception:return {'state':'paused','reason':'store_or_clock_uncertain','outcome':'refusal','alert':None}
 if reserved is None:return {'state':state,'reason':reason,'outcome':'refusal','alert':None}
 token,old=reserved;new=old;state='eligible';reason='checked';outcome='unchanged';alert=None
 try:
  s,h,t=response(fetch(ROBOTS,{}))
  if s in(403,429):state='stopped';raise Refusal('robots_block_or_rate')
  if s!=404:state='paused';raise Refusal('conservative_policy_pause'if s==200 else 'robots_uncertain')
  sent={}
  if old is not None:
   old=baseline(old,now)
   age=(now-old['checked_at']).total_seconds();obs=dt.datetime.fromisoformat(old['snapshot']['observed_at'])
   if age<=86400 and (now-obs).total_seconds()<=604800:
    if old['validators'].get('etag'):sent['If-None-Match']=old['validators']['etag']
    if old['validators'].get('last-modified'):sent['If-Modified-Since']=old['validators']['last-modified']
  # immutable copy prevents fake collaborator silently rewriting generated headers
  expected=copy.deepcopy(sent)
  s,h,t=response(fetch(HOME,copy.deepcopy(sent)))
  if s in(403,429):state='stopped';raise Refusal('page_block_or_rate')
  if s==304:
   if old is None or not expected or t:raise Refusal('unconditional_or_body_304')
   for key,value in [('etag','If-None-Match'),('last-modified','If-Modified-Since')]:
    if key in h and (value not in expected or h[key]!=expected[value]):raise Refusal('mismatched_304_validator')
   new=copy.deepcopy(old);new['checked_at']=now;outcome='checked_unchanged'
  elif s==200:
   if 'html'not in h.get('content-type','').lower():raise Refusal('not_html')
   if any(marker in t.lower()for marker in ['captcha','cloudflare','access denied','verify you are human','cf-chl-','too many requests']):state='stopped';raise Refusal('challenge')
   sn=snapshot(HOME,t,now.isoformat());validators={k:h[k]for k in('etag','last-modified')if k in h}
   probe={'source':HOME,'policy':POLICY,'revision':1 if old is None else old['revision']+1,'snapshot':sn,'validators':validators,'checked_at':now};baseline(probe,now)
   if old is not None:
    if len(old['snapshot']['text'].encode())+len(sn['text'].encode())+sum(len(v.encode())for v in validators.values())+sum(len(v.encode())for v in old['validators'].values())+16000>262144:raise Refusal('combined_retained_output_bounds')
    change=compare(old['snapshot'],sn);outcome='changed'if change['state']=='changed'else 'unchanged'
    if outcome=='changed':alert=change
   else:outcome='first_baseline'
   new={'source':HOME,'policy':POLICY,'revision':1 if old is None else old['revision']+1,'snapshot':sn,'validators':validators,'checked_at':now};baseline(new,now)
  else:raise Refusal('page_status')
 except Exception as e:
  reason=str(e)if type(e)is Refusal else 'fetch_or_parser_uncertain';state=state if state=='stopped'else 'paused';new=old;outcome='refusal';alert=None
 if alert is not None and len(repr(alert).encode())>16000:
  state='paused';reason='output_bounds';outcome='refusal';new=old;alert=None
 try:committed=store.finish(token,new,state,reason)
 except Exception:return {'state':'paused','reason':'store_commit_uncertain','outcome':'refusal','alert':None}
 if not committed:return {'state':'paused','reason':'commit_conflict','outcome':'commit-conflict','alert':None}
 # Bounded alerts are existing compare format. Never send/store external content outside fixture.
 return {'state':state,'reason':reason,'outcome':outcome,'alert':alert}
