import copy,json,threading,time,unittest
from unittest.mock import patch
from datetime import datetime,timezone,timedelta
from flask import Flask
from integration.weather_public import *
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
from integration.weather_public_prep import UNITS
BASE='https://preview.example'
def raw(code=0):return json.dumps(dict(timezone='GMT',utc_offset_seconds=0,current_units=UNITS,current=dict(time='2026-10-11T00:00',interval=900,temperature_2m=25,relative_humidity_2m=50,weather_code=code,wind_speed_10m=10,wind_direction_10m=0))).encode()
def env():return dict(PUBLIC_WEATHER_ENABLED='true',OPEN_METEO_TERMS_ACK='2026-10-11/noncommercial',PUBLIC_WEATHER_NONCOMMERCIAL='true',PUBLIC_WEATHER_CAPACITY_REVIEWED='true',PUBLIC_WEATHER_SINGLE_WORKER_VERIFIED='true')
class Tests(unittest.TestCase):
 def service(self,transport=None):
  self.t=0;self.wall=0;self.utc=datetime(2026,10,11,tzinfo=timezone.utc)
  return Service(transport=transport or(lambda *a:raw()),clock=lambda:self.t,wall=lambda:self.wall,utcnow=lambda:self.utc)
 def app(self,service):
  a=Flask(__name__);install_if_enabled(a,BASE,env(),factory=lambda:service,source_path=ROOT/'src/worldports.ts');return a.test_client()
 def test_off_no_factory(self):
  a=Flask(__name__);f=lambda:(_ for _ in ()).throw(AssertionError('factory'))
  self.assertFalse(install_if_enabled(a,BASE,{},factory=f));self.assertEqual(a.test_client().get(PATH).status_code,404)
 def test_on_gates(self):
  for k in env():
   e=env();e.pop(k)
   if k=='PUBLIC_WEATHER_ENABLED':self.assertFalse(enabled(e))
   else:
    with self.assertRaises(ValueError):enabled(e)
 def test_head_zero_io(self):
  s=self.service(lambda *a:(_ for _ in ()).throw(AssertionError('IO')));c=self.app(s)
  self.assertEqual(c.head(PATH,base_url=BASE).status_code,200);self.assertEqual(s.requests,0);self.assertEqual(s.attempts,0)
 def test_params_origin(self):
  s=self.service();c=self.app(s)
  for query in ['place=INCOK','place=INBOM&place=INBOM','place=INBOM&x=1','']:
   self.assertEqual(c.get(PATH+'?'+query,base_url=BASE,headers={'Sec-Fetch-Site':'same-origin'}).status_code,400)
  self.assertEqual(c.get(PATH+'?place=INBOM',base_url=BASE).status_code,403)
  self.assertEqual(c.get(PATH+'?place=INBOM',base_url=BASE,headers={'Sec-Fetch-Site':'same-origin','Origin':'https://evil.example'}).status_code,403)
  self.assertEqual(s.attempts,0)
 def test_copy_cache_ttl(self):
  s=self.service();a=s.get('INBOM');a['source']['name']='bad';a['values']['temperature_2m']['value']=999
  b=s.get('INBOM');self.assertEqual(b['source']['name'],'Open-Meteo');self.assertEqual(b['values']['temperature_2m']['value'],25);self.assertEqual(s.attempts,1)
  self.t=900;self.utc+=timedelta(seconds=900);s.get('INBOM');self.assertEqual(s.attempts,2)
 def test_request_quota_cache(self):
  s=self.service()
  for _ in range(10):s.get('INBOM')
  with self.assertRaises(Limited):s.get('INBOM')
  self.wall=60;s.get('INBOM');self.assertEqual(s.attempts,1)
 def test_exception_release_once_failurecache(self):
  s=self.service(lambda *a:(_ for _ in ()).throw(RuntimeError('fail')))
  for _ in range(2):
   with self.assertRaises(Unavailable):s.get('INBOM')
  self.assertEqual(s.attempts,1);self.assertTrue(s.slot.acquire(False));self.assertFalse(s.slot.acquire(False));s.slot.release()
  self.t=15
  with self.assertRaises(Unavailable):s.get('INBOM')
  self.assertEqual(s.attempts,2)
 def test_stale_boundary(self):
  s=self.service();s.get('INBOM');s.transport=lambda *a:(_ for _ in ()).throw(RuntimeError())
  self.t=901;self.utc+=timedelta(seconds=901);x=s.get('INBOM');self.assertEqual(x['freshness'],'stale_forecast');self.assertTrue(x['provider_unavailable'])
  self.t=3601;self.utc=datetime(2026,10,11,tzinfo=timezone.utc)+timedelta(seconds=3601)
  with self.assertRaises(Unavailable):s.get('INBOM')
 def test_timeout_keeps_slot_until_exit(self):
  gate=threading.Event();started=threading.Event()
  def f(*a):started.set();gate.wait(1);raise RuntimeError()
  s=self.service(f);s.deadline_seconds=.02
  start=time.monotonic()
  with self.assertRaises(Unavailable):s.get('INBOM')
  self.assertLess(time.monotonic()-start,.15);self.assertTrue(started.is_set())
  with self.assertRaises(Limited):s.get('INMAA')
  gate.set()
  for _ in range(100):
   if s.slot.acquire(False):s.slot.release();break
   time.sleep(.001)
  else:self.fail('slot not released')
 def test_daily_reset_not_durable(self):
  s=self.service();s.day=0;s.attempts=200
  with self.assertRaises(Limited):s.get('INBOM')
  self.assertTrue(s.slot.acquire(False));s.slot.release();self.wall=86400;s.get('INBOM');self.assertEqual(s.attempts,1)
 def test_wmo_duplicate_json(self):
  for b in [raw(4),b'{"a":1,"a":2}',b'x'*65537,b'<html>',raw(0).replace(b'"GMT"',b'"Europe/Berlin"')]:
   with self.assertRaises(Refused):parse('INBOM',b,datetime.now(timezone.utc))
  for code in WMO:self.assertEqual(parse('INBOM',raw(code),datetime.now(timezone.utc))['values']['weather_code']['value'],code)
 def test_transport_stages_context_status_stream_close(self):
  import ssl
  class Sock:
   def __init__(self):self.timeouts=[]
   def settimeout(self,v):self.timeouts.append(v)
  class Response:
   def __init__(self,status=200,ctype='application/json',chunks=None):self.status=status;self.ctype=ctype;self.chunks=iter(chunks or [raw(),b''])
   def getheader(self,*a):return self.ctype
   def read1(self,n):return next(self.chunks)
  class Conn:
   def __init__(self,r):self.r=r;self.sock=Sock();self.closed=0;self.requests=[]
   def request(self,*a,**kw):self.requests.append((a,kw))
   def getresponse(self):return self.r
   def close(self):self.closed+=1
  for response in [Response(302),Response(500),Response(200,'text/html'),Response(chunks=[b'x'*65537]),Response()]:
   c=Conn(response);contexts=[];wraps=[];clock=[0]
   def construct(*args,**kwargs):contexts.append(kwargs['context']);return c
   def connect(*a):clock[0]=2
   def wrap(context,sock,server_hostname):
    self.assertEqual(server_hostname,'api.open-meteo.com');self.assertEqual(sock.timeouts[-1],3);clock[0]=3;wraps.append(True);return sock
   with patch('integration.weather_public.http.client.HTTPSConnection',side_effect=construct),patch('integration.weather_public.http.client.HTTPConnection.connect',side_effect=connect),patch.object(ssl.SSLContext,'wrap_socket',new=wrap):
    if response.status!=200 or response.ctype!='application/json' or len(c.r.chunks.__reduce__()[1][0])==1:
     with self.assertRaises(Unavailable):fetch('INBOM',5,lambda:clock[0])
    else:self.assertEqual(fetch('INBOM',5,lambda:clock[0]),raw())
   self.assertEqual(c.closed,1);self.assertEqual(len(c.requests),1);self.assertEqual(len(wraps),1)
   self.assertTrue(contexts[0].check_hostname);self.assertEqual(contexts[0].verify_mode,ssl.CERT_REQUIRED)
   self.assertEqual(c.sock.timeouts[:3],[3,2,2])
 def test_exact_cache_900(self):
  s=self.service();s.get('INBOM');self.t=899;self.utc+=timedelta(seconds=899);s.get('INBOM');self.assertEqual(s.attempts,1)
  self.t=900;self.utc+=timedelta(seconds=1);s.get('INBOM');self.assertEqual(s.attempts,2)
 def test_late_result_not_cached(self):
  s=self.service()
  def transport(*a):self.t=6;return raw()
  s.transport=transport
  with self.assertRaises(Unavailable):s.get('INBOM')
  self.assertNotIn('INBOM',s.cache)
 def test_copy_on_put(self):
  s=self.service();obj=parse('INBOM',raw(),self.utc)
  with patch('integration.weather_public.parse',return_value=obj):s.get('INBOM')
  obj['source']['name']='evil';obj['values']['temperature_2m']['value']=888
  x=s.get('INBOM');self.assertEqual(x['source']['name'],'Open-Meteo');self.assertEqual(x['values']['temperature_2m']['value'],25)
 def test_thread_start_failure_release(self):
  s=self.service()
  with patch('integration.weather_public.threading.Thread.start',side_effect=RuntimeError('secret traceback')):
   with self.assertRaises(Unavailable):s.get('INBOM')
  self.assertTrue(s.slot.acquire(False));self.assertFalse(s.slot.acquire(False));s.slot.release();self.assertEqual(s.attempts,1)
 def test_duplicate_valid_json(self):
  data=raw().replace(b'"timezone": "GMT"',b'"timezone":"BAD","timezone":"GMT"')
  with self.assertRaises(Refused):parse('INBOM',data,datetime.now(timezone.utc))
 def test_bytecap_before_parse(self):
  with patch('integration.weather_public.json.loads',side_effect=AssertionError('must not parse')):
   with self.assertRaises(Refused):parse('INBOM',b' '*65537,datetime.now(timezone.utc))
 def test_response_headers_querycap_unexpectedexception(self):
  s=self.service();c=self.app(s);h={'Sec-Fetch-Site':'same-origin'}
  x=c.get(PATH+'?place=INBOM'+(' '*33),base_url=BASE,headers=h);self.assertEqual(x.status_code,400);self.assertEqual(s.attempts,0)
  s.get=lambda p:(_ for _ in ()).throw(RuntimeError('PRIVATE_TRACEBACK'))
  x=c.get(PATH+'?place=INBOM',base_url=BASE,headers=h);self.assertEqual(x.status_code,503);self.assertEqual(x.json,{'error':'Weather unavailable'});self.assertNotIn(b'PRIVATE',x.data);self.assertEqual(x.headers['Cache-Control'],'no-store')
  self.assertEqual(c.head(PATH,base_url=BASE).headers['Cache-Control'],'no-store')
