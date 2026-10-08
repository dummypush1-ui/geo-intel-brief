"""Original feed selection over supplied parsed entries, never requests/feedparser."""
import ast,hashlib,re,math,warnings
from datetime import datetime,timezone
from integration.publication_dates.policy import publication_date
from pathlib import Path
import dateutil
from dateutil import parser
from dateutil.parser import UnknownTimezoneWarning
from dateutil.tz import tzutc,tzoffset,tzlocal
from integration.supplied_fulltext_fixture import Budget,FulltextRefused
ROOT=Path(__file__).resolve().parents[1]
PINS={'intelligence/geo/collectors/rss.py':'a882d01629181b8a14f1d6a2b9a695f3acd7aab83aae7a80165349689f84daef','intelligence/geo/processing/classifier.py':'5a87baba3a28b778d0d6b7a3091129e94a618c45ae346a99e13204790f2787ac'}
class FeedRefused(ValueError):pass
def _date(d):
 if type(d) is not datetime or type(d.tzinfo) not in (timezone,tzutc,tzoffset,tzlocal):raise FeedRefused('fixture reviewed aware date')
 try:
  offset=d.utcoffset();fixed=d.replace(tzinfo=timezone(offset));year=fixed.astimezone(timezone.utc).year
 except (ValueError,OverflowError,TypeError):raise FeedRefused('fixture date boundary') from None
 if not 1970<=year<=2100 or fixed.isoformat()!=d.isoformat():raise FeedRefused('fixture date boundary')
 return fixed
def _text(v,cap=10000):
 if type(v) is not str or len(v)>cap:raise FeedRefused('fixture bounded text')
 return v
def _source():
 sources={}
 for p,h in PINS.items():
  b=(ROOT/p).read_bytes()
  if hashlib.sha256(b).hexdigest()!=h:raise FeedRefused('reviewed source drift')
  sources[p]=ast.parse(b)
 rss=sources['intelligence/geo/collectors/rss.py'];cl=sources['intelligence/geo/processing/classifier.py'];defs=[]
 for tree,name,names,attrs in [(rss,'_fetch_feed',{'feed_spec','cutoff','source','url','credibility','out','resp','requests','REQUEST_TIMEOUT','_HEADERS','feedparser','feed','entry','MAX_ITEMS_PER_FEED','title','link','summary','strip_html','published','parse_date','publication_date','date_state','observed_at','datetime','timezone','record_date_hold','Exception','exc','print'},{'get','raise_for_status','parse','content','entries','strip','append','now','utc'}),(cl,'strip_html',{'text','_TAG_RE','entity','replacement','_ENTITY_MAP','re'},{'sub','items','replace','strip'}),(cl,'parse_date',{'value','publication_date','datetime','timezone'},{'parse','now','utc','tzinfo','replace'})]:
  node=next(n for n in tree.body if type(n) is ast.FunctionDef and n.name==name)
  if node.decorator_list:raise FeedRefused('reviewed AST')
  for n in ast.walk(node):
   if isinstance(n,(ast.Import,ast.ImportFrom,ast.Global,ast.Nonlocal,ast.ClassDef)) or isinstance(n,ast.Name) and n.id not in names or isinstance(n,ast.Attribute) and n.attr not in attrs:raise FeedRefused('reviewed AST allowlist')
  defs.append(node)
 def assignment(tree,name):return next(n.value for n in tree.body if type(n) is ast.Assign and any(type(t) is ast.Name and t.id==name for t in n.targets))
 headers=ast.literal_eval(assignment(rss,'_HEADERS'));entities=ast.literal_eval(assignment(cl,'_ENTITY_MAP'));pattern=assignment(cl,'_TAG_RE')
 if type(pattern) is not ast.Call or not isinstance(pattern.func,ast.Attribute) or pattern.func.attr!='compile' or len(pattern.args)!=1:raise FeedRefused('reviewed regex literal')
 return defs,headers,entities,re.compile(ast.literal_eval(pattern.args[0]))
class _Clock:
 def __init__(self,fixed):self.fixed=fixed
 def now(self,tz):return self.fixed.astimezone(tz)
class _DateParser:
 def __init__(self,fixed):self.fixed=fixed;self.fallbacks=0
 def parse(self,value):
  try:
   with warnings.catch_warnings():
    warnings.simplefilter('error',UnknownTimezoneWarning)
    return parser.parse(value,default=self.fixed.astimezone(timezone.utc).replace(tzinfo=None))
  except Exception:self.fallbacks+=1;raise
