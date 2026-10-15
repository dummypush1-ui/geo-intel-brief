import hashlib,json,os,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from integration import finder_refresh_f1 as m
ROOT=Path(__file__).resolve().parents[1]
ENV={m.FLAG:'true'}
class Tests(unittest.TestCase):
 def row(self,n,text):return {'path':n,'content':text,'sha256':hashlib.sha256(text.encode()).hexdigest()}
 def bundle(self,rows):return {'state':'supplied_candidate_not_approved','source_files':rows}
 def test_OFF_no_git_build_copy_or_provider(self):
  with patch.object(m,'pin_check',side_effect=AssertionError()),patch.object(m,'source_state',side_effect=AssertionError()),patch.object(m.shutil,'copytree',side_effect=AssertionError()),patch.object(m.subprocess,'run',side_effect=AssertionError()):
   self.assertEqual(m.prepare({})['state'],'disabled');self.assertEqual(m.prepare({m.FLAG:'false'},bundle={'secret':'PRIVATE'})['state'],'disabled')
 def test_exact_env(self):
  for value in ['TRUE','yes','1','',True,None]:
   with self.assertRaises(m.Held):m.prepare({m.FLAG:value})
  for env in [None,[],{m.FLAG:'true','x':False}]:
   with self.assertRaises(m.Held):m.prepare(env)
 def test_closed_data_inputs(self):
  x=self.row('src/tradevalues.ts','public fixture');self.assertEqual(m.checked_inputs(self.bundle([x])),{x['path']:x['content'].encode()})
  for n in ['src/app.js','build.mjs','proxy.js','.env','.github/workflows/refresh.yml','state/health.json','../src/tradevalues.ts','src//tradevalues.ts','/src/tradevalues.ts','src/datachunk0.ts\n']:
   with self.assertRaises(m.Held):m.checked_inputs(self.bundle([self.row(n,'x')]))
  for b in [self.bundle([x,x]),{'state':'approved','source_files':[]},{**self.bundle([]),'auto_publish':True},self.bundle([{**x,'sha256':'0'*64}]),self.bundle([{**x,'api_key':'PRIVATE'}]),self.bundle([{'path':x['path'],'content':'\ud800','sha256':'x'}])]:
   with self.assertRaises(m.Held):m.checked_inputs(b)
 def test_input_cap(self):
  with patch.object(m,'MAX_INPUT',3),self.assertRaises(m.Held):m.checked_inputs(self.bundle([self.row('src/tradevalues.ts','1234')]))
 def test_pin_schema_and_drift(self):
  original=json.loads((ROOT/'integration/finder_refresh_f1/pins.json').read_text())
  for p in [{**original,'extra':'0'*64},{k:v for k,v in original.items()if k!='build.mjs'},{**original,'build.mjs':'0'*64}]:
   with patch.object(m.json,'loads',return_value=p),self.assertRaises(m.Held):m.prepare(ENV)
 def tree_digest(self):
  names=['index.html','offline.html','sw.js','src/tradevalues.ts']+[x.name for x in ROOT.glob('data.*.js')]
  return {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest()for n in names}
 def test_actual_last_good_rebuild_NO_network_secrets_publication(self):
  before=self.tree_digest();original=m.subprocess.run;calls=[]
  def run(*a,**k):calls.append((a,k));return original(*a,**k)
  with patch.dict(os.environ,{'GITHUB_TOKEN':'PRIVATE','COMTRADE_KEY':'PRIVATE','GEMINI_API_KEY':'PRIVATE'}),patch.object(m.subprocess,'run',side_effect=run):out=m.prepare(ENV)
  self.assertEqual(out['state'],'unchanged_rebuild_not_source_refresh');self.assertEqual(before,self.tree_digest());self.assertEqual(out['changed_files'],[]);self.assertFalse(out['published']);self.assertFalse(out['writes']);self.assertEqual(out['source_fetches'],0);self.assertEqual(out['ai_calls'],0);self.assertEqual(len(calls),3);self.assertEqual(calls[1][0][0],['node','build.mjs']);self.assertEqual(set(calls[1][1]['env']),{'PATH','HOME','TMPDIR'});self.assertNotIn('PRIVATE',json.dumps(out))
 def test_actual_changed_data_holds_consumer_review_last_good_unchanged(self):
  before=self.tree_digest();text=(ROOT/'src/tradevalues.ts').read_text()+'\n// supplied fixture candidate only\n';out=m.prepare(ENV,bundle=self.bundle([self.row('src/tradevalues.ts',text)]));self.assertEqual(before,self.tree_digest());self.assertEqual(out['state'],'held_consumer_review_required');self.assertFalse(out['auto_repin']);self.assertFalse(out['published']);self.assertFalse(out['writes']);self.assertIn('integration/finder_offline.py',out['consumer_review']);self.assertIn('integration/code_news_index/manifest.json',out['consumer_review']);self.assertTrue(out['orphan_data_delete_proposals']);self.assertTrue(any(r['path']=='src/tradevalues.ts'for r in out['changed_files']))
 def test_failure_sanitized_and_original_unchanged(self):
  before=self.tree_digest()
  for failure in [subprocess.TimeoutExpired('PRIVATE',45),RuntimeError('PRIVATE')]:
   with patch.object(m,'source_state',return_value='a'*40),patch.object(m.subprocess,'run',side_effect=failure),self.assertRaisesRegex(m.Held,'original unchanged'):m.prepare(ENV)
  self.assertEqual(before,self.tree_digest())
 def test_syntax_error_candidate_refused_no_source_mutation(self):
  before=self.tree_digest();text=(ROOT/'src/tradevalues.ts').read_text()+"\nthis is invalid JS;\n"
  with self.assertRaisesRegex(m.Held,'JavaScript syntax refused'):m.prepare(ENV,bundle=self.bundle([self.row('src/tradevalues.ts',text)]))
  self.assertEqual(before,self.tree_digest())
 def test_workflow_off_read_only_no_legacy_automation(self):
  s=(ROOT/'integration/finder_refresh_f1/finder-refresh-prep.yml.txt').read_text();self.assertIn("vars.MERGED_FINDER_REFRESH_PREP_ENABLED == 'true'",s);self.assertIn('contents: read',s);self.assertIn('persist-credentials: false',s);self.assertNotIn('secrets.',s);self.assertNotIn('git push',s);self.assertNotIn('node automate.mjs',s);self.assertIn('concurrency:',s);self.assertIn('cancel-in-progress: false',s);self.assertIn('30 3 * * *',s);self.assertIn(m.FLAG+'=false',(ROOT/'.env.example').read_text())
 def test_each_consumer_path_exists(self):
  for n in m.DEPENDENTS:self.assertTrue((ROOT/n).is_file(),n)
 def test_more_than150_files_and_single_file_cap(self):
  row=self.row('src/tradevalues.ts','x')
  with self.assertRaises(m.Held):m.checked_inputs(self.bundle([row]*151))
  large='x'*(32*1024*1024+1)
  with self.assertRaises(m.Held):m.checked_inputs(self.bundle([self.row('src/tradevalues.ts',large)]))
 def test_source_symlink_rejected(self):
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);(root/'src').mkdir();(root/'vendor').mkdir();(root/'src/link.ts').symlink_to(ROOT/'src/tradevalues.ts')
   with patch.object(m,'pin_check',return_value={}),patch.object(m,'source_state',return_value='a'*40),self.assertRaisesRegex(m.Held,'symlink'):m.prepare(ENV,root=root)
 def test_generated_caps_identity_and_orphan_only(self):
  with patch.object(m,'MAX_OUTPUT',1),self.assertRaisesRegex(m.Held,'Generated bundle byte cap'):m.prepare(ENV)
  real=m.subprocess.run
  def modified(mode):
   def run(*a,**k):
    result=real(*a,**k)
    if a[0]==['node','build.mjs']:
     w=Path(k['cwd']);data=next(w.glob('data.*.js'))
     if mode=='multiple':(w/'data.000000000000.js').write_text('x')
     elif mode=='hash':data.write_text(data.read_text()+'\n')
     elif mode=='offline':(w/'offline.html').write_text('<html>missing data</html>')
    return result
   return run
  for mode in ('multiple','hash','offline'):
   with patch.object(m.subprocess,'run',side_effect=modified(mode)),self.assertRaises(m.Held):m.prepare(ENV)
  # Extra orphan only, with byte-identical normal build: still a held proposal.
  original=Path.glob
  def glob(path,pattern):
   values=list(original(path,pattern))
   if path==ROOT and pattern=='data.*.js':values.append(Path('data.000000000000.js'))
   return iter(values)
  with patch.object(Path,'glob',glob):out=m.prepare(ENV)
  self.assertEqual(out['state'],'held_consumer_review_required');self.assertEqual(out['changed_files'],[]);self.assertIn('data.000000000000.js',out['orphan_data_delete_proposals'])
 def test_cli_off_without_source_effects(self):
  r=subprocess.run([os.sys.executable,'-B','-m','integration.finder_refresh_f1'],cwd=ROOT,capture_output=True,text=True,env={'PATH':'/usr/bin:/bin',m.FLAG:'false'},timeout=5);self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout)['state'],'disabled')
if __name__=='__main__':unittest.main()
