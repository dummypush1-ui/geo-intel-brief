"""Bounded public projection from exact selected source. Never execute source JS."""
import ast,base64,gzip,io,json,re,hashlib
from integration.finder_composition_f9 import Selection
from integration.public_ai_answers import SYSTEMS,plain,Refused
def source_editions(selection):
 # F8 proves only HS/IN identities. Other system labels bind this exact source
 # hash, explicitly NOT an official-edition proof or currentness assertion.
 digest=next(pin for name,size,pin in selection.binding.files if name=='offline.html')
 return {**{tag:'source-sha256:'+digest for tag in SYSTEMS},**dict(selection.editions)}
class Evidence:
 def __init__(self,selection):
  if type(selection)is not Selection or not selection.report_enabled:raise Refused('Exact F11 selection required')
  selection.verify();self.selection=selection;self.digest=hashlib.sha256(selection.rendered.encode()).hexdigest()
  s=(selection.binding.root/'offline.html').read_text()
  encoded=re.findall(r'var DATA_B64 = "([A-Za-z0-9+/=]+)";',s)
  if len(encoded)!=1:raise Refused('Exact data literal required')
  with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(encoded[0],validate=True)))as stream:raw=stream.read(100_000_001)
  if len(raw)>100_000_000:raise Refused('Bounded data required')
  rows=json.loads(raw);supp=self.literal(s,'US_CH97_SUPPLEMENT');seen={r[1]for r in rows if type(r)is list and r and r[0]==2}
  rows.extend(r for r in supp if r[1]not in seen)
  self.rows={}
  for r in rows:
   if type(r)is not list or len(r)!=6 or type(r[0])is not int or not 0<=r[0]<len(SYSTEMS)or type(r[1])is not str or type(r[2])is not str:raise Refused('Source row schema')
   if re.fullmatch(r'[0-9]{2,12}',r[1]):self.rows[(SYSTEMS[r[0]],r[1])]=r
  self.editions=source_editions(selection)
  self.values={n:self.literal(s,n)for n in ('TRADE6','TRADE_CH','TRADE_PARTNERS','TRADE_TREND','GST_MAP','SCOMET','DOC_BASE_OUT','DOC_EXTRA')}
  # CERT_RULES contains bare JS object keys; do not parse or execute it. Preserve
  # its exact chapter-matched source labels as explicitly unverified strings.
  cert=re.search(r'const CERT_RULES = \[\n(.*?)\n\];',s,re.S)
  if not cert:raise Refused('Certificate source boundary')
  self.certs=[]
  for line in cert[1].splitlines():
   m=re.fullmatch(r"  \{ from: (\d+), to: (\d+), who: ('(?:\\.|[^'\\])*'), what: ('(?:\\.|[^'\\])*'), law: ('(?:\\.|[^'\\])*'), side: '(in|out)' \},?",line)
   if not m:raise Refused('Certificate source seam drift')
   self.certs.append((int(m[1]),int(m[2]),[ast.literal_eval(m[i])for i in (3,4,5)],m[6]))
  self.years={n:self.literal(s,n)for n in ('TRADE_YEAR','TRADE_PARTNERS_YEAR','DATA_BUILD')}
 @staticmethod
 def literal(s,name):
  hits=list(re.finditer(r'(?m)^(?:const|var) '+re.escape(name)+r' = ',s))
  if len(hits)!=1:raise Refused('Exact source declaration required')
  start=hits[0].end();i=start;quote=None;escape=False;depth=0
  while i<len(s)and i-start<=10_000_000:
   c=s[i]
   if quote:
    if escape:escape=False
    elif c=='\\':escape=True
    elif c==quote:quote=None
   elif c in "\"'":quote=c
   elif c in '[{(':depth+=1
   elif c in ']})':depth-=1
   elif c==';'and depth==0:
    text=s[start:i]
    # ast.literal_eval cannot call functions or resolve names. Closed literals
    # with JSON bool/null support only; tokens inside strings stay untouched.
    tree=ast.parse(text,mode='eval')
    class Constants(ast.NodeTransformer):
     def visit_Dict(self,node):
      for i,key in enumerate(node.keys):
       if isinstance(key,ast.Name)and key.id in ('x','m','gx','gm','xq','mq','xn','mn'):node.keys[i]=ast.copy_location(ast.Constant(key.id),key)
      return self.generic_visit(node)
     def visit_Name(self,node):
      if node.id not in ('true','false','null'):raise Refused('Executable source token refused')
      return ast.copy_location(ast.Constant({'true':True,'false':False,'null':None}[node.id]),node)
    try:return ast.literal_eval(Constants().visit(tree))
    except (ValueError,TypeError,RecursionError):raise Refused('Source literal refused')from None
   i+=1
  raise Refused('Bounded source declaration required')
 def project(self,identities,feature):
  self.selection.verify();out=[]
  for identity in identities:
   system,edition,code=(identity[k]for k in ('system','edition','code'))
   if self.editions.get(system)!=edition:raise Refused('Selected edition required')
   row=self.rows.get((system,code))
   if row is None:raise Refused('Exact preserved identity required')
   obj={'identity':identity,'wording':row[2],'chapter':row[4],'listed_rate':row[5],'source_state':'preserved_snapshot_not_current_verification','dataset':self.years}
   if feature in ('trade_brief','report_context'):
    c6=code[:6];obj['trade']={n:self.values[n].get(c6 if n!='TRADE_CH'else row[4])for n in ('TRADE6','TRADE_CH','TRADE_PARTNERS','TRADE_TREND')}
   if system=='IN':
    gst=self.values['GST_MAP'];obj['gst']=next((gst[code[:n]]for n in (8,6,4,2)if code[:n]in gst),gst.get('*'));obj['scomet_code_label']=self.values['SCOMET'].get(code)
    if feature in ('paperwork','report_context'):
     chapter=int(row[4]);obj['general_export_documents']=self.values['DOC_BASE_OUT']+[r[3]for r in self.values['DOC_EXTRA']if r[0]<=chapter<=r[1]and r[2]in ('both','out')]
     obj['chapter_certificate_source_labels']=[r[2]for r in self.certs if r[0]<=chapter<=r[1]and r[3]=='out']
   text=json.dumps(obj,ensure_ascii=False,separators=(',',':'))
   if len(text)>7500:raise Refused('Evidence exceeds bounded feature projection')
   for offset in range(0,len(text),1900):
    if len(out)>=4:raise Refused('Feature evidence exceeds four bounded source blocks')
    out.append(dict(id='S'+str(len(out)+1),text=text[offset:offset+1900],title=system+' '+code+' snapshot block '+str(offset//1900+1),url='/workspace/finder/offline.html#code='+str(SYSTEMS.index(system))+':'+code,source='Preserved Finder snapshot',date=edition,scope='edition_unverified'))
  return out
