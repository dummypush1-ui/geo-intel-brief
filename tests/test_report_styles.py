import unittest
from integration.html_safety import safe_style,sanitize_html
from integration.report_styles import color
class ReportStyleTests(unittest.TestCase):
 def test_original_gradient_background_typography(self):
  s=safe_style('background:linear-gradient(135deg,#1a365d,#2b6cb0);padding:26px 30px;color:white')
  self.assertIn('background-color:#1a365d',s);self.assertIn('background:linear-gradient(135deg,#1a365d,#2b6cb0)',s);self.assertIn('color:white',s)
  self.assertEqual(safe_style('background:#f4f6f8;font-family:Segoe UI,Arial,sans-serif'),'background:#f4f6f8;font-family:Segoe UI,Arial,sans-serif')
 def test_gradient_rgb_stops_and_named_colors(self):
  for c in ['rebeccapurple','#123','#abcd','#11223344','rgb(255, 0, 0)','rgba(100%,0%,0%,0.5)']:self.assertTrue(color(c),c)
  self.assertIn('linear-gradient',safe_style('background:linear-gradient(to right,rgba(255,0,0,0.5) 0%,blue 100%)'))
  for c in ['rgb(256,0,0)','rgba(0,0,0,2)','#12','madeup']:self.assertFalse(color(c))
 def test_resources_and_css_execution_rejected(self):
  for payload in ['background:url(https://evil.invalid/pixel)','background:linear-gradient(red,url(https://evil.invalid))','color:var(--secret)','width:expression(alert(1))','background:linear-gradient(red,blue);position:fixed;z-index:9999','color:r\\65 d','color:red!important','color:red/**/','@import:https://evil.invalid','background-image:image-set(url(x) 1x)','display:none','font-family:"x";src:url(x)']:
   s=safe_style(payload);self.assertNotIn('url',s);self.assertNotIn('expression',s);self.assertNotIn('position',s);self.assertNotIn('display',s);self.assertNotIn('var(',s)
  self.assertEqual(safe_style('x'*4001),'')
 def test_html_boundary_idempotent_and_attributes(self):
  s=sanitize_html('<div onclick="x" style="background:linear-gradient(135deg,#1a365d,#2b6cb0);color:white"><a href="javascript:x">Text</a><style>@import x</style></div>')
  self.assertNotIn('onclick',s);self.assertNotIn('javascript',s);self.assertNotIn('@import',s);self.assertEqual(sanitize_html(s),s)
 def test_invalid_declaration_does_not_drop_good_style(self):
  self.assertEqual(safe_style('color:red;bad;unknown:x;padding:10px;font-size:13px'),'color:red;padding:10px;font-size:13px')

 def test_cannot_hide_content_using_decorative_css(self):
  for payload in ['height:0;max-height:0;overflow:hidden;color:transparent;font-size:0;line-height:0','width:0','font-size:1px','opacity:0.01','color:rgba(0,0,0,0)','color:#0000','color:#00000000','opacity:0.9']:
   self.assertEqual(safe_style(payload),'',payload)
 def test_declaration_cap_idempotent(self):
  for payload in ['color:red;'*63+'background:linear-gradient(red,blue)','background:linear-gradient(red,blue);'*64,'color:red;'*64]:
   s=safe_style(payload);self.assertEqual(safe_style(s),s);self.assertLessEqual(len(s.split(';')),64)
 def test_positioned_stop_solid_fallback(self):
  s=safe_style('background:linear-gradient(to right,red 0%,blue 100%)');self.assertTrue(s.startswith('background-color:red;'));self.assertEqual(safe_style(s),s)
