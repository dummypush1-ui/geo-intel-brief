# Copyright (c) 2026 Push. All rights reserved.
import unittest
from pathlib import Path
from public_preview106 import build_public_preview
from integration.news_api import create_app

BASE='https://preview.example'
def env():return {'PREVIEW_PUBLIC_SAMPLE_ENABLED':'true','PREVIEW_GEO_ONLY_ENABLED':'true','PREVIEW_ACCESS_ENABLED':'false','NEWS_READ_ENABLED':'false','NEWS_EVENTS_READ_ENABLED':'false','FINDER_NETWORK_PREVIEW_ENABLED':'false','PREVIEW_ORIGIN':BASE}

class WatchlistFix(unittest.TestCase):
 def test_public_module_dependency_available(self):
  app=build_public_preview(env());c=app.test_client()
  for asset in ('countries.js','watch_updates.js'):
   r=c.get('/workspace/assets/'+asset,base_url=BASE);self.assertEqual(r.status_code,200);r.close()
 def test_country_button_suppressed_and_post_still_denied(self):
  c=build_public_preview(env()).test_client();r=c.get('/workspace/assets/countries.js',base_url=BASE)
  self.assertIn('Public Finder POST is unavailable',r.text)
  self.assertNotIn('card.append(find,matches);',r.text);r.close()
  self.assertEqual(c.post('/api/finder-context',base_url=BASE,json={}).status_code,403)
 def test_private_country_action_preserved(self):
  c=create_app(authorize=lambda r:True).test_client();r=c.get('/workspace/assets/countries.js')
  self.assertIn('card.append(find,matches);',r.text);r.close()
 def test_unrelated_public_asset_denied(self):
  c=build_public_preview(env()).test_client()
  self.assertEqual(c.get('/workspace/assets/live_channels.js',base_url=BASE).status_code,403)
 def test_gates_unchanged(self):
  e=env();e['NEWS_READ_ENABLED']='true'
  with self.assertRaises(ValueError):build_public_preview(e)

if __name__=='__main__':unittest.main()
