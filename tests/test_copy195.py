import unittest
from integration.news_api import create_app
class Tests(unittest.TestCase):
 def test_whole_labels_and_off_preserved(self):
  for enabled in (False,True):
   r=create_app(authorize=lambda _:True,full_news_pages=object()if enabled else None).test_client().get('/workspace');self.addCleanup(r.close)
   for old,new in [('Show daily UTC sample counts','Show daily UTC counts for the latest-100 summary view'),('Loaded Geo sample summary','Latest-100 Geo summary metrics, not full-store totals'),('Summary charts and CSV still cover the latest loaded sample.','Summary charts and CSV still cover up to 100 stored articles in the selected summary view, not the whole feed.')]:
    self.assertIn(new if enabled else old,r.text);self.assertNotIn(old if enabled else new,r.text)
 def test_signal_volume_export_and_bars_conditional_text(self):
  r=create_app(authorize=lambda _:True).test_client().get('/workspace/assets/workspace.js');self.addCleanup(r.close)
  for text in ('Latest-100 summary signals from ','Critical in 24h (latest-100 summary view): ','latest-100-summary.csv','Volume by category - latest-100 summary view','Risk level breakdown - latest-100 summary view','Source credibility - latest-100 summary view'):
   self.assertIn(text,r.text)
