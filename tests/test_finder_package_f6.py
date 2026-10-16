import hashlib,io,json,unittest,zipfile
from unittest.mock import patch
from integration import finder_package_f6 as m
class Tests(unittest.TestCase):
 def test_off_before_candidate_or_artifacts(self):
  with patch.object(m.rebind,'source_check',side_effect=AssertionError),patch.object(m,'pack',side_effect=AssertionError):self.assertIsNone(m.prepare({}));self.assertIsNone(m.prepare({m.FLAG:'false'}))
  for value in ('TRUE','yes','1',''):
   with self.assertRaises(m.Held):m.prepare({m.FLAG:value})
  for missing in (m.rebind.FLAG,m.render.FLAG):
   env={m.FLAG:'true',m.rebind.FLAG:'true',m.render.FLAG:'true'};del env[missing]
   with patch.object(m.rebind,'prepare',return_value=None),patch.object(m.render,'prepare',return_value=None),patch.object(m.rebind,'source_check',side_effect=AssertionError),self.subTest(missing=missing),self.assertRaises(m.Held):m.prepare(env,root='/synthetic',pins={'index.html':'0'*64,'offline.html':'0'*64,'sw.js':'0'*64,'data.000000000000.js':'0'*64},source_pins={n:'0'*64 for n in m.SOURCE_FILES},source_revision='a'*40,baseline='b'*40)
 def test_zip_deterministic_exact_bytes_names_manifest(self):
  files={'src/sanctions.ts':b'fixture','review/public-offline.html':b'<html>fixture only</html>'};manifest={'state':'held','files':{n:{'bytes':len(v),'sha256':m.sha(v)}for n,v in files.items()}}
  a=m.pack(files,manifest);reverse=dict(reversed(list(files.items())));other={'files':dict(reversed(list(manifest['files'].items()))),'state':'held'};self.assertEqual(a,m.pack(reverse,other))
  with zipfile.ZipFile(io.BytesIO(a))as z:
   self.assertEqual(z.namelist(),sorted(set(files)|{'manifest.json'}));self.assertEqual(json.loads(z.read('manifest.json')),manifest)
   for item in z.infolist():
    self.assertEqual(item.date_time,(1980,1,1,0,0,0));self.assertEqual(item.external_attr,0o100644<<16);self.assertEqual(item.compress_type,zipfile.ZIP_DEFLATED)
   for n,v in files.items():self.assertEqual(z.read(n),v)
  original=zipfile.ZipFile.read;names=zipfile.ZipFile.namelist
  def corrupt(archive,name,*args,**kwargs):return b'altered'if name=='src/sanctions.ts'else original(archive,name,*args,**kwargs)
  with patch.object(zipfile.ZipFile,'read',corrupt),self.assertRaisesRegex(m.Held,'hash mismatch'):m.pack(files,manifest)
  for fn in (lambda archive:names(archive)+['extra'],lambda archive:[n for n in names(archive)if n!='src/sanctions.ts']):
   with patch.object(zipfile.ZipFile,'namelist',fn),self.assertRaisesRegex(m.Held,'verification failed'):m.pack(files,manifest)
  with patch.object(zipfile.ZipFile,'testzip',return_value='src/sanctions.ts'),self.assertRaisesRegex(m.Held,'verification failed'):m.pack(files,manifest)
 def test_archive_traversal_caps_types_and_reserved_manifest(self):
  for name in ('../x','/x','a/../x','a//x','a\\x','./x','manifest.json'):
   with self.subTest(name=name),self.assertRaises(m.Held):m.pack({name:b'x'},{})
  for files in ({},{str(n):b'x'for n in range(17)},{'manifest.json':b'cannot overwrite','safe':b'x'}):
   with self.assertRaises(m.Held):m.pack(files,{'state':'cannot overwrite'})
  with self.assertRaises(m.Held):m.pack({'x':'not bytes'},{})
  with patch.object(m,'MAX_TOTAL',1),self.assertRaises(m.Held):m.pack({'x':b'xx'},{})
  with patch.object(m,'MAX_ZIP',1),self.assertRaises(m.Held):m.pack({'x':b'x'},{})
 def test_supplied_provenance_closed_before_io(self):
  env={m.FLAG:'true',m.rebind.FLAG:'true',m.render.FLAG:'true'};valid={n:'0'*64 for n in m.SOURCE_FILES}
  cases=[({},'a'*40,'b'*40),(valid,'main','b'*40),(valid,'a'*40,None)]
  for bad in ('a'*39,'a'*41,'A'*40):cases.extend([(valid,bad,'b'*40),(valid,'a'*40,bad)])
  with patch.object(m.rebind,'source_check',side_effect=AssertionError):
   for source_pins,revision,baseline in cases:
    with self.subTest(revision=revision,baseline=baseline),self.assertRaises(m.Held):m.prepare(env,source_pins=source_pins,source_revision=revision,baseline=baseline)
 def test_prepare_checks_raw_provider_constants_and_closed_manifest(self):
  names=('AI_PROXY_URL','AIS_PROXY_URL','BUILTIN_GEMINI_KEYS','BUILTIN_GROQ_KEYS','BUILTIN_MISTRAL_KEYS','BUILTIN_NVIDIA_KEYS');text=';'.join("const "+n+" = ''"for n in names);raw=text.encode();pins={'index.html':m.sha(raw),'offline.html':m.sha(raw),'sw.js':'0'*64,'data.000000000000.js':'0'*64};source_pins={n:'0'*64 for n in m.SOURCE_FILES};env={m.FLAG:'true',m.rebind.FLAG:'true',m.render.FLAG:'true'}
  contents={'index.html':raw,'offline.html':raw}
  def regular(root,name,pin,cap):return contents.get(name,b'fixture')
  artifacts={'integration/finder_identity_proof.bin':b'proof'};report={'editions':{'HS':'2022','IN':'snapshot:000000000000'},'raw_rows':1,'bound_count':1,'not_bound_reasons':{},'code_count':1,'identity_count':1}
  with patch.object(m.rebind,'source_check',return_value='data.000000000000.js'),patch.object(m,'regular',side_effect=regular),patch.object(m.rebind,'prepare',return_value=(report,artifacts)),patch.object(m.render,'prepare',return_value=({'writes':False},'<html>safe fixture</html>')):
   for revision,baseline in [('a'*40,'b'*40),('b'*40,'a'*40)]:
    result,payload,manifest=m.prepare(env,root='/synthetic',pins=pins,source_pins=source_pins,source_revision=revision,baseline=baseline)
    self.assertEqual(result['state'],'held_complete_candidate_bytes_not_runtime_rebound');self.assertEqual(manifest['state'],'held_not_runtime_rebound_not_approved');self.assertEqual(manifest['source_revision_binding'],'caller_must_verify_with_F3');self.assertEqual(result['sha256'],m.sha(payload));self.assertEqual(result['bytes'],len(payload));self.assertEqual(result['source_revision'],revision);self.assertEqual(result['baseline'],baseline);self.assertEqual(manifest['supplied_source_revision'],revision);self.assertEqual(manifest['baseline'],baseline)
    self.assertEqual(set(manifest),{'format','state','baseline','supplied_source_revision','source_revision_binding','source_pins','generated_pins','editions','identity_summary','safe_render','files','runtime_consumers','runtime_editions_and_pins','official_freshness','legal_accuracy','published','auto_repin'})
    self.assertEqual(manifest['editions'],report['editions']);self.assertEqual(manifest['runtime_editions_and_pins'],'not_modified');self.assertEqual(len(manifest['runtime_consumers']),18)
    for key in ('writes','published','auto_repin'):self.assertIs(result[key],False)
    for key in ('published','auto_repin'):self.assertIs(manifest[key],False)
    with zipfile.ZipFile(io.BytesIO(payload))as archive:
     self.assertEqual(result['file_count'],len(archive.namelist()));self.assertEqual(set(manifest['files']),set(archive.namelist())-{'manifest.json'});self.assertEqual(json.loads(archive.read('manifest.json')),manifest)
     self.assertIn('integration/finder_identity_proof.bin',archive.namelist());self.assertIn('review/public-offline.html',archive.namelist())
     for name,item in manifest['files'].items():self.assertEqual(item,{'bytes':len(archive.read(name)),'sha256':m.sha(archive.read(name))})
   for constant in names:
    declaration=("const "+constant+" = ''").encode()
    for shell in ('index.html','offline.html'):
     for bad in (raw.replace(declaration,("const "+constant+" = 'SECRET'").encode()),raw.replace(declaration,b''),raw+b';'+declaration):
      contents[shell]=bad
      with self.subTest(constant=constant,shell=shell,bad=bad),self.assertRaisesRegex(m.Held,'provider constants'):m.prepare(env,root='/synthetic',pins=pins,source_pins=source_pins,source_revision='a'*40,baseline='b'*40)
     contents[shell]=raw
 def test_regular_file_pin_symlink_and_bytes(self):
  import tempfile
  from pathlib import Path
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);(root/'file').write_bytes(b'fixture');pin=m.sha(b'fixture');self.assertEqual(m.regular(root,'file',pin,7),b'fixture')
   for wrong,cap in [('0'*64,7),(pin,6),('bad',7),('g'*64,7),('a'*63,7),('A'*64,7)]:
    with self.assertRaises(m.Held):m.regular(root,'file',wrong,cap)
   (root/'link').symlink_to(root/'file');(root/'directory').mkdir()
   for name in ('link','directory'):
    with self.assertRaises(m.Held):m.regular(root,name,pin,7)
   with patch.object(Path,'read_bytes',side_effect=AssertionError),self.assertRaises(m.Held):m.regular(root,'file',pin,6)
   with patch.object(Path,'read_bytes',return_value=b'oversize'),self.assertRaises(m.Held):m.regular(root,'file',pin,7)
if __name__=='__main__':unittest.main()
