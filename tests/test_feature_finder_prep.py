# Copyright (c) 2026 Push. All rights reserved.
import hashlib, pathlib, re, subprocess, tempfile, unittest
from feature_finder_prep.shell import prepare_shell, SOURCE_SHA
ROOT = pathlib.Path(__file__).resolve().parents[1]

class FinderPreparation(unittest.TestCase):
 def test_pin_and_source_preserved(self):
  source=(ROOT/'index.html').read_text();prepared=prepare_shell(source)
  self.assertEqual(hashlib.sha256(source.encode()).hexdigest(),SOURCE_SHA)
  self.assertEqual((ROOT/'index.html').read_text(),source)
  self.assertNotEqual(prepared,source)
 def test_drift_refused(self):
  with self.assertRaises(ValueError):prepare_shell((ROOT/'index.html').read_text()+' ')
 def test_three_provider_and_timeout_seams(self):
  s=prepare_shell((ROOT/'index.html').read_text())
  self.assertNotIn("arr.push('nvidia')",s)
  self.assertNotIn('<option value="nvidia"',s)
  self.assertIn('const timer = setTimeout(() => ctrl.abort(), 15000)',s)
  self.assertEqual(s.count('await mergedProviderFetch('),3)
  self.assertIn('const data = await res.json()',s)
  self.assertIn("if (ctrl.signal.aborted) throw new Error('AI response timed out')",s)
  self.assertIn('finally { clearTimeout(timer); }',s)
 def test_original_fallback_print_and_labels(self):
  s=prepare_shell((ROOT/'index.html').read_text())
  self.assertIn('async function openTemplateReport',s)
  self.assertIn("catch (err) { aiError = err.message || 'AI call failed'; }",s)
  self.assertNotIn('narrative sections written with live web research',s)
  self.assertIn('narrative sections may use model knowledge only',s)
  self.assertIn('min-height: 0 !important',s)
  self.assertIn('Copyright (c) 2026 Push. All rights reserved.',s)
 def test_main_script_syntax(self):
  s=prepare_shell((ROOT/'index.html').read_text());scripts=re.findall(r'<script>(.*?)</script>',s,re.S)
  with tempfile.TemporaryDirectory() as d:
   for i,js in enumerate(scripts):
    p=pathlib.Path(d)/('script%d.js'%i);p.write_text(js)
    r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    self.assertEqual(r.returncode,0,r.stderr)

class BodyTimeout(unittest.TestCase):
 def test_aborted_body_throws_and_timer_cleared(self):
  s=prepare_shell((ROOT/'index.html').read_text())
  helper=s[s.index('async function mergedProviderFetch('):s.index('async function geminiPost(')]
  js = "const savedSetTimeout=setTimeout;let aborted=false,cleared=false;global.setTimeout=(fn,ms)=>savedSetTimeout(fn,5);global.clearTimeout=(id)=>{cleared=true;};global.fetch=async (u,o)=>({ok:true,status:200,json:()=>new Promise((res,rej)=>o.signal.addEventListener('abort',()=>{aborted=true;rej(new Error('abort'))}))});"+helper+"mergedProviderFetch('fixture',{}).then(()=>{throw new Error('empty success')}).catch(e=>{if(e.message!=='AI response timed out'||!aborted||!cleared)process.exit(1);console.log('BODY_TIMEOUT_FAILOVER_OK')});"
  r=subprocess.run(['node','-e',js],capture_output=True,text=True,timeout=10)
  self.assertEqual(r.returncode,0,r.stderr);self.assertIn('BODY_TIMEOUT_FAILOVER_OK',r.stdout)
