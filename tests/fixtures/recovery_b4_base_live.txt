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

from integration.public_preview_builder import READ_PATHS, ASSETS, BRANDING, build_public_preview
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

def build_public_live_preview(environ,client_factory=None,clock=time.monotonic,coverage_binding_provider=None,tariff_snapshot=None,geo_export_binding=None,brics_live_binding=None):
 if type(environ) is not dict or any(type(k)is not str or type(v)is not str for k,v in environ.items()):raise ValueError('Plain environment strings required')
 from integration.news_export_e2 import prepare as export_prepare,install as export_install,PATH as EXPORT_PATH
 from integration.brics_live_b3 import prepare as brics_live_prepare,install as brics_live_install
 brics_binding=brics_live_prepare(environ,brics_live_binding)
 export_binding=export_prepare(environ,geo_export_binding)
 from integration.code_news_context_d4 import prepare as context_prepare,ContextBroker,validate as context_validate,install_ui as context_ui_install
 context_on=context_prepare(environ)
 from integration.news_search_progress import prepare as search_prepare,install as search_install
 search_on=search_prepare(environ)
 from integration.public_brics_news import prepare as brics_news_prepare,install as brics_news_install,PATHS as BRICS_NEWS_PATHS
 brics_news_on=brics_news_prepare(environ)
 from integration.public_map_prep import prepare as map_prepare,PATHS as MAP_PATHS,install as map_install
 map_on=map_prepare(environ)
 from integration.public_tariff_evidence import prepare as tariff_prepare,install as tariff_install,PATHS as TARIFF_PATHS
 tariff_on=tariff_prepare(environ)
 if tariff_snapshot is not None:
  from integration.tariff_evidence import TariffEvidenceSnapshot
  if not tariff_on or type(tariff_snapshot) is not TariffEvidenceSnapshot:raise ValueError('Explicit enabled tariff snapshot required')
  tariff_snapshot=TariffEvidenceSnapshot(tariff_snapshot._observed_at,tariff_snapshot._items)
 from integration.relationship_navigation import prepare as relationship_prepare,install as relationship_install,ASSET as RELATIONSHIP_ASSET
 relationship_on=relationship_prepare(environ)
 from integration.public_map_m2 import prepare as m2_prepare,PATHS as M2_PATHS,install as m2_install
 m2_on=m2_prepare(environ)
 from integration.public_map_m3 import prepare as m3_prepare,install as m3_install,PATHS as M3_PATHS
 m3_on=m3_prepare(environ)
 if m3_on:MAP_PATHS=MAP_PATHS|M3_PATHS
 if m2_on:MAP_PATHS=MAP_PATHS|M2_PATHS
 from integration.public_ai_answers import prepare as ai_prepare, PATHS as AI_PATHS, PAGES as AI_PAGES, POST as AI_POST, STATUS as AI_STATUS, install as ai_install
 ai_on=ai_prepare(environ)
 from integration.public_brics_streams import prepare as brics_prepare, PATHS as BRICS_PATHS, install as brics_install
 brics_on=brics_prepare(environ)
 from integration.public_weekly_pdf import prepare as weekly_prepare, PATHS as WEEKLY_PATHS, install as weekly_install
 weekly_on=weekly_prepare(environ)
 from integration.weekly_full_store import enabled as weekly_full_enabled, PeriodReader
 weekly_full=weekly_full_enabled(environ)
 from integration.news_finder_navigation_prep import enabled as finder_links_enabled
 finder_links=finder_links_enabled(environ)
 from integration.code_news_coverage_binding_prep import prepare
 coverage_ui,coverage_api,coverage_pins=prepare(environ,coverage_binding_provider)
 from integration.code_news_coverage_ui_prep import PATHS as COVERAGE_UI_PATHS,install as coverage_ui_install
 from integration.code_news_coverage_route_prep import PATH as COVERAGE_API_PATH,install as coverage_api_install
 pages_flag=environ.get('PUBLIC_NEWS_FULL_PAGES_ENABLED','false')
 if pages_flag not in ('true','false'):raise ValueError('Exact full pages flag required')
 if pages_flag=='true' and environ.get('PUBLIC_NEWS_READ_ENABLED','false')!='true':raise ValueError('Whole-store pages require reviewed public live reads')
 flag=environ.get('PUBLIC_NEWS_READ_ENABLED','false')
 if flag not in ('true','false'):raise ValueError('Exact public news flag required')
 if flag=='false':return build_public_preview(environ,client_factory=client_factory,tariff_snapshot=tariff_snapshot)
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
 from integration.public_finder import enabled, PATHS, install
 finder_rates=enabled(environ)
 from integration.code_news_public import enabled as code_enabled,PATHS as CODE_PATHS,install as code_install
 code_news=code_enabled(environ)
 from integration.weather_public import enabled as weather_enabled,PATH as WEATHER_PATH,install_if_enabled as weather_install
 weather_on=weather_enabled(environ)
 from integration.weather_ui import enabled as weather_ui_enabled,PATHS as WEATHER_UI_PATHS,install as weather_ui_install
 weather_ui_on=weather_ui_enabled(environ)
 def allow(req):
  if export_binding is not None and req.path==EXPORT_PATH:return req.host_url.rstrip('/')==origin and req.method in ('GET','HEAD')
  if brics_news_on and req.path in BRICS_NEWS_PATHS:return req.host_url.rstrip('/')==origin and req.method in ('GET','HEAD')
  if tariff_on and req.path in TARIFF_PATHS:return req.host_url.rstrip('/')==origin and req.method in ('GET','HEAD')
  if relationship_on and req.path==RELATIONSHIP_ASSET:return req.host_url.rstrip('/')==origin and req.method in ('GET','HEAD')
  if map_on and req.path in MAP_PATHS:return req.host_url.rstrip('/')==origin and req.method in ('GET','HEAD')
  if ai_on and req.path in AI_PATHS:return req.host_url.rstrip('/')==origin and req.method in (('GET','HEAD') if req.path in AI_PAGES else ('POST','HEAD'))
  if req.host_url.rstrip('/')!=origin:return False
  if coverage_api and req.path==COVERAGE_API_PATH:return req.method in ('POST','HEAD','OPTIONS')
  if coverage_ui and req.path in COVERAGE_UI_PATHS:return req.method in ('GET','HEAD')
  if req.method not in ('GET','HEAD'):return False
  if (brics_on and req.path in BRICS_PATHS) or (weekly_on and req.path in WEEKLY_PATHS) or req.path in READ_PATHS or req.path=='/' or (finder_rates and req.path in PATHS) or (code_news and req.path in CODE_PATHS) or (weather_on and req.path==WEATHER_PATH) or (weather_ui_on and req.path in WEATHER_UI_PATHS):return True
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
 pages=None;model=None;proof=None;closed=[False]
 def coverage_close():
  if closed[0]:return
  closed[0]=True
  try:
   if pages is not None:pages.close()
  finally:
   try:
    if model is not None:model.close()
    if proof is not None:proof.close()
   finally:client.close()
 try:
  if pages_flag=='true':
   from integration.news_pages import WholeGeoPages
   pages=WholeGeoPages(client['geo_intel']['articles'],sanitize_public_geo_rows,verified=True)
   import atexit
   atexit.register(pages.close)
  if coverage_api:
   from integration.code_news_disk import DiskLinks
   model=DiskLinks(coverage_pins.folder)
  app=create_app(reader=read,authorize=allow,allowed_origin=origin,full_news_pages=pages)
  if m2_on:m2_install(app,origin,read)
  elif map_on:map_install(app,origin)
  if m3_on:m3_install(app,origin)
  if ai_on:ai_install(app,origin)
  if brics_news_on:brics_news_install(app,origin)
  if brics_binding is not None:brics_live_install(app,brics_binding)
  if brics_on:brics_install(app)
  if weekly_on:weekly_install(app,read,period_reader=PeriodReader(client['geo_intel']['articles']) if weekly_full else None)
  from integration.news_finder_navigation_prep import install_mount
  install_mount(app)
  app.extensions['whole_news_pages']=pages
  if coverage_api:
   from integration.code_news_coverage_broker_prep import CoverageBroker
   if finder_links:
    from integration.finder_identity_proof_prep import FinderProof
    proof=FinderProof()
   broker=(ContextBroker if context_on else CoverageBroker)(pages,model,coverage_pins.manifest,coverage_pins.matcher_version,finder_proof=proof)
   coverage_api_install(app,origin,broker,environ,**({'response_validator':context_validate} if context_on else {}))
   app.extensions['code_news_coverage_broker']=broker
  if coverage_ui:coverage_ui_install(app,environ,coverage_available='code_news_coverage_broker'in app.extensions)
  if context_on:context_ui_install(app)
  if weather_ui_on:weather_ui_install(app,weather_available=weather_on)
  if weather_on:
   from pathlib import Path
   weather_install(app,origin,environ,source_path=Path(__file__).resolve().parents[1]/'src/worldports.ts')
  if finder_rates:install(app,origin)
  if code_news:code_install(app,origin,read)
  if relationship_on:relationship_install(app,origin)
  if tariff_on:tariff_install(app,origin,tariff_snapshot)
  if search_on:search_install(app)
  if export_binding is not None:export_install(app,origin,export_binding)
 except Exception:
  if not coverage_api:raise
  coverage_close();raise ValueError('Public composition unavailable')from None
 @app.before_request
 def coverage_off_paths():
  from flask import jsonify
  if (request.path in COVERAGE_UI_PATHS and not coverage_ui)or(request.path=='/api/code-news-coverage'and not coverage_api):return jsonify(state='unavailable'),404
 hooks=app.before_request_funcs[None];hooks.remove(coverage_off_paths);hooks.insert(0,coverage_off_paths)
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
   if pages is not None:html=html.replace('Geo news dashboard. Collection, mail and scraper remain off.','Public read-only Geo news. Scroll the whole article store; totals unknown and source can change. Summary panels and CSV remain latest100 sample. Collection, mail and scraper remain off.')
   html=html.replace('GEO INTEL MONITOR · PRIVATE PREVIEW','GEO INTEL MONITOR · PUBLIC NEWS PREVIEW')
   html=html.replace('Geo news dashboard. Collection, mail and scraper remain off.','Public read-only Geo news. Latest up to 100 stored articles, refreshed on demand at most once per minute. Not whole-database totals. Collection, mail and scraper remain off.')
   html=html.replace('src="/workspace/finder/index.html"','src="/workspace/finder/live.html"' if finder_rates else 'src="/workspace/finder/offline.html"')
   # These heavier/private workflows are deliberately outside the public scope.
   if not weekly_on:html=html.replace('<a href="/workspace/weekly">Weekly PDF</a>','')
   if not brics_on:html=html.replace('<a href="/workspace/brics-streams">BRICS streams</a>','')
   html=html.replace('<button data-view="live" aria-pressed="false">Live news</button>','').replace('<button data-view="channels" aria-pressed="false">My channels</button>','')
   html=html.replace('<script type="module" src="/workspace/assets/live_news.js"></script>','')
   response.set_data(html)
  response.headers['X-Preview-Mode']='public_geo_readonly'
  return response
 if coverage_api:
  app.extensions['coverage_close']=coverage_close
  import atexit
  atexit.register(coverage_close)
 app.extensions.update(preview_launcher_mode='public_geo_readonly',read_only_news_clients=[client],stored_news_projects=('geo',),geo_events_read_enabled=False)
 return app

def guarded_public_app(environ,build=build_public_live_preview):
 """Edge guard (rate limit, input checks, honeypots) around the reviewed app.
 Off by default: EDGE_GUARD_ENABLED must be true. Needs the Render proxy topology
 (single appended X-Forwarded-For hop) confirmed first. Counters are per worker."""
 from integration.edge_guard import install_edge_guard,edge_limits_from_env
 from integration.security_headers import install_security_headers
 app=build(environ)
 if environ.get('SECURITY_HEADERS_ENABLED','true').strip().lower()!='false':install_security_headers(app)
 limits=edge_limits_from_env(environ)
 return app if limits is None else install_edge_guard(app,**limits)
