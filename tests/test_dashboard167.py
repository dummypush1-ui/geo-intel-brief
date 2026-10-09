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

 def test_sort_and_tabs_query_encoding_attribute_safety(self):
  from intelligence.geo.reports import dashboard as d
  from html.parser import HTMLParser
  from urllib.parse import urlsplit,parse_qs
  class Links(HTMLParser):
   def __init__(self):super().__init__();self.links=[]
   def handle_starttag(self,tag,attrs):
    if tag=='a':self.links.append(dict(attrs))
  category='A & B" onclick="bad'
  with patch.object(d,'total_article_count',return_value=0),patch.object(d,'latest_collection_time',return_value=None),patch.object(d,'recent_articles',return_value=[]),patch.object(d,'upcoming_events',return_value=[]),patch.object(d,'critical_since',return_value=[]),patch.object(d,'category_counts',return_value=[]),patch.object(d,'top_countries',return_value=[]),patch.dict(d.CATEGORY_LABELS,{category:'Special'}):
   out=d.build_dashboard_html(category=category,trigger_key='secret-canary');parser=Links();parser.feed(out)
   self.assertTrue(parser.links);self.assertFalse(any('onclick' in a for a in parser.links));self.assertNotIn('secret-canary',out)
   sort=[parse_qs(urlsplit(a['href']).query) for a in parser.links if 'sort_by' in a['href']]
   self.assertEqual(len(sort),3)
   for q in sort:self.assertEqual(q['category'],[category]);self.assertEqual(q['limit'],['2000'])
   tabs=[parse_qs(urlsplit(a['href']).query) for a in parser.links if a.get('class','').startswith('tab')]
   self.assertTrue(any(q.get('category')==[category] for q in tabs))
