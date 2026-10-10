"""230 exact-source guards and explicit opt-in local SIMULATED browser wrapper."""
import hashlib,importlib.util,os,shutil,subprocess,sys,unittest
from pathlib import Path
from integration.news_api import create_app
from integration.finder_network import FINDER_CONNECT_ORIGINS
ROOT=Path(__file__).resolve().parents[1]
SPANS={'shipsLoad':('function shipsLoad()','function paintShips()','31541a4d8b136ed9882c68846cc01f46782af8d0bc387bc92b3588802b31121b'),'aiPickText':('async function aiPickText(','async function aiReportText(','15540c57008fd0bbc3d127dfc21ce7fd6f46adcdd68d0a40a577dc134d1b46c3'),'plainWordsRun':('async function plainWordsRun(','function briefHtml(','11fa1069aa306c8247743d40d9306dab1cd8a97866717b876586fbe2c89cc0f8'),'config':('const AI_PROXY_URL','\n\n','c6ca4c8fc4773bf429fa6c34e0bc097e18b4b578a8534b4c6d63a7675fae21ec')}
def verify_spans(text):
 for start,end,sha in SPANS.values():
  a=text.index(start);b=text.index(end,a)
  assert hashlib.sha256(text[a:b].encode()).hexdigest()==sha
class FinderNetwork230(unittest.TestCase):
 def test_source_spans_and_mutations(self):
  text=(ROOT/'src/app.js').read_text();verify_spans(text)
  for name in ['AI_PROXY_URL','AIS_PROXY_URL','BUILTIN_GEMINI_KEYS','BUILTIN_GROQ_KEYS','BUILTIN_MISTRAL_KEYS','BUILTIN_NVIDIA_KEYS']:
   self.assertIn('const '+name+" = '';",text)
   changed=text.replace('const '+name+" = '';",'const '+name+" = 'SIMULATED-change';")
   with self.assertRaises(AssertionError):verify_spans(changed)
  with self.assertRaises(AssertionError):verify_spans(text.replace("V.shipsErr='proxy-unavailable'","V.shipsErr='changed'"))
 def test_current_scope_sanitization(self):
  text=(ROOT/'tests/browser_finder_network.py').read_text()
  self.assertIn("make_server('127.0.0.1',0",text);self.assertIn("'method':r.request.method,'host':u.hostname,'path':u.path",text)
  for token in ['wait_for_timeout','time.sleep','post_data','print(r.request.headers','r.request.url);','AIS_PROXY_URL =','AI_PROXY_URL =']:self.assertNotIn(token,text)
  self.assertIn('SIMULATED LOCAL TEST',text)
 def test_csp_default_and_unauthorized_separate(self):
  denied=create_app(finder_network_preview_enabled=True).test_client().get('/workspace/finder/index.html');self.assertEqual(denied.status_code,403)
  for x in FINDER_CONNECT_ORIGINS:self.assertNotIn(x,denied.headers['Content-Security-Policy'])
  default=create_app(authorize=lambda r:True).test_client().get('/workspace/finder/index.html');self.assertIn("connect-src 'self';",default.headers['Content-Security-Policy'])
  enabled=create_app(authorize=lambda r:True,finder_network_preview_enabled=True).test_client().get('/workspace/finder/index.html')
  expected="connect-src 'self' "+' '.join(FINDER_CONNECT_ORIGINS)+';';self.assertIn(expected,enabled.headers['Content-Security-Policy']);self.assertNotIn('*',enabled.headers['Content-Security-Policy'])
  news=create_app(authorize=lambda r:True,finder_network_preview_enabled=True).test_client().get('/workspace')
  for x in FINDER_CONNECT_ORIGINS:self.assertNotIn(x,news.headers['Content-Security-Policy'])
  for response in [denied,default,enabled,news]:response.close()
 def test_browser_opt_in(self):
  if os.environ.get('RUN_FINDER230_BROWSER')!='1':self.skipTest('Opt-in SIMULATED browser: RUN_FINDER230_BROWSER=1 required; no browser PASS implied')
  if not Path('/usr/bin/google-chrome').exists() or importlib.util.find_spec('playwright') is None:self.skipTest('Chromium/Playwright missing; SIMULATED browser NOT run')
  run=subprocess.run([sys.executable,'tests/browser_finder_network.py'],cwd=ROOT,capture_output=True,text=True,timeout=120)
  self.assertEqual(run.returncode,0,run.stdout+run.stderr)
