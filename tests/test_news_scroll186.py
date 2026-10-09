import unittest,subprocess
from integration.news_api import create_app
from pathlib import Path
class Scroll(unittest.TestCase):
 def test_controller(self):
  r=subprocess.run(['node','tests/news_scroll_test.mjs'],capture_output=True,text=True,timeout=15);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
 def test_ui_default_sample_unchanged_and_enabled_marker(self):
  for pager,marker in [(None,'false'),(object(),'true')]:
   c=create_app(authorize=lambda _:True,full_news_pages=pager).test_client();r=c.get('/workspace');self.assertIn('data-full-news-pages="'+marker+'"',r.text);self.assertIn('news-load-more',r.text);r.close()
  c=create_app(authorize=lambda _:True).test_client();r=c.get('/workspace/assets/news_scroll.js');self.assertEqual(r.status_code,200);r.close()
 def test_public_module_and_geo_full_pages_heading(self):
  from integration.public_preview_builder import build_public_preview
  e={'PREVIEW_PUBLIC_SAMPLE_ENABLED':'true','PREVIEW_GEO_ONLY_ENABLED':'true','PREVIEW_ACCESS_ENABLED':'false','NEWS_READ_ENABLED':'false','NEWS_EVENTS_READ_ENABLED':'false','FINDER_NETWORK_PREVIEW_ENABLED':'false','PREVIEW_ORIGIN':'https://preview.example'}
  c=build_public_preview(e).test_client();r=c.get('/workspace/assets/news_scroll.js',base_url='https://preview.example');self.assertEqual(r.status_code,200);r.close()
 def test_old_news_source_not_switched_without_marker(self):
  js=Path('integration/ui/workspace.js').read_text();self.assertIn("byId('news-view').dataset.fullNewsPages === 'true'",js);self.assertIn("await request('/api/news?' + params)",js);self.assertIn('box.children.length>200',js);self.assertIn("scrollNews.cancel()",js)
