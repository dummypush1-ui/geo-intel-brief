import unittest
from integration.finder_network import connect_sources,FINDER_CONNECT_ORIGINS,from_env,manual_ships_shell
from integration.news_api import create_app
class FinderNetwork(unittest.TestCase):
 def test_default_deny_exact_opt_in(self):
  self.assertEqual(connect_sources(),"'self'")
  c=create_app(authorize=lambda r:True).test_client();r=c.get('/workspace/finder/index.html');self.assertEqual(r.status_code,200)
  self.assertIn("connect-src 'self';",r.headers['Content-Security-Policy'])
  self.assertNotIn('shipsTimer = setTimeout',r.text)
  c=create_app(authorize=lambda r:True,finder_network_preview_enabled=True).test_client();r=c.get('/workspace/finder/index.html')
  for origin in FINDER_CONNECT_ORIGINS:self.assertIn(origin,r.headers['Content-Security-Policy'])
  self.assertNotIn('*',r.headers['Content-Security-Policy']);self.assertNotIn('shipsTimer = setTimeout',r.text)
 def test_reject_non_boolean_and_bad_env(self):
  for x in [1,'true',None]:
   with self.assertRaises(ValueError):create_app(finder_network_preview_enabled=x)
  self.assertFalse(from_env({}));self.assertTrue(from_env({'FINDER_NETWORK_PREVIEW_ENABLED':'true'}))
  for v in ['TRUE','1','https://evil.com']:
   with self.assertRaises(ValueError):from_env({'FINDER_NETWORK_PREVIEW_ENABLED':v})
 def test_timer_seam_fail_closed(self):
  with self.assertRaises(ValueError):manual_ships_shell('<html>unknown version</html>')
 def test_routes_still_private_and_news_csp_unchanged(self):
  c=create_app(finder_network_preview_enabled=True).test_client()
  self.assertEqual(c.get('/workspace/finder/index.html').status_code,403)
  c=create_app(authorize=lambda r:True,finder_network_preview_enabled=True).test_client()
  for path in ['/workspace','/workspace/weekly','/workspace/map','/workspace/finder/offline.html']:
   r=c.get(path);self.assertEqual(r.status_code,200)
   for origin in FINDER_CONNECT_ORIGINS:self.assertNotIn(origin,r.headers['Content-Security-Policy'])
  denied=create_app(finder_network_preview_enabled=True).test_client().get('/workspace/finder/index.html')
  for origin in FINDER_CONNECT_ORIGINS:self.assertNotIn(origin,denied.headers['Content-Security-Policy'])
