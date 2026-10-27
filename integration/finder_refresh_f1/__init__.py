"""Default-OFF isolated Finder rebuild/review preparation. No live effects.
This is not a source fetcher, publisher, pin approver or deployment command.
"""
import hashlib,json,os,re,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
FLAG='MERGED_FINDER_REFRESH_PREP_ENABLED'
MAX_INPUT=64*1024*1024
MAX_OUTPUT=100*1024*1024
ALLOWED=re.compile(r'src/(?:datachunk[0-9]+\.ts|tradevalues\.ts|tradepartners\.ts|tradetrend\.ts|tradeseson\.ts|marketdata\.ts|marketexp\.ts|sancgap\.ts|sanctions\.ts|aliases\.ts|gstmap\.ts)')
DEPENDENTS=('integration/finder_offline.py','integration/public_ai_finder_bridge.py','integration/finder_identity_proof_prep.py','integration/code_news_pins.json','integration/code_news_index/manifest.json','integration/code_news_coverage_binding_prep.py','integration/news_finder_navigation_prep.py','integration/public_ai_answers.py','integration/ui/finder-offline-sw.js','integration/ui/finder_public.html','integration/ui/relationship_navigation.js','integration/ui/code_news_finder_navigation.js','integration/code_news_catalogue.py','integration/finder_index.py','integration/code_news_index/rows.jsonl','integration/finder_identity_proof.bin','scripts/build_code_news_index.py','scripts/build_finder_identity_proof.py')
class Held(ValueError):pass

def enabled(env):
 if type(env)is not dict or any(type(k)is not str or type(v)is not str for k,v in env.items()):raise Held('Plain environment strings required')
 flag=env.get(FLAG,'false')
 if flag not in ('true','false'):raise Held('Exact refresh preparation flag required')
 return flag=='true'

def pin_check(root):
 pins=json.loads((ROOT/'integration/finder_refresh_f1/pins.json').read_text())
 if set(pins)!={'build.mjs','updater_runtime/refresh-bundle.mjs','automate.mjs','refresh.mjs'}:raise Held('Exact refresh source pins required')
 if any(hashlib.sha256((root/n).read_bytes()).hexdigest()!=h for n,h in pins.items()):raise Held('Refresh executable source drift')
 return pins

def checked_inputs(bundle):
 if type(bundle)is not dict or set(bundle)!={'state','source_files'}or bundle['state']!='supplied_candidate_not_approved' or type(bundle['source_files'])is not list or len(bundle['source_files'])>150:raise Held('Closed supplied candidate required')
 out={};total=0
 for row in bundle['source_files']:
  if type(row)is not dict or set(row)!={'path','content','sha256'}or type(row['path'])is not str or not ALLOWED.fullmatch(row['path'])or row['path']in out or type(row['content'])is not str or type(row['sha256'])is not str:raise Held('Exact data-only candidate required')
  try:raw=row['content'].encode('utf-8')
  except UnicodeError:raise Held('UTF-8 candidate required')from None
  total+=len(raw)
  if len(raw)>32*1024*1024 or total>MAX_INPUT or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise Held('Candidate byte/hash boundary')
  # No executable app/style/build/proxy/workflow changes or arbitrary paths.
  out[row['path']]=raw
 return out

def source_state(root):
 try:
  sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,stderr=subprocess.DEVNULL,text=True,timeout=5).strip()
  if not re.fullmatch('[a-f0-9]{40}',sha):raise ValueError()
 except Exception:raise Held('Git baseline unavailable')from None
 return sha

