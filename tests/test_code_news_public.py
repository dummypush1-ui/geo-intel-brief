import unittest,hashlib
from unittest.mock import patch
from integration.public_preview_builder import build_public_preview
from integration.code_news_public import PATHS,Service
from integration.code_news_links import Links
BASE='https://preview.example'
def env(on=False):return dict(PREVIEW_PUBLIC_SAMPLE_ENABLED='true',PREVIEW_GEO_ONLY_ENABLED='true',PREVIEW_ACCESS_ENABLED='false',NEWS_READ_ENABLED='false',NEWS_EVENTS_READ_ENABLED='false',FINDER_NETWORK_PREVIEW_ENABLED='false',PREVIEW_ORIGIN=BASE,PUBLIC_CODE_NEWS_ENABLED='true'if on else'false',PUBLIC_CODE_NEWS_SCOPE_REVIEWED='true')
CAT=[dict(system='HS',edition='2022',code='100630',description='Rice'),dict(system='HS',edition='2022',code='1006',description='Rice')]
class Tests(unittest.TestCase):
 def app(self):
  app=build_public_preview(env(True));service=app.extensions['code_news_public'];service.model=Links(CAT,[]);service.reader=lambda:{'geo':[{'url':'https://example.com/one','title':'HS 100630 tariff news'}]};return app
 def test_off_closed(self):
  c=build_public_preview(env()).test_client()
  for path in PATHS:self.assertEqual(c.get(path,base_url=BASE).status_code,403)
 def test_invalid_gate(self):
  e=env(True);e.pop('PUBLIC_CODE_NEWS_SCOPE_REVIEWED')
  with self.assertRaises(ValueError):build_public_preview(e)
 def test_head_never_io(self):
  app=self.app();app.extensions['code_news_public'].model=None
  with patch('integration.code_news_public.DiskLinks',side_effect=AssertionError('IO')):
   for path in PATHS:self.assertEqual(app.test_client().head(path,base_url=BASE).status_code,200)
 def test_forward_reverse_same_article(self):
  c=self.app().test_client();f=c.get('/api/code-news-context?query=HS100630',base_url=BASE);self.assertEqual(f.status_code,200);self.assertTrue(f.json['relationships']);key=f.json['relationships'][0]['article_key'];r=c.get('/api/news-code-context?project=geo&article_key='+key,base_url=BASE);self.assertEqual(r.status_code,200);self.assertEqual(r.json['items'][0]['targets'][0]['code'],'100630')
 def test_numeric_mixed_never_generic(self):
  c=self.app().test_client()
  for q in ('100630 rice','10063O','tariff 1006'):
   r=c.get('/api/code-news-context',query_string={'query':q},base_url=BASE);self.assertEqual(r.status_code,400);self.assertIsNone(r.json['generic_q'])
 def test_unknown_and_wrong_inputs(self):
  c=self.app().test_client();self.assertEqual(c.get('/api/code-news-context?query=999999',base_url=BASE).json['state'],'unknown_code')
  for q in ('query=100630&query=1006','query=1006&url=https://evil','query='):
   self.assertEqual(c.get('/api/code-news-context?'+q,base_url=BASE).status_code,400)
 def test_private_and_method_still_closed(self):
  c=self.app().test_client()
  for p in ('/api/finder-context','/api/related-news','/collect','/api/mail'):self.assertEqual(c.get(p,base_url=BASE).status_code,403)
  self.assertEqual(c.post('/api/code-news-context',base_url=BASE).status_code,403);self.assertEqual(c.get('/workspace/code-news',base_url='https://evil.example').status_code,403)
 def test_request_quota(self):
  c=self.app().test_client()
  for _ in range(10):self.assertEqual(c.get('/api/code-news-context?query=999999',base_url=BASE).status_code,200)
  self.assertEqual(c.get('/api/code-news-context?query=999999',base_url=BASE).status_code,429)
 def test_headers(self):
  r=self.app().test_client().get('/workspace/code-news',base_url=BASE);self.assertEqual(r.headers['Cache-Control'],'no-store');self.assertIn("connect-src 'self'",r.headers['Content-Security-Policy'])
 def test_no_startup_extract(self):
  with patch('integration.code_news_public.DiskLinks',side_effect=AssertionError('IO')):build_public_preview(env(True))

class Gaps(unittest.TestCase):
 def app(self):return Tests().app()
 def test_label_trailing_junk(self):
  r=self.app().test_client().get('/api/code-news-context?query=HS100630junk',base_url=BASE);self.assertEqual(r.status_code,400);self.assertEqual(r.json['state'],'mixed_or_malformed_code')
 def test_query_cap(self):self.assertEqual(self.app().test_client().get('/api/code-news-context?query='+('x'*513),base_url=BASE).status_code,400)
 def test_100_row_cap(self):
  app=self.app();app.extensions['code_news_public'].reader=lambda:{'geo':[{'url':'https://example.com/a','title':'HS100630'}]*101}
  self.assertEqual(app.test_client().get('/api/code-news-context?query=HS100630',base_url=BASE).status_code,400)
 def test_article_identity_hex(self):
  c=self.app().test_client()
  for key in ('a'*63,'g'*64,'A'*64):self.assertEqual(c.get('/api/news-code-context?project=geo&article_key='+key,base_url=BASE).status_code,400)
 def test_no_store(self):
  r=self.app().test_client().get('/api/code-news-context?query=999999',base_url=BASE);self.assertEqual(r.headers['Cache-Control'],'no-store')
