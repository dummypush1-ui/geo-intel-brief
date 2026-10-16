import hashlib,io,json,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
from integration import finder_chain_f7 as m
ENV={flag:'true'for flag in (m.FLAG,m.source.FLAG,m.source.reconcile.FLAG,m.source.reconcile.build.FLAG,m.package.FLAG,m.package.rebind.FLAG,m.package.render.FLAG)}
class Tests(unittest.TestCase):
 def test_off_precedes_network_files_build_and_flags(self):
  with patch.object(m.source,'acquire',side_effect=AssertionError),patch.object(m.source.reconcile,'plan',side_effect=AssertionError),patch.object(m.source.reconcile.build,'prepare_package',side_effect=AssertionError):
   for env in ({},{m.FLAG:'false'}):self.assertIsNone(m.prepare(env))
  for v in ('TRUE','yes','1',''):
   with self.assertRaises(m.Held):m.prepare({m.FLAG:v})
 def test_all_flags_and_exact_commit_before_network(self):
  with patch.object(m.source,'acquire',side_effect=AssertionError):
   for flag in ENV:
    if flag==m.FLAG:continue
    env=dict(ENV);del env[flag]
    with self.subTest(flag=flag),self.assertRaises(m.Held):m.prepare(env,revision='a'*40)
   for revision in (None,'main','a'*39,'../x'):
    with self.assertRaises(m.Held):m.prepare(ENV,revision=revision)
 def test_fixed_flow_packages_exact_upstream_receipt_and_delta(self):
  rows=[{'path':n,'content':'SYNTHETIC DATA ONLY','sha256':m.package.sha(b'SYNTHETIC DATA ONLY')}for n in m.source.reconcile.FILES];snapshot={'source_files':rows};evidence={'source_file_sha256':{r['path']:r['sha256']for r in rows},'requests':5}
  acquired={'snapshot':snapshot,'evidence':evidence};bundle={'state':'fixture'};delta={'state':'held','sanctions':{'removals_applied':0}};rebuild={'baseline':'b'*40};files={'review/public-offline.html':b'fixture'};manifest={'files':{n:{'bytes':len(raw),'sha256':m.package.sha(raw)}for n,raw in files.items()}};payload=m.package.pack(files,manifest)
  # An undeclared extra F6 member is not propagated by repacking. Only its
  # already verified manifest's payload names are taken into the F7 package.
  buffer=io.BytesIO(payload)
  with zipfile.ZipFile(buffer,'a')as z:z.writestr('undeclared-extra',b'do not propagate')
  payload=buffer.getvalue();fake_fetch=object();fake_clock=object()
  expected={'format':'finder_source_chain_v1','source_evidence':evidence,'reconciliation':delta,'scratch_rebuild':rebuild,'runtime_rebinding':'not_applied','published':False,'auto_repin':False}
  with patch.object(m.source,'acquire',return_value=acquired)as acquire,patch.object(m.source.reconcile,'plan',return_value=(bundle,delta))as plan,patch.object(m.source.reconcile.build,'prepare_package',return_value=(rebuild,({},payload,manifest)))as build:
   report,actual,meta=m.prepare(ENV,revision='a'*40,root='/synthetic',fetch=fake_fetch,clock=fake_clock)
   acquire.assert_called_once_with(ENV,revision='a'*40,fetch=fake_fetch,clock=fake_clock)
   self.assertEqual(report['source_fetches'],5);self.assertEqual(report['state'],'held_complete_source_chain_not_runtime_rebound');self.assertEqual(report['source_revision'],'a'*40);self.assertEqual(report['baseline'],'b'*40);self.assertEqual(report['sha256'],m.package.sha(actual));self.assertEqual(report['bytes'],len(actual))
   for key in ('published','auto_repin','writes'):self.assertIs(report[key],False)
   self.assertEqual(meta['format'],'held_finder_chain_v1');self.assertEqual(meta['source_revision_binding'],'verified_git_commit_tree_regular_blobs_by_F3');self.assertEqual(meta['source_chain'],'provenance/source-chain.json');self.assertEqual(meta['upstream_source_files'],['upstream/'+n for n in m.source.reconcile.FILES])
   plan.assert_called_once_with(ENV,root='/synthetic',snapshot=snapshot);build.assert_called_once_with(ENV,root='/synthetic',bundle=bundle,source_revision='a'*40)
   with zipfile.ZipFile(io.BytesIO(actual))as archive:
    self.assertEqual(report['file_count'],len(archive.namelist()));self.assertEqual(set(meta['files']),set(archive.namelist())-{'manifest.json'});self.assertNotIn('undeclared-extra',archive.namelist());self.assertEqual(json.loads(archive.read('manifest.json')),meta)
    self.assertEqual(archive.read('upstream/src/sanctions.ts'),b'SYNTHETIC DATA ONLY');self.assertEqual(json.loads(archive.read('provenance/source-chain.json')),expected)
    for name,item in meta['files'].items():self.assertEqual({'sha256':m.package.sha(archive.read(name)),'bytes':len(archive.read(name))},item)
   # Construct an actual JSON provenance at exactly2MiB, not a mocked encoder.
   delta['padding']='';limit=2*1024*1024;delta['padding']='x'*(limit-len(m.encode(expected)));self.assertEqual(len(m.encode(expected)),limit)
   _,boundary,_=m.prepare(ENV,revision='a'*40,root='/synthetic')
   with zipfile.ZipFile(io.BytesIO(boundary))as archive:self.assertEqual(len(archive.read('provenance/source-chain.json')),limit)
   delta['padding']+='x'
   with self.assertRaisesRegex(m.Held,'Provenance byte cap'):m.prepare(ENV,revision='a'*40,root='/synthetic')
   del delta['padding'];acquired['evidence']['source_file_sha256'][rows[0]['path']]='0'*64
   with self.assertRaisesRegex(m.Held,'receipt mismatch'):m.prepare(ENV,revision='a'*40,root='/synthetic')
 def test_f1_package_gate_precedes_build(self):
  b=m.source.reconcile.build
  with patch.object(b,'_prepare',side_effect=AssertionError):
   self.assertIsNone(b.prepare_package({}))
   for flag in (m.package.FLAG,m.package.rebind.FLAG,m.package.render.FLAG):
    env=dict(ENV);del env[flag]
    with self.subTest(flag=flag),self.assertRaises(b.Held):b.prepare_package(env,source_revision='a'*40)
   for revision in ('main','a'*39,'a'*41,'A'*40):
    with self.subTest(revision=revision),self.assertRaises(b.Held):b.prepare_package(ENV,source_revision=revision)
 def test_f1_package_is_returned_before_scratch_cleanup(self):
  b=m.source.reconcile.build;seen=[];before={n:m.package.sha((b.ROOT/n).read_bytes())for n in ('index.html','offline.html','sw.js',*m.source.reconcile.FILES)}
  def capture(env,**kw):
   root=kw['root'];seen.append(root);self.assertTrue((root/'offline.html').is_file());self.assertEqual(set(kw['source_pins']),set(m.source.reconcile.FILES));self.assertEqual(kw['source_revision'],'a'*40);self.assertEqual(kw['baseline'],'b'*40);expected={p.name:m.package.sha(p.read_bytes())for p in root.iterdir()if p.is_file()and(p.name in ('index.html','offline.html','sw.js')or p.name.startswith('data.'))};self.assertEqual(kw['pins'],expected);self.assertEqual(len(expected),4);self.assertEqual(kw['source_pins'],{n:m.package.sha((root/n).read_bytes())for n in m.source.reconcile.FILES});return ({'state':'fixture'},b'fixture',{'state':'fixture'})
  with patch.object(m.package,'prepare',side_effect=capture),patch.object(b,'source_state',return_value='b'*40):
   report,packed=b.prepare_package(ENV,source_revision='a'*40);self.assertEqual(report['state'],'unchanged_rebuild_not_source_refresh');self.assertEqual(report['baseline'],'b'*40);self.assertEqual(packed[1],b'fixture')
  self.assertEqual(len(seen),1);self.assertFalse(seen[0].exists());self.assertEqual(before,{n:m.package.sha((b.ROOT/n).read_bytes())for n in before})
 def test_data_only_plan_never_builds(self):
  from tests.test_finder_reconcile_f2 import Tests as Fixture
  fixture=Fixture();r=m.source.reconcile
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);(root/'src').mkdir();(root/r.FILES[0]).write_text(fixture.partner());(root/r.FILES[1]).write_text(fixture.sanc())
   with patch.object(r.build,'prepare',side_effect=AssertionError):
    bundle,report=r.plan(ENV,root=root,snapshot=fixture.snapshot());self.assertEqual(bundle['source_files'],[]);self.assertEqual(report['sanctions']['removals_applied'],0);self.assertNotIn('rebuild',report)
if __name__=='__main__':unittest.main()
