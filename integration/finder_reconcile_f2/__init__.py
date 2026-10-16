"""Reconcile supplied public Finder snapshots without replacing last-good data.
No fetcher, credential reader, publisher, legal approval or automatic repinning.
"""
import hashlib,json,re
from pathlib import Path
from integration import finder_refresh_f1 as build
ROOT=Path(__file__).resolve().parents[2]
FLAG='MERGED_FINDER_RECONCILE_PREP_ENABLED'
FILES=('src/tradepartners.ts','src/sanctions.ts')
MAX_BYTES=32*1024*1024
class Held(ValueError):pass

def enabled(env):
 if type(env)is not dict or any(type(k)is not str or type(v)is not str for k,v in env.items()):raise Held('Plain environment strings required')
 value=env.get(FLAG,'false')
 if value not in ('true','false'):raise Held('Exact reconciliation flag required')
 return value=='true'

def digest(raw):return hashlib.sha256(raw).hexdigest()
def pairs(rows):
 out={}
 for k,v in rows:
  if k in out or k in ('__proto__','constructor','prototype'):raise Held('Duplicate or reserved data key')
  out[k]=v
 return out

def js_object(text):
 # Only JSON strings/numbers/arrays/objects/bools, with these closed bare keys.
 # Never evaluate or import a source file; quoted values are left byte intact.
 out=[];i=0;decoder=json.JSONDecoder()
 while i<len(text):
  if text[i]=='"':
   try:_,n=decoder.raw_decode(text[i:])
   except (ValueError,RecursionError):raise Held('Invalid data string')from None
   out.append(text[i:i+n]);i+=n;continue
  m=re.match(r'[A-Za-z_$][\w$]*',text[i:])
  if m:
   token=m.group();end=i+len(token)
   if token in ('x','m','gx','gm','xq','mq','xn','mn')and re.match(r'\s*:',text[end:]):out.append(json.dumps(token))
   elif token in ('true','false'):out.append(token)
   else:raise Held('Executable or unknown data token')
   i=end;continue
  if text[i]not in '0123456789-.,:[]{} \t':raise Held('Non-data syntax')
  out.append(text[i]);i+=1
 try:return json.loads(''.join(out),object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in()).throw(Held('Non-finite data')))
 except (ValueError,RecursionError):raise Held('Invalid data object')from None

def positive(v):return type(v)is int and 0<v<=9007199254740991
def partner_value(row):
 if type(row)is not dict or not {'x','m'}<=set(row)or set(row)-{'x','m','gx','gm','xq','mq','xn','mn'}:raise Held('Partner row schema')
 for key,value in row.items():
  if type(value)is not list:raise Held('Partner arrays required')
  if key in ('x','m','gx','gm'):
   if len(value)>5:raise Held('Top-five partner cap')
   for v in value:
    if type(v)is not list or len(v)not in (2,3)or type(v[0])is not str or not v[0].strip()or len(v[0])>256 or any(not positive(n)for n in v[1:])or key in ('gx','gm')and len(v)!=2:raise Held('Partner amount/name schema')
  elif len(value)!=2 or not positive(value[0])or(key in ('xn','mn')and type(value[1])is not bool)or(key in ('xq','mq')and value[1]not in ('m2','1000 kWh','m','items','pairs','litres','kg','thousand items','packs','dozens','m3','carats')):raise Held('Quantity/estimate schema')
 return row

def partners(text):
 lines=text.splitlines();at=next((i for i,s in enumerate(lines)if s.startswith('export const TRADE_PARTNERS: ')),None)
 if at is None or not lines[at].endswith(' = {')or lines[-1]!='};':raise Held('Partner declaration boundary')
 header=lines[:at+1];years=[re.fullmatch(r'export const TRADE_PARTNERS_YEAR = (\d{4});',s)for s in header];years=[int(x[1])for x in years if x]
 if len(years)!=1 or any(not(s.startswith('//')or re.fullmatch(r'export const TRADE_PARTNERS_YEAR = \d{4};',s)or i==at)for i,s in enumerate(header)):raise Held('Partner header boundary')
 expected=(ROOT/'integration/finder_reconcile_f2/partner-declaration.txt').read_text().strip()
 if lines[at]!=expected:raise Held('Partner type declaration drift')
 out={}
 if len(lines)>10050:raise Held('Partner source line cap')
 for line in lines[at+1:-1]:
  if len(line)>65536:raise Held('Partner line cap')
  m=re.fullmatch(r"  '(\d{6})': (\{.*\}),",line)
  if not m or m[1]in out:raise Held('Partner code/line boundary')
  out[m[1]]=partner_value(js_object(m[2]))
 if not out or len(out)>10000:raise Held('Partner coverage boundary')
 return years[0],out,header

