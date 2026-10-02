import unittest
import hashlib,ast,sys
from integration.news_api import create_app
from integration.relevance import match
from integration.html_safety import sanitize_html
class SecurityReviewTests(unittest.TestCase):
 def test_auth_fail_closed(self):
  def broken(r):raise RuntimeError('auth unavailable')
  self.assertEqual(create_app(authorize=broken).test_client().get('/workspace').status_code,403)
 def test_post_origin_and_terms(self):
  c=create_app(authorize=lambda r:True).test_client()
  self.assertEqual(c.post('/api/related-news',json={}).status_code,403)
  for terms in (None,'string',[None],['a'*201],['a']*21):
   self.assertEqual(c.post('/api/related-news',json={'product_terms':terms},headers={'Origin':'http://localhost'}).status_code,400)
  self.assertEqual(match({'product_terms':None},{'title':'safe'})['reasons'],[])
 def test_host_not_used_for_finder(self):
  c=create_app(reader=lambda:{'geo':[{'_id':'1','url':'https://example.com/a','title':'HS 123456'}]},authorize=lambda r:True,finder_context_reader=lambda:[{'code':'123456','system_index':0,'entry_index':1,'index_verified':True}]).test_client()
  d=c.post('/api/finder-context',headers={'Host':'attacker.test','Origin':'http://attacker.test'},json={'project':'geo','article_key':hashlib.sha256(b'geo\nhttps://example.com/a').hexdigest()}).json
  self.assertEqual(d['items'],[])
 def test_report_sanitizer(self):
  out=sanitize_html('<h2>Trade &amp; Tariffs</h2><a href="javascript:x" onclick="x">News</a><script>bad</script><p>Good</p>')
  self.assertIn('Trade &amp; Tariffs',out);self.assertIn('Good',out);self.assertNotIn('onclick',out);self.assertNotIn('javascript',out);self.assertNotIn('bad',out)
 def test_private_router_no_legacy_import(self):
  from pathlib import Path
  for name in ('private_router.py','news_api.py'):
   text=(Path(__file__).resolve().parents[1]/'integration'/name).read_text()
   for n in ast.walk(ast.parse(text)):
    if isinstance(n,ast.ImportFrom):self.assertFalse((n.module or '').startswith('intelligence.'))
 def test_finder_inline_scripts_have_hashes(self):
  c=create_app(authorize=lambda r:True).test_client();r=c.get('/workspace/finder/index.html')
  self.assertIn('sha256-',r.headers['Content-Security-Policy']);self.assertNotIn("script-src 'self' 'unsafe-inline'",r.headers['Content-Security-Policy']);r.close()
 def test_proxy_allowed_origin(self):
  c=create_app(authorize=lambda r:True,allowed_origin='https://private.example').test_client()
  self.assertEqual(c.post('/api/related-news',headers={'Origin':'https://private.example'},json={}).status_code,200)
 def test_safe_styles_preserved(self):
  out=sanitize_html('<table width="700" cellpadding="0"><td align="center"><p style="color:#c53030;background-color:#f7fafc;font-size:13px;background:url(https://evil.test);padding:10px">CRITICAL</p></td></table>')
  self.assertIn('color:#c53030',out);self.assertIn('background-color:#f7fafc',out);self.assertIn('padding:10px',out);self.assertNotIn('evil',out);self.assertIn('width="700"',out)
