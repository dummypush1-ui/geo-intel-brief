import unittest,json,hashlib,re,ast,zipfile,email
from pathlib import Path
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name,parse_wheel_filename
from packaging.tags import sys_tags
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'integration/dependency_audit'
def historical_lock(path):
 row=json.loads((ROOT/'integration/pypdf_remediation105/historical-locks.json').read_text())['locks'][path]
 raw=row['text'].encode();assert hashlib.sha256(raw).hexdigest()==row['sha256'];return raw

class Tests(unittest.TestCase):
 def setUp(self):
  self.a=json.loads((BASE/'audit.json').read_text());self.inv=json.loads((BASE/'import-inventory.json').read_text())
 def test_candidate_explicit_missing(self):
  a=self.a;self.assertEqual(a['status'],'candidate_blocked_missing_cached_wheel');self.assertEqual([x['distribution'] for x in a['missing']],['sgmllib3k']);self.assertIn('not attempted',a['fresh_install']);self.assertEqual(len(a['distributions']),25)
  s=historical_lock('requirements-offline-reviewed.candidate.txt').decode();self.assertIn('NOT VERIFIED INSTALLABLE',s);self.assertIn('sgmllib3k==1.0.0 # MISSING',s)
 def test_exact_lock_artifact_hash_equality(self):
  lines=[l for l in historical_lock('requirements-offline-reviewed.candidate.txt').decode().splitlines() if l and not l.startswith('#')];locks={}
  for l in lines:
   name,version=l.split()[0].split('==');key=canonicalize_name(name);self.assertNotIn(key,locks);locks[key]=(version,set(re.findall(r'--hash=sha256:([0-9a-f]{64})',l)))
  self.assertEqual(set(locks),set(self.a['distributions']))
  for key,d in self.a['distributions'].items():
   self.assertEqual(key,canonicalize_name(d['name']));self.assertEqual(locks[key][0],d['version'])
   hashes={x['sha256'] for x in self.a['artifacts'] if canonicalize_name(x['distribution'])==key and x['version']==d['version'] and x['compatible_here']}
   self.assertEqual(locks[key][1],hashes);self.assertEqual(not hashes,key in {canonicalize_name(x['distribution']) for x in self.a['missing']})
 def test_active_dependency_closure_specifiers(self):
  ds=self.a['distributions'];pending=[canonicalize_name(n) for n in self.a['roots']];seen=set()
  while pending:
   key=pending.pop();self.assertIn(key,ds)
   if key in seen:continue
   seen.add(key)
   for s in ds[key]['active_requires']:
    q=Requirement(s);self.assertTrue(q.marker is None or q.marker.evaluate({'extra':''}));dep=canonicalize_name(q.name);self.assertIn(dep,ds);self.assertIn(ds[dep]['version'],q.specifier);pending.append(dep)
   for s in ds[key]['inactive_markers_extras']:
    q=Requirement(s);self.assertIsNotNone(q.marker);self.assertFalse(q.marker.evaluate({'extra':''}))
  self.assertEqual(seen,set(ds))
 def test_cache_bytes_tags_metadata_or_explicit_unverified(self):
  absent=[x['filename'] for x in self.a['artifacts'] if not (Path(self.a['explicit_cache'])/x['filename']).is_file()]
  if absent:self.skipTest('UNVERIFIED artifact bytes/tags/metadata: unavailable explicit cache: '+', '.join(absent))
  tags=set(sys_tags());names=set()
  for x in self.a['artifacts']:
   self.assertNotIn(x['filename'],names);names.add(x['filename']);p=Path(self.a['explicit_cache'])/x['filename'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),x['sha256'])
   name,version,build,wt=parse_wheel_filename(p.name);self.assertEqual(canonicalize_name(x['distribution']),str(name));self.assertEqual(x['version'],str(version));self.assertEqual(x['tags'],sorted(map(str,wt)));self.assertEqual(x['compatible_here'],bool(wt&tags))
   with zipfile.ZipFile(p) as z:
    metas=[n for n in z.namelist() if n.endswith('.dist-info/METADATA')];self.assertEqual(len(metas),1);meta=email.message_from_bytes(z.read(metas[0]))
   self.assertEqual(canonicalize_name(meta['Name']),str(name));self.assertEqual(meta['Version'],str(version))
   d=self.a['distributions'][str(name)];active=sorted(str(Requirement(s)) for s in meta.get_all('Requires-Dist',[]) if Requirement(s).marker is None or Requirement(s).marker.evaluate({'extra':''}));self.assertEqual(active,d['active_requires'])
 def test_complete_classification(self):
  rows=self.inv['inventory'];self.assertEqual(len({r['import'] for r in rows}),len(rows));self.assertEqual(self.inv['unresolved'],[])
  for r in rows:
   self.assertIn(r['classification'],['stdlib','local','required_distribution','optional_absent','excluded','unresolved']);self.assertTrue(r['provenance'])
   if r['classification']=='required_distribution':
    self.assertTrue(r['distributions'])
    for d in r['distributions']:self.assertEqual(d['version'],self.a['distributions'][canonicalize_name(d['name'])]['version'])
   if r['classification']=='local':self.assertTrue(r['provenance']['paths'])
  mapped={r['import']:r for r in rows};self.assertEqual(mapped['bson']['distributions'][0]['name'],'pymongo');self.assertTrue(mapped['json']['stdlib']);self.assertEqual(mapped['pikepdf']['classification'],'optional_absent');self.assertEqual(mapped['playwright']['classification'],'excluded')
 def test_source_manifest_and_ast_inventory_consistency(self):
  b=self.inv['source_baseline'];self.assertEqual(b['revision'],self.a['source_baseline_revision']);self.assertEqual(hashlib.sha256(json.dumps(b['files'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),self.a['source_manifest_sha256'])
  expected={};dynamic=[];paths=[]
  for x in b['files']:
   paths.append(x['path']);p=ROOT/x['path'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),x['sha256'])
   for n in ast.walk(ast.parse(p.read_bytes())):
    if isinstance(n,ast.Import):
     for imp in n.names:expected.setdefault(imp.name.split('.')[0],set()).add(x['path'])
    if isinstance(n,ast.ImportFrom) and not n.level and n.module:expected.setdefault(n.module.split('.')[0],set()).add(x['path'])
    if isinstance(n,ast.Call) and ((isinstance(n.func,ast.Name) and n.func.id=='__import__') or (isinstance(n.func,ast.Attribute) and n.func.attr in ['import_module','spec_from_file_location'])):dynamic.append(x['path'])
  self.assertEqual(paths,sorted(set(paths)))
  actual=sorted(str(p.relative_to(ROOT)) for scope in b['scopes'] for p in (ROOT/scope).rglob('*.py') if '__pycache__' not in p.parts and str(p.relative_to(ROOT))!='tests/test_dependency_audit.py' and 'dependency_audit' not in p.parts and 'dependency_build' not in p.parts and str(p.relative_to(ROOT)) not in ('tests/test_dependency_build_runner.py','tests/accounts/test_wired_http.py','integration/accounts/wired_http.py','integration/nilgiri_watch_fixture/__init__.py','integration/nilgiri_watch_fixture/core.py','tests/test_nilgiri_watch_fixture.py','integration/manage_fixture95/__init__.py','integration/manage_fixture95/core.py','tests/test_manage_fixture95.py'))
  self.assertEqual(actual,paths);self.assertEqual({r['import']:set(r['files']) for r in self.inv['inventory']},expected);self.assertEqual(self.inv['dynamic_import_files'],sorted(set(dynamic)))
 def test_prerequisite_xfail_absence_distinct(self):
  a=self.a;self.assertIn('UNSUPPORTED_two_limiter',a['expected_failure']);self.assertEqual(a['prerequisites']['expat'],'expat_2.4.7');self.assertEqual(len(a['optional_absent']),2);self.assertIn('not verified',a['fresh_sdk_backend'])

class BuildReceiptTests(unittest.TestCase):
 def setUp(self):
  self.b=ROOT/'integration/dependency_build';self.r=json.loads((self.b/'receipt.json').read_text())
 def test_separate_immutable_baseline(self):
  self.assertEqual(hashlib.sha256(historical_lock('requirements-offline-reviewed.candidate.txt')).hexdigest(),self.r['baseline87_sha256']);self.assertIn('MISSING WHEEL/HASH',historical_lock('requirements-offline-reviewed.candidate.txt').decode());self.assertNotIn('MISSING WHEEL/HASH',historical_lock('integration/dependency_build/requirements-offline-built.txt').decode());self.assertEqual(hashlib.sha256((self.b/'executed-orchestrator.txt').read_bytes()).hexdigest(),self.r['orchestrator_sha256'])
 def test_build_inputs_isolation_and_stage_outcomes(self):
  s=self.r['stages'];self.assertEqual(s['source_inspection']['member_count'],11);self.assertEqual(s['source_inspection']['total_bytes'],20923);self.assertEqual(s['source_inspection']['sdist_sha256'],'7868fb1c8bfa764c1ac563d3cf369c381d1325d36124933a726f29fcdaa812e9');self.assertIn('bubblewrap',self.r['sandbox']['mechanism'])
  for stage in ['isolation_probe','wheel_build','fresh_venv','offline_install','pip_check','installed_metadata','sdk_smoke','guarded_sdk_backend']:self.assertEqual(s[stage]['status'],'passed');self.assertEqual(s[stage]['exit_code'],0);self.assertIsNone(s[stage]['stop_reason'])
  for n,v in [('wheel','0.37.1'),('setuptools','59.6.0')]:self.assertEqual(self.r['build_tools'][n]['version'],v);self.assertTrue(self.r['build_tools'][n]['files'])
 def test_exact_complete_lock_installed_closure(self):
  a=json.loads((BASE/'audit.json').read_text());w=self.r['stages']['wheel_inspection'];self.assertEqual(w['dependencies'],[]);self.assertIn('not claimed',w['deterministic_bytes']);self.assertEqual(self.r['stages']['artifact_closure']['count'],25)
  lines=[l for l in historical_lock('integration/dependency_build/requirements-offline-built.txt').decode().splitlines() if l and not l.startswith('#')];self.assertEqual(len(lines),25)
  for key,d in a['distributions'].items():
   line=next(l for l in lines if l.split('==')[0]==d['name']);hashes=set(re.findall(r'--hash=sha256:([0-9a-f]{64})',line));self.assertEqual(hashes,{w['sha256']} if key=='sgmllib3k' else {x['sha256'] for x in a['artifacts'] if canonicalize_name(x['distribution'])==key});self.assertTrue(line.startswith(d['name']+'=='+d['version']+' '))
  installed={canonicalize_name(n):v for n,v in self.r['installed_metadata']['packages']};self.assertEqual({k:v for k,v in installed.items() if k not in ('pip','setuptools')},{k:d['version'] for k,d in a['distributions'].items()});self.assertTrue(self.r['installed_metadata']['no_system_site']);self.assertEqual(self.r['installed_metadata']['expat'],'expat_2.4.7')
