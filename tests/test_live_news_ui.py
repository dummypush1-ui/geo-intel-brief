import unittest
from integration.news_api import create_app
class LiveNewsUITests(unittest.TestCase):
 def test_private_and_asset_allowlist(self):
  c=create_app().test_client();self.assertEqual(c.get('/workspace/assets/live_news.js').status_code,403)
  c=create_app(authorize=lambda r:True).test_client()
  for path in ('live_news.js','live_channels.js'):
   self.assertEqual(c.get('/workspace/assets/'+path).status_code,200)
  self.assertEqual(c.get('/workspace/assets/arbitrary.js').status_code,404)
 def test_workspace_sections_and_narrow_csp(self):
  c=create_app(authorize=lambda r:True).test_client();r=c.get('/workspace');s=r.get_data(as_text=True)
  self.assertNotIn('data-view="brics"',s)
  self.assertIn('data-view="live"',s);self.assertIn('data-view="channels"',s)
  self.assertIn("frame-src 'self' https://www.youtube-nocookie.com",r.headers['Content-Security-Policy'])
  self.assertNotIn('youtube',c.get('/api/news').headers['Content-Security-Policy'])
 def test_no_live_config_writes(self):
  c=create_app(authorize=lambda r:True).test_client()
  for path in ('/api/streams','/api/channels','/trigger-collect'):
   self.assertEqual(c.post(path,headers={'Origin':'http://localhost'}).status_code,404)
