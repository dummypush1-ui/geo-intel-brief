"""Explicit reviewed public Geo article reads. No write/collector/mail effects.
Default delegates unchanged sample/private106. Operator verifies public disclosure,
exact mapping and read-only credential. Env assertions do not prove those facts.
"""
import os
import re
from urllib.parse import urlsplit
from flask import redirect, request
from integration.preview_launcher import build_preview
from integration.news_api import create_app

from public_preview106 import READ_PATHS, ASSETS, BRANDING, build_public_preview
from integration.geo_read_factory import ReadClient
from integration.storage_reader import ReadOnlyNewsReader
from threading import Lock
from copy import deepcopy
import time

def sanitize_public_geo_rows(rows):
 """Never stringify nested objects or retain unapproved raw/private fields."""
 from datetime import datetime
 from math import isfinite
 if type(rows)is not list or len(rows)>100:raise ValueError('Bounded Geo rows required')
 def text(value,chars):
  if type(value)is not str or len(value)>chars:return False
  try:return len(value.encode('utf-8'))<=chars*4
  except UnicodeError:return False
 clean=[]
 for row in rows:
  if type(row)is not dict:continue
  if any(not text(row.get(k),2048) or not row[k].strip() for k in ('url','title')):continue
  out={'url':row['url'],'title':row['title']}
  for k in ('summary','source','country','category','risk_level','credibility'):
   value=row.get(k)
   if text(value,8000 if k=='summary' else 200):out[k]=value
  for k in ('published','created_at','collected_at'):
   value=row.get(k)
   if (text(value,100)) or (type(value)is datetime and value.tzinfo is not None):out[k]=value
  value=row.get('score')
  try:
   if type(value)in (int,float) and isfinite(value):out['score']=value
  except OverflowError:pass
  clean.append(out)
 return clean

def create_public_geo_client(uri,*,serverSelectionTimeoutMS=5000,connect=False):
 """New read facade factory preserves Mongo UTC dates for public normalization."""
 try:
  from pymongo import MongoClient
  return ReadClient(MongoClient(uri,connect=False,tls=True,tz_aware=True,
   serverSelectionTimeoutMS=5000,connectTimeoutMS=5000,socketTimeoutMS=5000,
   maxPoolSize=4,minPoolSize=0,waitQueueTimeoutMS=2000,
   tlsAllowInvalidCertificates=False,tlsAllowInvalidHostnames=False))
 except Exception:raise ValueError('Public Geo client unavailable')from None

