import unittest,re,hashlib,base64,os,subprocess,sys,shutil,json
from pathlib import Path
from integration.finder_offline import shell
from integration.finder_nested import TABLE,CSV_QUOTE,CSV_SAFE,REPLACEMENT,STYLE
from integration.news_api import create_app
ROOT=Path(__file__).resolve().parents[1]
class Offline232(unittest.TestCase):
 def test_anchors_fail_closed_and_single_source(self):
  raw=(ROOT/'offline.html').read_text();out=shell(raw);self.assertIn(STYLE,out);self.assertIn(CSV_SAFE,out)
  import integration.finder_offline as m
  from unittest.mock import patch
  for anchor in [TABLE,CSV_QUOTE]:
   for bad in [raw.replace(anchor,'missing'),raw.replace(anchor,anchor+anchor),raw.replace(anchor,REPLACEMENT if anchor==TABLE else CSV_SAFE)]:
    with patch.object(m,'OFFLINE_SHA',hashlib.sha256(bad.encode()).hexdigest()):
     with self.assertRaises(ValueError):shell(bad)
  source=(ROOT/'integration/finder_offline.py').read_text();self.assertIn('from integration.finder_nested import shortlist_scroll,shortlist_csv_safe',source);self.assertNotIn('const q =',source)
 def test_csp_actual_served_cache_id_and_policy(self):
  client=create_app(authorize=lambda r:True).test_client();r=client.get('/workspace/finder/offline.html',headers={'Range':'bytes=0-500'});self.assertEqual(r.status_code,200);self.assertEqual(r.headers['Cache-Control'],'no-store');self.assertEqual(r.headers['X-Finder-Public-Snapshot'],'true');self.assertEqual(create_app().test_client().get('/workspace/finder/offline.html').status_code,403)
  scripts=re.findall(r'<script>(.*?)</script>',r.text,re.S|re.I);expected={"'sha256-"+base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()+"'"for s in scripts}
  for csp in [r.headers['Content-Security-Policy'],re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"',r.text)[1]]:
   directive=next(x for x in csp.split(';')if x.strip().startswith('script-src'));self.assertEqual(set(re.findall(r"'sha256-[^']+'",directive)),expected);self.assertNotIn('unsafe-inline',directive);self.assertIn("connect-src 'none'",csp)
  cache=re.search("const CACHE='([^']+)';",(ROOT/'integration/ui/finder-offline-sw.js').read_text())[1];self.assertEqual(cache,'geo-public-finder-'+hashlib.sha256(r.data).hexdigest()[:12]+'-v1')
  self.assertNotIn('localStorage',r.text);self.assertIn("const fetch = async()=>{throw",r.text);self.assertIn(CSV_SAFE,r.text)
 def test_browser_optin(self):
  if os.environ.get('RUN_OFFLINE232_BROWSER')!='1':self.skipTest('232 browser opt-in RUN_OFFLINE232_BROWSER=1')
  if not shutil.which('google-chrome'):self.skipTest('Chromium missing')
  try:import playwright.sync_api
  except ImportError:self.skipTest('Playwright missing')
  subprocess.run([sys.executable,str(ROOT/'tests/browser_offline232.py')],cwd=ROOT,check=True,timeout=100)
