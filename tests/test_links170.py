import unittest
from unittest.mock import patch
from html.parser import HTMLParser
class Links(unittest.TestCase):
 def test_dashboard_and_critical_untrusted_url_schemes(self):
  from intelligence.geo.reports import dashboard as d,critical_alert as c
  class Parser(HTMLParser):
   def __init__(self):super().__init__();self.hrefs=[]
   def handle_starttag(self,t,a):
    if t=='a':self.hrefs.extend(v for k,v in a if k=='href')
  for url in ['javascript:alert(1)','data:text/html,bad','javascript&#58;alert(1)','https://example.org/\nbad','https://u:p@example.org/x']:
   row={'_id':'fixture-id','title':'fixture','url':url,'source':'s','category':'GENERAL','country':'','risk_level':'CRITICAL','score':5,'summary':'','credibility':'HIGH','published':'2026-10-09','corroboration':1}
   with patch.object(d,'total_article_count',return_value=1),patch.object(d,'latest_collection_time',return_value=None),patch.object(d,'recent_articles',return_value=[row]),patch.object(d,'upcoming_events',return_value=[{'name':'e','event_date':'2026-10-10','source_url':url,'description':''}]),patch.object(d,'critical_since',return_value=[]),patch.object(d,'category_counts',return_value=[]),patch.object(d,'top_countries',return_value=[]):
    text=d.build_dashboard_html(trigger_key='secret-canary');parser=Parser();parser.feed(text);self.assertNotIn(url,parser.hrefs);self.assertNotIn('secret-canary',text)
   parser=Parser();parser.feed(c.build_html([row]));self.assertEqual(parser.hrefs,['#'])
 def test_safe_https_query_and_quote_escaping_preserved(self):
  from intelligence.geo.reports import critical_alert as c
  row={'_id':'fixture-id','title':'fixture','url':'https://example.org/x?q="&a=1','source':'s','country':'','risk_level':'CRITICAL','score':5,'summary':''}
  out=c.build_html([row]);self.assertIn('&quot;',out);self.assertIn('&amp;',out);self.assertNotIn('href="https://example.org/x?q="',out)

 def test_digest_event_and_weekly_links_at_actual_renderer_boundary(self):
  from integration.renderer_scope import renderer
  from datetime import datetime,timezone
  now=datetime(2026,10,9,tzinfo=timezone.utc)
  for url in ['javascript:alert(1)','data:text/html,bad','javascript&#58;alert(1)','https://example.org/\nbad','https://u:p@example.org/x','https://example.org/x?q="&a=1']:
   row={'_id':'fixture-id','title':'fixture','url':url,'source':'s','category':'TRADE','country':'India','risk_level':'HIGH','score':8,'summary':'','credibility':'HIGH','published':'2026-10-09','corroboration':1}
   event={'name':'event','event_date':'2026-10-10','source_url':url,'description':'','confidence':'HIGH','category':'CONFERENCE'}
   digest=renderer('geo_digest',{'unemailed_articles':lambda *args,**kw:[row],'upcoming_events':lambda *args,**kw:[event]},now)
   weekly=renderer('geo_weekly',{'weekly_top_articles':lambda *args,**kw:[row],'category_counts':lambda *args,**kw:[],'top_countries':lambda *args,**kw:[]},now)
   for out in [digest()[0],weekly()]:
    if url.startswith('https://example.org/x?q='):
     self.assertIn('&quot;',out);self.assertIn('&amp;',out)
    else:self.assertNotIn(url,out);self.assertIn('href="#"',out)
