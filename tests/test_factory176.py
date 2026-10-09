import unittest,subprocess,sys
from unittest.mock import patch
from flask import Flask
class Factory(unittest.TestCase):
 def test_shared_import_no_wsgi_app_or_client(self):
  code='import flask; count=[]; original=flask.Flask.__init__; flask.Flask.__init__=lambda self,*a,**k: (count.append(1),original(self,*a,**k))[1];import sys;import integration.public_live_builder as b; assert not hasattr(b,"app"); assert "public_live107" not in sys.modules; assert "public_preview106" not in sys.modules; assert "app" not in vars(sys.modules["integration.news_api"]); assert count==[]'
  r=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
 def test_factory_uses_guard_once_in_fallback_and_enabled(self):
  import production_entry as p
  from integration import public_live_builder as b
  original=b.guarded_public_app
  for flag in ['false','true']:
   made=[]
   def build(e):
    a=Flask('fixture');a.add_url_rule('/',view_func=lambda:'ok');made.append(a);return a
   with patch.object(b,'build_public_live_preview',build):
    # default guarded function currently captures builder at definition: use explicit shared guard seam.
    with patch.object(b,'guarded_public_app',lambda e:original(e,build)):
     a=p.build_production_app({'PUBLIC_NEWS_READ_ENABLED':flag});self.assertEqual(len(made),1);self.assertTrue(a._security_headers);self.assertEqual(a.test_client().get('/').headers['X-Frame-Options'],'SAMEORIGIN')
 def test_shared_guard_headers_and_optional_edge_once(self):
  from integration.public_live_builder import guarded_public_app
  for enabled in ['false','true']:
   a=guarded_public_app({'EDGE_GUARD_ENABLED':enabled},lambda e:Flask('fixture'))
   self.assertEqual(sum(f.__name__=='extra_security_headers' for f in a.after_request_funcs[None]),1)
 def test_actual_factory_one_app_client_and_guard(self):
  import production_entry as p
  from integration import public_live_builder as b
  base={'PREVIEW_PUBLIC_SAMPLE_ENABLED':'true','PREVIEW_GEO_ONLY_ENABLED':'true','PREVIEW_ACCESS_ENABLED':'false','NEWS_READ_ENABLED':'false','NEWS_EVENTS_READ_ENABLED':'false','FINDER_NETWORK_PREVIEW_ENABLED':'false','NEWS_STORE_MAPPING_VERIFIED':'true','PUBLIC_NEWS_DISCLOSURE_VERIFIED':'true','GEO_READONLY_CREDENTIAL_VERIFIED':'true','GEO_MONGODB_URI':'mongodb://fixture','PREVIEW_ORIGIN':'https://example.org'}
  class Client:
   def __getitem__(self,key):return self
   def close(self):pass
  for flag in ['false','true']:
   count=[];original=Flask.__init__
   def init(obj,*args,**kw):count.append(1);original(obj,*args,**kw)
   with patch.object(b,'create_public_geo_client',return_value=Client()) as factory,patch.object(Flask,'__init__',init):
    app=p.build_production_app(dict(base,PUBLIC_NEWS_READ_ENABLED=flag))
   self.assertEqual(count,[1]);self.assertEqual(factory.call_count,1 if flag=='true' else 0)
   self.assertEqual(sum(f.__name__=='extra_security_headers' for f in app.after_request_funcs[None]),1)
   self.assertFalse(hasattr(app,'_edge_guard'))

 def test_compatibility_lazy_wsgi_app(self):
  code='import integration.news_api as n; assert "app" not in vars(n); a=n.app; assert n.app is a'
  r=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
