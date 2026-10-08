"""Original post-fetch RSS candidate/document contract, offline only.

Hash-pinned AST definitions, not original module imports. Caller supplies
already-fetched/enriched candidates. No fetch, full-text, threads, Telegram,
SMTP, MongoDB, scheduler, environment or arbitrary writer callback.
"""
import ast,hashlib,math
from copy import deepcopy
from datetime import datetime,timezone
from pathlib import Path
from integration.fake_collection_writer import plain
from dateutil.tz import tzutc,tzoffset,tzlocal

ROOT=Path(__file__).resolve().parents[1]
RSS_PIN='a7cbdeac2e7645e2477ecf64a9ad9cbf00d1ccf71b18235228d75ccaca3cbd41'

PROCESSING_PINS={'intelligence/geo/processing/classifier.py':'7c23324b2cbbc3b05f5e118a29456e0616e56146417bbbec65c5daf0559f38f0','intelligence/geo/processing/dedupe.py':'8326042d8a2adccafc690f86c47cc9baa67240792ef90060750313c81fb7382e'}
def _original_documents(candidates,categories,threshold):
 for path,pin in PROCESSING_PINS.items():
  if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=pin:raise ValueError('Original processing source review required')
 from intelligence.geo.processing.classifier import classify
 from intelligence.geo.processing.dedupe import dedupe_articles
 source=(ROOT/'intelligence/geo/collectors/rss.py').read_bytes()
 if hashlib.sha256(source).hexdigest()!=RSS_PIN:raise ValueError('Original RSS source review required')
 tree=ast.parse(source)
 collect=next(n for n in tree.body if type(n) is ast.FunctionDef and n.name=='collect')
 # Exact reviewed four statements: classification loop, dedupe assignment,
 # active-category filter, original document comprehension. Not collect().
 nodes=collect.body[5:9]
 if len(nodes)!=4 or type(nodes[0]) is not ast.For or any(isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef,ast.With,ast.Try)) for node in nodes for n in ast.walk(node)):raise ValueError('Original RSS contract review required')
 scope={'__builtins__':{},'candidates':candidates,'classify':classify,'dedupe_articles':dedupe_articles,'DEDUPE_THRESHOLD':threshold,'ACTIVE_CATEGORIES':categories}
 exec(compile(ast.Module(body=nodes,type_ignores=[]),'original-reviewed-rss-contract','exec'),scope)
 return scope['docs']

class GeoFixtureStore:
 """Exact in-memory article insert-only fixture, never a Mongo adapter."""
 def __init__(self):self._rows={}
 def snapshot(self):return deepcopy(self._rows)
 def __init_subclass__(cls,**kwargs):raise TypeError('Fixture cannot be subclassed')

def prepare_geo_documents(candidates,active_categories,threshold):
 if type(candidates) is not list or len(candidates)>1000 or type(active_categories) is not list or not 1<=len(active_categories)<=20 or any(type(c) is not str or not 1<=len(c)<=100 for c in active_categories) or type(threshold) not in (int,float) or not math.isfinite(threshold) or not 0<threshold<=1:raise ValueError('Explicit bounded candidates/categories/threshold required')
 rows=[]
 for row in candidates:
  if type(row) is not dict or len(row)>100 or any(type(k) is not str for k in row):raise ValueError('Plain candidate row required')
  # Input dates require exact zoned datetime here, matching original fetcher
  # shape. Fixed-offset zones only, no custom tzinfo hooks; no unknown objects.
  published=row.get('published')
  if type(published) is not datetime or type(published.tzinfo) not in (timezone,tzutc,tzoffset,tzlocal):raise ValueError('Reviewed original aware published datetime required')
  # Preserve original offset/instant/ISO representation while removing the
  # reviewed dateutil tz object from downstream fixture state.
  offset=published.utcoffset()
  if offset is None:raise ValueError('Aware published datetime required')
  normalized=published.replace(tzinfo=timezone(offset))
  if normalized.isoformat()!=published.isoformat():raise ValueError('Published ISO contract mismatch')
  copy={k:v for k,v in row.items() if k!='published'}
  if not plain(copy) or any(type(row.get(k)) is not str or not row[k].strip() for k in ('title','url','source')) or type(row.get('summary')) is not str:raise ValueError('Bounded plain candidate text required')
  credibility=row.get('credibility','MEDIUM')
  if type(credibility) is not str or credibility not in ('HIGH','MEDIUM','LOW'):raise ValueError('Exact credibility required')
  # Preserve fetched fields only; caller cannot seed ID/emailed/time/Telegram.
  rows.append({k:deepcopy(row[k]) for k in ('title','url','source','summary','credibility') if k in row}|{'published':normalized})
 docs=_original_documents(rows,list(active_categories),threshold)
 return {'state':'original_post_fetch_docs_only','candidate_count':len(candidates),'prepared_count':len(docs),'documents':docs,'network':False,'writes':False,'delivery':False,'telegram_backup':'unwired_not_dropped'}

def run_geo_fixture_cycle(candidates,active_categories,threshold,clock,store,failed_urls=()):
 if type(store) is not GeoFixtureStore or type(store._rows) is not dict or len(store._rows)>1000 or any(type(k) is not str or not plain(v) for k,v in store._rows.items()):raise ValueError('Exact plain fixture store required')
 if type(clock) is not datetime or type(clock.tzinfo) is not timezone:raise ValueError('Explicit aware created clock required')
 if type(failed_urls) not in (list,tuple) or len(failed_urls)>1000 or any(type(u) is not str or len(u)>10000 for u in failed_urls):raise ValueError('Explicit bounded fixture failures required')
 prepared=prepare_geo_documents(candidates,active_categories,threshold)
 if len(set(store._rows)|{d['url'] for d in prepared['documents'] if d['url'] not in failed_urls})>1000:raise ValueError('Fixture retained row budget exceeded')
 outcomes=[];stamp=clock.astimezone(timezone.utc).isoformat()
 for doc in prepared['documents']:
  url=doc['url']
  if url in failed_urls:state='failed'
  elif url in store._rows:state='duplicate'
  else:
   copy=deepcopy(doc);copy.setdefault('created_at',stamp);store._rows[url]=copy;state='inserted'
  outcomes.append({'url':url,'state':state})
 return {'state':'original_geo_in_memory_store_only','candidate_count':prepared['candidate_count'],'prepared_count':prepared['prepared_count'],'outcomes':outcomes,'inserted_count':sum(r['state']=='inserted' for r in outcomes),'duplicate_count':sum(r['state']=='duplicate' for r in outcomes),'failed_count':sum(r['state']=='failed' for r in outcomes),'network':False,'live_writes':False,'delivery':False,'telegram_backup':'unwired_not_dropped'}
