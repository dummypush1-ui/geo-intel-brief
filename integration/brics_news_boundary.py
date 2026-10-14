"""Typed supplied-fixture BRICS boundary. No configured store or Geo fallback.
The fixture policy is explicit input, never an assertion about live settings.
"""
from dataclasses import dataclass
from datetime import datetime,timezone,timedelta
import hashlib,json,re,unicodedata
from urllib.parse import urlsplit
from integration.brics_processing_offline import is_brics_relevant
from integration.text_matching.matcher import contains
MAX_ROWS=100
MAX_BYTES=250000
FIELDS=frozenset(('url','title','summary','source','country','category','published','collected_at','corroborated_by'))

def text(v,cap):
 if type(v)is not str or len(v)>cap or len(v.encode('utf-8'))>cap*4:raise ValueError('Bounded string required')
 return ''.join(c for c in v if unicodedata.category(c) not in ('Cc','Cf','Cs')).strip()
def stamp(v,naive=False):
 if v is None:return None
 if type(v)is datetime:d=v
 elif type(v)is str and len(v)<=100:d=datetime.fromisoformat(v.replace('Z','+00:00'))
 else:raise ValueError('ISO date required')
 if d.tzinfo is None:
  if not naive:raise ValueError('Publication date timezone required')
  d=d.replace(tzinfo=timezone.utc)
 return d.astimezone(timezone.utc).isoformat().replace('+00:00','Z')
@dataclass(frozen=True)
class BricsFixtureReader:
 """Explicit fixture callback, identity and configured keyword snapshot.
 Kept separate from ReadOnlyNewsReader and all store constructors.
 """
 read: object
 source_identity: object
 critical_keywords: tuple
 label: str='supplied offline fixtures, not live news'
 def __post_init__(self):
  if not callable(self.read) or self.source_identity is None or type(self.critical_keywords)is not tuple or not 1<=len(self.critical_keywords)<=30:raise ValueError('Explicit fixture reader required')
  if any(type(k)is not str or not text(k,80) for k in self.critical_keywords):raise ValueError('Keyword snapshot required')
  if self.label!='supplied offline fixtures, not live news':raise ValueError('Fixture label required')
def project(raw,keywords):
 if type(raw)is not dict:raise ValueError('Plain BRICS row required')
 # Unknown/private fields ignored, never stringified or serialized.
 row={k:v for k,v in raw.items() if k in FIELDS}
 out={k:text(row.get(k,''),8000 if k=='summary' else 2048 if k in ('url','title') else 200) for k in ('url','title','summary','source','country','category')}
 p=urlsplit(out['url'])
 if p.scheme!='https' or not p.hostname or p.username or p.password or p.port not in (None,443) or re.search(r'[\s\\]',out['url']) or not out['title']:raise ValueError('Safe supplied story required')
 out['published_at']=stamp(row.get('published'))
 out['collected_at']=stamp(row.get('collected_at'),naive=True)
 corroboration=row.get('corroborated_by')
 if corroboration is None:out.update(corroboration_state='unknown, not cleared',corroboration_count=None)
 else:
  if type(corroboration)is not list or len(corroboration)>30:raise ValueError('Corroboration list required')
  sources={text(v,200)for v in corroboration}
  if ''in sources:raise ValueError('Corroboration source required')
  out.update(corroboration_state='supplied source list, not independently verified',corroboration_count=len(sources))
 body=out['title']+' '+out['summary'];out['critical_keyword_match']=any(contains(body.lower(),k.lower().strip())for k in keywords)
 out['brics_relevant']=is_brics_relevant(out)
 out['article_key']=hashlib.sha256(('brics\0'+out['url']).encode()).hexdigest()
 # No Geo risk/credibility enum is admitted.
 return out
class Service:
 def __init__(self,reader=None,*,geo_identity=None,now=lambda:datetime.now(timezone.utc)):
  if reader is not None and type(reader)is not BricsFixtureReader:raise ValueError('Exact typed fixture reader required')
  if reader is not None and reader.source_identity is geo_identity:raise ValueError('Separate BRICS fixture identity required')
  self.reader=reader;self.now=now;self.geo_identity=geo_identity
 def run(self):
  if self.reader is None:return {'state':'source_not_connected','message':'BRICS news source not connected. No BRICS news data supplied.'},200
  try:
   if type(self.reader)is not BricsFixtureReader or self.reader.source_identity is self.geo_identity:raise ValueError('Fixture identity changed')
   self.reader.__post_init__()
   raw=self.reader.read()
   if type(raw)is not list or len(raw)>MAX_ROWS:raise ValueError('Row bound')
   items=[project(r,self.reader.critical_keywords)for r in raw]
   now=self.now()
   if type(now)is not datetime or now.tzinfo is None:raise ValueError('UTC clock required')
   critical=[];unknown=0
   for r in items:
    if r['critical_keyword_match'] and r['brics_relevant']:
     if r['collected_at'] is None:unknown+=1;continue
     age=now.astimezone(timezone.utc)-datetime.fromisoformat(r['collected_at'].replace('Z','+00:00'))
     if timedelta(0)<=age<timedelta(hours=24):critical.append(r['article_key'])
   result=dict(state='supplied_fixture',message=self.reader.label,scope='bounded_supplied_brics_fixture_not_full_store',date_policy='collected_at naive means UTC; publication requires explicit timezone; not publication recency',critical_policy='explicit supplied keyword snapshot + BRICS relevance + collected UTC (now-24h,now]; unknown corroboration is not cleared',items=items,relevant_count=sum(r['brics_relevant']for r in items),critical_24h_keys=critical,critical_time_unknown_count=unknown)
   if len(json.dumps(result,ensure_ascii=True,separators=(',',':')).encode())>MAX_BYTES:raise ValueError('Byte bound')
   return result,200
  except Exception:return {'state':'unavailable','message':'Supplied BRICS fixture unavailable. No Geo fallback.'},503
