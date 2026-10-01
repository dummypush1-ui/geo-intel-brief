import hashlib,json,unittest
from scripts.package_manifest import ROOT,commit_files
class PackageManifestTests(unittest.TestCase):
 def test_exact_paths_and_hashes(self):
  manifest=json.loads((ROOT/'staging-manifest.json').read_text())
  self.assertEqual({x['path'] for x in manifest['files']},{str(p.relative_to(ROOT)) for p in commit_files()})
  for row in manifest['files']:self.assertEqual(row['sha256'],hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest(),row['path'])
 def test_no_public_upload_instructions(self):
  names={str(p.relative_to(ROOT)) for p in commit_files()}
  self.assertNotIn('UPLOAD-INSTRUCTIONS.txt',names);self.assertNotIn('PATCH-V6-README.txt',names)
