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
