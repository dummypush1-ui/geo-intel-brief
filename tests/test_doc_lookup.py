"""Offline one-document migration integrity and hostile-section checks."""
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from scripts.doc_lookup import documentation, source_bytes
ROOT = Path(__file__).resolve().parents[1]
class DocumentationTests(unittest.TestCase):
 def test_single_md_and_all_original_sections(self):
  physical=[p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*.md') if '.git' not in p.parts]
  self.assertEqual(physical,['README.md'])
  docs=documentation(ROOT);self.assertEqual(len(docs),240)
  self.assertEqual(hashlib.sha256(docs['intelligence/geo/README.md']).hexdigest(),'adc826e5af1937625e557e98d9d851d4882cd33f4ab98769ad090cb94162522c')
 def section(self,path='docs/a.md',size=1,digest=None,content=b'x'):
  row={'path':path,'bytes':size,'sha256':digest or hashlib.sha256(content).hexdigest()}
  return b'<!-- ORIGINAL-DOC '+json.dumps(row).encode()+b' -->\n'+content+b'\n<!-- END-ORIGINAL-DOC -->'
 def test_tamper_shape_length_duplicate_refused(self):
  with TemporaryDirectory() as d:
   p=Path(d)/'README.md'
   for raw in [self.section(digest='0'*64),self.section(size=2),self.section(path='../x.md'),self.section(path='README.md'),self.section()+self.section()]:
    p.write_bytes(raw)
    with self.assertRaises(ValueError):documentation(d)
 def test_missing_non_doc_outside_symlink_refused(self):
  with TemporaryDirectory() as d:
   root=Path(d);(root/'README.md').write_bytes(self.section())
   self.assertEqual(source_bytes(root/'docs/a.md',root),b'x')
   with self.assertRaises(FileNotFoundError):source_bytes(root/'missing.py',root)
   with self.assertRaises(ValueError):source_bytes(root.parent/'outside.md',root)
   (root/'link.md').symlink_to('README.md')
   with self.assertRaises(ValueError):source_bytes(root/'link.md',root)
