import unittest
from unittest.mock import patch
class Channels(unittest.TestCase):
 def test_telegram_report_safe_urls_no_trigger_secret(self):
  from intelligence.geo.reports import telegram_report as t,whatsapp_report as w
  for url in ['javascript:alert(1)','data:text/html,x','javascript&#58;x','https://user:p@example.org/x','https://example.org/\nx']:
   row={'score':8,'risk_level':'HIGH','title':'Fixture_[x]','source':'S*x','url':url}
   with patch.object(t,'recent_articles',return_value=[row]),patch.object(t,'upcoming_events',return_value=[]),patch.object(t,'TRIGGER_SECRET','SECRET-CANARY'),patch.object(t,'DASHBOARD_BASE_URL','https://private.example'):
    msg=t.build_message();self.assertNotIn(url,msg);self.assertNotIn('SECRET-CANARY',msg);self.assertNotIn('private.example',msg);self.assertIn('[link omitted]',msg);self.assertIn('Fixture\\_\\[x]',msg)
   with patch.object(w,'recent_articles',return_value=[row]),patch.object(w,'upcoming_events',return_value=[]):self.assertNotIn(url,w.build_message())
 def test_archive_link_filter_and_legitimate_query(self):
  import ast,types
  from pathlib import Path
  from integration.news_view import safe_url
  tree=ast.parse(Path('intelligence/geo/reports/telegram_archive.py').read_text());scope={'safe_url':safe_url}
  node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_format_article_line');exec(compile(ast.Module(body=[node],type_ignores=[]),'original-archive-formatter','exec'),scope);a=types.SimpleNamespace(_format_article_line=scope['_format_article_line'])
  for url in ['javascript:alert(1)','data:text/html,x','https://u:p@example.org/x','https://example.org/\nx']:
   out=a._format_article_line({'url':url});self.assertNotIn(url,out);self.assertIn('[link omitted]',out)
  out=a._format_article_line({'url':'https://example.org/x?a=1&b=2#old'});self.assertIn('https://example.org/x?a=1&b=2',out);self.assertNotIn('#old',out)
