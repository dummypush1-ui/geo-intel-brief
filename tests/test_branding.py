import unittest,hashlib
from pathlib import Path
from integration.news_api import create_app
from integration.branding_meta import brand_head
class BrandingTests(unittest.TestCase):
 def test_original_canonical_preserved(self):
  root=Path(__file__).resolve().parents[1];before=(root/'index.html').read_bytes()
  c=create_app(authorize=lambda r:True).test_client();r=c.get('/workspace/finder/index.html');text=r.get_data(as_text=True)
  self.assertIn('https://finder-hsn-codee.onrender.com/',text);self.assertIn('rel="icon"',text);self.assertEqual((root/'index.html').read_bytes(),before);self.assertIn('sha256-',r.headers['Content-Security-Policy']);r.close()
 def test_assets_guard_and_allowlist(self):
  self.assertEqual(create_app().test_client().get('/workspace/branding/icon-48.png').status_code,403)
  c=create_app(authorize=lambda r:True).test_client()
  for n in ('favicon.ico','icon-48.png','icon-192.png','icon-512.png','apple-touch-icon.png','og-image.png'):
   r=c.get('/workspace/branding/'+n);self.assertEqual(r.status_code,200);r.close()
  self.assertEqual(c.get('/workspace/branding/.env').status_code,404)
 def test_absolute_social_not_host(self):
  c=create_app(authorize=lambda r:True,branding_public_base='https://preview.example').test_client();r=c.get('/workspace',headers={'Host':'evil.test'});s=r.get_data(as_text=True);self.assertIn('https://preview.example/workspace/branding/og-image.png',s);self.assertNotIn('evil.test',s);self.assertIn('noindex',s);r.close()
 def test_unconfigured_no_fabricated_image(self):
  self.assertNotIn('og:image',brand_head('<html><head></head></html>'))
  for base in ('http://site.test','https://site.test/path','https://user:secret@site.test'):
   with self.assertRaises(ValueError):brand_head('<head></head>',base)
 def test_manifest_workspace_scope(self):
  c=create_app(authorize=lambda r:True).test_client();r=c.get('/workspace/manifest.webmanifest');import json;d=json.loads(r.data);self.assertEqual(d['scope'],'/workspace/');self.assertEqual(d['start_url'],'/workspace');r.close()
 def test_existing_links_and_uppercase_head(self):
  s=brand_head('<HEAD><link rel="alternate icon" href="x>y"><link rel="mask-icon" href="old"><link rel="apple-touch-icon-precomposed" href="old"></HEAD>')
  self.assertNotIn('x>y',s);self.assertNotIn('href="old"',s);self.assertIn('icon-48.png',s)
 def test_missing_head_safe(self):
  self.assertEqual(brand_head('<p>hello</p>'),'<p>hello</p>')