def _prepare(env,*,root=ROOT,bundle=None,package_context=None):
 if not enabled(env):return {'state':'disabled','source_fetches':0,'ai_calls':0,'issues':0,'published':False,'writes':False}
 root=Path(root).resolve();pin_check(root);base=source_state(root)
 inputs=checked_inputs(bundle or {'state':'supplied_candidate_not_approved','source_files':[]})
 # Copy only the real build's data/assets/code. Never copy .git/env/state/secrets.
 with tempfile.TemporaryDirectory(prefix='merged-finder-review-')as tmp:
  work=Path(tmp)
  for name in ('src','vendor'):
   original=root/name
   if not original.is_dir():raise Held('Build source unavailable')
   for p in original.rglob('*'):
    if p.is_symlink()or p.is_file()and p.stat().st_size>32*1024*1024:raise Held('Source symlink/byte boundary')
   shutil.copytree(original,work/name)
  shutil.copy2(root/'build.mjs',work/'build.mjs')
  for name,raw in inputs.items():
   p=work/name
   if not p.is_file()or p.is_symlink():raise Held('Only existing reviewed data paths')
   p.write_bytes(raw)
  node=shutil.which('node')
  if not node:raise Held('Node runtime unavailable; original unchanged')
  node=str(Path(node).resolve())
  clean_env={'PATH':'/usr/bin:/bin','HOME':str(work),'TMPDIR':str(work)}
  try:
   run=subprocess.run([node,'build.mjs'],cwd=work,env=clean_env,capture_output=True,timeout=45)
   if run.returncode:raise ValueError()
  except Exception:raise Held('Isolated catalogue build unavailable; original unchanged')from None
  generated=sorted(p.name for p in work.iterdir()if p.is_file()and (p.name in ('index.html','offline.html','sw.js')or re.fullmatch(r'data\.[a-f0-9]{12}\.js',p.name)))
  data=[n for n in generated if n.startswith('data.')]
  if len(data)!=1 or not all(n in generated for n in ('index.html','offline.html','sw.js')):raise Held('Complete generated bundle required')
  total=sum((work/n).stat().st_size for n in generated)
  if total>MAX_OUTPUT:raise Held('Generated bundle byte cap')
  texts={n:(work/n).read_text()for n in generated};version=data[0][5:17]
  if hashlib.sha256(texts[data[0]].encode()).hexdigest()[:12]!=version or "data.src = './"+data[0]+"'"not in texts['index.html']or data[0]not in texts['sw.js']or 'hsn-data-'+version not in texts['sw.js']or texts[data[0]]not in texts['offline.html']:raise Held('Generated dataset/SW/offline identity mismatch')
  syntax="""const fs=require('fs'),vm=require('vm');for(const name of ['index.html','offline.html']){const html=fs.readFileSync(name,'utf8');for(const m of html.matchAll(/<script>([\s\S]*?)<\/script>/g))new vm.Script(m[1]);}for(const name of fs.readdirSync('.').filter(n=>/^data\.[a-f0-9]{12}\.js$/.test(n)||n==='sw.js'))new vm.Script(fs.readFileSync(name,'utf8'));"""
  try:
   check=subprocess.run([node,'-e',syntax],cwd=work,env=clean_env,capture_output=True,timeout=15)
   if check.returncode:raise ValueError()
  except Exception:raise Held('Generated JavaScript syntax refused; original unchanged')from None
  # Never refresh pins simply because generated bytes differ. Capture exact
  # changed outputs and consumer checks for independent review, keeping live
  # original routes at their last-good source/pins.
  rows=[]
  for name in sorted(set(generated)|set(inputs)):
   raw=(work/name).read_bytes();previous=root/name
   h=hashlib.sha256(raw).hexdigest();old=hashlib.sha256(previous.read_bytes()).hexdigest()if previous.is_file()else None
   if h!=old:rows.append({'path':name,'bytes':len(raw),'sha256':h,'old_sha256':old})
  orphan=[p.name for p in root.glob('data.*.js')if re.fullmatch(r'data\.[a-f0-9]{12}\.js',p.name)and p.name!=data[0]]
  changed=bool(rows or orphan)
  report={'state':'held_consumer_review_required'if changed else'unchanged_rebuild_not_source_refresh','baseline':base,'changed_files':rows,'orphan_data_delete_proposals':sorted(orphan),'consumer_review':list(DEPENDENTS)if changed else[],'source_fetches':0,'ai_calls':0,'issues':0,'published':False,'writes':False,'source_freshness':'not_checked','catalogue_accuracy':'not_verified','auto_repin':False,'retries':0}
  if package_context is None:return report
  from integration import finder_package_f6 as package
  pins={name:hashlib.sha256((work/name).read_bytes()).hexdigest()for name in generated}
  source_pins={name:hashlib.sha256((work/name).read_bytes()).hexdigest()for name in package.SOURCE_FILES}
  packed=package.prepare(env,root=work,pins=pins,source_pins=source_pins,source_revision=package_context['revision'],baseline=base)
  return report,packed

def prepare(env,*,root=ROOT,bundle=None):
 return _prepare(env,root=root,bundle=bundle)

def prepare_package(env,*,root=ROOT,bundle=None,source_revision=None):
 # This is an explicit new held-artifact path, not a changed ordinary report API.
 if not enabled(env):return None
 from integration import finder_package_f6 as package
 if not package.enabled(env)or not package.rebind.enabled(env)or env.get(package.render.FLAG)!='true':raise Held('Explicit complete candidate/artifact/safety package flags required')
 if type(source_revision)is not str or not re.fullmatch('[a-f0-9]{40}',source_revision):raise Held('Exact package source revision required')
 return _prepare(env,root=root,bundle=bundle,package_context={'revision':source_revision})

def main():
 # OFF performs no Git, copy, build or candidate read.
 try:result=prepare(dict(os.environ))
 except Held as e:print(json.dumps({'state':'held','reason':str(e),'published':False,'writes':False}));return 1
 except Exception:print(json.dumps({'state':'held','reason':'Preparation unavailable; no publication attempted','published':False,'writes':False}));return 1
 print(json.dumps(result,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
