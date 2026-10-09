import hashlib
from pathlib import Path
import re
import subprocess
import unittest

ROOT=Path(__file__).parents[1]
class Tests(unittest.TestCase):
 def test_mocked_node_contract(self):
  out=subprocess.run(['node','feature_mail_mount/test_handlers216.js'],cwd=ROOT,capture_output=True,text=True,timeout=15)
  self.assertEqual(out.returncode,0,out.stdout+out.stderr);self.assertIn('PASS216:',out.stdout)
 def test_existing_bridge_and_companion_unchanged(self):
  for path,digest in [('feature_mail_mount/bridge.gs','c1851a96f40089ad5bfbf9ee35c39fdd3b21f87ff3a514b1b9225b4e7f59c199'),('intelligence/geo/apps_script/Code.gs','d4d3da4f6b44d962e1c59e88baa9e4c54b786a723dc4ce7f1c5cb2289eb85c67')]:
   self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest)
 def test_literal_surface_no_current_caller(self):
  src=(ROOT/'feature_mail_mount/handlers216.gs').read_text()
  self.assertEqual(re.findall(r'runMailV1\([^)]*\)',src),["runMailV1('digest')","runMailV1('critical')","runMailV1('weekly')"])
  self.assertNotRegex(src,r'216\s*\(\s*true\b')
  self.assertNotRegex(src,r'PropertiesService|ScriptApp|MAIL_V1_ENABLED|GmailApp|MailApp|UrlFetchApp|Logger|console')
  for p in ROOT.rglob('*.gs'):
   if p.name=='handlers216.gs':continue
   self.assertNotRegex(p.read_text(),r'mailV1(?:Digest|Critical|Weekly)216\s*\(')
 def test_namespace_and_handlers_unchanged(self):
  from feature_mail_mount.operations import HANDLERS
  self.assertEqual(HANDLERS,{'digest':'mailV1Digest','critical':'mailV1Critical','weekly':'mailV1Weekly'})
  allnames=[]
  for p in ROOT.rglob('*.gs'):
   allnames+=re.findall(r'function\s+(\w+)\s*\(',p.read_text())
  for n in ['mailV1Digest216','mailV1Critical216','mailV1Weekly216','mail216Result']:
   self.assertEqual(allnames.count(n),1);self.assertFalse(n.endswith('_'))
