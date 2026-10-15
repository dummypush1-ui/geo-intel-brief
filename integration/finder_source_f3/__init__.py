"""Exact public Finder commit acquisition into held snapshot reconciliation.
No branch selection, credentials, redirects, retries, writes, publish or repin.
"""
import hashlib,json,re,time,urllib.error,urllib.request
from integration import finder_reconcile_f2 as reconcile
FLAG='MERGED_FINDER_SOURCE_PREP_ENABLED'
API='https://api.github.com/repos/push2006/finder-hsn-codee/git/'
RAW='https://raw.githubusercontent.com/push2006/finder-hsn-codee/'
MAX_JSON=2*1024*1024
MAX_FILE=32*1024*1024
TOTAL_SECONDS=90
class Held(ValueError):pass
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):raise Held('Source redirect held')

def enabled(env):
 if type(env)is not dict or any(type(k)is not str or type(v)is not str for k,v in env.items()):raise Held('Plain environment strings required')
 value=env.get(FLAG,'false')
 if value not in ('true','false'):raise Held('Exact source flag required')
 return value=='true'

def sha(value):return type(value)is str and re.fullmatch('[a-f0-9]{40}',value)is not None

def download(url,limit,timeout):
 # Called only with generated fixed-origin URLs. No ambient proxy, cookie or
 # auth headers are inherited. A failure holds rather than falling back/retrying.
 opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
 request=urllib.request.Request(url,headers={'User-Agent':'merged-finder-source-review','Accept':'application/vnd.github+json'if url.startswith(API)else'text/plain'})
 try:
  with opener.open(request,timeout=timeout)as response:
   if response.status!=200 or response.geturl()!=url:raise Held('Exact source response required')
   length=response.headers.get('Content-Length')
   if length is not None and (not length.isdigit()or int(length)>limit):raise Held('Source content length held')
   if response.headers.get('Content-Encoding','identity')not in ('','identity'):raise Held('Encoded source held')
   raw=response.read(limit+1)
 except Held:raise
 except Exception:raise Held('Source unavailable; last-good retained')from None
 if len(raw)>limit:raise Held('Source byte cap')
 return raw

def acquire(env,*,revision=None,fetch=download,clock=time.monotonic):
 if not enabled(env):return None
 if not reconcile.enabled(env)or not reconcile.build.enabled(env):raise Held('Explicit reconciliation and rebuild flags required')
 if not sha(revision):raise Held('Exact 40-character source commit required')
 start=clock();requests=0;byte_count=0
 def get(url,limit):
  nonlocal requests,byte_count
  remaining=TOTAL_SECONDS-(clock()-start)
  if remaining<=0:raise Held('Source total timeout; no retries')
  try:raw=fetch(url,limit,min(20,remaining))
  except Exception:raise Held('Source acquisition failed; last-good retained')from None
  requests+=1
  if type(raw)is not bytes or len(raw)>limit:raise Held('Source byte contract')
  byte_count+=len(raw)
  if clock()-start>TOTAL_SECONDS:raise Held('Source total timeout; no retries')
  return raw
 def obj(url):
  raw=get(url,MAX_JSON)
  try:value=json.loads(raw,object_pairs_hook=reconcile.pairs)
  except (ValueError,UnicodeError,RecursionError):raise Held('Invalid source metadata')from None
  if type(value)is not dict:raise Held('Source metadata object required')
  return value
 def tree(tree_sha):
  if not sha(tree_sha):raise Held('Source tree SHA required')
  value=obj(API+'trees/'+tree_sha)
  if value.get('sha')!=tree_sha or value.get('truncated')is not False or type(value.get('tree'))is not list or len(value['tree'])>20000:raise Held('Complete exact source tree required')
  entries={}
  for row in value['tree']:
   if type(row)is not dict or type(row.get('path'))is not str or row['path']in entries:raise Held('Unique source tree paths required')
   entries[row['path']]=row
  return entries
 commit=obj(API+'commits/'+revision)
 if commit.get('sha')!=revision or type(commit.get('tree'))is not dict:raise Held('Exact source commit binding required')
 top=tree(commit['tree'].get('sha'));src=top.get('src',{})
 if src.get('type')!='tree'or src.get('mode')!='040000':raise Held('Source directory must be a Git tree')
 entries=tree(src.get('sha'));files=[]
 for path in reconcile.FILES:
  entry=entries.get(path.split('/')[1],{})
  if entry.get('type')!='blob'or entry.get('mode')!='100644'or not sha(entry.get('sha'))or type(entry.get('size'))is not int or not 0<entry['size']<=MAX_FILE:raise Held('Exact regular source blob required')
  raw=get(RAW+revision+'/'+path,MAX_FILE)
  actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
  if len(raw)!=entry['size']or actual!=entry['sha']:raise Held('Git source blob identity mismatch')
  try:text=raw.decode('utf8')
  except UnicodeError:raise Held('UTF-8 source blob required')from None
  files.append({'path':path,'content':text,'sha256':hashlib.sha256(raw).hexdigest()})
 return {'snapshot':{'state':'supplied_public_snapshot_not_official_proof','repository':'push2006/finder-hsn-codee','revision':revision,'source_files':files},'evidence':{'repository':'push2006/finder-hsn-codee','revision':revision,'root_tree':commit['tree']['sha'],'src_tree':src['sha'],'source_urls':[RAW+revision+'/'+n for n in reconcile.FILES],'git_blob_sha1':{n:entries[n.split('/')[1]]['sha']for n in reconcile.FILES},'source_file_sha256':{r['path']:r['sha256']for r in files},'requests':requests,'bytes':byte_count,'redirects':0,'retries':0,'credentials_sent':False,'official_freshness_verified':False}}

def prepare(env,*,revision=None,root=reconcile.ROOT,fetch=download,clock=time.monotonic):
 if not enabled(env):return {'state':'disabled','source_fetches':0,'writes':False,'published':False}
 source=acquire(env,revision=revision,fetch=fetch,clock=clock)
 result=reconcile.prepare(env,root=root,snapshot=source['snapshot'])
 return {'state':'held_source_and_consumer_review_required','source_evidence':source['evidence'],'reconciliation':result,'source_fetches':source['evidence']['requests'],'writes':False,'published':False,'ai_calls':0,'auto_repin':False}
