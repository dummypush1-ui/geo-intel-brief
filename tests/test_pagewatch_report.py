import unittest
from integration.pagewatch_report import build_pagewatch_report
class PagewatchReportTests(unittest.TestCase):
 def test_initial_no_mail_no_content(self):
  for state in ['baseline','unchanged']:self.assertEqual(build_pagewatch_report({'state':state})['html'],'')
 def test_diff_full_safe_and_separate(self):
  text='-Old value\n+<img src=x onerror=alert(1)> new value\n[Diff truncated. Review source page.]'
  r=build_pagewatch_report({'state':'changed','items':[{'id':'hash','url':'https://nilgiried.com/','title':'Page changed','summary':text}]})
  self.assertNotIn('<img',r['html']);self.assertIn('&lt;img',r['html']);self.assertIn('white-space:pre-wrap',r['html']);self.assertIn('[Diff truncated.',r['html']);self.assertFalse(r['mail']);self.assertFalse(r['marking'])
 def test_invalid_url_identity(self):
  with self.assertRaises(ValueError):build_pagewatch_report({'state':'changed','items':[{'id':'hash','url':'javascript:evil','summary':'x'}]})
