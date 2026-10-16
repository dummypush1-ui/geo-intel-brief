import copy,hashlib,io,json,tempfile,unittest,zipfile
from dataclasses import FrozenInstanceError,replace
from pathlib import Path
from unittest.mock import patch
from integration import finder_binding_f8 as m,finder_identity_proof_prep as p
from integration.finder_package_f6 import pack
ENV={m.FLAG:'true'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def encoded(v):return (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
class Tests(unittest.TestCase):
 def fixture(self,root,seed=b'SYNTHETIC DATA ONLY'):
  data='data.'+sha(seed)[:12]+'.js';edition='snapshot:'+sha(seed)[:12];files={n:b'SYNTHETIC ONLY'for n in m.FIXED};files[data]=seed
  proof=b''.join(p.RECORD.pack(i,b'090121'.ljust(12,b' '),hashlib.sha256(b'Coffee').digest())for i in (0,1));files[p.ARTIFACT]=proof
  gen={n:sha(files[n])for n in ('index.html','offline.html','sw.js',data)};source={n:sha(files[n])for n in ('src/tradepartners.ts','src/sanctions.ts')};upstream={n:sha(files['upstream/'+n])for n in source}
  evidence={'repository':'push2006/finder-hsn-codee','revision':'a'*40,'source_file_sha256':upstream,'git_blob_sha1':{n:hashlib.sha1(b'blob '+str(len(files['upstream/'+n])).encode()+b'\0'+files['upstream/'+n]).hexdigest()for n in source}}
  files['provenance/source-chain.json']=encoded({'format':'finder_source_chain_v1','source_evidence':evidence,'reconciliation':{'source_revision':'a'*40,'source_file_hashes':upstream,'sanctions':{'removals_applied':0}},'scratch_rebuild':{'baseline':'b'*40},'runtime_rebinding':'not_applied','published':False,'auto_repin':False})
  files['integration/code_news_index/manifest.json']=encoded({'format':'code_news_flat_v1','source_pins':{'expected_shell_sha256':gen['index.html'],'expected_bundle_sha256':gen[data]},'files':{n:{'bytes':len(files['integration/code_news_index/'+n]),'sha256':sha(files['integration/code_news_index/'+n])}for n in ('codes.idx','rows.jsonl')}})
  meta={'format':'held_finder_chain_v1','state':'held_not_runtime_rebound_not_approved','baseline':'b'*40,'supplied_source_revision':'a'*40,'source_revision_binding':'verified_git_commit_tree_regular_blobs_by_F3','source_pins':source,'generated_pins':gen,'editions':{'HS':'2022','IN':edition},'identity_summary':{},'safe_render':{'source_sha256':gen['offline.html'],'rendered_sha256':sha(files['review/public-offline.html']),'bytes':len(files['review/public-offline.html']),**{k:True for k in ('network_disabled','keys_removed','device_storage_disabled','csv_formula_safe','shortlist_wrap')}},'files':{},'runtime_consumers':list(m.DEPENDENTS),'runtime_editions_and_pins':'not_modified','official_freshness':'not_verified','legal_accuracy':'not_verified','published':False,'auto_repin':False,'source_chain':'provenance/source-chain.json','upstream_source_files':['upstream/'+n for n in source]}
  for n,raw in files.items():
   dest=root/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
  return files,meta
 def archive(self,root,files,meta):
  meta['files']={n:{'bytes':len(raw),'sha256':sha(raw)}for n,raw in files.items()};payload=pack(files,meta);path=root/'fixture.zip';path.write_bytes(payload);return path,sha(payload)
 def load(self,root,files,meta):
  path,pin=self.archive(root,files,meta);return m.prepare(ENV,archive=path,expected_sha256=pin,root=root)
 def test_off_before_path_hash_and_any_reads(self):
  with patch.object(Path,'open',side_effect=AssertionError),patch.object(zipfile,'ZipFile',side_effect=AssertionError):
   self.assertIsNone(m.prepare({}));self.assertIsNone(m.prepare({m.FLAG:'false'},archive='../bad',root=None))
  for value in ('TRUE','yes','1',''):
   with self.assertRaises(m.Held):m.prepare({m.FLAG:value})
  for pin in (None,'a'*63,'A'*64,'g'*64):
   with self.assertRaises(m.Held):m.prepare(ENV,expected_sha256=pin)
 def test_real_synthetic_binding_immutable_and_no_mount(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);files,meta=self.fixture(root);before={n:sha((root/n).read_bytes())for n in files};binding=self.load(root,files,meta)
   self.assertEqual(binding.baseline,'b'*40);self.assertEqual(binding.source_revision,'a'*40);self.assertEqual(dict(binding.profile.editions),meta['editions']);self.assertEqual(len(binding.files),14);binding.verify()
   with self.assertRaises(FrozenInstanceError):binding.baseline='c'*40
   with self.assertRaises(FrozenInstanceError):binding.profile.artifact_sha256='0'*64
   proof=binding.proof()
   try:
    self.assertEqual(proof.bound('IN',meta['editions']['IN'],'090121')['code'],'090121');self.assertIsNone(proof.bound('IN',p.EDITIONS['IN'],'090121'))
    with self.assertRaises(TypeError):proof.editions['IN']='wrong'
   finally:proof.close()
   self.assertEqual(before,{n:sha((root/n).read_bytes())for n in files})
 def test_two_profiles_and_last_good_are_independent(self):
  with tempfile.TemporaryDirectory()as tmp:
   parent=Path(tmp);a=parent/'a';b=parent/'b';a.mkdir();b.mkdir();fa,ma=self.fixture(a,b'SYNTHETIC-A');fb,mb=self.fixture(b,b'SYNTHETIC-B');ba=self.load(a,fa,ma);bb=self.load(b,fb,mb);pa=ba.proof();pb=bb.proof();old=p.FinderProof()
   try:
    self.assertNotEqual(ma['editions']['IN'],mb['editions']['IN'])
    for proof,edition,wrong in ((pa,ma['editions']['IN'],mb['editions']['IN']),(pb,mb['editions']['IN'],ma['editions']['IN']),(old,p.EDITIONS['IN'],ma['editions']['IN'])):
     self.assertIsNotNone(proof.bound('IN',edition,'090121'));self.assertIsNone(proof.bound('IN',wrong,'090121'))
    self.assertEqual(dict(old.editions),p.EDITIONS)
   finally:pa.close();pb.close();old.close()
 def test_root_drift_invalidates_lookup_and_revalidation(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);files,meta=self.fixture(root);binding=self.load(root,files,meta);proof=binding.proof()
   try:
    (root/'offline.html').write_bytes(b'changed')
    with self.assertRaises(m.Held):binding.verify()
    self.assertIsNone(proof.bound('HS','2022','090121'))
   finally:proof.close()
 def test_wrong_archive_hash_missing_root_and_symlinks(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);files,meta=self.fixture(root);path,pin=self.archive(root,files,meta)
   for archive,expected,folder in ((path,'0'*64,root),(path,pin,None),(root/'missing',pin,root)):
    with self.assertRaises(m.Held):m.prepare(ENV,archive=archive,expected_sha256=expected,root=folder)
   link=root/'link.zip';link.symlink_to(path)
   with self.assertRaises(m.Held):m.prepare(ENV,archive=link,expected_sha256=pin,root=root)
   target=root/'offline.html';target.unlink();target.symlink_to(root/'index.html')
   with self.assertRaises(m.Held):m.prepare(ENV,archive=path,expected_sha256=pin,root=root)
 def test_exact_manifest_editions_sources_and_receipt(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);files,meta=self.fixture(root)
   mutations=[lambda d:d.update(format='other'),lambda d:d.update(published=True),lambda d:d.update(auto_repin=True),lambda d:d.update(baseline='main'),lambda d:d['editions'].update(IN=p.EDITIONS['IN']),lambda d:d['generated_pins'].update(index='0'*64),lambda d:d.update(runtime_consumers=[]),lambda d:d.update(extra=True),lambda d:d['safe_render'].update(network_disabled=False)]
   for mutate in mutations:
    changed=copy.deepcopy(meta);mutate(changed)
    with self.subTest(meta=changed),self.assertRaises(m.Held):self.load(root,files,changed)
   receipt=json.loads(files['provenance/source-chain.json'])
   for field,value in (('source_evidence',dict(receipt['source_evidence'],revision='c'*40)),('scratch_rebuild',{'baseline':'c'*40}),('reconciliation',dict(receipt['reconciliation'],sanctions={'removals_applied':1}))):
    bad=dict(files);bad['provenance/source-chain.json']=encoded(dict(receipt,**{field:value}))
    with self.assertRaises(m.Held):self.load(root,bad,copy.deepcopy(meta))
 def test_profile_closed_paths_hashes_and_edition(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);files,meta=self.fixture(root);profile=self.load(root,files,meta).profile
   for bad in (replace(profile,pins=list(profile.pins)),replace(profile,pins=profile.pins+profile.pins[:1]),replace(profile,pins=profile.pins[:-1]),replace(profile,editions=(('HS','2022'),('IN','snapshot:wrong'))),replace(profile,artifact_sha256='A'*64),replace(profile,pins=tuple((n,'g'*64)for n,_ in profile.pins))):
    with self.assertRaises(p.Unavailable):bad.validate()
   with self.assertRaises(p.Unavailable):p.FinderProof(root,profile=object())
 def test_decode_duplicate_invalid_and_cap(self):
  for raw in (b'{"a":1,"a":2}',b'\xff',b'{',b'x'*(2*1024*1024+1)):
   with self.assertRaises(m.Held):m.decode(raw)
 def test_stream_boundaries(self):
  self.assertEqual(m.digest_stream(io.BytesIO(b'ab'),2),sha(b'ab'))
  for raw,size in ((b'ab',1),(b'a',2)):
   with self.assertRaises(m.Held):m.digest_stream(io.BytesIO(raw),size)
 def test_closed_archive_names_and_types_and_bounded_reads(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);files,meta=self.fixture(root);path,pin=self.archive(root,files,meta)
   payload=path.read_bytes()
   cases=[]
   for change in ('extra','missing','duplicate','stored','permissions'):
    buffer=io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(payload))as original,zipfile.ZipFile(buffer,'w')as archive:
     for item in original.infolist():
      raw=original.read(item.filename)
      if change=='missing'and item.filename=='offline.html':continue
      if change=='stored'and item.filename=='offline.html':item.compress_type=zipfile.ZIP_STORED
      if change=='permissions'and item.filename=='offline.html':item.external_attr=0o120777<<16
      archive.writestr(item,raw)
     if change in ('extra','duplicate'):archive.writestr('extra'if change=='extra'else'offline.html',b'x')
    cases.append((change,buffer.getvalue()))
   for change,raw in cases:
    path.write_bytes(raw)
    with self.subTest(change=change),self.assertRaises(m.Held):m.prepare(ENV,archive=path,expected_sha256=sha(raw),root=root)
   path.write_bytes(payload)
   for limit in ('MAX_ARCHIVE','MAX_TOTAL','MAX_FILE'):
    with patch.object(m,limit,1),self.assertRaises(m.Held):m.prepare(ENV,archive=path,expected_sha256=pin,root=root)
 def test_same_length_root_hash_drift_and_parent_symlink(self):
  with tempfile.TemporaryDirectory()as tmp:
   parent=Path(tmp);root=parent/'root';root.mkdir();files,meta=self.fixture(root);binding=self.load(root,files,meta)
   target=root/'index.html';target.write_bytes(b'x'*len(files['index.html']))
   with self.assertRaisesRegex(m.Held,'hash drift'):binding.verify()
   target.write_bytes(files['index.html']);link=parent/'linked';link.symlink_to(root,target_is_directory=True)
   with self.assertRaises(m.Held):replace(binding,root=link).verify()
   directory=root/'integration';directory.rename(root/'original-integration');directory.symlink_to(root/'original-integration',target_is_directory=True)
   with self.assertRaises(m.Held):binding.verify()
 def test_profile_artifact_swap_and_short_reads_fail_closed(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);files,meta=self.fixture(root);binding=self.load(root,files,meta);proof=binding.proof();target=root/p.ARTIFACT
   try:
    with patch.object(p.os,'pread',return_value=b''):self.assertIsNone(proof.bound('HS','2022','090121'))
    replacement=target.with_suffix('.new');replacement.write_bytes(files[p.ARTIFACT]);replacement.replace(target);self.assertIsNone(proof.bound('HS','2022','090121'))
   finally:proof.close()
 def raw_archive(self,root,files,meta,*,order=None,mutate_info=None):
  members={**files,'manifest.json':encoded(meta)};buffer=io.BytesIO()
  with zipfile.ZipFile(buffer,'w')as archive:
   for name in (sorted(members)if order is None else order):
    info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
    if mutate_info:mutate_info(info)
    archive.writestr(info,members[name])
  payload=buffer.getvalue();path=root/'raw.zip';path.write_bytes(payload);return path,sha(payload)
 def assert_bad(self,root,files,meta,reason):
  path,pin=self.raw_archive(root,files,meta)
  with self.assertRaisesRegex(m.Held,reason):m.prepare(ENV,archive=path,expected_sha256=pin,root=root)
 def test_each_closed_manifest_field_and_label(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);files,meta=self.fixture(root);self.archive(root,files,meta)
   for key,value in [('state','approved'),('source_revision_binding','caller'),('runtime_editions_and_pins','changed'),('source_chain','wrong.json'),('upstream_source_files',[]),('official_freshness','verified'),('legal_accuracy','verified')]:
    bad=copy.deepcopy(meta);bad[key]=value
    with self.subTest(key=key):self.assert_bad(root,files,bad,'Exact held chain manifest')
   for field in ('baseline','supplied_source_revision'):
    for value in ('a'*39,'a'*41,'A'*40):
     bad=copy.deepcopy(meta);bad[field]=value
     with self.subTest(field=field,value=value):self.assert_bad(root,files,bad,'Exact source/baseline labels')
   bad=copy.deepcopy(meta);bad['files'].pop('sw.js');self.assert_bad(root,files,bad,'Closed candidate payload')
   for rename in [('sw.js','replacement'),(next(n for n in files if n.startswith('data.')),'notdata.js')]:
    altered=dict(files);altered[rename[1]]=altered.pop(rename[0]);bad=copy.deepcopy(meta);bad['files'][rename[1]]=bad['files'].pop(rename[0]);self.assert_bad(root,altered,bad,'Closed candidate payload'if rename[0]=='sw.js'else'Exact candidate bundle name')
   altered=dict(files);altered.pop('sw.js');bad=copy.deepcopy(meta);bad['files'].pop('sw.js');self.assert_bad(root,altered,bad,'Closed candidate archive')
   for item in ({'bytes':1,'sha256':'0'*64,'extra':1},{'bytes':'1','sha256':'0'*64},{'bytes':True,'sha256':'0'*64},{'bytes':999,'sha256':'0'*64},{'bytes':len(files['sw.js']),'sha256':'g'*64},{'bytes':len(files['sw.js']),'sha256':'a'*63}):
    bad=copy.deepcopy(meta);bad['files']['sw.js']=item;self.assert_bad(root,files,bad,'Exact candidate payload hashes')
   for field in ('generated_pins','source_pins'):
    for kind in ('missing','extra','wrongsha'):
     bad=copy.deepcopy(meta);name=next(iter(bad[field]))
     if kind=='missing':bad[field].pop(name)
     elif kind=='extra':bad[field]['extra']='0'*64
     else:bad[field][name]='0'*64
     with self.subTest(field=field,kind=kind):self.assert_bad(root,files,bad,'Generated/source manifest binding')
 def test_each_receipt_index_and_safe_render_field(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);files,meta=self.fixture(root);self.archive(root,files,meta);receipt=json.loads(files['provenance/source-chain.json'])
   changes=[('format','other'),('runtime_rebinding','applied'),('published',True),('auto_repin',True)]
   for field,value in changes:
    body=copy.deepcopy(receipt);body[field]=value;altered=dict(files);altered['provenance/source-chain.json']=encoded(body);bad=copy.deepcopy(meta);bad['files']['provenance/source-chain.json']={'bytes':len(altered['provenance/source-chain.json']),'sha256':sha(altered['provenance/source-chain.json'])}
    with self.subTest(field=field):self.assert_bad(root,altered,bad,'Source chain receipt binding')
   for section,field,value in [('source_evidence','revision','c'*40),('source_evidence','repository','wrong/repo'),('scratch_rebuild','baseline','c'*40),('reconciliation','source_revision','c'*40),('reconciliation','sanctions',{'removals_applied':1}),('source_evidence','source_file_sha256',{}),('reconciliation','source_file_hashes',{}),('source_evidence','git_blob_sha1',{})]:
    body=copy.deepcopy(receipt);body[section][field]=value;altered=dict(files);altered['provenance/source-chain.json']=encoded(body);bad=copy.deepcopy(meta);bad['files']['provenance/source-chain.json']={'bytes':len(altered['provenance/source-chain.json']),'sha256':sha(altered['provenance/source-chain.json'])}
    reason='Upstream source receipt'if field in ('source_file_sha256','source_file_hashes','git_blob_sha1')else'Source chain receipt binding'
    with self.subTest(section=section,field=field):self.assert_bad(root,altered,bad,reason)
   index=json.loads(files['integration/code_news_index/manifest.json'])
   for field,value in [('format','wrong'),('source_pins',{}),('files',{}),('files',dict(index['files'],**{'rows.jsonl':{'bytes':1,'sha256':'0'*64}}))]:
    altered=dict(files);altered['integration/code_news_index/manifest.json']=encoded(dict(index,**{field:value}));bad=copy.deepcopy(meta);bad['files']['integration/code_news_index/manifest.json']={'bytes':len(altered['integration/code_news_index/manifest.json']),'sha256':sha(altered['integration/code_news_index/manifest.json'])};self.assert_bad(root,altered,bad,'Index/source manifest')
   for field,value in [('source_sha256','0'*64),('rendered_sha256','0'*64),('bytes',1),*[(k,False)for k in ('keys_removed','device_storage_disabled','csv_formula_safe','shortlist_wrap')]]:
    bad=copy.deepcopy(meta);bad['safe_render'][field]=value
    with self.subTest(field=field):self.assert_bad(root,files,bad,'Safe render/source binding')
 def test_zip_hash_names_encryption_manifest_cap_and_stream_errors(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);files,meta=self.fixture(root);path,pin=self.archive(root,files,meta)
   for expected in ('A'*64,'g'*64,'a'*63,'a'*65):
    with self.assertRaises(m.Held):m.prepare(ENV,archive=path,expected_sha256=expected,root=root)
   with self.assertRaises(m.Held):m.prepare(ENV,archive=root,expected_sha256=pin,root=root)
   raw=bytearray(path.read_bytes());raw[0]^=1;path.write_bytes(raw)
   with self.assertRaisesRegex(m.Held,'archive hash mismatch'):m.prepare(ENV,archive=path,expected_sha256=pin,root=root)
   names=sorted([*files,'manifest.json']);path,pin=self.raw_archive(root,files,meta,order=list(reversed(names)))
   with self.assertRaisesRegex(m.Held,'Closed candidate archive'):m.prepare(ENV,archive=path,expected_sha256=pin,root=root)
   path,pin=self.raw_archive(root,files,meta,order=[n for n in names if n!='manifest.json'])
   with self.assertRaisesRegex(m.Held,'Closed candidate archive'):m.prepare(ENV,archive=path,expected_sha256=pin,root=root)
   bad=copy.deepcopy(meta);bad['oversize']='x'*(2*1024*1024);path,pin=self.raw_archive(root,files,bad)
   with self.assertRaisesRegex(m.Held,'Manifest byte cap'):m.prepare(ENV,archive=path,expected_sha256=pin,root=root)
   badfiles=dict(files);badfiles['sw.js']=b'x'*len(files['sw.js']);self.assert_bad(root,badfiles,meta,'Archived payload hash mismatch')
   path,pin=self.archive(root,files,meta);original_open=zipfile.ZipFile.open
   def extra_bytes(archive,name,*args,**kwargs):return io.BytesIO(files['sw.js']+b'x')if name=='sw.js'else original_open(archive,name,*args,**kwargs)
   with patch.object(zipfile.ZipFile,'open',extra_bytes),self.assertRaisesRegex(m.Held,'Candidate byte cap'):m.prepare(ENV,archive=path,expected_sha256=pin,root=root)
   def short_bytes(archive,name,*args,**kwargs):return io.BytesIO(files['sw.js'][:-1])if name=='sw.js'else original_open(archive,name,*args,**kwargs)
   with patch.object(zipfile.ZipFile,'open',short_bytes),self.assertRaisesRegex(m.Held,'size mismatch'):m.prepare(ENV,archive=path,expected_sha256=pin,root=root)
   path,pin=self.archive(root,files,meta);original=zipfile.ZipFile.infolist
   def encrypted(archive):
    entries=original(archive);entries[0].flag_bits|=1;return entries
   with patch.object(zipfile.ZipFile,'infolist',encrypted),self.assertRaisesRegex(m.Held,'entry type/byte cap'):m.prepare(ENV,archive=path,expected_sha256=pin,root=root)
  with self.assertRaisesRegex(m.Held,'Candidate byte cap'):m.digest_stream(io.BytesIO(b'ab'),1)
  with self.assertRaisesRegex(m.Held,'size mismatch'):m.digest_stream(io.BytesIO(b'a'),2)
 def test_root_verify_before_proof_and_package_identity(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);files,meta=self.fixture(root);path,pin=self.archive(root,files,meta);binding=m.prepare(ENV,archive=path,expected_sha256=pin,root=root);self.assertEqual(binding.package_sha256,pin)
   with patch.object(m.Binding,'verify',side_effect=m.Held('first verify'))as verify,patch.object(m,'FinderProof',side_effect=AssertionError),self.assertRaisesRegex(m.Held,'first verify'):binding.proof()
   verify.assert_called_once_with()
   (root/'sw.js').write_bytes(b'oversize root')
   with self.assertRaisesRegex(m.Held,'size drift'):binding.verify()
 def test_profile_symlink_regular_type_and_artifact_lifecycle(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);files,meta=self.fixture(root);profile=self.load(root,files,meta).profile
   with self.assertRaises(p.Unavailable):p.verify_sources(root,object())
   for target in ('index.html','integration/code_news_index/rows.jsonl'):
    path=root/target;raw=path.read_bytes();path.unlink();path.symlink_to(root/'offline.html')
    with self.assertRaises(p.Unavailable):p.verify_sources(root,profile)
    path.unlink();path.mkdir()
    with self.assertRaises(p.Unavailable):p.verify_sources(root,profile)
    path.rmdir();path.write_bytes(raw)
   directory=root/'integration/code_news_index';directory.rename(root/'original-index');directory.symlink_to(root/'original-index',target_is_directory=True)
   with self.assertRaises(p.Unavailable):p.verify_sources(root,profile)
   directory.unlink();(root/'original-index').rename(directory)
   artifact=root/p.ARTIFACT;raw=artifact.read_bytes();other=artifact.with_suffix('.saved');artifact.rename(other);artifact.symlink_to(other)
   with self.assertRaises(p.Unavailable):p.FinderProof(root,profile=profile)
   artifact.unlink();other.rename(artifact);proof=p.FinderProof(root,profile=profile)
   try:
    artifact.rename(other);artifact.symlink_to(other);self.assertIsNone(proof.bound('HS','2022','090121'))
   finally:proof.close()
if __name__=='__main__':unittest.main()
