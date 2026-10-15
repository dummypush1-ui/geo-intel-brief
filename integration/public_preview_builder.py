"""Explicit public, empty-sample preview. No live data or account effects.

The old private entrypoint is unchanged. This entrypoint delegates to it unless
PREVIEW_PUBLIC_SAMPLE_ENABLED is exactly true. Never injects a DB/client/reader.
"""
import os
import re
from urllib.parse import urlsplit
from flask import redirect, request
from integration.preview_launcher import build_preview
from integration.news_api import create_app

READ_PATHS=frozenset(('/workspace','/workspace/countries','/workspace/map',
 '/api/news','/api/news-page','/api/news-stats','/api/dashboard-signals','/api/dashboard-snapshots',
 '/api/sample-volume','/api/critical-stories','/api/source-health',
 '/api/country-page','/api/country-signals','/api/map-data','/api/story-groups',
 '/api/news-export.csv','/workspace/manifest.webmanifest',
 '/workspace/finder/offline.html'))
from integration.api_v1 import READ_ALIASES,versioned
READ_PATHS=READ_PATHS|frozenset(versioned(p)for p in READ_ALIASES if p in READ_PATHS)
ASSETS=frozenset(('workspace.js','context_excerpt208.js','news_scroll.js','workspace.css',
 'countries.js','watch_updates.js','countries.css','map.js','map.css','geo_map_ui.js','geo_map.css'))
BRANDING=frozenset(('favicon.ico','icon-48.png','icon-192.png','icon-512.png',
 'apple-touch-icon.png','og-image.png','logo.svg'))

