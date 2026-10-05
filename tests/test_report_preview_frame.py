import unittest
from datetime import datetime,timezone
from integration.digest_preview import preview
from integration.report_preview_frame import responsive_preview
from integration.renderer_scope import renderer,ROOT,PINS,SPECS
import hashlib
NOW=datetime(2026,10,5,tzinfo=timezone.utc)
ROW={'title':'Trade fixture','url':'https://example.com/a','summary':'x'*1000,'source':'Fixture','category':'TRADE','score':50,'risk_level':'CRITICAL','country':'India','created_at':NOW.isoformat()}
class Tests(unittest.TestCase):
 def test_two_preview_kinds_only_fixed_style(self):
  for kind in ('digest','weekly'):
   r=preview([ROW],kind,NOW);self.assertIn('name="viewport"',r['html']);self.assertIn('max-width:700px',r['html']);self.assertIn('font-family:Segoe UI,Arial,sans-serif',r['html']);self.assertFalse(r['delivery']);self.assertFalse(r['writes']);self.assertIn('Trade fixture',r['html'])
  self.assertNotIn('name="viewport"',preview([ROW],'critical',NOW)['html'])
 def test_original_hashes_and_direct_renderer_no_frame(self):
  for kind in ('geo_digest','geo_weekly'):
   self.assertEqual(hashlib.sha256((ROOT/SPECS[kind][0]).read_bytes()).hexdigest(),PINS[kind])
  html=renderer('geo_weekly',{'weekly_top_articles':lambda *a,**k:[],'category_counts':lambda *a,**k:[],'top_countries':lambda *a,**k:[]},now=NOW)()
  self.assertNotIn('name="viewport"',html);self.assertIn('width="680"',html)
 def test_untrusted_style_scripts_links_not_accepted(self):
  h=responsive_preview('<html><body><style>body{display:none}</style><script>alert(1)</script><p>safe</p><a href="javascript:bad">bad</a></body></html>')
  self.assertNotIn('display:none',h);self.assertNotIn('alert(1)',h);self.assertNotIn('javascript:',h);self.assertIn('safe',h)
 def test_invalid_body_shape_rejected(self):
  with self.assertRaises(ValueError):responsive_preview('<p>not original body</p>')
