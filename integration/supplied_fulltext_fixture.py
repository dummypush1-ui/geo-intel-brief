"""Supplied extraction outcome experiment only. No fetch, real extractor or Telegram."""
import ast,hashlib,math,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PINS={'intelligence/geo/collectors/rss.py':'a7cbdeac2e7645e2477ecf64a9ad9cbf00d1ccf71b18235228d75ccaca3cbd41','intelligence/geo/processing/extract.py':'42aa24d7cb788d45ee5c22e0c4c45ffe901d32fff3ab82227575ffc299eee44a','integration/geo_collector_contract.py':'3d35ed17b5df48b580a705100cf1e0aaa596f8fb948d12c128d6f00be2022f3d','intelligence/geo/processing/classifier.py':'7c23324b2cbbc3b05f5e118a29456e0616e56146417bbbec65c5daf0559f38f0','intelligence/geo/processing/dedupe.py':'8326042d8a2adccafc690f86c47cc9baa67240792ef90060750313c81fb7382e','integration/fake_collection_writer.py':'f209fe293d3fab5702476682b9b7d3a659ddaea466dc3e9d88e52a56dbd05c64'}
class FulltextRefused(ValueError):pass
class Budget:
 def __init__(self):self.nodes=0;self.size=0
 def take(self,value):
  self.nodes+=1
  if self.nodes>5000:raise FulltextRefused('fixture node budget')
  if type(value) is str:
   if len(value)>10000:raise FulltextRefused('fixture text budget')
   try:self.size+=len(value.encode('utf8'))
   except UnicodeError:raise FulltextRefused('fixture UTF8 text required') from None
   if self.size>1048576:raise FulltextRefused('fixture byte budget')
  elif type(value) is datetime:self.size+=len(value.isoformat())
  elif type(value) is list:
   for v in value:self.take(v)
  elif type(value) is dict:
   for k,v in value.items():self.take(k);self.take(v)
  elif value is None or type(value) in (int,float,bool):pass
  else:raise FulltextRefused('fixture scalar required')
def _text(v,nonempty=False):
 if type(v) is not str or len(v)>10000 or nonempty and not v.strip():raise FulltextRefused('fixture bounded text required')
 return v
def _definitions():
 sources={}
 for p,h in PINS.items():
  b=(ROOT/p).read_bytes()
  if hashlib.sha256(b).hexdigest()!=h:raise FulltextRefused('reviewed source drift')
  sources[p]=b
 defs=[]
 for path,name,names in [('intelligence/geo/processing/extract.py','extract_full_text',{'url','max_chars','HAS_TRAFILATURA','trafilatura','downloaded','text','len','Exception'}),('intelligence/geo/collectors/rss.py','_enrich_with_full_text',{'articles','ENABLE_FULL_TEXT','process','art','extract_full_text','FULL_TEXT_MAX_CHARS','ThreadPoolExecutor','FULL_TEXT_WORKERS','executor','list','len','full'})]:
  matches=[n for n in ast.parse(sources[path]).body if type(n) is ast.FunctionDef and n.name==name]
  if len(matches)!=1:raise FulltextRefused('reviewed definition required')
  node=matches[0]
  for n in ast.walk(node):
   if isinstance(n,(ast.Import,ast.ImportFrom,ast.Global,ast.Nonlocal,ast.ClassDef,ast.AsyncFunctionDef)) or isinstance(n,ast.Name) and n.id not in names:raise FulltextRefused('reviewed AST allowlist')
  if node.decorator_list or any(isinstance(n,ast.Attribute) and n.attr not in ('fetch_url','extract','strip','map') for n in ast.walk(node)):raise FulltextRefused('reviewed AST attributes')
  defs.append(node)
 return defs
class _Provider:
 def __init__(self,outcomes):self.outcomes=outcomes;self.trace=[];self.current=None
 def fetch_url(self,url):
  self.trace.append({'call':'download','url':url,'occurrence':len(self.trace)});self.current=url;o=self.outcomes[url]
  if o['download']=='error':raise ValueError('inert download fault')
  return url if o['download']=='text' else '' # opaque supplied handle, NOT parsed HTML
 def extract(self,downloaded,**flags):
  assert downloaded==self.current and flags=={'include_comments':False,'include_tables':False}
  self.trace.append({'call':'extract','url':downloaded,'occurrence':len(self.trace)});o=self.outcomes[downloaded]
  if o['extract']=='error':raise ValueError('inert extraction fault')
  return o['text'] if o['extract']=='text' else ''
