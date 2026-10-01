import unittest
from integration.site_parsers import sanews_listing,sanews_article
URL='https://www.sanews.gov.za/south-africa/trade-story'
HTML='<head><meta property="article:published_time" content="2026-10-01T12:00:00Z"></head><h1>South Africa trade talks</h1><article class="node node-detail"><time datetime="2026-10-01T12:00:00Z"></time><p>'+('Trade talks details. '*12)+'</p></article><article><p>Related story must not be included</p></article>'
class SiteParserTests(unittest.TestCase):
 def test_article_body_scope_and_date(self):
  r=sanews_article(HTML,URL,'2026-10-02T00:00:00Z','User-agent: *\nAllow: /',reviewed=True);self.assertEqual(r['published'],'2026-10-01T12:00:00+00:00');self.assertNotIn('Related story',r['summary']);self.assertEqual(r['attribution'],'SAnews')
 def test_no_date_invention(self):
  r=sanews_article(HTML.replace('<meta property="article:published_time" content="2026-10-01T12:00:00Z">',''),URL,'2026-10-02','User-agent: *\nAllow: /',reviewed=True);self.assertEqual(r['published'],'')
 def test_stub_and_wrong_site_rejected(self):
  with self.assertRaises(ValueError):sanews_article('<h1>Home</h1>',URL,'2026-10-02','User-agent: *\nAllow: /',reviewed=True)
  with self.assertRaises(ValueError):sanews_article(HTML,'https://evil.example/south-africa/a','2026-10-02','User-agent: *\nAllow: /',reviewed=True)
 def test_listing_disabled_and_robots(self):
  h='<a href="/south-africa/trade-story">South Africa trade talks</a><a href="/user/login">Login to this website</a>'
  self.assertEqual(sanews_listing(h,'User-agent: *\nAllow: /'),[])
  self.assertEqual(len(sanews_listing(h,'User-agent: *\nDisallow: /user/',reviewed=True)),1)
  self.assertEqual(sanews_listing(h,'User-agent: *\nDisallow: /south-africa/',reviewed=True),[])

 def test_article_robots_and_traversal(self):
  with self.assertRaises(ValueError):sanews_article(HTML,URL,'2026-10-02','User-agent: *\nDisallow: /',reviewed=True)
  with self.assertRaises(ValueError):sanews_article(HTML,'https://www.sanews.gov.za/south-africa/../user/login','2026-10-02','User-agent: *\nAllow: /',reviewed=True)
 def test_malformed_footer_and_multiple_title(self):
  h=HTML.replace('</p></article>','</p><div><li>bad nesting</article>')+'<h1>Second heading</h1><footer><p>Footer leak</p></footer>'
  r=sanews_article(h,URL,'2026-10-02','User-agent: *\nAllow: /',reviewed=True);self.assertNotIn('Footer leak',r['summary']);self.assertNotIn('Second heading',r['title'])

 def test_truncated_root_rejected(self):
  with self.assertRaises(ValueError):sanews_article(HTML.replace('</article>','',1),URL,'2026-10-02','User-agent: *\nAllow: /',reviewed=True)
