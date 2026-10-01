import unittest
from unittest.mock import patch
from integration.report_adapters import geo_report_builder,brics_report_builder
from integration.project_reports import combined_reports
class OriginalReportTests(unittest.TestCase):
 def test_real_preserved_builders_no_network_or_mark(self):
  geo={'_id':'mongo-1','title':'Trade update','url':'https://example.com/geo','summary':'Summary','score':80,'category':'TRADE','risk_level':'HIGH','source':'Source','country':'India'}
  brics={'id':'hash-1','title':'<script>alert(1)</script>','url':'javascript:alert(1)','source':"A'B",'country':'India','category':'TRADE'}
  with patch('intelligence.geo.database.connect',side_effect=AssertionError('No live DB')):
   builders={'finder':lambda:{'html':'','ids':[]},'geo':geo_report_builder(lambda:[geo],lambda days:[{'name':'Event','event_date':'2026-10-02','category':'Conference','confidence':'High','description':'Event details','source_url':'https://example.com/event'}]),'brics':brics_report_builder(lambda:[brics],lambda:[{'name':'BRICS stream','watch_url':'https://example.com/watch'}])}
   d=combined_reports(builders)
  self.assertIn('Trade update',d['html']);self.assertIn('Event details',d['html']);self.assertIn('BRICS stream',d['html']);self.assertNotIn('<script>',d['html']);self.assertNotIn('javascript:',d['html']);self.assertNotIn('?key=',d['html']);self.assertEqual(d['project_ids']['brics'],['hash-1']);self.assertEqual(d['project_ids']['geo'],['mongo-1'])
 def test_global_isolation(self):
  from intelligence.brics.reports.email_report import build_digest
  original=build_digest.__globals__['load_streams']
  brics_report_builder(lambda:[],lambda:[])()
  self.assertIs(build_digest.__globals__['load_streams'],original)
 def test_geo_hostile_fields_and_brics_group_keys(self):
  geo={'_id':'g','title':'<img onerror=x>','url':'javascript:bad','summary':'<script>bad</script>','score':80,'category':'TRADE','risk_level':'HIGH','source':'<b>source</b>','country':'<b>India</b>'}
  d=geo_report_builder(lambda:[geo],lambda days:[])()
  self.assertNotIn('<img',d['html']);self.assertNotIn('href="javascript',d['html']);self.assertIn('&lt;img',d['html'])
  rows=[{'id':'b','title':None,'url':'https://example.com/a','source':None,'category':'Trade & Tariffs'}]
  html=brics_report_builder(lambda:rows,lambda:[])()['html'];self.assertIn('Trade &amp; Tariffs',html);self.assertNotIn('None',html)
 def test_falsy_brics_category_and_missing_url(self):
  html=brics_report_builder(lambda:[{'id':'b','title':'Story','source':'Source','category':None}],lambda:[])()['html']
  self.assertIn('GENERAL',html);self.assertNotIn('None',html)
