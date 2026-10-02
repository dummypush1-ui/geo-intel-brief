import unittest
from integration.dashboard_snapshots import DashboardSnapshots
from integration.news_api import create_app
STAMP='2026-10-02T00:00:00Z'
class DashboardSnapshotTests(unittest.TestCase):
 def reader(self,key,rows,stamp=STAMP):return DashboardSnapshots({key:lambda:{'observed_at':stamp,'items':rows}},True,allowed_hosts={key:['example.com']})
 def test_unavailable_not_empty_claim(self):
  d=DashboardSnapshots({},True)('geo');self.assertEqual(d['panels']['geo_events']['state'],'unavailable')
  d=self.reader('geo_events',[])('geo');self.assertEqual(d['panels']['geo_events']['state'],'supplied_snapshot')
 def test_events_exact_fields_safe_links(self):
  rows=[{'_id':'secret','name':'<script>x</script>','source_url':'https://example.com/a','event_date':'2026-10-03','description':'x'},{'name':'bad','source_url':'javascript:x','event_date':'2026-10-03'}]
  d=self.reader('geo_events',rows)('geo')['panels']['geo_events'];self.assertEqual(d['rejected_count'],1);self.assertNotIn('_id',d['items'][0]);self.assertEqual(d['items'][0]['name'],'<script>x</script>')
 def test_source_status_no_naive_time_or_defaults(self):
  d=self.reader('brics_sources',[{'name':'A','url':'https://example.com/a','last_status':'ok','last_checked':'2026-10-02T00:00:00','last_count':True}])('brics')['panels']['brics_sources']['items'][0]
  self.assertIsNone(d['last_checked']);self.assertIsNone(d['last_count'])
 def test_stream_link_not_live_embed(self):
  r=self.reader('brics_streams',[{'name':'A','watch_url':'https://example.com/a','embed_url':'https://evil.com','video_id':'private'}])('brics')['panels']['brics_streams']['items'][0]
  self.assertEqual(r['availability'],'not_checked');self.assertNotIn('embed_url',r)
 def test_invalid_bounded_snapshot_fails_unavailable(self):
  for rows,stamp in [([{}]*1001,STAMP),([], '2026-10-02')]:self.assertEqual(self.reader('geo_events',rows,stamp)('geo')['panels']['geo_events']['state'],'unavailable')
 def test_verified_true_only(self):
  for value in [False,1,'true']:
   with self.assertRaises(ValueError):DashboardSnapshots({},value)
 def test_guard_route_and_redaction(self):
  self.assertEqual(create_app().test_client().get('/api/dashboard-snapshots?project=geo').status_code,403)
  c=create_app(authorize=lambda r:True).test_client();self.assertEqual(c.get('/api/dashboard-snapshots').status_code,400);self.assertEqual(c.get('/api/dashboard-snapshots?project=geo').json['state'],'snapshot_readers_unwired')
  def bad(project):raise RuntimeError('private password')
  c=create_app(authorize=lambda r:True,dashboard_snapshot_reader=bad).test_client();r=c.get('/api/dashboard-snapshots?project=geo');self.assertEqual(r.status_code,503);self.assertNotIn('password',r.text)

 def test_route_rejects_arbitrary_outputs(self):
  for reader in [lambda p:{'password':'secret'},lambda p:[],object()]:
   c=create_app(authorize=lambda r:True,dashboard_snapshot_reader=reader).test_client()
   r=c.get('/api/dashboard-snapshots?project=geo');self.assertEqual(r.status_code,503);self.assertNotIn('secret',r.text)
 def test_valid_adapter_route_and_project_guard(self):
  c=create_app(authorize=lambda r:True,dashboard_snapshot_reader=self.reader('geo_events',[])).test_client()
  self.assertEqual(c.get('/api/dashboard-snapshots?project=geo').json['panels']['geo_events']['state'],'supplied_snapshot')
  self.assertEqual(c.get('/api/dashboard-snapshots?project=all').status_code,400)
 def test_unreviewed_hosts_and_queries_withheld(self):
  rows=[{'name':'x','watch_url':u} for u in ['https://example.com/x?token=secret','https://127.0.0.1/x','https://localhost/x','https://internal.company/x','https://evil.com/x','https://example.com:999/x','https://example.com:bad/x','https://user:pass@example.com/x']]
  panel=self.reader('brics_streams',rows)('brics')['panels']['brics_streams'];self.assertEqual(panel['items'],[]);self.assertEqual(panel['rejected_count'],len(rows))
 def test_reader_host_contract(self):
  for hosts in [None,{}, {'geo_events':['127.0.0.1']},{'geo_events':['a.local']},{'geo_events':['EXAMPLE.com']},{'geo_events':['example.com'],'brics_sources':['example.com']}]:
   with self.assertRaises(ValueError):DashboardSnapshots({'geo_events':lambda:{}},True,hosts)
 def test_deterministic_cap_order_and_no_mutation(self):
  rows=[{'name':str(i).zfill(3),'event_date':'2026-10-03','source_url':'https://example.com/'+str(i)} for i in range(105)]
  panel=self.reader('geo_events',list(reversed(rows)))('geo')['panels']['geo_events']
  self.assertEqual([r['name'] for r in panel['items']],[str(i).zfill(3) for i in range(100)])
  self.assertTrue(panel['truncated']);self.assertEqual(len(rows),105)

 def test_numeric_ipv4_aliases_not_allowlist_hosts(self):
  for host in ['127.1','127.0.1','0x7f.0.0.1','0177.0.0.1','192.168.1','10.1','0x7f.1','2130706433']:
   with self.assertRaises(ValueError):DashboardSnapshots({'geo_events':lambda:{}},True,{'geo_events':[host]})
 def test_full_payload_tiebreak_at_cap(self):
  cases={'geo_events':[{'name':'x','source_url':'https://example.com/a','event_date':'2026-10-03','description':str(i)} for i in range(105)],'brics_sources':[{'name':'x','url':'https://example.com/a','country':'A','last_status':'ok','last_count':i,'last_checked':STAMP} for i in range(105)],'brics_streams':[{'name':'X' if i%2 else 'x','watch_url':'https://example.com/a','country':'a' if i%2 else 'A'} for i in range(105)]}
  for key,rows in cases.items():
   project='geo' if key=='geo_events' else 'brics'
   forward=self.reader(key,rows)(project)['panels'][key]['items']
   reverse=self.reader(key,list(reversed(rows)))(project)['panels'][key]['items']
   self.assertEqual(forward,reverse);self.assertEqual(len(forward),100)

 def test_normalized_ports_and_bidi_paths(self):
  reader=self.reader('brics_streams',[])
  for url,want in [('https://example.com:00443/x','https://example.com/x'),('http://example.com:080/x','http://example.com/x'),('https://example.com:00080/x','https://example.com:80/x')]:self.assertEqual(reader.link('brics_streams',url),want)
  for path in ['/x\u202ey','/x%e2%80%aey','/x%E2%81%A6y','/x%d8%9cy']:self.assertIsNone(reader.link('brics_streams','https://example.com'+path))
 def test_numeric_or_hex_last_label_refused(self):
  for host in ['a.1','1e3.1','x.0x','x.0xff']:
   with self.assertRaises(ValueError):DashboardSnapshots({'geo_events':lambda:{}},True,{'geo_events':[host]})

 def test_backslash_percent_and_format_paths_withheld(self):
  r=self.reader('brics_streams',[])
  for path in ['/a\\b','/a%5cb','/a%20b','/a\u200bb','/a\ufeffb','/a\u2060b']:
   self.assertIsNone(r.link('brics_streams','https://example.com'+path))
 def test_blank_or_format_labels_withheld(self):
  for key,url_key in [('geo_events','source_url'),('brics_sources','url'),('brics_streams','watch_url')]:
   for name in ['','  ','\u200b','\ufeff','\u202eSource','Valid\u2060name']:
    row={'name':name,url_key:'https://example.com/x','event_date':'2026-10-03'}
    project='geo' if key=='geo_events' else 'brics'
    self.assertEqual(self.reader(key,[row])(project)['panels'][key]['items'],[])
 def test_format_country_not_displayed(self):
  r=self.reader('brics_sources',[{'name':'Valid','url':'https://example.com/x','country':'\u202eCountry'}])('brics')['panels']['brics_sources']['items'][0]
  self.assertEqual(r['country'],'')

 def test_nonformat_invisible_controls_and_surrogates(self):
  invisible=['\u2800','\u3164','\u115f','\u1160','\uffa0','\x00ok\x7f','a\ud800','a\ue000','a\u0378']
  for key,urlkey in [('geo_events','source_url'),('brics_sources','url'),('brics_streams','watch_url')]:
   for name in invisible:
    row={'name':name,urlkey:'https://example.com/x','event_date':'2026-10-03'}
    project='geo' if key=='geo_events' else 'brics'
    self.assertEqual(self.reader(key,[row])(project)['panels'][key]['items'],[])
  reader=self.reader('brics_streams',[])
  for value in invisible:self.assertIsNone(reader.link('brics_streams','https://example.com/a'+value))

 def test_nonspacing_invisible_names_and_countries(self):
  for name in ['\u034f','\ufe0f','\u180b','\u17b4','\u17b5','\U000e0100','\ufffc','\u0301','...']:
   row={'name':name,'watch_url':'https://example.com/x'}
   self.assertEqual(self.reader('brics_streams',[row])('brics')['panels']['brics_streams']['items'],[])
   item=self.reader('brics_sources',[{'name':'Valid','url':'https://example.com/x','country':name}])('brics')['panels']['brics_sources']['items'][0];self.assertEqual(item['country'],'')
 def test_visible_multilingual_and_combining_labels(self):
  for name in ['भारत','ایران','a\u0301','中','😀','2026']:
   self.assertEqual(self.reader('brics_streams',[{'name':name,'watch_url':'https://example.com/x'}])('brics')['panels']['brics_streams']['items'][0]['name'],name)
  for name in ['ای\u200cران','क\u200dष','👩\u200d💻']:
   self.assertEqual(self.reader('brics_streams',[{'name':name,'watch_url':'https://example.com/x'}])('brics')['panels']['brics_streams']['items'],[])
 def test_description_spoof_controls_omitted(self):
  for description,want in [('abc\u202edef',''),('abc\x7fdef',''),('a\ud800',''),('Line one\nLine two\tend','Line one\nLine two\tend')]:
   item=self.reader('geo_events',[{'name':'Valid','source_url':'https://example.com/x','event_date':'2026-10-03','description':description}])('geo')['panels']['geo_events']['items'][0]
   self.assertEqual(item['description'],want)