class _Response:
 content=b'supplied-entry-handle'
 def __init__(self,mode):self.mode=mode
 def raise_for_status(self):
  if self.mode=='error':raise ValueError('inert source failure')
class _Requests:
 def __init__(self,mode):self.mode=mode;self.trace=[]
 def get(self,url,**kw):self.trace.append({'call':'supplied_http','url':url,'timeout':kw['timeout']});return _Response(self.mode)
class _FeedParser:
 def __init__(self,entries,mode):self.entries=entries;self.mode=mode;self.calls=0
 def parse(self,token):
  assert token==b'supplied-entry-handle';self.calls+=1
  if self.mode=='error':raise ValueError('inert parser failure')
  return self
def prepare_supplied_feed(feed,entries,*,cutoff,fallback_clock,max_items=50,timeout=20,http_mode='ok',parser_mode='ok'):
 if type(feed) not in (tuple,list) or len(feed)!=3 or type(entries) is not list or len(entries)>100:raise FeedRefused('fixture input shape')
 spec=tuple(_text(v,2000) for v in feed)
 if any(not v.strip() for v in spec) or spec[2] not in ('HIGH','MEDIUM','LOW'):raise FeedRefused('fixture feed spec')
 if type(max_items) is not int or not 1<=max_items<=100 or type(timeout) not in (int,float) or not math.isfinite(timeout) or not 0<timeout<=30 or type(http_mode) is not str or http_mode not in ('ok','error') or type(parser_mode) is not str or parser_mode not in ('ok','error'):raise FeedRefused('fixture exact config')
 if dateutil.__version__!='2.9.0.post0':raise FeedRefused('reviewed dateutil version required')
 if type(cutoff) is not datetime or type(cutoff.tzinfo) is not timezone or type(fallback_clock) is not datetime or type(fallback_clock.tzinfo) is not timezone:raise FeedRefused('fixed-offset fixture clocks required')
 cut=_date(cutoff);fixed=_date(fallback_clock);rows=[];budget=Budget()
 try:
  budget.take(list(spec))
  for entry in entries:
   if type(entry) is not dict or len(entry)>6 or any(type(k) is not str for k in entry) or set(entry)-{'title','link','summary','description','published','updated'}:raise FeedRefused('closed supplied entry')
   row={k:_text(v) for k,v in entry.items()};budget.take(row);rows.append(row)
 except FulltextRefused:raise FeedRefused('fixture input budget') from None
 holds={}
 definitions,headers,entities,tag=_source();req=_Requests(http_mode);fp=_FeedParser(rows,parser_mode);dp=_DateParser(fixed);log_count=[]
 scope={'__builtins__':{'Exception':Exception,'print':lambda *a:log_count.append(1)},'requests':req,'feedparser':fp,'REQUEST_TIMEOUT':timeout,'MAX_ITEMS_PER_FEED':max_items,'_HEADERS':headers,'_TAG_RE':tag,'_ENTITY_MAP':entities,'re':re,'publication_date':publication_date,'record_date_hold':lambda state:holds.__setitem__(state,holds.get(state,0)+1),'dateparser':dp,'datetime':_Clock(fixed),'timezone':timezone}
 exec(compile(ast.Module(body=definitions,type_ignores=[]),'reviewed-supplied-feed','exec'),scope)
 out=scope['_fetch_feed'](spec,cut)
 for row in out:row['published']=_date(row['published'])
 try:
  b=Budget();b.take(out);b.take(req.trace)
 except FulltextRefused:raise FeedRefused('fixture output budget') from None
 return {'state':'supplied_parsed_entry_selection_only','scope':'PRIVATE supplied entries, no live HTTP/XML/health proof','candidates':out,'trace':req.trace,'input_count':len(rows),'selected_count':len(out),'parser_calls':fp.calls,'declared_source_mode':'error' if log_count else 'ok','coarse_errors':['supplied_source_error'] if log_count else [],'date_fallback_count':0,'publication_date_holds':holds,'date_policy':'strict aware complete publication; unknown/naive/future held, never now','dateutil_version':dateutil.__version__,'network':False,'writes':False,'delivery':False}
