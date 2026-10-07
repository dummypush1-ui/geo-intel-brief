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
 '/api/news','/api/news-stats','/api/dashboard-signals','/api/dashboard-snapshots',
 '/api/sample-volume','/api/critical-stories','/api/source-health',
 '/api/country-page','/api/country-signals','/api/map-data','/api/story-groups',
 '/api/news-export.csv','/workspace/manifest.webmanifest',
 '/workspace/finder/offline.html'))
ASSETS=frozenset(('workspace.js','workspace.css',
 'countries.js','countries.css','map.js','map.css','geo_map_ui.js','geo_map.css'))
BRANDING=frozenset(('favicon.ico','icon-48.png','icon-192.png','icon-512.png',
 'apple-touch-icon.png','og-image.png','logo.svg'))

def build_public_preview(environ,client_factory=None):
 if type(environ) is not dict or any(type(k)is not str or type(v)is not str for k,v in environ.items()):raise ValueError('Plain environment strings required')
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
 def allow(req):
  if req.method not in ('GET','HEAD') or req.host_url.rstrip('/')!=origin:return False
  if req.path in READ_PATHS or req.path=='/':return True
  if req.path.startswith('/workspace/assets/'):return req.path.removeprefix('/workspace/assets/')in ASSETS
  if req.path.startswith('/workspace/branding/'):return req.path.removeprefix('/workspace/branding/')in BRANDING
  return False
 app=create_app(reader=lambda:{'geo':[],'brics':[]},authorize=allow,allowed_origin=origin)
 @app.get('/')
 def home():return redirect('/workspace',302)
 @app.after_request
 def sample_notice(response):
  if request.path=='/workspace' and response.status_code==200:
   response.direct_passthrough=False
   html=response.get_data(as_text=True)
   html=html.replace('GEO INTEL MONITOR · PRIVATE PREVIEW','GEO INTEL MONITOR · PUBLIC SAMPLE PREVIEW')
   html=html.replace('Geo news dashboard. Collection, mail and scraper remain off.','Public empty-sample dashboard. No stored news or private data. Collection, mail and scraper remain off.')
   html=html.replace('src="/workspace/finder/index.html"','src="/workspace/finder/offline.html"')
   # These heavier/private workflows are deliberately outside the public scope.
   html=html.replace('<a href="/workspace/weekly">Weekly PDF</a>','').replace('<a href="/workspace/brics-streams">BRICS streams</a>','')
   html=html.replace('<button data-view="live" aria-pressed="false">Live news</button>','').replace('<button data-view="channels" aria-pressed="false">My channels</button>','')
   html=html.replace('<script type="module" src="/workspace/assets/live_news.js"></script>','')
   response.set_data(html)
  response.headers['X-Preview-Mode']='public_empty_sample'
  return response
 app.extensions.update(preview_launcher_mode='public_empty_sample',read_only_news_clients=[],stored_news_projects=('geo',),geo_events_read_enabled=False)
 return app

app=build_public_preview(dict(os.environ))
