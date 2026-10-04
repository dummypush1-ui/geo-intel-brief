import unittest
from datetime import datetime,timezone
from integration.news_api import create_app
class DigestPreviewRoutes(unittest.TestCase):
 def test_private_and_disabled_marks(self):
  c=create_app().test_client()
  for p in ['/digest-data','/critical','/weekly']:self.assertEqual(c.get(p).status_code,403)
  c=create_app(authorize=lambda r:True).test_client()
  self.assertEqual(c.post('/mark-emailed').status_code,403)
  r=c.post('/mark-emailed',headers={'Origin':'http://localhost'},json={'article_ids':['x']});self.assertEqual(r.status_code,503);self.assertFalse(r.json['writes'])
 def test_original_renderers_public_only(self):
  raw={'geo':[{'_id':'SECRET-ID','emailed':True,'telegram_url':'https://t.me/secret','title':'Fixture only','source':'Fixture','url':'https://example.com/a','category':'TRADE','risk_level':'CRITICAL','score':50,'created_at':datetime.now(timezone.utc).isoformat(),'published':datetime.now(timezone.utc).isoformat()}]}
  c=create_app(reader=lambda:raw,authorize=lambda r:True).test_client()
  for p in ['/digest-data','/critical','/weekly']:
   r=c.get(p);self.assertEqual(r.status_code,200,p);d=r.json
   self.assertFalse(d['delivery']);self.assertFalse(d['writes']);self.assertFalse(d['unsent_queue_verified']);self.assertNotIn('article_ids',d);self.assertIn('Fixture only',d['html']);self.assertNotIn('SECRET-ID',r.text);self.assertNotIn('t.me',r.text);self.assertEqual(r.headers['Cache-Control'],'no-store')
  self.assertTrue(raw['geo'][0]['emailed'])
 def test_bad_rows_generic503_and_query400(self):
  for raw in [None,{'geo':[None]},{'other':[]},{'geo':[{}]*2001}]:
   c=create_app(reader=lambda:raw,authorize=lambda r:True).test_client()
   for p in ['/digest-data','/critical','/weekly']:self.assertEqual(c.get(p).status_code,503)
  self.assertEqual(create_app(authorize=lambda r:True).test_client().get('/digest-data?send=true').status_code,400)

 def test_report_boundary_network_env_db_traps(self):
  from unittest.mock import patch
  from contextlib import ExitStack
  from integration.digest_preview import preview,legacy_rows
  from integration.geonews_digest.model import normalise_all
  import intelligence.geo.reports.email_report as digest
  import intelligence.geo.reports.critical_alert as critical
  import intelligence.geo.reports.weekly_report as weekly
  row={'_id':'IDENTIFIER-PRIVATE','article_key':'PUBLIC-KEY-NOT-OUTPUT','title':'Trap fixture','url':'https://example.com/a','score':50,'risk_level':'CRITICAL','created_at':datetime.now(timezone.utc).isoformat()}
  trap=lambda *a,**k: (_ for _ in ()).throw(AssertionError('live dependency accessed'))
  with ExitStack() as stack:
   for target in ['socket.socket','smtplib.SMTP','smtplib.SMTP_SSL','os.getenv','requests.get','requests.post','intelligence.geo.database.connect']:
    stack.enter_context(patch(target,trap))
   for module in [digest,critical,weekly]:
    for name in ['critical_since','weekly_top_articles','category_counts','top_countries','unemailed_articles','upcoming_events','mark_emailed']:
     if hasattr(module,name):stack.enter_context(patch.object(module,name,trap))
   for kind in ['digest','critical','weekly']:
    result=preview([row],kind,datetime.now(timezone.utc));self.assertIn('Trap fixture',result['html']);self.assertNotIn('IDENTIFIER-PRIVATE',str(result));self.assertNotIn('PUBLIC-KEY-NOT-OUTPUT',str(result));self.assertNotIn('preview-only-no-record-id',result['html'])
  self.assertEqual(legacy_rows(normalise_all([row])[0])[0]['_id'],'preview-only-no-record-id')

 def test_reviewed_event_gate_date_scope_and_literal_html(self):
  from integration.dashboard_snapshots import DashboardSnapshots
  from datetime import timedelta
  today=datetime.now(timezone.utc).date();rows=[{'name':'Summit <script>alert(1)</script>','event_date':today.isoformat(),'source_url':'https://example.com/event','description':'fixture only','_id':'PRIVATEEVENTID'}, {'name':'Out of period','event_date':(today+timedelta(days=91)).isoformat(),'source_url':'https://example.com/future'}, {'name':'Rejected URL','event_date':today.isoformat(),'source_url':'https://evil.com/private'}]
  adapter=DashboardSnapshots({'geo_events':lambda:{'observed_at':datetime.now(timezone.utc).isoformat(),'items':rows}},True,{'geo_events':['example.com']})
  c=create_app(authorize=lambda r:True,dashboard_snapshot_reader=adapter).test_client();r=c.get('/digest-data');self.assertEqual(r.status_code,200);d=r.json
  self.assertEqual(d['events'],'supplied_snapshot');self.assertEqual(d['event_snapshot']['shown'],1);self.assertEqual(d['event_snapshot']['rejected_count'],1)
  self.assertIn('Summit &lt;script&gt;',d['html']);self.assertNotIn('<script>',d['html']);self.assertNotIn('PRIVATEEVENTID',r.text);self.assertNotIn('Out of period',d['html']);self.assertNotIn('evil.com',d['html']);self.assertFalse(d['delivery']);self.assertFalse(d['writes'])
  self.assertEqual(c.get('/weekly').json['events'],'unwired')
 def test_missing_bad_and_empty_events_distinct(self):
  from integration.dashboard_snapshots import DashboardSnapshots
  c=create_app(authorize=lambda r:True).test_client();self.assertEqual(c.get('/digest-data').json['events'],'unwired')
  for rows,stamp,state in [([],datetime.now(timezone.utc).isoformat(),'supplied_snapshot'),([], 'bad','unavailable')]:
   adapter=DashboardSnapshots({'geo_events':lambda:{'observed_at':stamp,'items':rows}},True,{'geo_events':['example.com']});r=create_app(authorize=lambda r:True,dashboard_snapshot_reader=adapter).test_client().get('/digest-data');self.assertEqual(r.json['events'],state)
  r=create_app(authorize=lambda r:True,dashboard_snapshot_reader=lambda p:{'token':'SECRET'}).test_client().get('/digest-data');self.assertEqual(r.status_code,503);self.assertNotIn('SECRET',r.text)

 def test_injected_utc_header_naive_refusal_and_window_metadata(self):
  from integration.digest_preview import preview
  from integration.dashboard_snapshots import DashboardSnapshots
  fixed=datetime(2026,10,4,23,0,tzinfo=timezone.utc)
  adapter=DashboardSnapshots({'geo_events':lambda:{'observed_at':fixed.isoformat(),'items':[{'name':'old','source_url':'https://example.com/a','event_date':'2026-10-03'}]}},True,{'geo_events':['example.com']})
  d=preview([],'digest',fixed,adapter);self.assertIn('04 October 2026',d['html']);self.assertEqual(d['event_snapshot']['out_of_window'],1)
  self.assertFalse(d['event_snapshot']['truncation_may_hide_in_window'])
  with self.assertRaises(ValueError):preview([],'digest',datetime(2026,10,4))
  rows=[{'name':str(i),'source_url':'https://example.com/a','event_date':'2026-10-03'} for i in range(101)]
  adapter.readers['geo_events']=lambda:{'observed_at':fixed.isoformat(),'items':rows}
  d=preview([],'digest',fixed,adapter);self.assertTrue(d['event_snapshot']['truncation_may_hide_in_window']);self.assertEqual(d['event_snapshot']['out_of_window'],100)
