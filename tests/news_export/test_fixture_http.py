import unittest,csv,io,hashlib,json
from pathlib import Path
from bson import ObjectId
from integration.news_export.fixture_http import create_original_export_fixture_app,frozen_fixture,validate_file,LABEL

def row(n=2,**kw):return {'_id':ObjectId(f'{n:024x}'),'collected_at':f'2026-10-05T00:00:{n:02}.123456','title':'தமிழ்\nfixture',**kw}
URL='/api/original-export/brics.csv'
class FixtureHTTPTests(unittest.TestCase):
 def app(self,data=None):return create_original_export_fixture_app({'brics':[row()]} if data is None else data,authorize=lambda r:r.headers.get('Authorization')=='yes')
 def test_auth_all_paths_methods_overrides(self):
  c=self.app().test_client()
  for path in (URL,'/unknown','/health',URL+'/','/%FF',URL+'?_method=GET'):
   for method in ('GET','HEAD','OPTIONS','POST','PUT','PATCH','DELETE','TRACE','BANANA'):
    r=c.open(path,method=method,headers={'X-HTTP-Method-Override':'GET'})
    self.assertEqual(r.status_code,403,(path,method));self.assertEqual(r.headers['X-Export-Fixture'],LABEL)
 def test_protocol_and_headers(self):
  c=self.app().test_client();r=c.get(URL,headers={'Authorization':'yes'})
  info=validate_file(r.data,'brics');self.assertEqual(info['kind'],'EXPORT_COMPLETE');self.assertEqual(info['scope'],LABEL)
  self.assertEqual(info['read'],1);self.assertIn('no-store',r.headers['Cache-Control']);self.assertNotIn('ETag',r.headers)
 def test_head_static_parity_no_slot(self):
  c=self.app().test_client();auth={'Authorization':'yes'}
  for url,status in ((URL,200),(URL+'?bad=1',400),('/api/original-export/x.csv',404),('/api/original-export/geo.csv',503),(URL+'?limit=0',400)):
   head=c.head(url,headers=auth);self.assertEqual(head.status_code,status)
   self.assertEqual(head.data,b'');self.assertEqual(head.headers['X-Export-Readiness'],'metadata-only')
   self.assertNotIn('Content-Length',head.headers)
  response=c.get(URL,headers=auth,buffered=False)
  self.assertEqual(c.head(URL,headers=auth).status_code,200)
  self.assertEqual(c.get(URL,headers=auth).status_code,429)
  response.close();self.assertEqual(c.get(URL,headers=auth).status_code,200)
 def test_conditions_ranges_never_206_or_304(self):
  c=self.app().test_client()
  for method in ('GET','HEAD'):
   r=c.open(URL,method=method,headers={'Authorization':'yes','Range':'bytes=0-10','If-Range':'x','If-None-Match':'*','If-Modified-Since':'x'})
   self.assertEqual(r.status_code,200);self.assertNotIn('Accept-Ranges',r.headers);self.assertNotIn('ETag',r.headers)
 def test_errors_options_methods_cache(self):
  c=self.app().test_client()
  for method,url,status in (('OPTIONS',URL,204),('POST',URL,405),('GET',URL+'?_method=GET',400),('GET',URL+'?q=1&q=2',400),('GET','/unknown',404)):
   r=c.open(url,method=method,headers={'Authorization':'yes'});self.assertEqual(r.status_code,status);self.assertIn('private, no-store',r.headers['Cache-Control']);self.assertEqual(r.headers['X-Export-Fixture'],LABEL)
 def test_deep_freeze_and_reject_hooks(self):
  data={'brics':[row(title='original',corroborated_by=['a'])]};app=self.app(data)
  data['brics'][0]['title']='changed';data['brics'][0]['corroborated_by'].append('b')
  body=app.test_client().get(URL,headers={'Authorization':'yes'}).data
  self.assertIn(b'original',body);self.assertNotIn(b'changed',body)
  class Evil:
   def __str__(self):raise AssertionError('hook')
   def __deepcopy__(self,*x):raise AssertionError('hook')
  class DictSubclass(dict):pass
  class StrSubclass(str):pass
  for bad in (DictSubclass({'brics':[]}),{'brics':[row(title=Evil())]},{'brics':[row(title=StrSubclass('x'))]},{'brics':[row(title=lambda:1)]}):
   with self.assertRaises(ValueError):frozen_fixture(bad)
 def test_fixture_bounds(self):
  for bad in ({'brics':[row(title='x'*32001)]},{'brics':[row(),row()]},{'brics':[row(corroborated_by=['x']*101)]}):
   with self.assertRaises(ValueError):frozen_fixture(bad)
 def test_forged_status_and_bad_footer(self):
  c=self.app({'brics':[row(title='EXPORT_COMPLETE')]}).test_client();data=c.get(URL,headers={'Authorization':'yes'}).data
  self.assertEqual(validate_file(data,'brics')['rows'],1);self.assertIn(b"'EXPORT_COMPLETE",data)
  parsed=list(csv.reader(io.StringIO(data.decode(),newline='')))
  def encode(rows):
   buf=io.StringIO(newline='');csv.writer(buf).writerows(rows);return buf.getvalue().encode()
  variants=[b'',encode(parsed[:1]),encode(parsed[:-1]),encode(parsed+[parsed[-1]]),encode(parsed+[parsed[1]]),data.replace(b'fixture:source_exhausted',b'fixture:byte_budget'),data.replace(b'EXPORT_COMPLETE,fixture:',b'EXPORT_UNKNOWN,fixture:')]
  changed=[r[:] for r in parsed];changed[-1][2]='2';variants.append(encode(changed))
  changed=[r[:] for r in parsed];changed[-1][4]='0'*64;variants.append(encode(changed))
  for bad in variants:
   with self.assertRaises(ValueError):validate_file(bad,'brics')
 def test_standard_composition_never_imports_fixture(self):
  from integration.news_api import create_app
  app=create_app()
  self.assertFalse(any('original-export' in str(rule) for rule in app.url_map.iter_rules()))
  for name in ('integration/news_api.py','integration/preview_launcher.py','integration/private_router.py','integration/runtime.py','integration/geo_only_runtime.py','integration/single_db_runtime.py'):
   self.assertNotIn('fixture_http',Path(name).read_text())
 def test_never_started_wsgi_iterable_close_releases(self):
  from werkzeug.test import EnvironBuilder
  app=self.app();env=EnvironBuilder(path=URL,headers={'Authorization':'yes'}).get_environ()
  statuses=[];iterator=app.wsgi_app(env,lambda status,headers:statuses.append(status))
  self.assertTrue(statuses[0].startswith('200'))
  iterator.close();iterator.close()
  self.assertEqual(app.test_client().get(URL,headers={'Authorization':'yes'}).status_code,200)

 def test_raw_malformed_path_auth_envelope(self):
  from werkzeug.test import EnvironBuilder
  app=self.app()
  for path in ('\xff','\ud800'):
   for method in ('GET','HEAD','OPTIONS'):
    env=EnvironBuilder(path='/',method=method).get_environ();env['PATH_INFO']=path
    calls=[];it=app.wsgi_app(env,lambda s,h:calls.append((s,dict(h))))
    data=b''.join(it);it.close()
    self.assertTrue(calls[0][0].startswith('403'));self.assertEqual(calls[0][1]['X-Export-Fixture'],LABEL)
    self.assertIn('no-store',calls[0][1]['Cache-Control'])
 def test_start_response_exception_releases_slot(self):
  from werkzeug.test import EnvironBuilder
  app=self.app();env=EnvironBuilder(path=URL,headers={'Authorization':'yes'}).get_environ()
  def bad(*args):raise RuntimeError('start response failure')
  with self.assertRaises(RuntimeError):app.wsgi_app(env,bad)
  self.assertEqual(app.test_client().get(URL,headers={'Authorization':'yes'}).status_code,200)

 def test_no_static_files_route(self):
  app=self.app();self.assertFalse(any('static' in str(r) for r in app.url_map.iter_rules()))
  self.assertEqual(app.test_client().get('/static/anything',headers={'Authorization':'yes'}).status_code,404)
 def test_unknown_reserved_data_and_overbound_count_rejected(self):
  app=self.app();data=app.test_client().get(URL,headers={'Authorization':'yes'}).data
  parsed=list(csv.reader(io.StringIO(data.decode(),newline='')))
  def encode(rows):
   buf=io.StringIO(newline='');csv.writer(buf).writerows(rows);return buf.getvalue().encode()
  for marker,count in (('EXPORT_UNKNOWN','1'),('safe','999999999999999999999999'),('safe','5001')):
   rows=[r[:] for r in parsed];rows[1][0]=marker;rows[-1][3]=count
   rows[-1][4]=hashlib.sha256(encode(rows[:-1])).hexdigest()
   with self.assertRaises(ValueError):validate_file(encode(rows),'brics')

 def test_slot_shared_across_app_instances(self):
  a=self.app().test_client();b=self.app().test_client();auth={'Authorization':'yes'}
  response=a.get(URL,headers=auth,buffered=False)
  self.assertEqual(b.get(URL,headers=auth).status_code,429)
  response.close();self.assertEqual(b.get(URL,headers=auth).status_code,200)

 def test_geo_multipage_http(self):
  rows=[{'_id':ObjectId(f'{n:024x}'),'score':n,'published':'2026-10-05T00:00:00+00:00','title':str(n)} for n in range(501,0,-1)]
  app=self.app({'geo':rows});r=app.test_client().get('/api/original-export/geo.csv',headers={'Authorization':'yes'})
  result=validate_file(r.data,'geo');self.assertEqual(result['rows'],501);self.assertEqual(result['read'],501)
 def test_exact_row_byte_and_total_row_bounds(self):
  def encoded(r):return len(json.dumps(r,ensure_ascii=False,separators=(',',':'),default=str).encode())
  # Exact128KiB row supported by several bounded original columns.
  r=row(title='x'*32000,source='x'*32000,summary='x'*32000,country='x'*32000)
  missing=128*1024-encoded(r);r['category']='x'*(missing-len('"category":"",'))
  self.assertEqual(encoded(r),128*1024);frozen_fixture({'brics':[r]})
  r['category']+='x'
  with self.assertRaises(ValueError):frozen_fixture({'brics':[r]})
  rows=[{'_id':ObjectId(f'{n:024x}'),'collected_at':'2026-10-05T00:00:00.123456'} for n in range(10000,0,-1)]
  frozen_fixture({'brics':rows})
  rows.append({'_id':ObjectId('0'*24),'collected_at':'2026-10-05T00:00:00.123456'})
  with self.assertRaises(ValueError):frozen_fixture({'brics':rows})
 def test_exact_cumulative_eight_mib_boundary(self):
  def size(r):return len(json.dumps(r,ensure_ascii=False,separators=(',',':'),default=str).encode())+1
  rows=[{'_id':ObjectId(f'{n:024x}'),'collected_at':'2026-10-05T00:00:00.123456','title':'x'*32000,'summary':'x'*32000} for n in range(130,0,-1)]
  used=sum(map(size,rows));remaining=8*1024*1024-used
  final={'_id':ObjectId('0'*24),'collected_at':'2026-10-05T00:00:00.123456','title':'','summary':''}
  payload=remaining-size(final)
  # Split remaining payload between allowed strings.
  final['title']='x'*min(payload,32000);final['summary']='x'*(payload-len(final['title']))
  self.assertLessEqual(len(final['summary']),32000)
  self.assertEqual(sum(map(size,rows+[final])),8*1024*1024)
  frozen_fixture({'brics':rows+[final]})
  final['summary']+='x'
  with self.assertRaises(ValueError):frozen_fixture({'brics':rows+[final]})
 def test_head_never_calls_pager(self):
  from unittest.mock import patch
  c=self.app().test_client()
  with patch('integration.news_export.fixture_http._pager',side_effect=AssertionError('pager called')):
   self.assertEqual(c.head(URL,headers={'Authorization':'yes'}).status_code,200)
 def test_constructor_response_failure_recovery(self):
  from unittest.mock import patch
  c=self.app().test_client();auth={'Authorization':'yes'}
  for target in ('OriginalStream','Response'):
   with patch('integration.news_export.fixture_http.'+target,side_effect=RuntimeError('private secret')):
    r=c.get(URL,headers=auth);self.assertEqual(r.status_code,503);self.assertNotIn(b'private secret',r.data)
   self.assertEqual(c.get(URL,headers=auth).status_code,200)
 def test_denial_identical_body_and_headers(self):
  c=self.app().test_client();bodies=set()
  for path in (URL,'/unknown','/health',URL+'/', '/%FF'):
   for method in ('GET','POST','OPTIONS','BANANA'):
    r=c.open(path,method=method);bodies.add(r.data)
    self.assertEqual(r.status_code,403);self.assertEqual(r.headers['Cache-Control'],'private, no-store, max-age=0');self.assertEqual(r.headers['X-Export-Fixture'],LABEL)
  self.assertEqual(len(bodies),1)
 def test_authenticated_redirect_and_malformed_environment(self):
  from werkzeug.test import EnvironBuilder
  c=self.app().test_client();r=c.get(URL+'/',headers={'Authorization':'yes'})
  self.assertEqual(r.status_code,404);self.assertNotIn('Location',r.headers)
  app=self.app();env=EnvironBuilder(path='/',headers={'Authorization':'yes'}).get_environ();env['PATH_INFO']='\ud800'
  captured=[];it=app.wsgi_app(env,lambda s,h:captured.append((s,dict(h))))
  b''.join(it);it.close();self.assertTrue(captured[0][0].startswith('403'));self.assertIn('no-store',captured[0][1]['Cache-Control'])
 def test_production_import_graph_subprocess(self):
  import subprocess,sys
  code='''
import sys
from integration.preview_launcher import build_preview
import integration.private_router
import integration.runtime, integration.geo_only_runtime, integration.single_db_runtime
from integration.news_api import create_app
for app in (create_app(),build_preview({}),build_preview({'PREVIEW_GEO_ONLY_ENABLED':'true'}),integration.private_router.app):
 assert not any('original-export' in str(x) for x in app.url_map.iter_rules())
 assert not any('fixture' in x for x in app.extensions)
assert 'integration.news_export.fixture_http' not in sys.modules
'''
  result=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stderr)

 def test_reserved_prefix_rejected_in_every_data_column(self):
  c=self.app().test_client();data=c.get(URL,headers={'Authorization':'yes'}).data
  original=list(csv.reader(io.StringIO(data.decode(),newline='')))
  def encode(rows):
   buf=io.StringIO(newline='');csv.writer(buf).writerows(rows);return buf.getvalue().encode()
  for column in range(8):
   rows=[r[:] for r in original];rows[1][column]='EXPORT_UNKNOWN'
   rows[-1][4]=hashlib.sha256(encode(rows[:-1])).hexdigest()
   with self.assertRaises(ValueError):validate_file(encode(rows),'brics')
 def test_accepted_large_fixture_servable_across_pages(self):
  rows=[{'_id':ObjectId(f'{n:024x}'),'collected_at':'2026-10-05T00:00:00.123456','title':'fixture','source':'x'*5000} for n in range(500,0,-1)]
  app=self.app({'brics':rows});c=app.test_client();auth={'Authorization':'yes'}
  self.assertEqual(c.head(URL,headers=auth).status_code,200)
  response=c.get(URL,headers=auth);self.assertEqual(response.status_code,200)
  info=validate_file(response.data,'brics');self.assertEqual(info['kind'],'EXPORT_COMPLETE');self.assertEqual(info['rows'],500)
 def test_max_row_boundary_fixture_fully_servable(self):
  def encoded(r):return len(json.dumps(r,ensure_ascii=False,separators=(',',':'),default=str).encode())
  base=row(title='x'*32000,source='x'*32000,summary='x'*32000,country='x'*32000)
  missing=128*1024-encoded(base);base['category']='x'*(missing-len('"category":"",'))
  rows=[]
  for n in range(63,0,-1):
   r=dict(base);r['_id']=ObjectId(f'{n:024x}');r['collected_at']='2026-10-05T00:00:00.123456';rows.append(r)
  app=self.app({'brics':rows});response=app.test_client().get(URL,headers={'Authorization':'yes'})
  info=validate_file(response.data,'brics');self.assertEqual(info['kind'],'EXPORT_COMPLETE');self.assertEqual(info['rows'],63)

 def test_corroboration_surrogate_clean_value_error(self):
  with self.assertRaisesRegex(ValueError,'^plain list$'):frozen_fixture({'brics':[row(corroborated_by=['\ud800'])]})