class BuilderTests(unittest.TestCase):
 def base(self):return dict(PREVIEW_PUBLIC_SAMPLE_ENABLED='true',PREVIEW_GEO_ONLY_ENABLED='true',PREVIEW_ACCESS_ENABLED='false',NEWS_READ_ENABLED='false',NEWS_EVENTS_READ_ENABLED='false',FINDER_NETWORK_PREVIEW_ENABLED='false',PREVIEW_ORIGIN=BASE)
 def test_sample_off_no_factory(self):
  from integration.public_preview_builder import build_public_preview
  with patch('integration.weather_public.Service',side_effect=AssertionError('factory')),patch('integration.weather_public.verify_catalogue',side_effect=AssertionError('pin')):
   a=build_public_preview(self.base())
  self.assertNotIn(PATH,[str(x)for x in a.url_map.iter_rules()]);self.assertEqual(a.test_client().get(PATH,base_url=BASE).status_code,403)
 def test_sample_on_allowlist_head(self):
  from integration.public_preview_builder import build_public_preview
  a=build_public_preview(dict(self.base(),**env()));s=a.extensions['public_weather'];s.get=lambda p:(_ for _ in ()).throw(AssertionError('IO'))
  self.assertEqual(a.test_client().head(PATH,base_url=BASE).status_code,200);self.assertEqual(s.attempts,0)
  x=a.test_client().get(PATH+'?place=INBOM',base_url=BASE,headers={'Sec-Fetch-Site':'same-origin'});self.assertEqual(x.status_code,503);self.assertEqual(x.headers['Cache-Control'],'no-store')
