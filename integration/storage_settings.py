"""Environment settings with original defaults. No connection on import."""
from dataclasses import dataclass,field
import os
@dataclass(frozen=True)
class StorageSettings:
 geo_database:str='geo_intel'
 geo_articles:str='articles'
 geo_events:str='events'
 brics_backend:str='mongodb'
 brics_database:str='newsbot'
 brics_articles:str='articles'
 brics_sqlite_path:str='data/newsbot.db'
 geo_uri:str=field(default='',repr=False)
 brics_uri:str=field(default='',repr=False)
 read_enabled:bool=False
 @classmethod
 def from_env(cls,environ=None):
  e=os.environ if environ is None else environ
  # Separate project overrides prevent the two legacy MONGODB_URI names colliding.
  settings=cls(
   geo_database=e.get('GEO_MONGODB_DB_NAME',e.get('MONGODB_DB_NAME','geo_intel')),
   geo_articles=e.get('GEO_ARTICLES_COLLECTION','articles'),
   geo_events=e.get('GEO_EVENTS_COLLECTION','events'),
   brics_backend=e.get('BRICS_STORAGE_BACKEND',e.get('STORAGE_BACKEND','mongodb')).lower(),
   brics_database=e.get('BRICS_MONGODB_DB',e.get('MONGODB_DB','newsbot')),
   brics_articles=e.get('BRICS_ARTICLES_COLLECTION','articles'),
   brics_sqlite_path=e.get('BRICS_SQLITE_PATH',e.get('SQLITE_PATH','data/newsbot.db')),
   geo_uri=e.get('GEO_MONGODB_URI',e.get('MONGODB_URI','')),
   brics_uri=e.get('BRICS_MONGODB_URI',e.get('MONGODB_URI','')),
   read_enabled=e.get('NEWS_READ_ENABLED','false').lower()=='true')
  if settings.brics_backend not in ('sqlite','mongodb'):raise ValueError('Unsupported BRICS backend')
  if any(not v.strip() for v in (settings.geo_database,settings.geo_articles,settings.geo_events,settings.brics_database,settings.brics_articles,settings.brics_sqlite_path)):raise ValueError('Storage labels must not be blank')
  return settings
