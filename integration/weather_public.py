"""W2 candidate, default-OFF manual land forecast. No activation or DB.
One thread may outlive its caller on DNS/OS hangs; slot stays held until exit.
200/day is resettable worker memory, NOT a durable/site aggregate guarantee.
"""
import copy,http.client,json,ssl,threading,time
from datetime import datetime,timezone
from urllib.parse import urlsplit
from integration.weather_public_prep import PORTS,typed,display,params,url,verify_catalogue,Refused
PATH='/api/public-weather'
WMO=frozenset((0,1,2,3,45,48,51,53,55,56,57,61,63,65,66,67,71,73,75,77,80,81,82,85,86,95,96,99))
class Limited(Exception):pass
class Unavailable(Exception):pass

def parse(place,raw,fetched):
 if type(raw)is not bytes or len(raw)>65536:raise Refused('Bounded response bytes')
 def unique(pairs):
  d={}
  for k,v in pairs:
   if k in d:raise Refused('Duplicate JSON key')
   d[k]=v
  return d
 try:data=json.loads(raw,object_pairs_hook=unique)
 except (ValueError,UnicodeError,RecursionError):raise Refused('Invalid response JSON')from None
 obj=typed(place,data,fetched_at=fetched)
 w=obj['values']['weather_code']['value']
 if w is not None and w not in WMO:raise Refused('Unsupported WMO code')
 return obj

def fetch(place,deadline,clock=time.monotonic):
 """Fixed HTTPS, no redirects/proxy/cookies/auth, bounded stream before parse.
 DNS may block beyond socket timeout. Caller holds slot until this exits.
 """
 p=urlsplit(url(place));connection=None
 def remaining():
  value=deadline-clock()
  if value<=0:raise Unavailable('Weather deadline')
  return value
 try:
  context=ssl.create_default_context()
  connection=http.client.HTTPSConnection('api.open-meteo.com',443,timeout=remaining(),context=context)
  # Split TCP/DNS from TLS so a slow TCP connect does not give TLS another
  # full five seconds. Fixed host, no tunnel, standard verified TLS context.
  http.client.HTTPConnection.connect(connection)
  connection.sock.settimeout(remaining())
  connection.sock=context.wrap_socket(connection.sock,server_hostname='api.open-meteo.com')
  sock=connection.sock
  sock.settimeout(remaining())
  connection.request('GET',p.path+'?'+p.query,headers={'Accept':'application/json','User-Agent':'GeoIntel-Weather/1'})
  sock.settimeout(remaining());response=connection.getresponse()
  if response.status!=200 or response.getheader('Content-Type','').split(';',1)[0].strip().lower()!='application/json':raise Unavailable('Weather response refused')
  raw=bytearray()
  while True:
   sock.settimeout(remaining());chunk=response.read1(min(8192,65537-len(raw)))
   remaining()
   if not chunk:break
   raw.extend(chunk)
   if len(raw)>65536:raise Unavailable('Weather byte cap')
  return bytes(raw)
 finally:
  if connection is not None:connection.close()

class Service:
 def __init__(self,transport=fetch,clock=time.monotonic,utcnow=lambda:datetime.now(timezone.utc),wall=time.time,deadline_seconds=5):
  self.transport=transport;self.clock=clock;self.utcnow=utcnow;self.wall=wall;self.deadline_seconds=deadline_seconds
  self.lock=threading.Lock();self.slot=threading.BoundedSemaphore(1);self.cache={};self.failures={};self.window=None;self.requests=0;self.day=None;self.attempts=0
 def _stale(self,place):
  cached=self.cache.get(place)
  if cached:
   try:return dict(display(copy.deepcopy(cached[1]),now=self.utcnow()),freshness='stale_forecast',provider_unavailable=True)
   except Refused:pass
  raise Unavailable('Weather unavailable')
 def get(self,place):
  if place not in PORTS:raise Refused('Unknown place')
  now=self.clock()
  with self.lock:
   minute=int(self.wall()//60)
   if minute!=self.window:self.window=minute;self.requests=0
   self.requests+=1
   if self.requests>10:raise Limited('Manual request quota')
   cached=self.cache.get(place)
   if cached and now-cached[0]<900:return display(copy.deepcopy(cached[1]),now=self.utcnow())
   failed=self.failures.get(place)
   if failed is not None and now-failed<15:return self._stale(place)
   if not self.slot.acquire(False):raise Limited('Provider busy')
   day=int(self.wall()//86400)
   if day!=self.day:self.day=day;self.attempts=0
   if self.attempts>=200:self.slot.release();raise Limited('Worker daily quota')
   self.attempts+=1
  deadline=now+self.deadline_seconds;event=threading.Event();result={}
  def worker():
   try:
    raw=self.transport(place,deadline,self.clock)
    obj=parse(place,raw,self.utcnow())
    if self.clock()>deadline:raise Unavailable('Weather deadline')
    with self.lock:self.cache[place]=(self.clock(),copy.deepcopy(obj));self.failures.pop(place,None);result['obj']=obj
   except Exception:
    with self.lock:self.failures[place]=self.clock();result['failed']=True
   finally:self.slot.release();event.set()
  thread=threading.Thread(target=worker,name='public-weather',daemon=True)
  try:thread.start()
  except Exception:
   self.slot.release()
   with self.lock:self.failures[place]=self.clock()
   raise Unavailable('Weather worker unavailable')from None
  if not event.wait(self.deadline_seconds):
   # No cancellation or slot release while thread still runs.
   with self.lock:return self._stale(place)
  if 'obj' in result:return display(copy.deepcopy(result['obj']),now=self.utcnow())
  with self.lock:return self._stale(place)

def enabled(env):
 flag=env.get('PUBLIC_WEATHER_ENABLED','false')
 if flag not in ('true','false'):raise ValueError('Exact weather flag')
 if flag=='false':return False
 required={'OPEN_METEO_TERMS_ACK':'2026-10-11/noncommercial','PUBLIC_WEATHER_NONCOMMERCIAL':'true','PUBLIC_WEATHER_CAPACITY_REVIEWED':'true','PUBLIC_WEATHER_SINGLE_WORKER_VERIFIED':'true'}
 if any(env.get(k)!=v for k,v in required.items()):raise ValueError('Weather terms/noncommercial/capacity gate')
 return True

def install_if_enabled(app,origin,env,factory=Service,source_path=None):
 if not enabled(env):return False
 if source_path is None:raise ValueError('Reviewed catalogue source required')
 verify_catalogue(source_path)
 service=factory()
 from flask import request,Response,jsonify
 @app.route(PATH,methods=['GET','HEAD'])
 def weather():
  if request.method=='HEAD':return Response(status=200)
  if request.headers.get('Sec-Fetch-Site')!='same-origin' or request.headers.get('Origin')not in (None,origin):return jsonify(error='Same-origin manual requests required'),403
  try:
   if len(request.query_string)>32:raise Refused('Query cap')
   place=params(list(request.args.items(multi=True)))
   return jsonify(service.get(place))
  except Refused:return jsonify(error='Invalid weather request'),400
  except Limited:return jsonify(error='Weather busy; retry manually later'),429,{'Retry-After':'60'}
  except Unavailable:return jsonify(error='Weather unavailable'),503
  except Exception:return jsonify(error='Weather unavailable'),503
 @app.after_request
 def weather_headers(response):
  if request.path==PATH:
   response.headers['Cache-Control']='no-store';response.headers['X-Content-Type-Options']='nosniff';response.headers['Referrer-Policy']='no-referrer'
  return response
 app.extensions['public_weather']=service
 return True
