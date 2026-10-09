import unittest,re
from unittest.mock import patch
class DashboardArgs(unittest.TestCase):
 def test_invalid_limit400_before_renderer(self):
  from intelligence.geo import web
  with patch.object(web,'TRIGGER_SECRET','known'),patch.object(web,'_db_check',return_value=None),patch.object(web,'build_dashboard_html',side_effect=AssertionError('render')):
   for v in ['0','2001','bad','-1','2.5']:
    r=web.app.test_client().get('/dashboard?limit='+v,headers={'X-Trigger-Secret':'known'});self.assertEqual(r.status_code,400,v)
 def test_export_link_category_only_no_key(self):
  from intelligence.geo.reports import dashboard as d
  with patch.object(d,'total_article_count',return_value=0),patch.object(d,'latest_collection_time',return_value=None),patch.object(d,'recent_articles',return_value=[]),patch.object(d,'upcoming_events',return_value=[]),patch.object(d,'critical_since',return_value=[]),patch.object(d,'category_counts',return_value=[]),patch.object(d,'top_countries',return_value=[]):
   out=d.build_dashboard_html(category='A & B',trigger_key='secret-canary')
   self.assertIn('/export.csv?category=A+%26+B',out);self.assertNotIn('secret-canary',out);self.assertNotIn('Export all articles',out)
