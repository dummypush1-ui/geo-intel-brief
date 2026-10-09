import unittest,json,re,hashlib,zipfile,email
from pathlib import Path
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def setUp(self):self.a=json.loads((ROOT/'integration/runner199lock-audit.json').read_text())
 def test_versions_complete_officialhashsets_preserveold(self):
  lines=[l for l in (ROOT/'requirements-future-deploy.lock').read_text().splitlines()if l and not l.startswith('#')];self.assertEqual(len(lines),25)
  for row,line in zip(self.a['packages'],lines):
   self.assertEqual(line.split()[0],row['name']+'=='+row['version']);hashes=set(re.findall(r'--hash=sha256:([0-9a-f]{64})',line));official={x['sha256']for x in row['artifacts']};self.assertEqual(hashes,official|set(row['local_previously_reviewed_hashes']));self.assertTrue(set(row['original_hashes'])<=hashes);self.assertEqual(row['artifact_count'],len(row['artifacts']));self.assertTrue(row['metadata_url'].startswith('https://pypi.org/pypi/'))
 def test_charset_exact_reportedwheel_in_complete172(self):
  r=next(x for x in self.a['packages']if x['name']=='charset-normalizer');self.assertEqual(len(r['artifacts']),172);self.assertIn('3d31298449090ab8d47b7b1b2a555ff73cac7ed438a08b7ac160980c7ebed649',r['hashes'])
 def test_all25_runnerdownloads_and_five_oldmismatches(self):
  rows=self.a['runner_cp312_download_verification'];self.assertEqual(len(rows),25);self.assertEqual({r['name']for r in rows if r['old_lock_would_fail']},{'charset-normalizer','markupsafe','pymongo','pyyaml','sgmllib3k'})
  for row in rows:
   package=next(p for p in self.a['packages']if p['name']==row['name']);self.assertIn(row['sha256'],package['hashes']);self.assertTrue(any(x['url']==row['url']and x['sha256']==row['sha256']for x in package['artifacts']))
 def test_sgmllib_reviewed_buildhash_vs_officialsdist_explicit(self):
  r=next(p for p in self.a['packages']if p['name']=='sgmllib3k');self.assertEqual(r['local_previously_reviewed_hashes'],['d697b1ce32621812e6fbf5d3dac57818192068f47e4b6f39bc76e14a8fb4c534']);self.assertEqual(r['artifacts'][0]['sha256'],'7868fb1c8bfa764c1ac563d3cf369c381d1325d36124933a726f29fcdaa812e9')
 def test_no_version_changes_or_workflowsecret_activation(self):
  s=(ROOT/'integration/RUNNER199LOCK.md').read_text();self.assertIn('no version change',s);self.assertIn('--require-hashes',s);self.assertIn('3.12 execution not performed',s)
