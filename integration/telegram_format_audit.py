"""Private explicitly synthetic original formatting audit, NOT FOR DELIVERY."""
import ast,hashlib,math
from pathlib import Path
from datetime import datetime,timezone
from .supplied_fulltext_fixture import Budget,FulltextRefused
ROOT=Path(__file__).resolve().parents[1]
SOURCE='intelligence/geo/reports/telegram_backup.py'
PIN='0a0f7f0dcf7955e8e8a7cf1981f8669fc63180f0f2c18152131c9dc211de0b0c'
class FormatRefused(ValueError):pass
def _functions():
 source=(ROOT/SOURCE).read_bytes()
 if hashlib.sha256(source).hexdigest()!=PIN:raise FormatRefused('reviewed source drift')
 tree=ast.parse(source);defs=[]
 for name,names,attrs in [('_format_full_record',{'a'},{'get'}),('_split_into_batches',{'articles','batches','current_records','current_indices','current_len','start_idx','i','a','record','_format_full_record','record_len','len','enumerate','TELEGRAM_MSG_LIMIT'},{'append','join'})]:
  node=next(n for n in tree.body if type(n) is ast.FunctionDef and n.name==name)
  for n in ast.walk(node):
   if isinstance(n,(ast.Import,ast.ImportFrom,ast.Global,ast.Nonlocal,ast.ClassDef)) or isinstance(n,ast.Name) and n.id not in names or isinstance(n,ast.Attribute) and n.attr not in attrs:raise FormatRefused('reviewed AST allowlist')
  if node.decorator_list:raise FormatRefused('reviewed AST decorator')
  defs.append(node)
 literal=next(n.value for n in tree.body if type(n) is ast.Assign and any(type(t) is ast.Name and t.id=='TELEGRAM_MSG_LIMIT' for t in n.targets))
 limit=ast.literal_eval(literal)
 if type(limit) is not int or limit!=3500:raise FormatRefused('reviewed source policy')
 return defs,limit
def _metrics(text):return {'python_codepoints':len(text),'utf8_bytes':len(text.encode('utf8')),'utf16_code_units':len(text.encode('utf-16-le'))//2}
def audit_synthetic_telegram_format(records,*,synthetic=False):
 if synthetic is not True or type(records) is not list or len(records)>100:raise FormatRefused('explicit synthetic records required')
 copied=[];fields={'title','url','source','category','summary','score','risk_level','country','credibility','corroboration','published'}
 for row in records:
  if type(row) is not dict or len(row)>11 or any(type(k) is not str for k in row) or set(row)-fields:raise FormatRefused('closed synthetic fields')
  r={}
  for k,v in row.items():
   if k=='score':
    if type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=100:raise FormatRefused('bounded score')
   elif k=='corroboration':
    if type(v) is not int or not 1<=v<=100:raise FormatRefused('bounded corroboration')
   elif k=='published' and type(v) is datetime:
    if type(v.tzinfo) is not timezone:raise FormatRefused('fixed aware published')
    try:year=v.astimezone(timezone.utc).year
    except (ValueError,OverflowError):raise FormatRefused('published range') from None
    if not 1970<=year<=2100:raise FormatRefused('published range')
    v=v.isoformat()
   elif type(v) is not str or len(v)>10000 or k=='published' and v!='':raise FormatRefused('exact text required')
   r[k]=v
  copied.append(r)
 try:Budget().take(copied)
 except FulltextRefused:raise FormatRefused('input budget') from None
 definitions,limit=_functions();scope={'__builtins__':{'len':len,'enumerate':enumerate},'TELEGRAM_MSG_LIMIT':limit}
 exec(compile(ast.Module(body=definitions,type_ignores=[]),'original-synthetic-format','exec'),scope)
 texts=[scope['_format_full_record'](r) for r in copied];batches=scope['_split_into_batches'](copied);audit=[];cursor=0
 for span,text in batches:
  start,end=span
  if start!=cursor or not start<end<=len(texts) or text!='\n\n====\n\n'.join(texts[start:end]):raise FormatRefused('original batch coverage')
  cursor=end;estimate=sum(len(x)+2 for x in texts[start:end]);actual=len(text)
  audit.append({'span':[start,end],'original_text':text,'metrics':_metrics(text),'source_packing_estimate':estimate,'actual_minus_estimate':actual-estimate,'estimate_over_source3500':estimate>limit,'actual_over_source3500':actual>limit,'unsplit_single_oversized':end-start==1 and actual>limit})
 if cursor!=len(texts):raise FormatRefused('original coverage')
 result={'scope':'PRIVATE EXPLICITLY SYNTHETIC AUDIT - NOT FOR DELIVERY','synthetic_assertion_only':True,'notice':'Formatting diagnostics only, no current provider-limit/availability/fullcontent/delivery proof. Embedded secrets in caller strings are not detected.','source_native_policy':limit,'records':[{'original_text':t,'metrics':_metrics(t)} for t in texts],'batches':audit,'input_count':len(copied),'network':False,'writes':False,'delivery':False,'ready_for_delivery':False}
 try:Budget().take(result)
 except FulltextRefused:raise FormatRefused('combined output budget') from None
 return result
