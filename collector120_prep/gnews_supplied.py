"""Inactive hash-pinned original GNews over supplied SDK outcomes. No clients."""
import ast,hashlib
from pathlib import Path
from datetime import datetime,timezone
from collector110_prep.input_budget import capture
from collector115_prep.profile import compile_profile
from intelligence.geo.processing.classifier import classify,strip_html
from intelligence.geo.processing.dedupe import dedupe_articles
ROOT=Path(__file__).resolve().parents[1]
PIN='b2d2ba35db61a47993d1bb3a50b2677e02e677f1a3758756eb514033d457bcdc'
class GNewsRefused(ValueError):pass
class SuppliedWriteOutcomeError(ValueError):pass

def prepare_supplied_gnews(settings,outcomes,*,clock,available=True):
 p=compile_profile(settings)
 for path,h in {'intelligence/geo/processing/classifier.py':'7c23324b2cbbc3b05f5e118a29456e0616e56146417bbbec65c5daf0559f38f0','intelligence/geo/processing/dedupe.py':'8326042d8a2adccafc690f86c47cc9baa67240792ef90060750313c81fb7382e'}.items():
  if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=h:raise GNewsRefused('Processing source drift')
 if type(clock)is not datetime or type(clock.tzinfo)is not timezone or type(available)is not bool:raise GNewsRefused('Exact clock/provider availability')
 if type(outcomes)is not dict or len(outcomes)>3:raise GNewsRefused('Supplied SDK mapping')
 if any(type(q)is not str or len(q)>2000 for q in outcomes):raise GNewsRefused('Exact bounded query')
 records=capture({'outcome_records':[{'query':q,'outcome':o}for q,o in list(outcomes.items())]})['captured']['outcome_records']
 bounded={r['query']:r['outcome']for r in records}
 raw=(ROOT/'intelligence/geo/collectors/gnews_search.py').read_bytes()
 if hashlib.sha256(raw).hexdigest()!=PIN:raise GNewsRefused('Original GNews drift')
 config=(ROOT/'intelligence/geo/config.py').read_bytes()
 if hashlib.sha256(config).hexdigest()!='42d014d1b5134a24c10ccafdc23200e2b91a4ea19fa6466091beb97e8043e5cb':raise GNewsRefused('Original config drift')
 tree=ast.parse(config);group_node=next(n.value for n in tree.body if type(n)is ast.Assign and any(type(t)is ast.Name and t.id=='GNEWS_QUERY_GROUPS'for t in n.targets))
 groups=ast.literal_eval(group_node);queries=[' OR '.join(g)for g in groups]
 expected=set(queries)if p['source_flags']['ENABLE_GNEWS']and available else set()
 if set(bounded)!=expected:raise GNewsRefused('Missing or unused query outcome')
 for query,o in bounded.items():
  if type(o)is not dict or set(o)!={'state','results'} or o['state']not in ('ok','error') or type(o['results'])is not list or len(o['results'])>100 or o['state']=='error'and o['results']:raise GNewsRefused('SDK outcome shape')
  for r in o['results']:
   if type(r)is not dict or set(r)-{'title','url','description','publisher'}:raise GNewsRefused('Closed SDK result')
   if any(type(r.get(k,''))is not str for k in ('title','url','description')):raise GNewsRefused('Exact SDK strings')
   pub=r.get('publisher',{})
   if type(pub)is not dict or set(pub)-{'title'}or type(pub.get('title','Google News'))is not str:raise GNewsRefused('Publisher shape')
 result={'scope':'inactive_original_gnews_supplied','state':'disabled_by_config','documents':[],
         'query_trace':[],'backup':'held_pending_durable_adapter','network':False,'writes':False,'delivery':False,'production_ready':False,
         'pending_gates':['real_gnews_sdk_transport_isolation','backup_adapter','source_health']}
 if not p['source_flags']['ENABLE_GNEWS']:return result
 defs=[n for n in ast.parse(raw).body if type(n)is ast.FunctionDef and n.name in ('collect','_build_queries')]
 if len(defs)!=2:raise GNewsRefused('Original definitions')
 for node in defs:
  if node.decorator_list or any(isinstance(n,(ast.Import,ast.ImportFrom,ast.Global,ast.Nonlocal,ast.ClassDef,ast.With))for n in ast.walk(node)):raise GNewsRefused('Original AST structure')
 class Clock:
  @staticmethod
  def now(tz):return clock.astimezone(tz)
 class Client:
  def __init__(self,**kwargs):result['client_config']=kwargs
  def get_news(self,q):
   result['query_trace'].append(q);o=bounded[q]
   if o['state']=='error':raise ValueError('Supplied source error')
   return o['results']
 def save(docs):result['documents']=capture({'documents':docs})['captured']['documents'];return len(docs)
 log=[]
 scope={'__builtins__':{'print':lambda *a:log.append(1),'set':set,'Exception':Exception},
        'HAS_GNEWS':available,'GNews':Client,'GNEWS_LANGUAGE':'en','GNEWS_COUNTRY':'US','GNEWS_PERIOD':'1d','GNEWS_MAX_RESULTS':15,
        'GNEWS_QUERY_GROUPS':groups,'DEDUPE_THRESHOLD':p['threshold'],'ACTIVE_CATEGORIES':p['active_categories'],
        'ENABLE_TELEGRAM_BACKUP':p['source_flags']['ENABLE_TELEGRAM_BACKUP'],'classify':classify,'strip_html':strip_html,
        'ArticleWriteOutcomeError':SuppliedWriteOutcomeError,'dedupe_articles':dedupe_articles,'save_articles_bulk':save,'datetime':Clock,'timezone':timezone}
 exec(compile(ast.Module(body=defs,type_ignores=[]),'original-supplied-gnews','exec'),scope)
 scope['collect']();result['state']='prepared'if available else 'sdk_unavailable'
 result['coarse_source_error_count']=len(log)
 return result
