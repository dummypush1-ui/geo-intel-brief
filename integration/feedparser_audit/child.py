from integration.html_text209 import strip_html_once
"""Fixed synthetic parser child. Resource/network guards, not general sandbox."""
import sys,os,json,resource,hashlib,io,socket,urllib.request,ast,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
resource.setrlimit(resource.RLIMIT_CPU,(3,3));resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024));resource.setrlimit(resource.RLIMIT_FSIZE,(1048576,1048576))
def blocked(*a,**k):raise ValueError('network refused')
socket.socket=blocked;socket.create_connection=blocked;urllib.request.urlopen=blocked;urllib.request.OpenerDirector.open=blocked
import feedparser,feedparser.http,sgmllib,xml.sax,xml.parsers.expat
feedparser.http.get=blocked
from datetime import datetime,timezone
from dateutil import parser
from integration.supplied_feed_fixture import prepare_supplied_feed,_DateParser,_Clock,PINS,ROOT as SOURCE_ROOT
from integration.feedparser_audit.corpus import CORPUS
from integration.publication_dates.policy import publication_date
from integration.supplied_fulltext_fixture import Budget
base=Path(__file__).parent
assert feedparser.__version__=='6.0.11'
pins=json.loads((base/'sdk-pins.json').read_text());sdk=Path(feedparser.__file__).parent
assert {str(p.relative_to(sdk)) for p in sdk.rglob('*.py')}==set(pins)
for p,h in pins.items():assert hashlib.sha256((sdk/p).read_bytes()).hexdigest()==h
assert hashlib.sha256(Path(sgmllib.__file__).read_bytes()).hexdigest()=='9180791aa507111207d7c14f36db574a11fbedda257debfb9d030b273b773f44'
backend=xml.sax.make_parser(feedparser.api.PREFERRED_XML_PARSERS)
assert type(backend).__module__=='xml.sax.expatreader' and xml.parsers.expat.EXPAT_VERSION=='expat_2.4.7'
q=json.loads(sys.stdin.buffer.read(16385));assert set(q)=={'case','cutoff','clock','max_items'}
case=q['case'];assert type(case) is str and case in CORPUS
for s in ('cutoff','clock'):assert type(q[s]) is str and len(q[s])<=100
assert type(q['max_items']) is int and 1<=q['max_items']<=100
blob=CORPUS[case];h=hashlib.sha256(blob).hexdigest();assert h==json.loads((base/'corpus-pins.json').read_text())[case] and len(blob)<=65536
assert not re.search(br'\b(?:SYSTEM|PUBLIC)\b',blob)
clock=datetime.fromisoformat(q['clock']);cutoff=datetime.fromisoformat(q['cutoff'])
# BytesIO bypasses SDK's filename probe. All corpus data fixed internal.
parsed=feedparser.parse(io.BytesIO(blob));assert type(parsed.entries) is list and len(parsed.entries)<=100
rows=[];presence=[]
for e in parsed.entries:
 r={};present=[]
 for k in ('title','link','summary','description','published','updated'):
  # SDK .get alias semantics exactly like original accesses, not raw key lookup.
  v=e.get(k,None)
  if v is not None:
   assert type(v) is str and len(v)<=10000;r[k]=v;present.append(k)
 rows.append(r);presence.append(present)
Budget().take(rows)
selected=prepare_supplied_feed(('Synthetic','https://example.invalid/feed','HIGH'),rows,cutoff=cutoff,fallback_clock=clock,max_items=q['max_items'])
# Independent original AST oracle, real parser BytesIO in same guarded child.
class Response:
 content=blob
 def raise_for_status(self):pass
class Requests:
 def get(self,*a,**kw):return Response()
class Feed:
 def parse(self,b):return feedparser.parse(io.BytesIO(b))
definitions=[];scope={'strip_html_once':strip_html_once,'publication_date':publication_date,'record_date_hold':lambda state:None,'requests':Requests(),'feedparser':Feed(),'REQUEST_TIMEOUT':20,'MAX_ITEMS_PER_FEED':q['max_items'],'dateparser':_DateParser(clock),'datetime':_Clock(clock),'timezone':timezone,'re':re,'print':lambda *a:None}
for p,names in [('intelligence/geo/collectors/rss.py',('_fetch_feed',)),('intelligence/geo/processing/classifier.py',('strip_html','parse_date'))]:
 b=(ROOT/p).read_bytes();assert hashlib.sha256(b).hexdigest()==PINS[p];tree=ast.parse(b);definitions.extend(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names)
 for n in tree.body:
  if isinstance(n,ast.Assign):
   for t in n.targets:
    if isinstance(t,ast.Name) and t.id in ('_HEADERS','_ENTITY_MAP'):scope[t.id]=ast.literal_eval(n.value)
    if isinstance(t,ast.Name) and t.id=='_TAG_RE':scope[t.id]=re.compile(ast.literal_eval(n.value.args[0]))
exec(compile(ast.Module(body=definitions,type_ignores=[]),'independent-original-fixedbytes','exec'),scope)
oracle=scope['_fetch_feed'](('Synthetic','https://example.invalid/feed','HIGH'),cutoff)
assert oracle==selected['candidates']
for r in selected['candidates']:r['published']=r['published'].isoformat()
checks=0
for fn,args in ((socket.socket,()),(urllib.request.urlopen,('https://example.invalid',)),(feedparser.http.get,('https://example.invalid',))):
 try:fn(*args)
 except ValueError:checks+=1
assert checks==3
result={'scope':'PUBLIC SYNTHETIC FIXED-BYTES PARSER EXPERIMENT, NOT LIVE','case':case,'corpus_hash':h,'config_echo':q,'feedparser_version':feedparser.__version__,'backend':'ExpatParser/expat_2.4.7','bozo':bool(parsed.get('bozo',False)),'bozo_label':'parser_flag_only_not_health','field_presence':presence,'candidates':selected['candidates'],'entry_count':len(rows),'oracle_equal':True,'network_guard_checks':checks,'network':False,'writes':False,'delivery':False}
Budget().take(result);sys.stdout.write(json.dumps(result,ensure_ascii=False))
