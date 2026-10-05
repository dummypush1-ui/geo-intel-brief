"""Explicit offline-reviewed preview launcher selection, no deployment effects.

Geo-only opt-in is default off and does not enable reads. The Geo-only path has
no default client factory: future live reads require a separately reviewed
injected factory and all existing read/private/mapping gates. Legacy branch
remains unchanged for rollback, never inferred from missing BRICS settings.
"""
from integration.runtime import compose
from integration.geo_only_runtime import compose_geo_only

def build_preview(environ,client_factory=None):
 if type(environ) is not dict or any(type(k) is not str or type(v) is not str for k,v in environ.items()):raise ValueError('Plain environment strings required')
 flag=environ.get('PREVIEW_GEO_ONLY_ENABLED','false')
 if flag not in ('true','false'):raise ValueError('Exact Geo-only preview flag required')
 if flag=='true':
  for name in ('PREVIEW_ACCESS_ENABLED','NEWS_READ_ENABLED','NEWS_STORE_MAPPING_VERIFIED','GEO_MAPPING_OVERRIDE_VERIFIED','PREVIEW_TRUST_ONE_PROXY','FINDER_NETWORK_PREVIEW_ENABLED'):
   if environ.get(name,'false') not in ('true','false'):raise ValueError('Exact boolean Geo-only preview settings required')
  # Reject ambiguous legacy database label instead of silently ignoring it.
  old=environ.get('GEO_MONGODB_DB_NAME')
  if old and old!=environ.get('GEO_DATABASE','geo_intel'):raise ValueError('Conflicting Geo database labels')
  app=compose_geo_only(environ,client_factory=client_factory)
  app.extensions['preview_launcher_mode']='geo_only'
 else:
  app=compose(environ,client_factory=client_factory)
  app.extensions['preview_launcher_mode']='legacy_isolated'
 return app