def sanctions(text):
 lines=text.splitlines()
 if len(lines)!=3 or not lines[0].startswith('//')or not lines[1].startswith('export const SANCTIONS_META = ')or not lines[1].endswith(';')or not lines[2].startswith('export const SANCTIONS: [string, string, string][] = ')or not lines[2].endswith(';'):raise Held('Sanctions declaration boundary')
 try:
  meta=json.loads(lines[1][len('export const SANCTIONS_META = '):-1],object_pairs_hook=pairs)
  rows=json.loads(lines[2][len('export const SANCTIONS: [string, string, string][] = '):-1])
 except (ValueError,RecursionError):raise Held('Sanctions JSON boundary')from None
 if type(meta)is not dict or type(rows)is not list or not rows or len(rows)>200000:raise Held('Sanctions row cap')
 if any(type(r)is not list or len(r)!=3 or any(type(v)is not str or not v.strip()or len(v)>4096 for v in r)or r[1]not in ('OFAC','EU','UFLPA')for r in rows):raise Held('Sanctions row schema')
 return rows,lines[:2]

def candidate(snapshot):
 if type(snapshot)is not dict or set(snapshot)!={'state','repository','revision','source_files'}or snapshot['state']!='supplied_public_snapshot_not_official_proof'or snapshot['repository']!='push2006/finder-hsn-codee'or type(snapshot['revision'])is not str or not re.fullmatch('[a-f0-9]{40}',snapshot['revision'])or type(snapshot['source_files'])is not list or len(snapshot['source_files'])!=2:raise Held('Closed source snapshot required')
 out={}
 for row in snapshot['source_files']:
  if type(row)is not dict or set(row)!={'path','content','sha256'}or type(row['path'])is not str or row['path']not in FILES or row['path']in out or type(row['content'])is not str or type(row['sha256'])is not str:raise Held('Exact snapshot file required')
  try:raw=row['content'].encode('utf8')
  except UnicodeError:raise Held('UTF-8 source required')from None
  if len(raw)>MAX_BYTES or digest(raw)!=row['sha256']:raise Held('Source byte/hash boundary')
  out[row['path']]=row['content']
 return out

def plan(env,*,snapshot=None,root=ROOT):
 if not enabled(env):return {'state':'disabled','writes':False,'published':False,'source_fetches':0}
 if not build.enabled(env):raise Held('Explicit isolated-build preparation flag required')
 root=Path(root);incoming=candidate(snapshot)
 baseline={}
 for name in FILES:
  p=root/name
  if p.is_symlink()or not p.is_file()or p.stat().st_size>MAX_BYTES:raise Held('Last-good source boundary')
  baseline[name]=p.read_text()
 year,old,header=partners(baseline[FILES[0]]);newyear,new,_=partners(incoming[FILES[0]])
 if year!=newyear:raise Held('Trade year rollover requires separate review')
 added=sorted(set(new)-set(old));removed=sorted(set(old)-set(new));changed=sorted(k for k in old.keys()&new.keys()if old[k]!=new[k])
 merged=dict(old);merged.update({k:new[k]for k in added})
 header=[('// Unverified mixed snapshot candidate; coverage '+str(len(merged))+' codes; review required.')if line.startswith('// Baked ')else line for line in header]
 partner_text='\n'.join(header)+'\n'+''.join("  '"+k+"': "+json.dumps(merged[k],ensure_ascii=False,separators=(',',':'))+',\n'for k in sorted(merged))+'};\n'
 prior,sh= sanctions(baseline[FILES[1]]);proposed,_=sanctions(incoming[FILES[1]])
 a,b=set(map(tuple,prior)),set(map(tuple,proposed));sa=sorted(b-a);sr=sorted(a-b)
 # Every old row is retained. Snapshot disappearance is never delisting proof.
 union=list(prior)+[list(r)for r in sa]
 sanctions_text='\n'.join(sh)+'\nexport const SANCTIONS: [string, string, string][] = '+json.dumps(union,ensure_ascii=False,separators=(',',':'))+';\n'
 # Avoid cosmetic rewrites when no data additions. Keep prior freshness labels,
 # and label the scratch output as unverified mixed snapshot in the report.
 files=[]
 for name,text,has_add in [(FILES[0],partner_text,bool(added)),(FILES[1],sanctions_text,bool(sa))]:
  if has_add:files.append({'path':name,'content':text,'sha256':digest(text.encode())})
 bundle={'state':'supplied_candidate_not_approved','source_files':files}
 return bundle,{'state':'held_snapshot_and_consumer_review_required','repository':snapshot['repository'],'source_revision':snapshot['revision'],'source_file_hashes':{n:digest(incoming[n].encode())for n in FILES},'baseline_file_hashes':{n:digest(baseline[n].encode())for n in FILES},'source_freshness':'not_officially_verified','snapshot_is_approval':False,'partners':{'year':year,'previous_count':len(old),'snapshot_count':len(new),'candidate_count':len(merged),'added_codes':added,'held_changed_codes':changed,'retained_missing_codes':removed},'sanctions':{'previous_count':len(prior),'snapshot_count':len(proposed),'candidate_count':len(union),'additions':len(sa),'retained_missing_rows':len(sr),'delta_sha256':digest(json.dumps({'added':sa,'retained_missing':sr},ensure_ascii=False,separators=(',',':')).encode()),'removals_applied':0,'legal_screening_ready':False},'source_fetches':0,'ai_calls':0,'writes':False,'published':False,'auto_repin':False}


def prepare(env,*,snapshot=None,root=ROOT):
 if not enabled(env):return {'state':'disabled','writes':False,'published':False,'source_fetches':0}
 bundle,result=plan(env,snapshot=snapshot,root=root)
 result['rebuild']=build.prepare(env,root=root,bundle=bundle)
 return result