def build_public_preview(environ,client_factory=None,tariff_snapshot=None):
 if environ.get('PUBLIC_BRICS_LIVE_READ_ENABLED','false')!='false':raise ValueError('BRICS live source requires reviewed public live builder')
 if type(environ) is not dict or any(type(k)is not str or type(v)is not str for k,v in environ.items()):raise ValueError('Plain environment strings required')
 from integration.news_export_e2 import prepare as export_prepare
 if export_prepare(environ) is not None:raise ValueError('Original export requires reviewed live composition')
 from integration.code_news_context_d4 import prepare as context_prepare
 if context_prepare(environ):raise ValueError('Source context requires reviewed live composition')
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
 from integration.weekly_full_store import enabled as weekly_full_enabled
 if weekly_full_enabled(environ):raise ValueError('Whole-store PDF requires reviewed live composition')
 from integration.news_finder_navigation_prep import enabled as finder_links_enabled
 finder_links=finder_links_enabled(environ)
 from integration.code_news_coverage_ui_prep import enabled as coverage_ui_enabled,PATHS as COVERAGE_UI_PATHS,install as coverage_ui_install
 from integration.code_news_coverage_route_prep import enabled as coverage_api_enabled
 coverage_ui=coverage_ui_enabled(environ)
 if coverage_api_enabled(environ):raise ValueError('Coverage requires reviewed live composition')
 flag=environ.get('PREVIEW_PUBLIC_SAMPLE_ENABLED','false')
 if flag not in ('true','false'):raise ValueError('Exact public sample flag required')
 if flag=='false':return build_preview(environ,client_factory=client_factory)
 if client_factory is not None:raise ValueError('Public sample cannot inject clients')
 required={'PREVIEW_GEO_ONLY_ENABLED':'true','PREVIEW_ACCESS_ENABLED':'false',
  'NEWS_READ_ENABLED':'false','NEWS_EVENTS_READ_ENABLED':'false',
  'FINDER_NETWORK_PREVIEW_ENABLED':'false'}
 if any(environ.get(k,'false')!=v for k,v in required.items()):raise ValueError('Public sample requires Geo-only and all private/live reads OFF')
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
  if brics_news_on and req.path in BRICS_NEWS_PATHS:return req.host_url.rstrip('/')==origin and req.method in ('GET','HEAD')
  if tariff_on and req.path in TARIFF_PATHS:return req.host_url.rstrip('/')==origin and req.method in ('GET','HEAD')
  if relationship_on and req.path==RELATIONSHIP_ASSET:return req.host_url.rstrip('/')==origin and req.method in ('GET','HEAD')
  if map_on and req.path in MAP_PATHS:return req.host_url.rstrip('/')==origin and req.method in ('GET','HEAD')
  if ai_on and req.path in AI_PATHS:return req.host_url.rstrip('/')==origin and req.method in (('GET','HEAD') if req.path in AI_PAGES else ('POST','HEAD'))
  if req.method not in ('GET','HEAD') or req.host_url.rstrip('/')!=origin:return False
  if coverage_ui and req.path in COVERAGE_UI_PATHS:return True
  if (brics_on and req.path in BRICS_PATHS) or (weekly_on and req.path in WEEKLY_PATHS) or req.path in READ_PATHS or req.path=='/' or (finder_rates and req.path in PATHS) or (code_news and req.path in CODE_PATHS) or (weather_on and req.path==WEATHER_PATH) or (weather_ui_on and req.path in WEATHER_UI_PATHS):return True
  if req.path.startswith('/workspace/assets/'):return req.path.removeprefix('/workspace/assets/')in ASSETS
  if req.path.startswith('/workspace/branding/'):return req.path.removeprefix('/workspace/branding/')in BRANDING
  return False
 app=create_app(reader=lambda:{'geo':[],'brics':[]},authorize=allow,allowed_origin=origin)
 if m2_on:m2_install(app,origin,lambda:{'geo':[],'brics':[]})
 elif map_on:map_install(app,origin)
 if m3_on:m3_install(app,origin)
 if ai_on:ai_install(app,origin)
 if brics_news_on:brics_news_install(app,origin)
 if brics_on:brics_install(app)
 if weekly_on:weekly_install(app,lambda:{'geo':[],'brics':[]})
 from integration.news_finder_navigation_prep import install_mount
 install_mount(app)
 if coverage_ui:coverage_ui_install(app,environ,coverage_available=False)
 if finder_rates:install(app,origin)
 if weather_ui_on:weather_ui_install(app,weather_available=weather_on)
 if weather_on:
  from pathlib import Path
  weather_install(app,origin,environ,source_path=Path(__file__).resolve().parents[1]/'src/worldports.ts')
 if code_news:code_install(app,origin,lambda:{'geo':[],'brics':[]})
 if relationship_on:relationship_install(app,origin)
 if tariff_on:tariff_install(app,origin,tariff_snapshot)
 @app.before_request
 def coverage_off_paths():
  from flask import jsonify
  if (request.path in COVERAGE_UI_PATHS and not coverage_ui)or(request.path=='/api/code-news-coverage'and not False):return jsonify(state='unavailable'),404
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
  if request.path=='/workspace' and response.status_code==200:
   response.direct_passthrough=False
   html=response.get_data(as_text=True)
   html=html.replace('GEO INTEL MONITOR · PRIVATE PREVIEW','GEO INTEL MONITOR · PUBLIC SAMPLE PREVIEW')
   html=html.replace('Geo news dashboard. Collection, mail and scraper remain off.','Public empty-sample dashboard. No stored news or private data. Collection, mail and scraper remain off.')
   html=html.replace('src="/workspace/finder/index.html"','src="/workspace/finder/live.html"' if finder_rates else 'src="/workspace/finder/offline.html"')
   # These heavier/private workflows are deliberately outside the public scope.
   if not weekly_on:html=html.replace('<a href="/workspace/weekly">Weekly PDF</a>','')
   if not brics_on:html=html.replace('<a href="/workspace/brics-streams">BRICS streams</a>','')
   html=html.replace('<button data-view="live" aria-pressed="false">Live news</button>','').replace('<button data-view="channels" aria-pressed="false">My channels</button>','')
   html=html.replace('<script type="module" src="/workspace/assets/live_news.js"></script>','')
   response.set_data(html)
  response.headers['X-Preview-Mode']='public_empty_sample'
  return response
 app.extensions.update(preview_launcher_mode='public_empty_sample',read_only_news_clients=[],stored_news_projects=('geo',),geo_events_read_enabled=False)
 return app
