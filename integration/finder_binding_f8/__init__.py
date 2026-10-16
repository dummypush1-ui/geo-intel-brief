"""Default-OFF held package/root identity binding. No public mount or cutover.
Expected package hash is an internal review input, never evidence of approval.
"""
import hashlib,json,re,zipfile
from dataclasses import dataclass
from pathlib import Path
from integration.finder_identity_proof_prep import ProofProfile,FinderProof
from integration.finder_refresh_f1 import DEPENDENTS
FLAG='MERGED_FINDER_BINDING_PREP_ENABLED';MAX_ARCHIVE=40*1024*1024;MAX_TOTAL=140*1024*1024;MAX_FILE=64*1024*1024;CHUNK=65536
FIXED=frozenset(('index.html','offline.html','sw.js','src/tradepartners.ts','src/sanctions.ts','integration/code_news_index/codes.idx','integration/code_news_index/rows.jsonl','integration/code_news_index/manifest.json','integration/finder_identity_proof.bin','review/public-offline.html','upstream/src/tradepartners.ts','upstream/src/sanctions.ts','provenance/source-chain.json'))
MANIFEST=frozenset(('format','state','baseline','supplied_source_revision','source_revision_binding','source_pins','generated_pins','editions','identity_summary','safe_render','files','runtime_consumers','runtime_editions_and_pins','official_freshness','legal_accuracy','published','auto_repin','source_chain','upstream_source_files'))
class Held(ValueError):pass

def enabled(env):
 if type(env)is not dict or any(type(k)is not str or type(v)is not str for k,v in env.items()):raise Held('Plain environment strings required')
 value=env.get(FLAG,'false')
 if value not in ('true','false'):raise Held('Exact candidate binding flag required')
 return value=='true'
def sha(value):return type(value)is str and re.fullmatch('[a-f0-9]{64}',value)is not None
def decode(raw):
 if type(raw)is not bytes or len(raw)>2*1024*1024:raise Held('Bounded manifest/receipt required')
 def unique(pairs):
  result={}
  for k,v in pairs:
   if k in result:raise Held('Duplicate manifest/receipt field')
   result[k]=v
  return result
 try:return json.loads(raw,object_pairs_hook=unique)
 except (ValueError,UnicodeError,RecursionError):raise Held('Manifest/receipt unavailable')from None

def regular(root,name):
 path=root/name
 for p in (path,*list(path.parents)[:len(Path(name).parts)-1]):
  if p.is_symlink():raise Held('Candidate path symlink refused')
 if any(p.is_symlink()for p in (root,*root.parents))or not root.is_dir()or not path.is_file():raise Held('Regular candidate file required')
 return path

def digest_stream(stream,expected_size):
 total=0;h=hashlib.sha256()
 while True:
  raw=stream.read(CHUNK)
  if not raw:break
  total+=len(raw)
  if total>expected_size:raise Held('Candidate byte cap')
  h.update(raw)
 if total!=expected_size:raise Held('Candidate size mismatch')
 return h.hexdigest()

@dataclass(frozen=True)
class Binding:
 """Review preparation identity, not owner permission or public mount proof."""
 root:Path
 package_sha256:str
 baseline:str
 source_revision:str
 files:tuple
 profile:ProofProfile
 def verify(self):
  for name,size,pin in self.files:
   path=regular(self.root,name)
   if path.stat().st_size!=size:raise Held('Candidate root size drift')
   with path.open('rb')as stream:
    if digest_stream(stream,size)!=pin:raise Held('Candidate root hash drift')
 def proof(self):
  self.verify()
  return FinderProof(self.root,profile=self.profile)

