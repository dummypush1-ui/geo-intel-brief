import unittest
from unittest.mock import patch, Mock
from datetime import datetime, timezone
from integration import usitc_release_source as s
from integration.public_preview_builder import build_public_preview
from integration.public_live_builder import build_public_live_preview
from tests.test_code_news_public import env

URL='https://www.usitc.gov/2026_hts_revision_21'
RAW=b'<main><h1>2026 HTS Revision 21</h1><span>Release Date</span><div>October 09, 2026</div><a href="https://hts.usitc.gov/download?releaseDate=10%2F07%2F2026">download</a></main>'
STAMP='2026-10-15T00:00:00Z'
ARCHIVE=b'<main><h1>Modifications to the Harmonized Tariff Schedule (HTS)</h1><a href="/2026_hts_revision_21">rev21</a><a href="/2026_hts_revision_20">rev20</a></main>'
class Tests(unittest.TestCase):
 def snap(self):return s.parse_release(RAW,URL,STAMP)
 def test_discover_publisher_order_and_main_only(self):
  self.assertEqual(s.discover_release(ARCHIVE),URL)
  self.assertEqual(s.discover_release(b'<a href="/2026_hts_revision_99">evil</a>'+ARCHIVE),URL)
 def test_discovery_fail_closed(self):
  for raw in [b'',b'x'*(s.LIMIT+1),b'\xff',ARCHIVE.replace(b'Modifications',b'Challenge'),ARCHIVE.replace(b'/2026_hts_revision_',b'https://evil.test/')]:
   with self.assertRaises(s.SourceUnavailable):s.discover_release(raw)
 def test_release_date_not_download_date_or_effective(self):
  v=self.snap().view(datetime(2026,10,15,tzinfo=timezone.utc))
  self.assertEqual(v['items'][0]['published_date'],'2026-10-09')
  self.assertEqual(v['items'][0]['effective_dates'],[])
  self.assertEqual(v['items'][0]['codes'],[])
  self.assertEqual(v['items'][0]['review_state'],'candidate')
  self.assertIsNone(v['items'][0]['reviewed_at'])
  self.assertFalse(v['current_rates_verified']);self.assertFalse(v['legal_effect_independently_verified'])
  self.assertFalse(v['network']);self.assertFalse(v['polling'])
 def test_bad_url_title_date_and_capture(self):
  for u in ['http://www.usitc.gov/2026_hts_revision_21',URL+'?x=1',URL+'#x',URL.replace('www.usitc.gov','evil.test'),URL.replace('21','20')]:
   with self.assertRaises(s.SourceUnavailable):s.parse_release(RAW,u,STAMP)
  for raw in [RAW.replace(b'October 09',b'February 30'),RAW.replace(b'Release Date',b'Effective Date'),RAW.replace(b'2026 HTS Revision 21',b'Challenge'),RAW+b'<main><h1>duplicate</h1></main>']:
   with self.assertRaises(s.SourceUnavailable):s.parse_release(raw,URL,STAMP)
  for stamp in ['2026-10-08T00:00:00Z','2026-10-15T00:00:00',None,'garbage']:
   with self.assertRaises(s.SourceUnavailable):s.parse_release(RAW,URL,stamp)
 def test_explicit_capture_only_two_fixed_requests(self):
  with patch.object(s._Transport,'get',side_effect=[ARCHIVE,RAW]) as get:
   snap=s.capture_latest()
  self.assertEqual([c.args[0]for c in get.call_args_list],[s.ARCHIVE,URL]);self.assertEqual(len(snap._items),1)
 def test_no_redirects(self):
  self.assertIsNone(s._NoRedirect().redirect_request(None,None,302,'',{},'https://evil.test'))
 def test_transport_allowlist_no_IO(self):
  t=s._Transport()
  with patch.object(t.opener,'open',side_effect=AssertionError('IO')) as op:
   for u in ['http://www.usitc.gov/x','https://www.usitc.gov@evil.test/x','https://evil.test/x',URL+'?q=x',s.ARCHIVE+'?q=x']:
    with self.assertRaises(s.SourceUnavailable):t.get(u)
   op.assert_not_called()
 def response(self,raw=RAW):
  r=Mock();r.status=200;r.url=URL;r.headers={'Content-Encoding':'identity'}
  class H(dict):
   def get_content_type(self):return 'text/html'
  r.headers=H(r.headers);r.read.side_effect=[raw,b''];r.__enter__=Mock(return_value=r);r.__exit__=Mock(return_value=False);return r
 def test_transport_content_caps_status_encoding(self):
  for change in ['status','url','encoding','length','bytes','mime']:
   t=s._Transport();r=self.response()
   if change=='status':r.status=500
   if change=='url':r.url='https://evil.test'
   if change=='encoding':r.headers['Content-Encoding']='gzip'
   if change=='length':r.headers['Content-Length']=str(s.LIMIT+1)
   if change=='bytes':r.read.side_effect=[b'x'*(s.LIMIT+1)]
   if change=='mime':
    class BadMime(type(r.headers)):
     def get_content_type(self):return 'application/json'
    r.headers=BadMime({'Content-Encoding':'identity'})
   with patch.object(t.opener,'open',return_value=r),self.assertRaises(s.SourceUnavailable):t.get(URL)
 def test_transport_success_and_spacing(self):
  t=s._Transport()
  with patch.object(t.opener,'open',side_effect=[self.response(),self.response()]),patch.object(s.time,'monotonic',side_effect=[100,100,100,101,110,110,110]),patch.object(s.time,'sleep') as sleep:
   self.assertEqual(t.get(URL),RAW);self.assertEqual(t.get(URL),RAW);sleep.assert_called_once_with(9)
 def test_source_error_no_retry_no_details(self):
  t=s._Transport()
  with patch.object(t.opener,'open',side_effect=RuntimeError('private exception'))as op,self.assertRaisesRegex(s.SourceUnavailable,'^Official source unavailable; no tariff conclusion$'):t.get(URL)
  self.assertEqual(op.call_count,1)
 def test_builder_injection_OFF_refused_no_network(self):
  for build in [build_public_preview,build_public_live_preview]:
   with patch.object(s,'capture_latest',side_effect=AssertionError('network')):
    with self.assertRaises(ValueError):build(env(),tariff_snapshot=self.snap())
    for bad in [object(),[]]:
     with self.assertRaises(ValueError):build(dict(env(),PUBLIC_TARIFF_EVIDENCE_ENABLED='true'),tariff_snapshot=bad)
 def test_snapshot_is_defensive_manual_and_US_only(self):
  snap=self.snap()
  with patch.object(s,'capture_latest',side_effect=AssertionError('network')):
   app=build_public_preview(dict(env(),PUBLIC_TARIFF_EVIDENCE_ENABLED='true'),tariff_snapshot=snap)
   snap._items.clear();c=app.test_client()
   r=c.get('/api/tariff-evidence?jurisdiction=US',base_url='https://preview.example');self.assertEqual(r.status_code,200);self.assertEqual(r.json['total_supplied'],1)
   self.assertEqual(r.json['items'][0]['source_url'],URL)
   for j in ['IN','EU']:
    v=c.get('/api/tariff-evidence?jurisdiction='+j,base_url='https://preview.example').json;self.assertEqual(v['items'],[]);self.assertEqual(v['scope'],'supplied_evidence_not_complete_tariff_history')
 def test_live_fallback_keeps_explicit_snapshot(self):
  a=build_public_live_preview(dict(env(),PUBLIC_TARIFF_EVIDENCE_ENABLED='true'),tariff_snapshot=self.snap())
  self.assertEqual(a.test_client().get('/api/tariff-evidence',base_url='https://preview.example').json['total_supplied'],1)
 def test_live_composition_snapshot_and_failover(self):
  from tests.test_code_news_coverage_binding_prep import LIVE,Client
  flags=dict(LIVE,PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED='false',PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED='false',PUBLIC_TARIFF_EVIDENCE_ENABLED='true')
  app=build_public_live_preview(flags,client_factory=lambda *a,**k:Client(),tariff_snapshot=self.snap())
  self.addCleanup(app.extensions['whole_news_pages'].close)
  c=app.test_client();v=c.get('/api/tariff-evidence?jurisdiction=US',base_url=LIVE['PREVIEW_ORIGIN'])
  self.assertEqual(v.status_code,200);self.assertEqual(v.json['total_supplied'],1)
  self.assertEqual(c.get('/workspace',base_url=LIVE['PREVIEW_ORIGIN']).status_code,200)

 def test_opener_timeout_and_identity_encoding(self):
  t=s._Transport()
  with patch.object(t.opener,'open',return_value=self.response())as op:t.get(URL)
  self.assertEqual(op.call_args.kwargs,{'timeout':8})
  req=op.call_args.args[0];self.assertEqual(req.get_header('Accept-encoding'),'identity')
  self.assertEqual(req.full_url,URL)
 def test_elapsed_deadline_before_first_read(self):
  t=s._Transport();r=self.response()
  with patch.object(t.opener,'open',return_value=r),patch.object(s.time,'monotonic',side_effect=[100,116]),self.assertRaises(s.SourceUnavailable):t.get(URL)
  r.read.assert_not_called()
 def test_first_read_exact_LIMIT_plus_one(self):
  t=s._Transport();r=self.response();r.read.side_effect=[b'x'*(s.LIMIT+1)]
  with patch.object(t.opener,'open',return_value=r),self.assertRaises(s.SourceUnavailable):t.get(URL)
  self.assertEqual(r.read.call_count,1)
