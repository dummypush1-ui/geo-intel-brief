"""Default-OFF public Finder rates adapter. No AI, keys, storage or polling.

One fixed keyless reference-rate provider. All quotas are process-local and
conservative behind a proxy: socket peer, never caller-supplied forwarding IDs.
Multiple workers multiply limits; deploy capacity and provider policy review is
required before enabling. No shared credential or paid rail exists here.
"""
import json
import math
import re
import time
from collections import OrderedDict
from threading import BoundedSemaphore, Lock
from urllib.parse import urlencode
from urllib.request import build_opener, ProxyHandler, HTTPRedirectHandler, Request

CURRENCIES = frozenset(('USD','EUR','INR','GBP','JPY','CHF','CAD','AUD','CNY','SGD','HKD'))
ENDPOINT = 'https://api.frankfurter.dev/v1/latest'
PATHS = frozenset(('/workspace/finder/live.html','/workspace/finder/public-rates.js','/api/finder-public-rates'))
MAX_BYTES = 16384
class Held(ValueError):
 pass
class Limited(Held):
 pass
class NoRedirect(HTTPRedirectHandler):
 def redirect_request(self, req, fp, code, msg, headers, newurl):
  raise Held('Provider redirect refused')

def fetch_rates(base, quote):
 """Fixed GET, no environment proxies/cookies/auth/redirects, bounded bytes."""
 if base not in CURRENCIES or quote not in CURRENCIES or base==quote:
  raise Held('Unsupported currency pair')
 opener=build_opener(ProxyHandler({}),NoRedirect())
 req=Request(ENDPOINT+'?'+urlencode({'base':base,'symbols':quote}),headers={'Accept':'application/json','User-Agent':'GeoIntel-PublicRates/1'})
 with opener.open(req,timeout=3) as response:
  if response.status!=200 or response.headers.get_content_type()!='application/json':
   raise Held('Provider unavailable')
  raw=response.read(MAX_BYTES+1)
  if len(raw)>MAX_BYTES:raise Held('Provider response too large')
 return raw

def sanitize(raw, base, quote):
 if type(raw) is not bytes or len(raw)>MAX_BYTES:raise Held('Bounded response required')
 def unique(pairs):
  d={}
  for k,v in pairs:
   if k in d:raise Held('Duplicate response key')
   d[k]=v
  return d
 try:
  data=json.loads(raw,object_pairs_hook=unique)
  if type(data)is not dict or data.get('base')!=base or type(data.get('rates'))is not dict or set(data['rates'])!={quote}:raise Held('Unexpected provider shape')
  rate=data['rates'][quote];day=data.get('date')
  if type(rate)not in (float,int)or not math.isfinite(rate)or not 0<rate<=1000000:raise Held('Invalid rate')
  if type(day)is not str or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',day):raise Held('Invalid rate date')
  from datetime import date
  date.fromisoformat(day)
 except (ValueError,TypeError,OverflowError,RecursionError,UnicodeError):raise Held('Provider response refused') from None
 return {'base':base,'quote':quote,'rate':rate,'date':day,'provider':'Frankfurter reference rates','scope':'daily_reference_not_live_trade_price'}

class Rates:
 def __init__(self, transport=fetch_rates, clock=time.monotonic):
  self.transport=transport;self.clock=clock;self.lock=Lock();self.slot=BoundedSemaphore(1)
  self.peers=OrderedDict();self.cache=OrderedDict();self.window=None;self.calls=0
  self.upstream_window=None;self.upstream_calls=0;self.day=None;self.daily=0
 def get(self, base, quote, peer):
  if type(base)is not str or type(quote)is not str or base not in CURRENCIES or quote not in CURRENCIES or base==quote:raise Held('Unsupported currency pair')
  if type(peer)is not str or not 1<=len(peer)<=100:peer='unknown'
  now=self.clock();window=int(now//60);day=int(now//86400);key=(base,quote)
  with self.lock:
   if self.window!=window:self.window=window;self.calls=0;self.peers.clear()
   self.calls+=1
   if self.calls>60:raise Limited('Shared request limit')
   count=self.peers.get(peer,0)+1;self.peers[peer]=count
   if count>10:raise Limited('Peer request limit')
   if len(self.peers)>1000:raise Limited('Peer capacity')
   cached=self.cache.get(key)
   if cached and now-cached[0]<3600:return dict(cached[1],cached=True)
  if not self.slot.acquire(blocking=False):raise Limited('Provider busy')
  try:
   with self.lock:
    if self.upstream_window!=window:self.upstream_window=window;self.upstream_calls=0
    if self.day!=day:self.day=day;self.daily=0
    if self.upstream_calls>=30 or self.daily>=200:raise Limited('Shared provider limit')
    self.upstream_calls+=1;self.daily+=1
   result=sanitize(self.transport(base,quote),base,quote)
   with self.lock:
    self.cache[key]=(now,result)
    while len(self.cache)>32:self.cache.popitem(last=False)
   return dict(result,cached=False)
  except Limited:raise
  except Exception:raise Held('Reference rates unavailable')from None
  finally:self.slot.release()

def enabled(environ):
 value=environ.get('PUBLIC_FINDER_RATES_ENABLED','false')
 if value not in ('true','false'):raise ValueError('Exact public Finder rates flag required')
 if value=='true' and any(environ.get(k)!='true' for k in ('PUBLIC_FINDER_PROVIDER_REVIEWED','PUBLIC_FINDER_ABUSE_REVIEWED','PUBLIC_FINDER_SINGLE_WORKER_VERIFIED')):raise ValueError('Public Finder provider, abuse and single-worker review required')
 return value=='true'

def install(app, origin, service=None):
 from flask import request,Response,jsonify
 from pathlib import Path
 root=Path(__file__).resolve().parent/'ui';service=service or Rates()
 @app.get('/workspace/finder/live.html')
 def public_finder_shell():return Response((root/'finder_public.html').read_text(),mimetype='text/html')
 @app.get('/workspace/finder/public-rates.js')
 def public_finder_js():return Response((root/'finder_public_rates.js').read_text(),mimetype='application/javascript')
 @app.get('/api/finder-public-rates')
 def public_rates():
  # HEAD is metadata only, never an upstream request.
  if request.method=='HEAD':return Response(status=200)
  if request.headers.get('Sec-Fetch-Site')!='same-origin':return jsonify(error='Same-origin manual requests required'),403
  if request.headers.get('Origin')not in (None,origin):return jsonify(error='Same-origin manual requests required'),403
  if set(request.args)!={'base','quote'} or any(len(request.args.getlist(k))!=1 for k in request.args)or len(request.query_string)>64:return jsonify(error='Invalid currency pair'),400
  try:return jsonify(service.get(request.args['base'],request.args['quote'],request.remote_addr))
  except Limited:return jsonify(error='Rates busy; wait before another manual request'),429,{'Retry-After':'60'}
  except Held:return jsonify(error='Reference rates unavailable or currency pair unsupported'),503
 @app.after_request
 def finder_headers(response):
  if request.path in PATHS:
   response.headers['Cache-Control']='no-store'
   response.headers['X-Content-Type-Options']='nosniff'
   response.headers['Referrer-Policy']='no-referrer'
   response.headers['Content-Security-Policy']="default-src 'none'; script-src 'self'; style-src 'self'; frame-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'"
  return response
 # Run last: create_app's existing response hook sets the baseline CSP.
 hooks=app.after_request_funcs[None];hooks.remove(finder_headers);hooks.insert(0,finder_headers)
 app.extensions['public_finder_rates']=service
