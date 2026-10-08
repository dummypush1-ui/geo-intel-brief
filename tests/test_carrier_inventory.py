import ast,hashlib,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class CarrierInventoryTests(unittest.TestCase):
 def test_exact_path_hash_and_ast(self):
  inv=json.loads((ROOT/'feature_carrier_prep/inventory.json').read_text())
  actual=sorted([str(p.relative_to(ROOT)) for p in (ROOT/'feature_carrier_prep').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='inventory.json']+['tests/test_carrier_core.py','tests/test_carrier_boundary.py'])
  self.assertEqual(actual,[r['path'] for r in inv['files']]);imports={}
  for row in inv['files']:
   p=ROOT/row['path'];self.assertEqual(row['sha256'],hashlib.sha256(p.read_bytes()).hexdigest())
   if p.suffix=='.py':
    for n in ast.walk(ast.parse(p.read_bytes())):
     if isinstance(n,ast.Import):
      for item in n.names:imports.setdefault(item.name.split('.')[0],set()).add(row['path'])
     elif isinstance(n,ast.ImportFrom) and n.module and not n.level:imports.setdefault(n.module.split('.')[0],set()).add(row['path'])
  self.assertEqual(inv['imports'],{k:sorted(v) for k,v in sorted(imports.items())})
