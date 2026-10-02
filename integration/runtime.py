"""Explicit private preview composition. No legacy service import or writes.

Store validation is a review gate, not proof supplied by this module. An operator
must verify database/collection ownership before NEWS_STORE_MAPPING_VERIFIED is
set. Clients are created only when read access is explicitly enabled. Preview
access is single-worker only; no public account registration is provided.
"""
from integration.storage_settings import StorageSettings
from integration.storage_reader import ReadOnlyNewsReader
from integration.preview_access import create_preview_from_env
from integration.finder_index import load_bundled_index
from pathlib import Path

def compose(environ,client_factory=None):
 settings=StorageSettings.from_env(environ)
 clients=[];reader=None;finder_config={}
 if environ.get('PREVIEW_ACCESS_ENABLED','false').lower()=='true':
  index=load_bundled_index(Path(__file__).resolve().parents[1])
  finder_config={'finder_context_reader':index.for_article,'finder_base':environ.get('PREVIEW_ORIGIN','').rstrip('/')+'/workspace/finder/index.html','finder_index_verified':True}
 if settings.read_enabled:
  if environ.get('PREVIEW_ACCESS_ENABLED','false').lower()!='true':raise ValueError('Private preview access required for live reads')
  if environ.get('NEWS_STORE_MAPPING_VERIFIED','false').lower()!='true':raise ValueError('Store ownership/schema review required')
  if settings.brics_backend!='mongodb':raise ValueError('This runtime requires reviewed MongoDB stores')
  if not environ.get('GEO_MONGODB_URI') or not environ.get('BRICS_MONGODB_URI'):raise ValueError('Both reviewed project URIs required')
  if (settings.geo_uri,settings.geo_database,settings.geo_articles)==(settings.brics_uri,settings.brics_database,settings.brics_articles):raise ValueError('Geo and BRICS stores must remain isolated')
  # Validate access config BEFORE any client creation or network read.
  app=create_preview_from_env(environ,branding_public_base=environ.get('MERGED_PUBLIC_BASE_URL') or None)
  if client_factory is None:
   from pymongo import MongoClient
   client_factory=MongoClient
  try:
   geo=client_factory(settings.geo_uri,serverSelectionTimeoutMS=5000,connect=False)
   clients.append(geo)
   brics=client_factory(settings.brics_uri,serverSelectionTimeoutMS=5000,connect=False)
   clients.append(brics)
   stores={'geo':geo[settings.geo_database][settings.geo_articles],'brics':brics[settings.brics_database][settings.brics_articles]}
   reader=ReadOnlyNewsReader(stores,verified=True,limit=100)
  except Exception:
   for client in clients:client.close()
   raise
 # Fixture-free reads are empty unless the explicit reviewed config above is on.
 app=create_preview_from_env(environ,reader=reader,**finder_config,branding_public_base=environ.get('MERGED_PUBLIC_BASE_URL') or None)
 app.extensions['read_only_news_clients']=clients
 return app