def build_public_live_preview(environ,client_factory=None,clock=time.monotonic):
 if type(environ) is not dict or any(type(k)is not str or type(v)is not str for k,v in environ.items()):raise ValueError('Plain environment strings required')
 flag=environ.get('PUBLIC_NEWS_READ_ENABLED','false')
 if flag not in ('true','false'):raise ValueError('Exact public news flag required')
 if flag=='false':return build_public_preview(environ,client_factory=client_factory)
 required={'PREVIEW_PUBLIC_SAMPLE_ENABLED':'true','PREVIEW_GEO_ONLY_ENABLED':'true',
  'PREVIEW_ACCESS_ENABLED':'false','NEWS_READ_ENABLED':'false',
  'NEWS_EVENTS_READ_ENABLED':'false','FINDER_NETWORK_PREVIEW_ENABLED':'false',
  'NEWS_STORE_MAPPING_VERIFIED':'true','PUBLIC_NEWS_DISCLOSURE_VERIFIED':'true',
  'GEO_READONLY_CREDENTIAL_VERIFIED':'true'}
 if any(environ.get(k,'false')!=v for k,v in required.items()):raise ValueError('Explicit public news review gates required')
 if environ.get('GEO_DATABASE','geo_intel')!='geo_intel' or environ.get('GEO_ARTICLES_COLLECTION','articles')!='articles':raise ValueError('Exact Geo article mapping required')
 uri=environ.get('GEO_MONGODB_URI','')
 if not uri:raise ValueError('Explicit read-only Geo URI required')
 origin=environ.get('PREVIEW_ORIGIN','')
 try:
  p=urlsplit(origin)
  if p.scheme!='https' or not p.hostname or p.netloc!=p.hostname or p.path not in ('','/') or p.query or p.fragment or origin!=origin.lower() or not re.fullmatch(r'[a-z0-9]+(?:[.-][a-z0-9]+)*',p.hostname):raise ValueError()
 except ValueError:raise ValueError('Canonical HTTPS public sample origin required')from None
 origin=origin.rstrip('/')
 def allow(req):
  if req.method not in ('GET','HEAD') or req.host_url.rstrip('/')!=origin:return False
  if req.path in READ_PATHS or req.path=='/':return True
  if req.path.startswith('/workspace/assets/'):return req.path.removeprefix('/workspace/assets/')in ASSETS
  if req.path.startswith('/workspace/branding/'):return req.path.removeprefix('/workspace/branding/')in BRANDING
  return False
 # No connection, URI parsing or secret logging until all public gates validate.
 factory=client_factory or create_public_geo_client
 try:client=factory(uri,serverSelectionTimeoutMS=5000,connect=False)
 except Exception:raise ValueError('Public Geo client unavailable')from None
 if client is None:raise ValueError('Public Geo client unavailable')
 try:source=ReadOnlyNewsReader({'geo':client['geo_intel']['articles']},verified=True,limit=100,query_timeout_ms=2000)
 except Exception:
  try:client.close()
  except Exception:pass
  raise ValueError('Public Geo mapping unavailable')from None
 lock=Lock();state={'rows':None,'until':0,'failed':False}
 def read():
  if not lock.acquire(timeout=2):raise ValueError('Public Geo read busy')
  try:
   if state['failed']:raise ValueError('Public Geo read unavailable; restart after repair')
   if state['rows'] is not None and clock()<state['until']:return deepcopy(state['rows'])
   try:
    rows=source()
    # Hard boundary even with an injected test store or misbehaving cursor.
    if type(rows) is not dict or set(rows)!={'geo'} or type(rows['geo'])is not list or len(rows['geo'])>100:raise ValueError()
    state['rows']={'geo':sanitize_public_geo_rows(rows['geo'])};state['until']=clock()+60
    return deepcopy(state['rows'])
   except Exception:
    state['failed']=True;state['rows']=None
    try:client.close()
    except Exception:pass
    raise ValueError('Public Geo read unavailable')from None
  finally:lock.release()
 app=create_app(reader=read,authorize=allow,allowed_origin=origin)
 @app.get('/')
 def home():return redirect('/workspace',302)
 @app.after_request
 def sample_notice(response):
  if request.path=='/workspace/assets/countries.js' and response.status_code==200:
   response.direct_passthrough=False
   js=response.get_data(as_text=True)
   seam="card.append(find,matches);$('country-stories').append(card);"
   if js.count(seam)!=1:raise ValueError('Public country Finder action seam changed')
   response.set_data(js.replace(seam,"/* Public Finder POST is unavailable; do not show its action. */$('country-stories').append(card);"))
  if request.path=='/workspace/assets/workspace.js' and response.status_code==200:
   response.direct_passthrough=False
   js=response.get_data(as_text=True)
   seam="if(article.article_key && ['geo','brics'].includes(article.project)) {"
   if js.count(seam)!=1:raise ValueError('Public Finder action seam changed')
   response.set_data(js.replace(seam,"if(false) { /* Public exact-code lookup unavailable. */"))
  if request.path=='/workspace' and response.status_code==200:
   response.direct_passthrough=False
   html=response.get_data(as_text=True)
   html=html.replace('GEO INTEL MONITOR · PRIVATE PREVIEW','GEO INTEL MONITOR · PUBLIC NEWS PREVIEW')
   html=html.replace('Geo news dashboard. Collection, mail and scraper remain off.','Public read-only Geo news. Latest up to 100 stored articles, refreshed on demand at most once per minute. Not whole-database totals. Collection, mail and scraper remain off.')
   html=html.replace('src="/workspace/finder/index.html"','src="/workspace/finder/offline.html"')
   # These heavier/private workflows are deliberately outside the public scope.
   html=html.replace('<a href="/workspace/weekly">Weekly PDF</a>','').replace('<a href="/workspace/brics-streams">BRICS streams</a>','')
   html=html.replace('<button data-view="live" aria-pressed="false">Live news</button>','').replace('<button data-view="channels" aria-pressed="false">My channels</button>','')
   html=html.replace('<script type="module" src="/workspace/assets/live_news.js"></script>','')
   response.set_data(html)
  response.headers['X-Preview-Mode']='public_geo_readonly'
  return response
 app.extensions.update(preview_launcher_mode='public_geo_readonly',read_only_news_clients=[client],stored_news_projects=('geo',),geo_events_read_enabled=False)
 return app

app=build_public_live_preview(dict(os.environ))
