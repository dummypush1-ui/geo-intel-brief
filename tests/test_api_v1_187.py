import unittest
from unittest.mock import patch
from datetime import datetime,timezone
class FixedDate(datetime):
 @classmethod
 def now(cls,tz=None):return datetime(2026,10,9,8,0,tzinfo=timezone.utc)
from integration.news_api import create_app
from integration.api_v1 import READ_ALIASES,versioned
class V1(unittest.TestCase):
 def setUp(self):
  patcher=patch('integration.news_api.datetime',FixedDate);patcher.start();self.addCleanup(patcher.stop)
 def test_same_handler_json_csv_headers_and_head(self):
  app=create_app(reader=lambda:{'geo':[{'title':'Test','url':'https://fixture.invalid/one','country':'India'}]},authorize=lambda _:True);c=app.test_client()
  for path in READ_ALIASES:
   old=next(r for r in app.url_map.iter_rules()if r.rule==path);new=next(r for r in app.url_map.iter_rules()if r.rule==versioned(path));self.assertIs(app.view_functions[old.endpoint],app.view_functions[new.endpoint]);self.assertEqual(old.methods,new.methods)
   q='?project=geo'if path in ('/api/news','/api/news-page','/api/news-stats','/api/dashboard-signals','/api/dashboard-snapshots','/api/sample-volume','/api/news-export.csv')else '?country=India'if path in ('/api/country-page','/api/country-signals')else ''
   a=c.get(path+q);b=c.get(versioned(path)+q);self.assertEqual(a.status_code,b.status_code,path);self.assertEqual(a.data,b.data,path)
   for h in ('Cache-Control','Content-Type','Content-Disposition','X-Export-Scope','Content-Security-Policy'):self.assertEqual(a.headers.get(h),b.headers.get(h),path)
   a=c.head(path+q);b=c.head(versioned(path)+q);self.assertEqual(a.status_code,b.status_code,path);self.assertEqual(b.data,b'')
 def test_auth_and_error_old_compatibility(self):
  c=create_app().test_client()
  for path in READ_ALIASES:self.assertEqual(c.get(versioned(path)).status_code,403)
  c=create_app(authorize=lambda _:True).test_client()
  for q in ('limit=0','limit=2&limit=3','project=wrong','cursor=bad'):
   a=c.get('/api/news-page?'+q);b=c.get('/api/v1/news-page?'+q);self.assertEqual(a.status_code,b.status_code);self.assertEqual(a.json,b.json)
  self.assertEqual(c.get('/api/v1/news-page').status_code,503)
 def test_public_only_same_approved_reads_no_new_writes(self):
  from integration.public_preview_builder import build_public_preview
  e={'PREVIEW_PUBLIC_SAMPLE_ENABLED':'true','PREVIEW_GEO_ONLY_ENABLED':'true','PREVIEW_ACCESS_ENABLED':'false','NEWS_READ_ENABLED':'false','NEWS_EVENTS_READ_ENABLED':'false','FINDER_NETWORK_PREVIEW_ENABLED':'false','PREVIEW_ORIGIN':'https://preview.example'}
  c=build_public_preview(e).test_client()
  for path in READ_ALIASES:
   a=c.get(path,base_url=e['PREVIEW_ORIGIN']);b=c.get(versioned(path),base_url=e['PREVIEW_ORIGIN']);self.assertEqual(a.status_code,b.status_code,path);self.assertEqual(a.data,b.data,path)
   self.assertEqual(c.post(versioned(path),base_url=e['PREVIEW_ORIGIN']).status_code,403)
  for path in ('/api/v1/export-full.csv','/api/v1/tariff-evidence','/api/v1/finder-context','/api/v1/brics/streams','/api/v1/health','/api/v1/workspace'):
   self.assertEqual(c.get(path,base_url=e['PREVIEW_ORIGIN']).status_code,403)
 def test_private_routes_not_installed_aliases(self):
  app=create_app(authorize=lambda _:True);rules={r.rule for r in app.url_map.iter_rules()}
  self.assertNotIn('/api/v1/tariff-evidence',rules);self.assertNotIn('/api/v1/export-full.csv',rules);self.assertNotIn('/api/v1/related-news',rules)
  c=app.test_client();self.assertEqual(c.post('/api/v1/news',headers={'Origin':'http://localhost'}).status_code,405);self.assertEqual(c.get('/api/v1/health').status_code,404)
