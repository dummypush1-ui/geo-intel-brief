"""Fixed F3 -> data-only F2 -> scratch F1 -> F4/F5/F6 held package.
No source code execution, runtime rebind, publication, provider or credentials.
"""
import hashlib,io,json,re,time,zipfile
from integration import finder_source_f3 as source,finder_package_f6 as package
FLAG='MERGED_FINDER_CHAIN_PREP_ENABLED'
class Held(ValueError):pass

def enabled(env):
 if type(env)is not dict or any(type(k)is not str or type(v)is not str for k,v in env.items()):raise Held('Plain environment strings required')
 value=env.get(FLAG,'false')
 if value not in ('true','false'):raise Held('Exact source chain flag required')
 return value=='true'
def encode(obj):return (json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True)+'\n').encode()

def prepare(env,*,revision=None,root=source.reconcile.ROOT,fetch=source.download,clock=time.monotonic):
 if not enabled(env):return None
 # Check the whole required grant-shaped preparation surface before network or
 # scratch build. These flags enable review only, never source approval/cutover.
 for check in (source.enabled,source.reconcile.enabled,source.reconcile.build.enabled,package.enabled,package.rebind.enabled):
  if not check(env):raise Held('Every source/build/artifact/package preparation flag required')
 if env.get(package.render.FLAG)!='true':raise Held('Explicit candidate safety rendering required')
 if not source.sha(revision):raise Held('Exact 40-character source commit required')
 acquired=source.acquire(env,revision=revision,fetch=fetch,clock=clock)
 bundle,delta=source.reconcile.plan(env,root=root,snapshot=acquired['snapshot'])
 rebuilt,packed=source.reconcile.build.prepare_package(env,root=root,bundle=bundle,source_revision=revision)
 report,payload,manifest=packed
 # Read actual F6 ZIP, then add bounded provenance + original supplied bytes.
 # No ZIP extraction or filesystem output. F6 independently checked the exact
 # generated source/artifact bytes before returning this package.
 with zipfile.ZipFile(io.BytesIO(payload))as archive:
  files={name:archive.read(name)for name in manifest['files']}
 for row in acquired['snapshot']['source_files']:
  raw=row['content'].encode();name=row['path']
  if hashlib.sha256(raw).hexdigest()!=acquired['evidence']['source_file_sha256'][name]:raise Held('Acquired source receipt mismatch')
  files['upstream/'+name]=raw
 provenance={'format':'finder_source_chain_v1','source_evidence':acquired['evidence'],'reconciliation':delta,'scratch_rebuild':rebuilt,'runtime_rebinding':'not_applied','published':False,'auto_repin':False}
 if len(encode(provenance))>2*1024*1024:raise Held('Provenance byte cap')
 files['provenance/source-chain.json']=encode(provenance)
 manifest=dict(manifest,format='held_finder_chain_v1',source_revision_binding='verified_git_commit_tree_regular_blobs_by_F3',files={n:{'bytes':len(raw),'sha256':package.sha(raw)}for n,raw in files.items()},source_chain='provenance/source-chain.json',upstream_source_files=['upstream/'+n for n in source.reconcile.FILES])
 complete=package.pack(files,manifest)
 return {'state':'held_complete_source_chain_not_runtime_rebound','sha256':package.sha(complete),'bytes':len(complete),'file_count':len(files)+1,'baseline':rebuilt['baseline'],'source_revision':revision,'source_fetches':acquired['evidence']['requests'],'retries':0,'ai_calls':0,'writes':False,'published':False,'auto_repin':False},complete,manifest
