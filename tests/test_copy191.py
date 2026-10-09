import unittest
from integration.news_api import create_app
from pathlib import Path
class Copy(unittest.TestCase):
 def test_truthful_whole_copy_only_when_adapter(self):
  c=create_app(authorize=lambda _:True,full_news_pages=object()).test_client();r=c.get('/workspace');self.assertIn('Summary metrics use up to the latest 100 stored articles, not the whole-store total. The feed can load more below.',r.text);self.assertNotIn('Loaded sample only. Database totals',r.text);self.assertIn('Export latest-100 view CSV',r.text);r.close()
 def test_sample_fixture_copy_preserved(self):
  c=create_app(authorize=lambda _:True).test_client();r=c.get('/workspace');self.assertIn('Loaded sample only. Database totals',r.text);self.assertIn('Export loaded sample CSV',r.text);self.assertNotIn('Summary metrics use up to the latest',r.text);r.close()
 def test_conditional_stats_and_no_semantics_change(self):
  s=Path('integration/ui/workspace.js').read_text();self.assertIn("whole?'Latest 100 metrics (not total)':'Articles in loaded view'",s);self.assertIn("fullPages?'Latest-100 metrics, not full-store count: '",s);self.assertIn("await request('/api/news?' + params)",s)
