"""Static file-by-file inventory. Not proof of runtime behavior or live state."""
import ast,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'integration/file-connections.json'
def inventory():
 paths=sorted(p for p in ROOT.rglob('*') if p.is_file() and not any(x in p.parts for x in ('.git','__pycache__','.venv','node_modules')) and p!=OUTPUT)
 known={str(p.relative_to(ROOT)) for p in paths}
 modules={x[:-3].replace('/','.'):(x) for x in known if x.endswith('.py')}
 modules.update({x[:-12].replace('/','.'):(x) for x in known if x.endswith('/__init__.py')})
 rows=[]
 for p in paths:
  name=str(p.relative_to(ROOT));project='geo' if name.startswith('intelligence/geo/') else 'brics' if name.startswith('intelligence/brics/') else 'integration' if name.startswith('integration/') else 'test' if name.startswith('tests/') else 'finder_or_build'
  edges=[];unresolved=[]
  if p.suffix=='.py':
   tree=ast.parse(p.read_text())
   for node in ast.walk(tree):
    names=[n.name for n in node.names] if isinstance(node,ast.Import) else [node.module] if isinstance(node,ast.ImportFrom) and node.module else []
    for m in names:
     if m in modules:edges.append(modules[m])
     elif m.startswith('intelligence.') or m.startswith('integration.'):unresolved.append(m)
  if p.suffix in ('.js','.mjs','.html','.gs','.ts'):
   for item in re.findall(r'''(?:from\s*|import\s*|src=|href=)["']([^"']+)["']''',p.read_text(errors='replace')):
    local=item.split('?')[0].split('#')[0]
    if not local or '://' in local:continue
    target=str((p.parent/local).resolve().relative_to(ROOT)) if (p.parent/local).resolve().is_relative_to(ROOT) else ''
    if target in known:edges.append(target)
    elif target+'.ts' in known:edges.append(target+'.ts')
    elif target+'.js' in known:edges.append(target+'.js')
  role=('isolated_legacy_execution' if p.name in ('app.py','web.py','scheduler.py','run_all.py','Code.gs','server.js','worker.mjs','Procfile') and project!='integration' else 'preserved_engine_or_asset' if project in ('geo','brics','finder_or_build') else 'offline_contract_or_private_view' if project=='integration' else 'fixture_test')
  rows.append({'path':name,'project':project,'role':role,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'static_file_edges':sorted(set(edges)),'unresolved_internal_imports':sorted(set(unresolved)),'runtime_verified':False})
 return {'status':'static_audit_not_runtime_acceptance','files':rows,'file_count':len(rows),'limits':['Dynamic references and network endpoints need runtime adapter tests','Legacy launchers deliberately not connected to merged private entrypoint','Live services and database mappings not audited by this inventory']}
if __name__=='__main__':OUTPUT.write_text(json.dumps(inventory(),indent=2)+'\n')