def prepare(env,*,archive=None,expected_sha256=None,root=None):
 if not enabled(env):return None
 if not sha(expected_sha256)or archive is None or root is None:raise Held('Exact internal package hash/path/root required')
 try:
  path=Path(archive);root=Path(root)
  if path.is_symlink()or not path.is_file()or path.stat().st_size>MAX_ARCHIVE:raise Held('Regular bounded candidate archive required')
  with path.open('rb')as stream:
   if digest_stream(stream,path.stat().st_size)!=expected_sha256:raise Held('Candidate archive hash mismatch')
   stream.seek(0)
   with zipfile.ZipFile(stream)as z:
    entries=z.infolist();names=[i.filename for i in entries]
    if len(names)!=15 or len(set(names))!=15 or names!=sorted(names)or 'manifest.json'not in names:raise Held('Closed candidate archive required')
    if any(i.file_size>MAX_FILE or i.compress_type!=zipfile.ZIP_DEFLATED or i.external_attr!=0o100644<<16 or i.flag_bits&1 for i in entries)or sum(i.file_size for i in entries)>MAX_TOTAL:raise Held('Candidate entry type/byte cap')
    sizes={i.filename:i.file_size for i in entries}
    if sizes['manifest.json']>2*1024*1024:raise Held('Manifest byte cap')
    manifest=decode(z.read('manifest.json'))
    if type(manifest)is not dict or set(manifest)!=MANIFEST or manifest['format']!='held_finder_chain_v1'or manifest['state']!='held_not_runtime_rebound_not_approved'or manifest['source_revision_binding']!='verified_git_commit_tree_regular_blobs_by_F3'or manifest['runtime_editions_and_pins']!='not_modified'or manifest['runtime_consumers']!=list(DEPENDENTS)or manifest['source_chain']!='provenance/source-chain.json'or manifest['upstream_source_files']!=['upstream/src/tradepartners.ts','upstream/src/sanctions.ts']or manifest['official_freshness']!='not_verified'or manifest['legal_accuracy']!='not_verified'or manifest['published']is not False or manifest['auto_repin']is not False:raise Held('Exact held chain manifest required')
    if any(type(manifest[k])is not str or not re.fullmatch('[a-f0-9]{40}',manifest[k])for k in ('baseline','supplied_source_revision')):raise Held('Exact source/baseline labels required')
    files=manifest['files']
    if type(files)is not dict or set(files)!=set(names)-{'manifest.json'}or not FIXED<set(files)or len(files)!=14:raise Held('Closed candidate payload required')
    data=next(n for n in files if n not in FIXED)
    if not re.fullmatch(r'data\.[a-f0-9]{12}\.js',data):raise Held('Exact candidate bundle name required')
    for name,item in files.items():
     if type(item)is not dict or set(item)!={'bytes','sha256'}or type(item['bytes'])is not int or item['bytes']!=sizes[name]or not sha(item['sha256']):raise Held('Exact candidate payload hashes required')
     with z.open(name)as stream:
      if digest_stream(stream,item['bytes'])!=item['sha256']:raise Held('Archived payload hash mismatch')
    generated=manifest['generated_pins'];sources=manifest['source_pins']
    if type(generated)is not dict or set(generated)!={'index.html','offline.html','sw.js',data}or type(sources)is not dict or set(sources)!={'src/tradepartners.ts','src/sanctions.ts'}or any(v!=files[n]['sha256']for n,v in {**generated,**sources}.items()):raise Held('Generated/source manifest binding mismatch')
    editions=(('HS','2022'),('IN','snapshot:'+generated[data][:12]))
    if manifest['editions']!=dict(editions)or data[5:17]!=generated[data][:12]:raise Held('Candidate edition mismatch')
    receipt=decode(z.read('provenance/source-chain.json'));evidence=receipt.get('source_evidence',{});delta=receipt.get('reconciliation',{});rebuild=receipt.get('scratch_rebuild',{})
    if receipt.get('format')!='finder_source_chain_v1'or receipt.get('runtime_rebinding')!='not_applied'or receipt.get('published')is not False or receipt.get('auto_repin')is not False or evidence.get('revision')!=manifest['supplied_source_revision']or evidence.get('repository')!='push2006/finder-hsn-codee'or rebuild.get('baseline')!=manifest['baseline']or delta.get('source_revision')!=evidence.get('revision')or delta.get('sanctions',{}).get('removals_applied')!=0:raise Held('Source chain receipt binding mismatch')
    for name in sources:
     upstream='upstream/'+name;raw=z.read(upstream)
     if evidence.get('source_file_sha256',{}).get(name)!=files[upstream]['sha256']or delta.get('source_file_hashes',{}).get(name)!=files[upstream]['sha256']or hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=evidence.get('git_blob_sha1',{}).get(name):raise Held('Upstream source receipt mismatch')
    index=decode(z.read('integration/code_news_index/manifest.json'))
    if index.get('format')!='code_news_flat_v1'or index.get('source_pins')!={'expected_shell_sha256':generated['index.html'],'expected_bundle_sha256':generated[data]}or any(index.get('files',{}).get(n)!={'bytes':files['integration/code_news_index/'+n]['bytes'],'sha256':files['integration/code_news_index/'+n]['sha256']}for n in ('codes.idx','rows.jsonl')):raise Held('Index/source manifest mismatch')
    safe=manifest['safe_render']
    if safe.get('source_sha256')!=generated['offline.html']or safe.get('rendered_sha256')!=files['review/public-offline.html']['sha256']or safe.get('bytes')!=files['review/public-offline.html']['bytes']or any(safe.get(k)is not True for k in ('network_disabled','keys_removed','device_storage_disabled','csv_formula_safe','shortlist_wrap')):raise Held('Safe render/source binding mismatch')
    pins=tuple(sorted((n,files[n]['sha256'])for n in ('index.html','offline.html',data,'integration/code_news_index/manifest.json','integration/code_news_index/codes.idx','integration/code_news_index/rows.jsonl')))
    profile=ProofProfile(pins,editions,files['integration/finder_identity_proof.bin']['sha256']);profile.validate()
    binding=Binding(root,expected_sha256,manifest['baseline'],manifest['supplied_source_revision'],tuple(sorted((n,v['bytes'],v['sha256'])for n,v in files.items())),profile)
  binding.verify()
  return binding
 except Held:raise
 except Exception:raise Held('Candidate binding unavailable; last-good unchanged')from None
