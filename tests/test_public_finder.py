import json,unittest
from unittest.mock import patch
from integration.public_finder import Rates,Held,Limited,sanitize,enabled,install,fetch_rates,CURRENCIES,PATHS
from integration.public_preview_builder import build_public_preview
BASE='https://preview.example'
def env(on=False):
 return dict(PREVIEW_PUBLIC_SAMPLE_ENABLED='true',PREVIEW_GEO_ONLY_ENABLED='true',PREVIEW_ACCESS_ENABLED='false',NEWS_READ_ENABLED='false',NEWS_EVENTS_READ_ENABLED='false',FINDER_NETWORK_PREVIEW_ENABLED='false',PREVIEW_ORIGIN=BASE,PUBLIC_FINDER_RATES_ENABLED='true' if on else 'false',PUBLIC_FINDER_PROVIDER_REVIEWED='true',PUBLIC_FINDER_ABUSE_REVIEWED='true',PUBLIC_FINDER_SINGLE_WORKER_VERIFIED='true')
def raw(base='USD',quote='INR'):
 return json.dumps({'base':base,'date':'2026-10-09','rates':{quote:83.4},'secret':'must-not-return'}).encode()
class PublicFinder(unittest.TestCase):
 def test_default_held(self):
  c=build_public_preview(env()).test_client()
  for path in PATHS:self.assertEqual(c.get(path,base_url=BASE).status_code,403)
 def test_flag_gates(self):
  for key in ('PUBLIC_FINDER_PROVIDER_REVIEWED','PUBLIC_FINDER_ABUSE_REVIEWED','PUBLIC_FINDER_SINGLE_WORKER_VERIFIED'):
   e=env(True);e.pop(key)
   with self.assertRaises(ValueError):build_public_preview(e)
  e=env(True);e['FINDER_NETWORK_PREVIEW_ENABLED']='true'
  with self.assertRaises(ValueError):build_public_preview(e)
 def test_manual_route(self):
  app=build_public_preview(env(True));calls=[]
  app.extensions['public_finder_rates'].transport=lambda b,q:(calls.append((b,q))or raw(b,q))
  c=app.test_client();r=c.get('/workspace',base_url=BASE);self.assertIn('src="/workspace/finder/live.html"',r.text)
  for path in ('/workspace/finder/live.html','/workspace/finder/public-rates.js'):
   r=c.get(path,base_url=BASE);self.assertEqual(r.status_code,200);self.assertIn("connect-src 'self'",r.headers['Content-Security-Policy'])
  self.assertEqual(calls,[])
  path='/api/finder-public-rates?base=USD&quote=INR'
  self.assertEqual(c.head(path,base_url=BASE).status_code,200);self.assertEqual(calls,[])
  self.assertEqual(c.get(path,base_url=BASE).status_code,403)
  r=c.get(path,base_url=BASE,headers={'Sec-Fetch-Site':'same-origin'});self.assertEqual(r.status_code,200);self.assertEqual(calls,[('USD','INR')]);self.assertNotIn('secret',r.text)
  for query in ('base=USD&quote=INR&url=http://evil','base=USD&base=EUR&quote=INR','base=USD','base=USD&quote=usd'):
   self.assertIn(c.get('/api/finder-public-rates?'+query,base_url=BASE,headers={'Sec-Fetch-Site':'same-origin'}).status_code,(400,503))
  for method in ('post','delete','options'):self.assertEqual(getattr(c,method)(path,base_url=BASE).status_code,403)
  self.assertEqual(c.get(path,base_url='https://evil.example',headers={'Sec-Fetch-Site':'same-origin'}).status_code,403)
  self.assertEqual(c.get(path,base_url=BASE,headers={'Sec-Fetch-Site':'same-origin','Origin':'https://evil.example'}).status_code,403)
 def test_public_live_builder_keeps_private_and_default_routes_closed(self):
  from integration.public_live_builder import build_public_live_preview
  e=env(True);e.update(PUBLIC_NEWS_READ_ENABLED='true',NEWS_STORE_MAPPING_VERIFIED='true',PUBLIC_NEWS_DISCLOSURE_VERIFIED='true',GEO_READONLY_CREDENTIAL_VERIFIED='true',GEO_MONGODB_URI='mongodb://fixture')
  class Store:
   def __getitem__(self,key):return self
   def close(self):pass
  with patch('integration.public_finder.fetch_rates',side_effect=AssertionError('no live calls')):
   app=build_public_live_preview(e,client_factory=lambda *a,**k:Store())
   c=app.test_client()
   self.assertEqual(c.get('/workspace/finder/live.html',base_url=BASE).status_code,200)
   for path in ('/workspace/finder/index.html','/api/finder-context','/collect','/api/mail','/workspace/weekly'):
    self.assertEqual(c.get(path,base_url=BASE).status_code,403)
   self.assertEqual(c.get('/workspace/finder/offline.html',base_url=BASE).status_code,200)
 def test_transport_contract_and_redirects(self):
  from integration.public_finder import NoRedirect
  class Headers:
   def get_content_type(self):return 'application/json'
  class Reply:
   status=200;headers=Headers()
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def read(self,n):self.n=n;return raw()
  reply=Reply()
  with patch('integration.public_finder.build_opener')as factory:
   factory.return_value.open.return_value=reply
   self.assertEqual(fetch_rates('USD','INR'),raw())
   req=factory.return_value.open.call_args.args[0]
   self.assertEqual(req.full_url,'https://api.frankfurter.dev/v1/latest?base=USD&symbols=INR')
   self.assertEqual(factory.return_value.open.call_args.kwargs,{'timeout':3})
   self.assertEqual(reply.n,16385)
   self.assertEqual(factory.call_args.args[0].proxies,{})
  with self.assertRaises(Held):NoRedirect().redirect_request(None,None,302,'',{},'https://evil.invalid')
 def test_bounded_cache_and_concurrency(self):
  s=Rates(lambda b,q:raw(b,q))
  self.assertTrue(s.slot.acquire(False))
  with self.assertRaises(Limited):s.get('USD','INR','peer')
  s.slot.release()
  currencies=list(CURRENCIES)
  now=[0];s=Rates(lambda b,q:raw(b,q),lambda:now[0])
  count=0
  for b in currencies:
   for q in currencies:
    if b!=q:
     s.get(b,q,str(count));count+=1;now[0]+=61
     if count==40:break
   if count==40:break
  self.assertEqual(len(s.cache),32)
 def test_shared_request_count_cache_hits(self):
  s=Rates(lambda b,q:raw(b,q),lambda:0)
  for i in range(60):s.get('USD','INR',str(i))
  with self.assertRaises(Limited):s.get('USD','INR','next')
 def test_cache_limits(self):
  now=[0];calls=[];s=Rates(lambda b,q:(calls.append(1)or raw(b,q)),lambda:now[0])
  for i in range(10):s.get('USD','INR','peer')
  self.assertEqual(len(calls),1)
  with self.assertRaises(Limited):s.get('USD','INR','peer')
  now[0]=60;s.get('USD','INR','peer');self.assertEqual(len(calls),1)
  now[0]=3600;s.get('USD','INR','peer');self.assertEqual(len(calls),2)
 def test_shared_and_daily_limits_failures_count(self):
  now=[0];s=Rates(lambda b,q:(_ for _ in()).throw(Exception('secret')),lambda:now[0])
  for i in range(30):
   with self.assertRaises(Held):s.get('USD','INR',str(i))
  with self.assertRaises(Limited):s.get('USD','INR','next')
  s.daily=200;now[0]=60
  with self.assertRaises(Limited):s.get('USD','INR','new')
 def test_sanitize(self):
  for value in (b'{}',b'{"base":"USD","date":"2026-99-99","rates":{"INR":2}}',b'{"base":"USD","date":"2026-10-09","rates":{"INR":true}}',b'{"base":"USD","date":"2026-10-09","rates":{"INR":NaN}}',b'{"base":"USD","base":"USD","date":"2026-10-09","rates":{"INR":2}}',b'x'*16385):
   with self.assertRaises(Held):sanitize(value,'USD','INR')
 def test_no_network_startup_and_fixed_transport(self):
  with patch('urllib.request.OpenerDirector.open',side_effect=AssertionError('network')):
   build_public_preview(env(True))
   for b,q in [('http://127.0.0.1','INR'),('USD','USD'),('USD','ZZZ')]:
    with self.assertRaises(Held):fetch_rates(b,q)
if __name__=='__main__':unittest.main()
