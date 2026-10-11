import unittest
from unittest.mock import patch
from flask import Flask
from integration.code_news_coverage_ui_prep import install,enabled,PATHS
class Tests(unittest.TestCase):
 def test_gate_off404_allpaths_HEADzero(self):
  app=Flask(__name__);install(app);client=app.test_client()
  with patch('pathlib.Path.read_text',side_effect=AssertionError('read')):
   for path in PATHS:
    self.assertEqual(client.get(path).status_code,404);self.assertEqual(client.head(path).status_code,404)
 def test_exactflag(self):
  for flag in ['TRUE','1','yes',True]:
   with self.assertRaises(ValueError):enabled({'PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED':flag})
  self.assertFalse(enabled({}));self.assertTrue(enabled({'PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED':'true'}))
 def test_shell_headers_HEAD_zero_noAPI(self):
  app=Flask(__name__);install(app,{'PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED':'true'});c=app.test_client()
  with patch('pathlib.Path.read_text',side_effect=AssertionError('read')):
   for path in PATHS:self.assertEqual(c.head(path).status_code,200)
  for path in PATHS:
   r=c.get(path);self.assertEqual(r.status_code,200);self.assertEqual(r.headers['Cache-Control'],'no-store');self.assertEqual(r.headers['Referrer-Policy'],'no-referrer');self.assertEqual(r.headers['X-Content-Type-Options'],'nosniff');self.assertIn("connect-src 'self'",r.headers['Content-Security-Policy']);self.assertNotIn('unsafe-inline',r.headers['Content-Security-Policy'])
  self.assertEqual(c.post('/api/code-news-coverage').status_code,404);s=c.get('/workspace/code-news-coverage').text;self.assertIn('data-coverage-available="false"',s);self.assertNotIn('<style',s);self.assertNotIn('https://',s);self.assertNotIn('<script>',s)
 def test_fixtureavailability_only(self):
  app=Flask(__name__);install(app,{'PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED':'true'},coverage_available=True);self.assertIn('data-coverage-available="true"',app.test_client().get('/workspace/code-news-coverage').text)
