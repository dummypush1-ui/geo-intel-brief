import unittest
from flask import Flask, jsonify
from integration.security_headers import install_security_headers, HSTS
import test_edge_guard as eg

SECURE=('Strict-Transport-Security',)
BASE='https://example.onrender.com'


class HeaderTests(unittest.TestCase):
 def app(self):
  app=Flask(__name__)
  @app.get('/x')
  def x():return jsonify(ok=1)
  @app.get('/pre')
  def pre():
   r=jsonify(ok=1);r.headers['X-Frame-Options']='DENY';return r
  return install_security_headers(app)
 def test_https_adds_all_headers(self):
  r=self.app().test_client().get('/x',base_url=BASE)
  self.assertEqual(r.headers['Strict-Transport-Security'],HSTS)
  self.assertEqual(HSTS,'max-age=604800');self.assertNotIn('includeSubDomains',HSTS);self.assertNotIn('preload',HSTS)
  self.assertEqual(r.headers['X-Frame-Options'],'SAMEORIGIN')
  self.assertIn('geolocation=()',r.headers['Permissions-Policy'])
  self.assertEqual(r.headers['Cross-Origin-Opener-Policy'],'same-origin')
 def test_forwarded_proto_https_counts(self):
  r=self.app().test_client().get('/x',base_url='http://x.test',headers={'X-Forwarded-Proto':'https'})
  self.assertIn('Strict-Transport-Security',r.headers)
 def test_plain_http_has_no_hsts(self):
  r=self.app().test_client().get('/x',base_url='http://x.test')
  self.assertNotIn('Strict-Transport-Security',r.headers);self.assertIn('X-Frame-Options',r.headers)
 def test_existing_header_not_replaced(self):
  r=self.app().test_client().get('/pre',base_url=BASE)
  self.assertEqual(r.headers['X-Frame-Options'],'DENY')
 def test_double_install_rejected(self):
  with self.assertRaises(ValueError):install_security_headers(self.app())


class PublicAppHeaderTests(eg.EntryRunner,unittest.TestCase):
 SCRIPT=r"""
import json
import public_live107 as m
c=m.app.test_client();B='https://example.onrender.com'
out={}
for path in ('/health','/api/news','/workspace','/workspace/assets/workspace.js','/nope'):
 r=c.get(path,base_url=B);out[path]=dict(r.headers)
print(json.dumps(out))
"""
 def check(self,o,expect_hsts=True):
  for path,h in o.items():
   self.assertEqual('Strict-Transport-Security' in h,expect_hsts,path)
   if expect_hsts:self.assertEqual(h['Strict-Transport-Security'],HSTS,path)
   self.assertEqual(h.get('X-Frame-Options'),'SAMEORIGIN',path)
   self.assertEqual(h.get('X-Content-Type-Options'),'nosniff',path)
   self.assertEqual(h.get('Referrer-Policy'),'same-origin',path)
   self.assertIn('default-src',h.get('Content-Security-Policy',''),path)
   self.assertEqual(h.get('Cache-Control'),'no-store',path)
 def test_public_app_headers_and_existing_ones_kept(self):
  self.check(self.run_entry({}))
 def test_switch_off_case_insensitive(self):
  o=self.run_entry({'SECURITY_HEADERS_ENABLED':'FALSE'})
  for h in o.values():
   self.assertNotIn('Strict-Transport-Security',h);self.assertNotIn('X-Frame-Options',h)


if __name__=='__main__':unittest.main()
