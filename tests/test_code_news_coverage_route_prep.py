import unittest,json,io
from unittest.mock import Mock,patch
from flask import Flask
from integration.code_news_coverage_route_prep import install,parse,validate,Invalid,PATH,enabled
from integration.code_news_coverage_contract_prep import RESOLUTIONS,serialize,script
from tests import test_code_news_coverage_broker_prep as broker_fixture
P=broker_fixture.P
ON={'PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED':'true'};ORIGIN='https://example.test';H={'Origin':ORIGIN,'Sec-Fetch-Site':'same-origin','Sec-Fetch-Mode':'cors','Sec-Fetch-Dest':'empty','Content-Type':'application/json'}
class Tests(unittest.TestCase):
 def make(self,real=False):
  self.app=Flask(__name__)
  if real:
   self.owner=broker_fixture.Tests();self.broker=self.owner.make();self.addCleanup(self.owner.doCleanups)
  else:self.broker=Mock();self.broker.head.return_value=({'state':'metadata_only'},200);self.broker.page.return_value=({'state':'busy'},429)
  install(self.app,ORIGIN,self.broker,ON);self.c=self.app.test_client();return self.broker
 def post(self,body=P,headers=H,**kwargs):return self.c.post(PATH,data=serialize(body),headers=headers,**kwargs)
 def test_OFF_no_origin_broker_and404(self):
  app=Flask(__name__);broker=Mock();self.assertFalse(install(app,None,broker));c=app.test_client()
  for method in ['post','get','head','options']:self.assertEqual(getattr(c,method)(PATH).status_code,404)
  broker.head.assert_not_called();broker.page.assert_not_called()
 def test_exactflag_origin_explicit(self):
  for flag in ['yes','TRUE',True]:
   with self.assertRaises(ValueError):enabled({'PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED':flag})
  for origin in [None,'https://example.test/','https://user@example.test','https://example.test?q=x']:
   with self.assertRaises(ValueError):install(Flask('bad'),origin,Mock(),ON)
 def test_head_options_only_head_GET405(self):
  b=self.make();self.assertEqual(self.c.head(PATH).status_code,200);self.assertEqual(self.c.options(PATH).status_code,204);self.assertEqual(b.head.call_count,2);b.page.assert_not_called();self.assertEqual(self.c.get(PATH).status_code,405);self.assertEqual(b.head.call_count,2)
 def test_headers_origin_Hostforwarded_not_authority(self):
  b=self.make()
  for key in ['Origin','Sec-Fetch-Site','Sec-Fetch-Mode','Sec-Fetch-Dest']:
   headers=dict(H);headers.pop(key);self.assertEqual(self.post(headers=headers).status_code,403)
   headers=dict(H);headers[key]='evil';self.assertEqual(self.post(headers=headers).status_code,403)
  forged=dict(H,Origin='https://evil.test',Host='example.test',**{'X-Forwarded-Host':'example.test','X-Forwarded-Proto':'https'});self.assertEqual(self.post(headers=forged).status_code,403);b.page.assert_not_called()
  valid=dict(H,Host='evil.test',**{'X-Forwarded-Host':'evil.test'});self.assertEqual(self.post(headers=valid).status_code,429)
 def test_query_content_body_zero_broker(self):
  b=self.make()
  for headers in [dict(H,**{'Content-Type':'text/plain'}),dict(H,**{'Content-Encoding':'gzip'}),dict(H,**{'Content-Type':'application/json; charset=latin1'}),dict(H,**{'Content-Type':'application/json; x=1'})]:self.assertEqual(self.post(headers=headers).status_code,400)
  self.assertEqual(self.c.post(PATH+'?x=1',data=serialize(P),headers=H).status_code,400)
  bad=[b'',b'[]',b'null',b'{"x": NaN}',b'{"system":"HS","system":"IN","edition":"2022","code":"8517"}',b'\xef\xbb\xbf'+serialize(P),b'\xff',serialize(dict(P,code=8517)),serialize(dict(P,code='8517\n')),serialize(dict(P,code='８５１７')),serialize(dict(P,code={'x':'a'})),serialize(dict(P,extra='private'))]
  for raw in bad:self.assertEqual(self.c.post(PATH,data=raw,headers=H).status_code,400)
  b.page.assert_not_called()
 def test_body1024_1025_stream_chunked_noContentLength(self):
  b=self.make();raw=serialize(P);valid=raw+b' '*(1024-len(raw));self.assertEqual(self.c.post(PATH,data=valid,headers=H).status_code,429);b.page.reset_mock()
  for size in [1025,3000]:
   data=raw+b' '*(size-len(raw));response=self.c.open(PATH,method='POST',headers=H,environ_overrides={'wsgi.input':io.BytesIO(data),'wsgi.input_terminated':True,'CONTENT_LENGTH':''});self.assertEqual(response.status_code,413)
  b.page.assert_not_called()
  self.assertEqual(self.c.open(PATH,method='POST',headers=H,environ_overrides={'wsgi.input':io.BytesIO(raw),'CONTENT_LENGTH':''}).status_code,400);b.page.assert_not_called()
 def test_closed_error_table_no_private_echo_retry(self):
  b=self.make()
  table={429:['resolve_busy','shared_capacity','busy','quota_wait'],400:['target_unavailable'],410:['expired_restart','binding_changed_restart','target_mismatch'],503:['source_unavailable','admission_fault']}
  for status,states in table.items():
   for state in states:
    b.page.return_value=({'state':state,'private':'TOKEN-SECRET'},status);r=self.post();self.assertEqual(r.status_code,status);self.assertNotIn(b'TOKEN-SECRET',r.data);self.assertEqual('Retry-After'in r.headers,status==429 and state in ['resolve_busy','quota_wait'])
  for status,state in [(200,'busy'),(418,'busy'),(429,'unknown'),(410,'source_unavailable')]:b.page.return_value=({'state':state},status);self.assertEqual(self.post().status_code,503)
 def test_all_resolution_values_unknown_invalid(self):
  b=self.make()
  for value in RESOLUTIONS:
   b.page.return_value=({'state':'target_unavailable','target':None,'resolution':value},200);r=self.post();self.assertEqual(r.status_code,200);self.assertEqual(r.json['resolution'],value)
  for value in ['invalid','private',None]:b.page.return_value=({'state':'target_unavailable','target':None,'resolution':value},200);self.assertEqual(self.post().status_code,400)
  self.assertIn(json.dumps(RESOLUTIONS),script())
 def test_real60_25_25_10_replay_samebytes_measure(self):
  b=self.make(True);r=self.post();self.assertEqual(r.status_code,200);self.assertEqual(len(r.json['items']),25);self.assertEqual(r.data,serialize(next(iter(b.replies.values()))['body']));params={k:r.json[k]for k in ['scope','manifest','matcher_version']}
  r2=self.post(params);replay=self.post(params);self.assertEqual(r2.data,replay.data);self.assertEqual(len(r2.json['items']),25);r3=self.post({k:r2.json[k]for k in params});self.assertEqual(len(r3.json['items']),10);self.assertEqual(r3.json['state'],'complete_mutable_read');self.assertEqual(len(self.owner.store.calls),1)
 def test_start_resume_exactonce(self):
  b=self.make();self.post();b.page.assert_called_once_with(P);b.page.reset_mock();params={'scope':'A'*43,'manifest':'a'*64,'matcher_version':'v1'};self.post(params);b.page.assert_called_once_with(**params)
 def test_response_cap_exact_andfaultTTL(self):
  b=self.make(True);r=self.post();body=r.json
  # Exact route envelope cap verified independent validator, no extra wire fields.
  with patch('integration.code_news_coverage_route_prep.validate',return_value=(body,200)):
   with patch('integration.code_news_coverage_route_prep.serialize',side_effect=lambda obj: b' ' *524288 if obj==body else serialize(obj)):self.assertEqual(self.post().status_code,200)
   with patch('integration.code_news_coverage_route_prep.serialize',side_effect=lambda obj:b' '*524289 if obj==body else serialize(obj)):self.assertEqual(self.post().status_code,503)
  self.assertTrue(b.ledger.rows)
 def test_headers_noCORS_existing_routes_unchanged(self):
  app=Flask('legacy');app.add_url_rule('/api/code-news-context','old1',lambda:('OLD1',200));app.add_url_rule('/api/news-code-context','old2',lambda:('OLD2',200));before=[b'OLD1',b'OLD2'];c=app.test_client();b=Mock();b.head.return_value=({},200);b.page.return_value=({'state':'busy'},429);install(app,ORIGIN,b,ON);self.assertEqual(before,[c.get(p).data for p in ['/api/code-news-context','/api/news-code-context']]);r=c.post(PATH,data=serialize(P),headers=H)
  self.assertEqual(r.headers['Vary'],'Origin');self.assertEqual(r.headers['Cache-Control'],'no-store');self.assertEqual(r.headers['X-Content-Type-Options'],'nosniff');self.assertEqual(r.headers['Referrer-Policy'],'no-referrer');self.assertNotIn('Access-Control-Allow-Origin',r.headers);self.assertNotIn('Set-Cookie',r.headers)
 def test_malformed_broker_success_private_shapes_counters(self):
  b=self.make(True);good=self.post().json
  fake=Mock();self.broker=fake;app=Flask('malformed');install(app,ORIGIN,fake,ON);self.c=app.test_client()
  for field,value in [('private','SECRET'),('evidence_complete',True),('coverage_gap',True),('articles_checked_this_page',101),('items',[]),('scope','bad')]:
   body=json.loads(json.dumps(good));body[field]=value
   if field=='items':body[field]=[{'article_key':'a','relationships':[{'private':'SECRET'}]}]
   fake.page.return_value=(body,200);r=self.post();self.assertEqual(r.status_code,503);self.assertNotIn(b'SECRET',r.data)
 def test_shared_contract_measure_equal_default_and_nan_refused(self):
  sample={'state':'x','unicode':'தமிழ்','items':[1,2]};self.assertEqual(serialize(sample),json.dumps(sample,ensure_ascii=False).encode())
  with self.assertRaises(ValueError):serialize({'x':float('nan')})
 def test_real_binding_expiry_capacity(self):
  b=self.make(True);r=self.post();params={k:r.json[k]for k in ['scope','manifest','matcher_version']};self.assertEqual(self.post(dict(params,manifest='b'*64)).status_code,410)
  for _ in range(4):self.assertEqual(self.post().status_code,200)
  response=self.post();self.assertEqual(response.status_code,429);self.assertEqual(response.json['state'],'shared_capacity');self.assertNotIn('Retry-After',response.headers)
  self.owner.now=120;self.assertEqual(self.post(params).status_code,410)

 def test_largest_valid_serialized_reply_boundary_plus1(self):
  b=self.make(True);good=self.post().json;link=good['items'][0]['relationships'][0];good['items']=[{'article_key':link['article_key'],'relationships':[dict(link,evidence='')for _ in range(32)]}]
  remaining=524288-len(serialize(good))
  for item in good['items'][0]['relationships']:
   n=min(remaining,18000);item['evidence']='x'*n;remaining-=n
  self.assertEqual(remaining,0);self.assertEqual(len(serialize(good)),524288)
  fake=Mock();app=Flask('boundary');install(app,ORIGIN,fake,ON);self.c=app.test_client();fake.page.return_value=(good,200);r=self.post();self.assertEqual(r.status_code,200);self.assertEqual(r.data,serialize(good))
  good['items'][0]['relationships'][-1]['evidence']+='x';self.assertEqual(len(serialize(good)),524289);self.assertEqual(self.post().status_code,503)
 def test_legalfalse_invalid_exact_targetcontrols(self):
  b=self.make(True);body=self.post().json;body['items'][0]['relationships'][0]['legal_classification_verified']=True
  fake=Mock();fake.page.return_value=(body,200);app=Flask('legal');install(app,ORIGIN,fake,ON);self.c=app.test_client();self.assertEqual(self.post().status_code,503)
