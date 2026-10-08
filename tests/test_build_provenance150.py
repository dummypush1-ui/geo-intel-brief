import unittest,json,hashlib,re,ast,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Provenance(unittest.TestCase):
 def setUp(self):self.r=json.loads((ROOT/'integration/build_provenance/receipt.json').read_text())
 def test_inputs_outputs_exact(self):
  for p,h in {**self.r['inputs'],**self.r['outputs']}.items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h,p)
  self.assertTrue(self.r['double_build_equal']);self.assertTrue(self.r['source_bytes_unchanged'])
 def test_market_sections_trace_source(self):
  data=next(p for p in self.r['outputs']if re.fullmatch(r'data\.[a-f0-9]{12}\.js',p))
  built=(ROOT/data).read_text();offline=(ROOT/'offline.html').read_text()
  for source,names in [('src/marketdata.ts',['MARKET_IMPORTERS','MARKET_WORLD']),('src/marketexp.ts',['MARKET_EXPORTERS','MARKET_WORLD_X'])]:
   raw=(ROOT/source).read_text()
   for name in names:
    pattern=r'(?:export )?const '+name+r'(?:\s*:\s*[^=]+)?\s*=\s*(\{[\s\S]*?\n\});'
    expected=ast.literal_eval(re.search(pattern,raw)[1])
    for text in (built,offline):self.assertEqual(ast.literal_eval(re.search(pattern,text)[1]),expected,name)
   comment=next(l for l in raw.splitlines()if l.startswith('// Baked '));self.assertIn(comment,built);self.assertIn(comment,offline)
 def test_orphans_and_consistency(self):
  data=next(p for p in self.r['outputs']if re.fullmatch(r'data\.[a-f0-9]{12}\.js',p))
  self.assertEqual({p.name for p in ROOT.glob('data.*.js')},{data})
  self.assertEqual(hashlib.sha256((ROOT/data).read_bytes()).hexdigest()[:12],data[5:17])
  self.assertIn(data,(ROOT/'index.html').read_text());self.assertIn(data,(ROOT/'sw.js').read_text())
  self.assertIn((ROOT/data).read_text(),(ROOT/'offline.html').read_text())
 def test_repeat_build_equal(self):
  script="import {prepare} from './scripts/finder_provenance.mjs';import fs from 'node:fs';const {receipt}=prepare(process.cwd());const saved=JSON.parse(fs.readFileSync('integration/build_provenance/receipt.json'));if(JSON.stringify(receipt.inputs)!==JSON.stringify(saved.inputs)||JSON.stringify(receipt.outputs)!==JSON.stringify(saved.outputs))throw Error('Receipt mismatch');"
  r=subprocess.run(['node','--input-type=module','-e',script],cwd=ROOT,capture_output=True,text=True,timeout=45);self.assertEqual(r.returncode,0,r.stderr)