class LiveBuilderTests(unittest.TestCase):
 def base(self):return dict(PUBLIC_NEWS_READ_ENABLED='true',PREVIEW_PUBLIC_SAMPLE_ENABLED='true',PREVIEW_GEO_ONLY_ENABLED='true',PREVIEW_ACCESS_ENABLED='false',NEWS_READ_ENABLED='false',NEWS_EVENTS_READ_ENABLED='false',FINDER_NETWORK_PREVIEW_ENABLED='false',PREVIEW_ORIGIN=BASE,NEWS_STORE_MAPPING_VERIFIED='true',PUBLIC_NEWS_DISCLOSURE_VERIFIED='true',GEO_READONLY_CREDENTIAL_VERIFIED='true',GEO_MONGODB_URI='mongodb://fixture')
 class Store:
  def __getitem__(self,key):return self
  def close(self):pass
  def find(self,*a,**k):raise AssertionError('No store read in weather tests')
 def make(self,e):
  from integration.public_live_builder import build_public_live_preview
  return build_public_live_preview(e,client_factory=lambda *a,**k:self.Store())
 def test_live_off_absent_and_not_allowlisted(self):
  with patch('integration.weather_public.verify_catalogue',side_effect=AssertionError('pin')):
   a=self.make(self.base())
  self.assertNotIn('public_weather',a.extensions);self.assertNotIn(PATH,[str(x)for x in a.url_map.iter_rules()]);self.assertEqual(a.test_client().get(PATH,base_url=BASE).status_code,403)
 def test_live_on_registered_allowed_head_zero_io(self):
  a=self.make(dict(self.base(),**env()));s=a.extensions['public_weather'];s.get=lambda p:(_ for _ in ()).throw(AssertionError('IO'))
  self.assertIn(PATH,[str(x)for x in a.url_map.iter_rules()]);self.assertEqual(a.test_client().head(PATH,base_url=BASE).status_code,200);self.assertEqual(s.attempts,0);self.assertEqual(s.requests,0)
  x=a.test_client().get(PATH+'?place=INBOM',base_url=BASE,headers={'Sec-Fetch-Site':'same-origin'});self.assertEqual(x.status_code,503);self.assertEqual(x.json,{'error':'Weather unavailable'})
 def test_live_on_missing_gate_raises_before_client(self):
  from integration.public_live_builder import build_public_live_preview
  for k in ['OPEN_METEO_TERMS_ACK','PUBLIC_WEATHER_NONCOMMERCIAL','PUBLIC_WEATHER_CAPACITY_REVIEWED','PUBLIC_WEATHER_SINGLE_WORKER_VERIFIED']:
   e=dict(self.base(),**env());e.pop(k)
   with self.assertRaises(ValueError):build_public_live_preview(e,client_factory=lambda *a,**k:(_ for _ in ()).throw(AssertionError('factory')))
 def test_pin_checked_at_install(self):
  a=Flask(__name__);e=env()
  with patch('integration.weather_public.verify_catalogue',side_effect=Refused('Pin drift')) as pin:
   with self.assertRaises(Refused):install_if_enabled(a,BASE,e,factory=lambda:(_ for _ in ()).throw(AssertionError('factory')),source_path=ROOT/'src/worldports.ts')
  pin.assert_called_once_with(ROOT/'src/worldports.ts');self.assertNotIn(PATH,[str(x)for x in a.url_map.iter_rules()])

