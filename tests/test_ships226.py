import hashlib,json,re,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]
class Tests(unittest.TestCase):
 def test_original_pins_catalog_names_and_string_mmsi(self):
  pins={'src/app.js':'f8ecf57f73c28c376c4508f2ce7315f3ffad0a8a26d925a9782db6bb53e38f91','proxy.js':'dc6a77bd88d294a84c012d9e6928fb24ed5e8b3504877f7dcf13950829e0869c'}
  for path,sha in pins.items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),sha)
  proxy=(ROOT/'proxy.js').read_text();ports=re.findall(r"code: '([^']+)', name: '([^']+)'",proxy[proxy.index('const AIS_PORTS ='):proxy.index('const AIS_BOXES =')]);self.assertEqual(len(ports),42)
  from integration.finder198_connector import PORTS
  self.assertEqual({v[0]for v in ports},PORTS)
  r=subprocess.run(['node','--input-type=module','-e',"import {PORT_OPTIONS226} from './integration/finder198_ui/ships226.mjs';console.log(JSON.stringify(PORT_OPTIONS226));"],cwd=ROOT,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout),[list(v)for v in ports])
  self.assertIn("const mmsi = String(",proxy)
 def test_pure_shape_node(self):
  r=subprocess.run(['node','tests/ships226_test.mjs'],cwd=ROOT,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
 def test_safe_dom_no_request_or_timer_client_unchanged(self):
  text=(ROOT/'integration/finder198_ui/ships226.mjs').read_text()
  for value in ('innerHTML','fetch(','setTimeout','setInterval','href','localStorage','sessionStorage','hsn-ai-proxy','x-app-token'):self.assertNotIn(value,text)
  self.assertIn('textContent',text);self.assertIn('renderShips226', (ROOT/'integration/finder198_ui/panel.mjs').read_text())
  # 198d account, hold, nonce, timeout and request protocol unchanged.
  self.assertEqual(hashlib.sha256((ROOT/'integration/finder198_ui/client.mjs').read_bytes()).hexdigest(),'0b7d53db4843cb5f2d5350965a67d4befcaa281f91ca4e7c3ce76b652fda3730')
