"""Complete held candidate bytes/manifest, never runtime deployment or rebinding.
Closed source/artifact names, exact hashes, deterministic bounded ZIP in memory.
"""
import hashlib,io,json,re,zipfile
from pathlib import Path
from integration import finder_rebind_f4 as rebind,finder_render_f5 as render
from integration.finder_refresh_f1 import DEPENDENTS
FLAG='MERGED_FINDER_PACKAGE_PREP_ENABLED';MAX_TOTAL=140*1024*1024;MAX_ZIP=40*1024*1024
SOURCE_FILES=('src/tradepartners.ts','src/sanctions.ts')
class Held(ValueError):pass

def enabled(env):
 if type(env)is not dict or any(type(k)is not str or type(v)is not str for k,v in env.items()):raise Held('Plain environment strings required')
 value=env.get(FLAG,'false')
 if value not in ('true','false'):raise Held('Exact candidate package flag required')
 return value=='true'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def regular(root,name,expected,cap):
 p=root/name
 if p.is_symlink()or not p.is_file()or p.stat().st_size>cap or type(expected)is not str or not re.fullmatch('[a-f0-9]{64}',expected):raise Held('Exact regular candidate file required')
 raw=p.read_bytes()
 if len(raw)>cap or sha(raw)!=expected:raise Held('Candidate file hash/byte boundary')
 return raw

def pack(files,manifest):
 names=set(files)
 if not names or len(names)>16 or any(type(n)is not str or n.startswith('/')or '\\'in n or any(p in ('','..','.')for p in n.split('/'))for n in names)or'manifest.json'in names:raise Held('Closed candidate archive names required')
 if any(type(raw)is not bytes for raw in files.values())or sum(len(raw)for raw in files.values())>MAX_TOTAL:raise Held('Candidate archive byte cap')
 encoded=(json.dumps(manifest,sort_keys=True,separators=(',',':'),ensure_ascii=True)+'\n').encode();out=io.BytesIO()
 with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as archive:
  for name,raw in sorted({**files,'manifest.json':encoded}.items()):
   info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;archive.writestr(info,raw)
 if out.tell()>MAX_ZIP:raise Held('Compressed candidate package cap')
 result=out.getvalue()
 # Inspect the actual completed bytes, not merely the writes that built them.
 with zipfile.ZipFile(io.BytesIO(result))as archive:
  if archive.testzip()is not None or set(archive.namelist())!=names|{'manifest.json'}:raise Held('Candidate archive verification failed')
  for name,raw in files.items():
   if sha(archive.read(name))!=sha(raw):raise Held('Archived artifact hash mismatch')
 return result

def prepare(env,*,root=None,pins=None,source_pins=None,source_revision=None,baseline=None):
 if not enabled(env):return None
 if env.get(rebind.FLAG)!='true'or env.get(render.FLAG)!='true':raise Held('Explicit artifact and safety preparation flags required')
 if type(source_pins)is not dict or set(source_pins)!=set(SOURCE_FILES)or any(type(v)is not str or not re.fullmatch('[a-f0-9]{64}',v)for v in source_pins.values())or any(type(v)is not str or not re.fullmatch('[a-f0-9]{40}',v)for v in (source_revision,baseline)):raise Held('Exact supplied candidate provenance required')
 root=Path(root);data_name=rebind.source_check(root,pins)
 files={name:regular(root,name,h,40*1024*1024)for name,h in pins.items()}
 files.update({name:regular(root,name,h,32*1024*1024)for name,h in source_pins.items()})
 # A candidate must not carry provider/proxy secrets in its raw generated shell.
 # These exact merged-source constants are empty today. Refuse unexpected keys
 # rather than silently strip and invalidate the raw dataset/source pins.
 for name in ('index.html','offline.html'):
  text=files[name].decode('utf8')
  for constant in ('AI_PROXY_URL','AIS_PROXY_URL','BUILTIN_GEMINI_KEYS','BUILTIN_GROQ_KEYS','BUILTIN_MISTRAL_KEYS','BUILTIN_NVIDIA_KEYS'):
   values=re.findall(r'const\s+'+constant+r"\s*=\s*'([^']*)'",text)
   if values!=['']:raise Held('Candidate raw provider constants must be empty')
 artifacts_report,artifacts=rebind.prepare(env,root=root,pins=pins)
 safe_report,safe=render.prepare(env,source=files['offline.html'].decode('utf8'),source_sha256=pins['offline.html'])
 files.update(artifacts);files['review/public-offline.html']=safe.encode()
 manifest={'format':'held_finder_candidate_v1','state':'held_not_runtime_rebound_not_approved','baseline':baseline,'supplied_source_revision':source_revision,'source_revision_binding':'caller_must_verify_with_F3','source_pins':dict(source_pins),'generated_pins':dict(pins),'editions':artifacts_report['editions'],'identity_summary':{k:artifacts_report[k]for k in ('raw_rows','bound_count','not_bound_reasons','code_count','identity_count')},'safe_render':safe_report,'files':{n:{'bytes':len(raw),'sha256':sha(raw)}for n,raw in files.items()},'runtime_consumers':list(DEPENDENTS),'runtime_editions_and_pins':'not_modified','official_freshness':'not_verified','legal_accuracy':'not_verified','published':False,'auto_repin':False}
 payload=pack(files,manifest)
 return {'state':'held_complete_candidate_bytes_not_runtime_rebound','sha256':sha(payload),'bytes':len(payload),'file_count':len(files)+1,'baseline':baseline,'source_revision':source_revision,'writes':False,'published':False,'auto_repin':False},payload,manifest