class _Executor:
 def __init__(self,**kwargs):assert kwargs=={'max_workers':1}
 def __enter__(self):return self
 def __exit__(self,*args):return False
 def map(self,fn,rows):return [fn(row) for row in rows]
def prepare_supplied_fulltext(candidates,outcomes,*,enabled=True,available=True,max_chars=700,categories=('TRADE',),threshold=.85):
 if type(enabled) is not bool or type(available) is not bool or type(max_chars) is not int or not 1<=max_chars<=9997 or type(threshold) not in (int,float) or not math.isfinite(threshold) or not 0<threshold<=1:raise FulltextRefused('fixture exact config')
 if type(candidates) is not list or len(candidates)>100 or type(outcomes) is not dict or len(outcomes)>100 or type(categories) not in (list,tuple) or not 1<=len(categories)<=20:raise FulltextRefused('fixture containers')
 if any(type(c) is not str or not 1<=len(c)<=100 for c in categories):raise FulltextRefused('fixture category contract')
 cats=list(categories);rows=[];expected=set();budget=Budget();budget.take(cats)
 for row in candidates:
  if type(row) is not dict or len(row)!=6 or any(type(k) is not str for k in row) or set(row)!={'title','url','source','summary','published','credibility'}:raise FulltextRefused('closed candidate fields')
  r={k:_text(row[k],k!='summary') for k in ('title','url','source','summary','credibility')}
  if len(r['url'])>2000 or r['url']!=r['url'].strip() or r['title']!=r['title'].strip() or r['credibility'] not in ('HIGH','MEDIUM','LOW'):raise FulltextRefused('fixture candidate boundary')
  d=row['published']
  if type(d) is not datetime or type(d.tzinfo) is not timezone:raise FulltextRefused('fixed offset date required')
  try:year=d.astimezone(timezone.utc).year
  except (OverflowError,ValueError):raise FulltextRefused('fixture date boundary') from None
  if not 1970<=year<=2100:raise FulltextRefused('fixture date boundary')
  r['published']=d;budget.take(r);rows.append(r)
  if enabled and available and len(r['summary'])<200:expected.add(r['url'])
 supplied={}
 for url,o in outcomes.items():
  _text(url,True)
  if type(o) is not dict or len(o)!=3 or any(type(k) is not str for k in o) or set(o)!={'download','extract','text'}:raise FulltextRefused('closed outcome required')
  c={k:_text(o[k]) for k in ('download','extract','text')}
  if c['download'] not in ('text','empty','error') or c['extract'] not in ('text','empty','error') or c['extract']!='text' and c['text'] or c['download']!='text' and (c['extract']!='empty' or c['text']):raise FulltextRefused('fixture outcome consistency')
  budget.take(url);budget.take(c);supplied[url]=c
 if set(supplied)!=expected:raise FulltextRefused('missing or unused fixture outcome')
 definitions=_definitions();provider=_Provider(supplied)
 scope={'__builtins__':{'len':len,'list':list,'Exception':Exception},'HAS_TRAFILATURA':available,'ENABLE_FULL_TEXT':enabled,'FULL_TEXT_MAX_CHARS':max_chars,'FULL_TEXT_WORKERS':1,'trafilatura':provider,'ThreadPoolExecutor':_Executor}
 exec(compile(ast.Module(body=definitions,type_ignores=[]),'reviewed-supplied-fulltext','exec'),scope)
 enriched=scope['_enrich_with_full_text'](rows)
 # Budget all outputs BEFORE downstream composition/publication.
 output_budget=Budget();output_budget.take(enriched);output_budget.take(provider.trace)
 from integration.geo_collector_contract import prepare_geo_documents
 documents=prepare_geo_documents(enriched,cats,threshold)['documents']
 output_budget.take(documents)
 return {'state':'supplied_fulltext_preparation_only','scope':'PRIVATE supplied text, not fetched/verified/lossless full article','candidates':enriched,'documents':documents,'trace':provider.trace,'candidate_count':len(rows),'prepared_count':len(documents),'network':False,'writes':False,'delivery':False,'telegram_backup':'unwired_not_dropped'}
