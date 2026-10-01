import unittest
from integration.page_watch import snapshot,compare
URL='https://nilgiried.com/'
HTML='<html><body><h1>Nilgiris Economic Dialogue</h1><p>Event dates: February 6 to 8</p></body></html>'
class PageWatchTests(unittest.TestCase):
 def make(self,s=HTML):return snapshot(URL,s,'2026-10-02T03:00:00+05:30')
 def test_baseline_and_unchanged(self):
  a=self.make();self.assertEqual(compare(None,a)['state'],'baseline');self.assertEqual(compare(a,self.make())['items'],[])
 def test_changed_details_no_invented_publication(self):
  a=self.make();b=self.make(HTML.replace('6 to 8','7 to 9'));r=compare(a,b);self.assertEqual(r['state'],'changed');self.assertIn('-Event dates: February 6 to 8',r['items'][0]['summary']);self.assertIn('+Event dates: February 7 to 9',r['items'][0]['summary']);self.assertEqual(r['items'][0]['published'],'');self.assertFalse(r['items'][0]['emailed'])
 def test_script_nav_hidden_noise_ignored(self):
  a=self.make();b=self.make(HTML.replace('</body>','<script>alert(1)</script><nav>Navigation changed</nav><p hidden>private hidden stuff</p></body>'));self.assertEqual(a['sha256'],b['sha256'])
 def test_bad_identity_empty_and_timestamp(self):
  with self.assertRaises(ValueError):compare(self.make(),snapshot('https://example.com/',HTML,'2026-10-02'))
  with self.assertRaises(ValueError):snapshot(URL,'<script>only script</script>','2026-10-02')
  with self.assertRaises(ValueError):snapshot(URL,HTML,'not-a-time')
 def test_id_deterministic_and_raw_text_safe(self):
  a=self.make();b=self.make(HTML.replace('February','&lt;img src=x onerror=alert(1)&gt; February'));self.assertEqual(compare(a,b)['items'][0]['id'],compare(a,b)['items'][0]['id']);self.assertIn('<img',compare(a,b)['items'][0]['summary'])

 def test_malformed_style_and_unclosed_hidden(self):
  self.assertTrue(self.make(HTML.replace('<p>','<p style>'))['text'])
  with self.assertRaises(ValueError):self.make(HTML.replace('</body>','<div hidden>x<p>after</p><p>visible</p></body>'))
 def test_invalid_snapshot_and_html_boundary(self):
  with self.assertRaises(ValueError):compare({},self.make())
  a=self.make();b=self.make(HTML.replace('February','&lt;img src=x onerror=alert(1)&gt; February'));row=compare(a,b)['items'][0]
  self.assertNotIn('<img',row['summary_html']);self.assertEqual(row['summary_format'],'plain_text')
 def test_truncation_marker(self):
  a=self.make();b=self.make(HTML.replace('</body>',''.join('<p>New detail line %d</p>'%i for i in range(100))+'</body>'));r=compare(a,b);self.assertTrue(r['diff_truncated']);self.assertIn('[Diff truncated.',r['items'][0]['summary'])

 def test_deep_nesting_bounded(self):
  with self.assertRaises(ValueError):self.make('<div>'*501+HTML+'</div>'*501)
 def test_aria_hidden_uppercase(self):
  self.assertEqual(self.make()['sha256'],self.make(HTML.replace('</body>','<p aria-hidden="TRUE">Hidden noise</p></body>'))['sha256'])
