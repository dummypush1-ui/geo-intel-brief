import unittest,re,hashlib,base64
from pathlib import Path
from integration.finder_nested import shortlist_scroll,TABLE,STYLE,REPLACEMENT
from integration.finder_network import manual_ships_shell
from integration.news_api import create_app
class FinderNestedTests(unittest.TestCase):
 def test_exact_seam_and_first_real_head_only(self):
  s=(Path(__file__).resolve().parents[1]/'index.html').read_text();out=shortlist_scroll(s)
  self.assertNotIn(TABLE,out);self.assertEqual(out.count(STYLE),1);self.assertEqual(out.count('<style id="finder-nested-shortlist">'),1)
  self.assertFalse(any(m.start()<=out.index(STYLE)<m.end() for m in re.finditer(r'<script\b[^>]*>.*?</script>',out,re.S|re.I)))
  self.assertEqual(out.replace(STYLE,'',1).replace(REPLACEMENT,TABLE),s)
  self.assertLess(out.index(STYLE),out.index('</head>'));self.assertEqual(s.count('</head>'),out.count('</head>'))
 def test_seam_changes_fail_closed(self):
  for s in ('<head></head>',TABLE+TABLE+'</head>',TABLE):
   with self.assertRaises(ValueError):shortlist_scroll(s)
 def test_private_served_only_and_csp_hashes(self):
  self.assertEqual(create_app().test_client().get('/workspace/finder/index.html').status_code,403)
  c=create_app(authorize=lambda r:True).test_client();r=c.get('/workspace/finder/index.html');self.assertEqual(r.status_code,200);self.assertIn(STYLE,r.text);self.assertIn('sha256-',r.headers['Content-Security-Policy']);self.assertEqual(r.headers['Cache-Control'],'no-store')

 def test_served_pipeline_seam_and_exact_script_csp(self):
  s=(Path(__file__).resolve().parents[1]/'index.html').read_text();before=manual_ships_shell(s);after=shortlist_scroll(before)
  def scripts(text):return [body for attrs,body in re.findall(r'<script\b([^>]*)>(.*?)</script>',text,flags=re.S|re.I) if body.strip() and not re.search(r'\bsrc\s*=',attrs,re.I)]
  def hashes(text):return {"'sha256-"+base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()+"'" for body in scripts(text)}
  # The seam port only adds markup in the one original UI script, so that
  # script hash necessarily changes; all other original scripts are unchanged.
  self.assertEqual(len(scripts(before)),len(scripts(after)))
  self.assertEqual(len(hashes(before)-hashes(after)),1)
  self.assertEqual(len(hashes(after)-hashes(before)),1)
  r=create_app(authorize=lambda r:True).test_client().get('/workspace/finder/index.html')
  directive=next(x.strip() for x in r.headers['Content-Security-Policy'].split(';') if x.strip().startswith('script-src'))
  self.assertNotIn("'unsafe-inline'",directive)
  self.assertEqual(set(re.findall(r"'sha256-[^']+'",directive)),hashes(r.text))
  self.assertEqual(len(scripts(r.text)),len(scripts(before)))
  with self.assertRaises(ValueError):shortlist_scroll(before.replace(TABLE,'seam changed'))
 def test_fake_head_inside_script_not_selected(self):
  with self.assertRaises(ValueError):shortlist_scroll('<script>"</head><body>"</script>'+TABLE)

 def test_two_real_head_boundaries_refused(self):
  with self.assertRaises(ValueError):shortlist_scroll('</head><body>'+TABLE+'</head><body>')
