import unittest,ast
from pathlib import Path
class Tests(unittest.TestCase):
 def test_download_explicit_hold_not_empty_success(self):
  from intelligence.geo.collectors.sanctions import update_ofac_names,LegacySanctionsHeld
  with self.assertRaises(LegacySanctionsHeld):update_ofac_names()
 def test_screen_explicit_hold_not_clean_or_substring(self):
  from intelligence.geo.collectors.sanctions import screen_text,LegacySanctionsHeld
  for text,names in [('foobar',['foo']),('safe',[]),(None,None)]:
   with self.assertRaises(LegacySanctionsHeld):screen_text(text,names)
 def test_no_transport_import_or_activation(self):
  tree=ast.parse(Path('intelligence/geo/collectors/sanctions.py').read_text());self.assertFalse(any(isinstance(n,(ast.Import,ast.ImportFrom)) for n in ast.walk(tree)))
  for name in ['app.py','scheduler.py','web.py']:
   t=ast.parse(Path('intelligence/geo',name).read_text());self.assertFalse(any(isinstance(n,ast.Name)and n.id in ('update_ofac_names','screen_text')for n in ast.walk(t)))
