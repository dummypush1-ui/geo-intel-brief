import unittest,ast
from pathlib import Path
from flask import Flask
from unittest.mock import patch
from feature_mail_mount.composition import compose_private_mail,LegacyMailHeld
ROOT=Path(__file__).resolve().parents[1]
class MailBoundaryTests(unittest.TestCase):
 def test_off_has_no_routes_or_capabilities(self):
  a=Flask(__name__);compose_private_mail(a);self.assertEqual(a.extensions['mail_receipt_mode'],'off');self.assertFalse(any('/internal/mail/' in r.rule for r in a.url_map.iter_rules()))
  with self.assertRaises(ValueError):compose_private_mail(Flask('other'),store=object())
 def test_fake_non_durable_store_refused(self):
  with self.assertRaises(ValueError):compose_private_mail(Flask(__name__),enabled=True,store=object(),secret='x'*48,clock=lambda:None)
 def test_legacy_sends_and_mark_never_touch_network(self):
  from intelligence.geo.reports import email_report,critical_alert,weekly_report
  for f in [email_report.send,critical_alert.send_if_critical,weekly_report.send,lambda:email_report.mark_sent(['1']),lambda:email_report.build_html(True)]:
   with self.assertRaises(LegacyMailHeld):f()
 def test_digest_shown_only_and_no_trigger_key(self):
  from intelligence.geo.reports import email_report as m
  row={'_id':'yes','title':'safe','score':4,'risk_level':'CRITICAL','source':'s','category':'GENERAL','country':'','summary':'','url':'https://example.test'}
  hidden=dict(row,_id='hidden',score=1)
  with patch.object(m,'unemailed_articles',return_value=[row,hidden]),patch.object(m,'upcoming_events',return_value=[]),patch.object(m,'DASHBOARD_BASE_URL','https://example.test'),patch.object(m,'TRIGGER_SECRET','secret-canary'):
   text,critical,ids=m.build_digest();self.assertEqual(ids,['yes']);self.assertEqual(critical,1);self.assertNotIn('secret-canary',text)
 def test_legacy_http_hold_before_services(self):
  from intelligence.geo import web
  with patch.object(web,'TRIGGER_SECRET','known'),patch.object(web,'_service',side_effect=AssertionError('effect')):
   c=web.app.test_client()
   for method,url in [('get','/digest-data'),('post','/mark-emailed'),('post','/send-digest'),('post','/critical'),('post','/weekly')]:
    r=getattr(c,method)(url,headers={'X-Trigger-Secret':'known'});self.assertEqual(r.status_code,403);self.assertFalse(r.json['retry_send'])
 def test_scheduler_never_retries_unknown(self):
  tree=ast.parse((ROOT/'intelligence/geo/scheduler.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_send_with_retry')
  class Logger:
   def info(self,*a):pass
   def error(self,*a):pass
  scope={'logger':Logger(),'LegacyMailHeld':LegacyMailHeld};exec(compile(ast.Module(body=[fn],type_ignores=[]),'retry','exec'),scope)
  calls=[]
  def fail():calls.append(1);raise RuntimeError('unknown')
  self.assertFalse(scope['_send_with_retry']('fixture',fail));self.assertEqual(calls,[1])
 def test_enabled_injected_receipts_prepare_claim_ack(self):
  from tests.test_feature_mail_mount import Client,REVIEW,CHANNEL,NOW,ID,payload
  from feature_mail_mount.store import MongoMailStore
  from bson import ObjectId
  client=Client();store=MongoMailStore(client,review=REVIEW,channel_id=CHANNEL,marking_policy='displayed')
  app=Flask('injected');compose_private_mail(app,enabled=True,store=store,secret='s'*48,clock=lambda:NOW)
  self.assertEqual(app.extensions['mail_receipt_mode'],'private_receipt_bridge_no_send')
  c=app.test_client();headers={'Authorization':'Bearer '+'s'*48}
  with patch('feature_mail_mount.store.build',side_effect=lambda a,b,k,n,p:payload(p,k)):
   self.assertEqual(c.post('/internal/mail/v1/prepare',json={'kind':'digest','nonce':'n'*24}).status_code,401)
   r=c.post('/internal/mail/v1/prepare',headers=headers,json={'kind':'digest','nonce':'n'*24});self.assertEqual(r.status_code,200)
   self.assertFalse(client.rows['articles'][ObjectId(ID)]['emailed'])
   args={'receipt':r.json['receipt'],'hash':r.json['hash'],'attempt':'a'*24}
   claim=c.post('/internal/mail/v1/claim',headers=headers,json=args);self.assertTrue(claim.json['permit'])
   duplicate=c.post('/internal/mail/v1/claim',headers=headers,json=args);self.assertFalse(duplicate.json['permit'])
   ack=c.post('/internal/mail/v1/ack',headers=headers,json=args);self.assertEqual(ack.status_code,200)
   self.assertTrue(client.rows['articles'][ObjectId(ID)]['emailed'])
   self.assertEqual(ack.json['scope'],'bridge_send_returned_not_delivery')
   with self.assertRaises(ValueError):compose_private_mail(app,enabled=True,store=store,secret='s'*48,clock=lambda:NOW)
 def test_fetched_policy_refused_and_input_contract(self):
  from tests.test_feature_mail_mount import Client,REVIEW,CHANNEL,NOW
  from feature_mail_mount.store import MongoMailStore
  store=MongoMailStore(Client('fetched'),review=REVIEW,channel_id=CHANNEL,marking_policy='fetched')
  with self.assertRaises(ValueError):compose_private_mail(Flask('fetched'),enabled=True,store=store,secret='s'*48,clock=lambda:NOW)
  for v in ['true',1,None]:
   with self.assertRaises(ValueError):compose_private_mail(Flask('off'),enabled=v)

 def test_scheduler_labels_hold_once_for_step_and_mail(self):
  tree=ast.parse((ROOT/'intelligence/geo/scheduler.py').read_text());fns=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_step','_send_with_retry')]
  class Logger:
   def __init__(self):self.logs=[]
   def info(self,*a):self.logs.append(a)
   def error(self,*a):raise AssertionError('not unknown')
   def exception(self,*a):raise AssertionError('not failure')
  log=Logger();scope={'logger':log,'LegacyMailHeld':LegacyMailHeld};exec(compile(ast.Module(body=fns,type_ignores=[]),'scheduler','exec'),scope)
  calls=[]
  def held():calls.append(1);raise LegacyMailHeld('held')
  self.assertIsNone(scope['_step']('critical',held));self.assertFalse(scope['_send_with_retry']('digest',held));self.assertEqual(len(calls),2);self.assertEqual(len(log.logs),2);self.assertTrue(all('HELD' in row[0] for row in log.logs))
