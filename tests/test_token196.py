import unittest,re,subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def test_three_files_no_public_token_or_headers_and_pinned_offline(self):
  from integration.finder_offline import shell
  for f in ('src/app.js','index.html','offline.html'):
   s=(ROOT/f).read_text();self.assertNotIn('AI_PROXY_TOKEN',s);self.assertNotIn('x-app-token',s);self.assertIn("const AI_PROXY_URL = '';",s);self.assertIn("const AIS_PROXY_URL = '';",s);self.assertIn("Built-in proxy access is unavailable",s)
  self.assertIn('Public offline Finder snapshot',shell((ROOT/'offline.html').read_text()))
 def test_vm_gates_zero_proxy_fetch_direct_provider_flow(self):
  s=(ROOT/'src/app.js').read_text()
  # Complete function source sections, executed in isolated VM with no real network.
  pieces=[s[s.index('async function geminiPost('):s.index('async function geminiText(')],s[s.index('async function groqPost('):s.index('async function oaiPoolPost(')],s[s.index('async function oaiPoolPost('):s.index('const PROVIDER_CALL')],s[s.index('function shipsLoad()'):s.index('function paintShips()')]]
  script='''const vm=require('node:vm');const assert=require('node:assert');let calls=[],paints=0,timers=0;const c={BUILTIN_PROXY_UNAVAILABLE:'Built-in proxy access is unavailable',AI_PROXY_URL:'',AIS_PROXY_URL:'',GEMINI_MODELS:['fixture'],GROQ_MODELS:['fixture'],V:{ships:true,shipsBusy:false},shipsTimer:4,shipsBlockedUntil:0,paintShips:()=>paints++,clearTimeout:()=>{},setTimeout:()=>{timers++;},fetch:async(u,o)=>{calls.push([u,o]);return {ok:true,json:async()=>({choices:[{message:{content:'fixture'}}],candidates:[]})};}};vm.createContext(c);vm.runInContext(SOURCE,c);(async()=>{for(const f of ['geminiPost','groqPost'])await assert.rejects(c[f]('', 'fixture', {}),/Built-in proxy access is unavailable/);await assert.rejects(c.oaiPoolPost('mistral','https://fixture.invalid',['fixture'],'','fixture',{}),/Built-in proxy access is unavailable/);c.shipsLoad();assert.equal(calls.length,0);assert.equal(timers,0);assert.equal(paints,1);assert.equal(c.V.shipsErr,'proxy-unavailable');await c.groqPost('fixture-owner-key','fixture',{});assert.equal(calls.length,1);assert.equal(calls[0][0],'https://api.groq.com/openai/v1/chat/completions');assert.equal(calls[0][1].headers.Authorization,'Bearer fixture-owner-key');assert(!('x-app-token'in calls[0][1].headers));console.log('PASS no proxy fetch/timers, owner-key direct flow');})().catch(e=>{console.error(e);process.exit(1)});'''.replace('SOURCE',json.dumps('\n'.join(pieces)))
  r=subprocess.run(['node','-e',script],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
