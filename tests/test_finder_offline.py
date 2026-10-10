import unittest
from integration.news_api import create_app
class OfflineFinderTests(unittest.TestCase):
 def test_private_routes_default_no_registration(self):
  c=create_app().test_client()
  for path in ['/workspace/finder/offline-sw.js','/workspace/finder/offline.html','/workspace/finder/offline-control.js']:self.assertEqual(c.get(path).status_code,403)
  c=create_app(authorize=lambda r:True).test_client();r=c.get('/workspace/finder/index.html');self.assertNotIn("navigator.serviceWorker.register('./sw.js')",r.text);self.assertIn('Store public snapshot on this device',r.text)
  r=c.get('/workspace/finder/offline-sw.js');self.assertEqual(r.headers['Service-Worker-Allowed'],'/workspace/finder/');self.assertIn('url.href!==OFFLINE',r.text)
 def test_keyfree_networkfree_offline(self):
  r=create_app(authorize=lambda r:True).test_client().get('/workspace/finder/offline.html');self.assertEqual(r.status_code,200);self.assertEqual(r.headers['X-Finder-Public-Snapshot'],'true');self.assertIn("connect-src 'none'",r.headers['Content-Security-Policy']);self.assertNotIn('localStorage',r.text);self.assertNotIn('navigator.serviceWorker.register',r.text);self.assertNotIn("AI_PROXY_TOKEN",r.text);self.assertNotIn('/workspace/assets/',r.text);self.assertNotIn('/workspace/branding/',r.text);self.assertIn('finder-shortlist-scroll',r.text);self.assertIn("const probe = text.replace",r.text)
 def test_scope_manifest(self):
  d=create_app(authorize=lambda r:True).test_client().get('/workspace/finder/offline-manifest.webmanifest').json;self.assertEqual(d['scope'],'/workspace/finder/');self.assertEqual(d['start_url'],'/workspace/finder/offline.html')

 def test_ranges_and_secret_source_values_stripped(self):
  from pathlib import Path
  import re
  source=(Path(__file__).resolve().parents[1]/'offline.html').read_text(encoding='utf-8')
  r=create_app(authorize=lambda r:True).test_client().get('/workspace/finder/offline.html',headers={'Range':'bytes=0-500'})
  self.assertEqual(r.status_code,200);self.assertIn('Public offline Finder snapshot',r.text);self.assertIn("connect-src 'none'",r.headers['Content-Security-Policy'])
  for name in ['BUILTIN_GEMINI_KEYS','BUILTIN_GROQ_KEYS','BUILTIN_MISTRAL_KEYS','BUILTIN_NVIDIA_KEYS']:
   value=re.search(r'const\s+'+name+r"\s*=\s*'([^']*)'",source)[1]
   if value:self.assertNotIn(value,r.text)
  for word in ['sessionStorage','indexedDB','document.cookie']:self.assertNotIn(word,r.text)