class SurvivorTests(unittest.TestCase):
 def test_get_copy_independent_of_put(self):
  now=datetime.now(timezone.utc);s=Service(utcnow=lambda:now);obj=parse('INBOM',raw(),now);s.cache['INBOM']=(s.clock(),obj)
  a=s.get('INBOM');a['values']['temperature_2m']['value']=999;a['source']['name']='bad'
  self.assertEqual(obj['values']['temperature_2m']['value'],25);self.assertEqual(obj['source']['name'],'Open-Meteo');self.assertEqual(s.get('INBOM')['values']['temperature_2m']['value'],25)
 def test_query_32byte_cap_and_nosniff(self):
  a=Flask(__name__);s=Service();s.get=lambda p: {'ok':True};install_if_enabled(a,BASE,env(),factory=lambda:s,source_path=ROOT/'src/worldports.ts');c=a.test_client();h={'Sec-Fetch-Site':'same-origin'}
  # Decode to INBOM while raw query is exactly 32 bytes, then 34 bytes.
  good='place='+('%49'*10)+'NBOM'
  with patch('integration.weather_public.params',return_value='INBOM') as parameter:
   self.assertEqual(c.get(PATH+'?'+('x'*32),base_url=BASE,headers=h).status_code,200);parameter.assert_called_once()
   parameter.reset_mock();r=c.get(PATH+'?'+('x'*33),base_url=BASE,headers=h);self.assertEqual(r.status_code,400);parameter.assert_not_called()
  self.assertEqual(r.headers['X-Content-Type-Options'],'nosniff');self.assertEqual(r.headers['Cache-Control'],'no-store')
 def test_per_read_timeout_and_fixed_host(self):
  import ssl
  elapsed=[0];timeouts=[];events=[];chunks=iter([b'{',b'}',b''])
  class Sock:
   def settimeout(self,x):timeouts.append(x)
  class Response:
   status=200
   def getheader(self,*a):return 'application/json'
   def read1(self,n):events.append(('read',timeouts[-1]));elapsed[0]+=1;return next(chunks)
  class Conn:
   sock=Sock()
   def request(self,*a,**k):pass
   def getresponse(self):return Response()
   def close(self):events.append(('closed',True))
  def wrap(context,sock,server_hostname):return sock
  with patch('integration.weather_public.http.client.HTTPSConnection',return_value=Conn()) as constructor,patch('integration.weather_public.http.client.HTTPConnection.connect'),patch.object(ssl.SSLContext,'wrap_socket',new=wrap):
   self.assertEqual(fetch('INMAA',5,lambda:elapsed[0]),b'{}')
  self.assertEqual(constructor.call_args.args,('api.open-meteo.com',443));self.assertEqual([x for kind,x in events if kind=='read'],[5,4,3]);self.assertEqual(events[-1],('closed',True))
