import hashlib,json,tempfile,unittest,zipfile,io,shutil
from pathlib import Path
from unittest.mock import Mock,patch
from integration import finder_composition_f9 as m,finder_binding_f8 as f8,finder_package_f6 as f6,news_finder_navigation_prep as nav
from integration.public_preview_builder import build_public_preview
from integration.public_live_builder import build_public_live_preview
from tests.test_code_news_coverage_binding_prep import SAMPLE,LIVE,ORIGIN,Client,Binding as CoverageBinding
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.root=Path(cls.tmp.name);root=cls.root
  # Synthetic equivalent-data new edition, built from exact local last-good
  # snapshot. No external lookup, official data claim or source acquisition.
  old='data.d6d1b417562b.js'
  data=(ROOT/old).read_text();newdata=data+'\n';name='data.'+hashlib.sha256(newdata.encode()).hexdigest()[:12]+'.js'
  values={name:newdata,'index.html':(ROOT/'index.html').read_text().replace(old,name),'offline.html':(ROOT/'offline.html').read_text().replace(data,newdata,1),'sw.js':(ROOT/'sw.js').read_text().replace(old,name).replace('hsn-data-'+old[5:17],'hsn-data-'+name[5:17])}
  for n,text in values.items():(root/n).write_text(text)
  for n in f6.SOURCE_FILES:(root/n).parent.mkdir(exist_ok=True);shutil.copy2(ROOT/n,root/n)
  pins={n:f6.sha((root/n).read_bytes())for n in values};sp={n:f6.sha((root/n).read_bytes())for n in f6.SOURCE_FILES};env={flag:'true'for flag in (f6.FLAG,f6.rebind.FLAG,f6.render.FLAG)}
  report,payload,manifest=f6.prepare(env,root=root,pins=pins,source_pins=sp,source_revision='a'*40,baseline='b'*40)
  with zipfile.ZipFile(io.BytesIO(payload))as z:files={n:z.read(n)for n in manifest['files']}
  evidence={'repository':'push2006/finder-hsn-codee','revision':'a'*40,'source_file_sha256':sp,'git_blob_sha1':{n:hashlib.sha1(b'blob '+str(len((root/n).read_bytes())).encode()+b'\0'+(root/n).read_bytes()).hexdigest()for n in sp}}
  receipt={'format':'finder_source_chain_v1','source_evidence':evidence,'reconciliation':{'source_revision':'a'*40,'source_file_hashes':sp,'sanctions':{'removals_applied':0}},'scratch_rebuild':{'baseline':'b'*40},'runtime_rebinding':'not_applied','published':False,'auto_repin':False}
  for n in sp:files['upstream/'+n]=(root/n).read_bytes()
  files['provenance/source-chain.json']=json.dumps(receipt).encode()
  manifest.update(format='held_finder_chain_v1',source_revision_binding='verified_git_commit_tree_regular_blobs_by_F3',files={n:{'bytes':len(raw),'sha256':f6.sha(raw)}for n,raw in files.items()},source_chain='provenance/source-chain.json',upstream_source_files=['upstream/'+n for n in sp])
  payload=f6.pack(files,manifest);archive=root/'held.zip';archive.write_bytes(payload)
  for n,raw in files.items():p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
  cls.binding=f8.prepare({f8.FLAG:'true'},archive=archive,expected_sha256=f6.sha(payload),root=root);cls.edition=dict(cls.binding.profile.editions)['IN'];cls.env=dict(SAMPLE,**{m.FLAG:'true',nav.FLAG:'true','PUBLIC_CODE_NEWS_ENABLED':'true','PUBLIC_CODE_NEWS_SCOPE_REVIEWED':'true','PUBLIC_RELATIONSHIP_NAV_ENABLED':'true','PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED':'true'})
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def app(self,**extra):return build_public_preview(dict(self.env,**extra),finder_candidate_binding=self.binding)
 def test_off_before_binding_reads_and_invalid_authority_shape(self):
  with patch.object(f8.Binding,'verify',side_effect=AssertionError):self.assertIsNone(m.prepare({}));self.assertIsNone(m.prepare({m.FLAG:'false'}))
  for env,binding in [({},self.binding),({m.FLAG:'TRUE'},None),({m.FLAG:'true'},self.binding),({**SAMPLE,m.FLAG:'true'},object())]:
   with self.assertRaises(m.Held):m.prepare(env,binding)
  factory=Mock()
  with self.assertRaises(m.Held):build_public_live_preview(dict(LIVE,**{m.FLAG:'true'}),client_factory=factory,finder_candidate_binding=object())
  factory.assert_not_called()
 def test_sample_selected_offline_same_app_mount_and_edition_assets(self):
  app=self.app();client=app.test_client();self.assertTrue(nav.mounted(app));selected=m.selected(app);self.assertEqual(dict(selected.editions)['IN'],self.edition)
  r=client.get(nav.PATH,base_url=ORIGIN);self.assertEqual(r.status_code,200);self.assertIn("connect-src 'none'",r.headers['Content-Security-Policy']);self.assertNotIn('localStorage',r.text);self.assertIn('X-Finder-Public-Snapshot',r.headers)
  for path in ('/workspace/assets/relationship_navigation.js','/workspace/assets/code_news_coverage.js'):
   text=client.get(path,base_url=ORIGIN).text;self.assertIn(self.edition,text);self.assertNotIn('snapshot:d6d1b417562b',text)
  with patch.object(f8.Binding,'verify',side_effect=AssertionError):self.assertEqual(client.head(nav.PATH,base_url=ORIGIN).status_code,200)
  self.assertEqual(client.get(nav.PATH,base_url='https://evil.test').status_code,403)
  self.assertEqual(client.get('/workspace/finder/index.html',base_url=ORIGIN).status_code,403)
 def test_live_coverage_code_news_and_proof_same_edition(self):
  client=Client()
  for row in client.store.rows:row.update(title='HSN090121;',summary='')
  env=dict(LIVE,**{k:v for k,v in self.env.items()if k not in SAMPLE})
  with patch('integration.public_live_builder.ReadOnlyNewsReader',return_value=lambda:{'geo':[]}):app=build_public_live_preview(env,client_factory=lambda *a,**k:client,coverage_binding_provider=lambda:CoverageBinding(True,True,True,True,'fixture-owner','fixture-deploy'),finder_candidate_binding=self.binding)
  self.addCleanup(app.extensions['finder_composition_close_f9'])
  broker=app.extensions['code_news_coverage_broker'];self.assertEqual(broker.model.folder,self.root/'integration/code_news_index');self.assertEqual(dict(broker.finder_proof.editions)['IN'],self.edition)
  headers={'Origin':ORIGIN,'Sec-Fetch-Site':'same-origin','Sec-Fetch-Mode':'cors','Sec-Fetch-Dest':'empty'}
  r=app.test_client().post('/api/code-news-coverage',base_url=ORIGIN,headers=headers,json={'system':'IN','edition':self.edition,'code':'090121'});self.assertEqual(r.status_code,200,r.text);self.assertEqual(r.json['finder_navigation']['state'],'ready',r.json);self.assertIn('#code=1:090121',r.json['finder_navigation']['url'])
  out=app.test_client().get('/api/code-news-context?query=090121&system=IN&edition='+self.edition,base_url=ORIGIN);self.assertEqual(out.status_code,200);self.assertEqual(app.extensions['code_news_public'].model.folder,self.root/'integration/code_news_index')
 def test_old_new_coexist_and_wrong_or_drift_mount_refused(self):
  new=self.app();old=build_public_preview(SAMPLE);self.assertTrue(nav.mounted(new));self.assertTrue(nav.mounted(old));self.assertIsNone(m.selected(old))
  with patch.object(f8.Binding,'verify',side_effect=f8.Held('drift')):
   self.assertFalse(nav.mounted(new));self.assertEqual(new.test_client().get(nav.PATH,base_url=ORIGIN).status_code,503);self.assertEqual(old.test_client().head(nav.PATH,base_url=ORIGIN).status_code,200)
  new.view_functions['offline_finder_snapshot']=lambda:None;self.assertFalse(nav.mounted(new))
 def test_manual_AI_bridge_selected_edition_no_live_service(self):
  app=self.app(PUBLIC_AI_ANSWERS_ENABLED='true');r=app.test_client().get(nav.PATH,base_url=ORIGIN);self.assertEqual(r.status_code,200);self.assertIn(self.edition,r.text);self.assertNotIn('snapshot:d6d1b417562b',r.text);self.assertIn('public-ai-question-v1',r.text);self.assertEqual(app.extensions['public_ai_answers']['state'],'held')
 def test_OFF_bytes_headers_original_sample(self):
  namespace={};path=ROOT/'tests/fixtures/f9_base_sample.txt';exec(compile(path.read_text(),str(path),'exec'),namespace);old=namespace['build_public_preview'](SAMPLE);new=build_public_preview(dict(SAMPLE,**{m.FLAG:'false'}))
  for route in ['/workspace',nav.PATH,'/workspace/assets/workspace.js']:
   for method in ('get','head','post'):
    a=getattr(old.test_client(),method)(route,base_url=ORIGIN);b=getattr(new.test_client(),method)(route,base_url=ORIGIN);self.assertEqual((a.status_code,a.data,dict(a.headers)),(b.status_code,b.data,dict(b.headers)))
 def test_consumer_pin_drift_precedes_client_and_partial_build_closes(self):
  env=dict(LIVE,**{m.FLAG:'true'});factory=Mock()
  original=Path.read_bytes
  def changed(path):return b'drift'if str(path).endswith('news_api.py')else original(path)
  with patch.object(Path,'read_bytes',changed),self.assertRaisesRegex(m.Held,'consumer drift'):build_public_live_preview(env,client_factory=factory,finder_candidate_binding=self.binding)
  factory.assert_not_called()
  client=Client();offcoverage=dict(env,PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED='false',PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED='false')
  with patch.object(m,'install',side_effect=m.Held('partial')),self.assertRaises(ValueError):build_public_live_preview(offcoverage,client_factory=lambda *a,**k:client,finder_candidate_binding=self.binding)
  self.assertEqual(client.closes,1)
 def test_navigation_wrong_edition_and_unsupported_target(self):
  app=self.app();proof=self.binding.proof()
  try:
   target={'system':'IN','edition':self.edition,'code':'090121','description':'NOT DECAFFEINATED :'};evidence=nav.prepare(proof,target);self.assertEqual(evidence['state'],'bound');self.assertEqual(nav.decorate(app,evidence)['state'],'ready')
   self.assertEqual(nav.prepare(proof,dict(target,edition='snapshot:d6d1b417562b'))['state'],'unavailable');self.assertEqual(nav.prepare(proof,dict(target,system='US'))['state'],'unavailable');self.assertEqual(nav.prepare(proof,dict(target,description='Other'))['state'],'unavailable')
  finally:proof.close()
 def test_same_selection_UI_seam_and_repeated_install_refusal(self):
  app=self.app();selection=m.selected(app)
  for value in ('no edition',"const editions={HS:'2022',IN:'snapshot:d6d1b417562b'}"*2):
   with self.assertRaises(m.Held):m.edition_asset(value,selection)
  with self.assertRaises(m.Held):m.install(app,selection)
  self.assertNotIn('snapshot:d6d1b417562b',m.edition_asset("const editions={HS:'2022',IN:'snapshot:d6d1b417562b'}",selection))
 def test_exact_flags_with_valid_binding_before_any_IO(self):
  for value in ('TRUE','1'):
   with self.subTest(value=value),patch.object(Path,'read_text',side_effect=AssertionError('IO')),patch.object(f8.Binding,'verify',side_effect=AssertionError('binding IO')),self.assertRaisesRegex(m.Held,'Exact Finder composition flag'):m.prepare(dict(SAMPLE,**{m.FLAG:value}),self.binding)
 def test_closed_consumer_pin_set_extra_and_missing(self):
  source=ROOT/'integration/finder_composition_f9/pins.json';pins=json.loads(source.read_text());original=Path.read_text
  for kind in ('extra','missing'):
   altered=dict(pins)
   if kind=='extra':altered['integration/not-a-consumer.py']='0'*64
   else:altered.pop(next(iter(altered)))
   def read(path,*args,**kwargs):return json.dumps(altered)if path==source else original(path,*args,**kwargs)
   with self.subTest(kind=kind),patch.object(Path,'read_text',read),self.assertRaisesRegex(m.Held,'consumer drift'):m.prepare(dict(SAMPLE,**{m.FLAG:'true'}),self.binding)
 def test_prepare_verifies_tamper_before_raw_offline_read(self):
  path=self.root/'src/tradepartners.ts';saved=path.read_bytes();original=Path.read_text;reads=[]
  def read(target,*args,**kwargs):
   if target==self.root/'offline.html':reads.append(target)
   return original(target,*args,**kwargs)
  try:
   path.write_bytes(saved+b'changed')
   with patch.object(Path,'read_text',read),self.assertRaises(f8.Held):m.prepare(dict(SAMPLE,**{m.FLAG:'true'}),self.binding)
   self.assertEqual(reads,[])
  finally:path.write_bytes(saved)
 def test_duplicate_install_guard_even_with_original_view_restored(self):
  from integration.news_api import offline_finder_snapshot
  app=self.app();selection=m.selected(app);app.view_functions['offline_finder_snapshot']=offline_finder_snapshot
  with patch.object(m.Selection,'verify',side_effect=AssertionError('guard must precede verify')),self.assertRaisesRegex(m.Held,'One exact Finder selection per app'):m.install(app,selection)
 def test_install_verifies_before_any_view_change(self):
  from integration.news_api import create_app,offline_finder_snapshot
  selection=m.prepare(dict(SAMPLE,**{m.FLAG:'true'}),self.binding);app=create_app(authorize=lambda r:True)
  with patch.object(m.Selection,'verify',side_effect=f8.Held('install verify')),self.assertRaisesRegex(f8.Held,'install verify'):m.install(app,selection)
  self.assertIs(app.view_functions['offline_finder_snapshot'],offline_finder_snapshot);self.assertNotIn(m.KEY,app.extensions)
 def test_app_close_closes_lazy_model_once_and_registers_per_app(self):
  from types import SimpleNamespace
  from integration.news_api import create_app
  selection=m.prepare(dict(SAMPLE,**{m.FLAG:'true'}),self.binding);app=create_app(authorize=lambda r:True);model=Mock();coverage=Mock();app.extensions.update(code_news_public=SimpleNamespace(model=model),coverage_close=coverage)
  with patch('atexit.register')as register:m.install(app,selection)
  close=app.extensions['finder_composition_close_f9'];register.assert_called_once_with(close);close();close();model.close.assert_called_once_with();coverage.assert_called_once_with()
 def test_prepare_rejects_safe_render_derivation_drift(self):
  with patch.object(m,'_candidate_safety_shell',return_value='different safe render'),self.assertRaisesRegex(m.Held,'safe-render derivation drift'):m.prepare(dict(SAMPLE,**{m.FLAG:'true'}),self.binding)
 def test_selected_rejects_nonexact_selection_type(self):
  from types import SimpleNamespace
  class DerivedSelection(m.Selection):pass
  value=m.Selection(self.binding,'',self.binding.profile.editions)
  for candidate in (object(),DerivedSelection(value.binding,value.rendered,value.editions)):
   with self.subTest(candidate=type(candidate).__name__):self.assertIsNone(m.selected(SimpleNamespace(extensions={m.KEY:candidate})))
  self.assertIs(m.selected(SimpleNamespace(extensions={m.KEY:value})),value)
 def test_install_rejects_nonexact_selection_type_before_verify(self):
  from integration.news_api import create_app,offline_finder_snapshot
  class DerivedSelection(m.Selection):pass
  app=create_app(authorize=lambda r:True);candidate=DerivedSelection(self.binding,'',self.binding.profile.editions)
  with patch.object(m.Selection,'verify',side_effect=AssertionError('type guard first')),self.assertRaisesRegex(m.Held,'One exact Finder selection per app'):m.install(app,candidate)
  self.assertIs(app.view_functions['offline_finder_snapshot'],offline_finder_snapshot);self.assertNotIn(m.KEY,app.extensions)
 def test_install_rejects_replaced_original_view(self):
  from integration.news_api import create_app
  app=create_app(authorize=lambda r:True);other=lambda:None;app.view_functions['offline_finder_snapshot']=other
  selection=m.prepare(dict(SAMPLE,**{m.FLAG:'true'}),self.binding)
  with self.assertRaisesRegex(m.Held,'Original offline view required'):m.install(app,selection)
  self.assertIs(app.view_functions['offline_finder_snapshot'],other);self.assertNotIn(m.KEY,app.extensions);self.assertNotIn('finder_composition_close_f9',app.extensions)
if __name__=='__main__':unittest.main()
