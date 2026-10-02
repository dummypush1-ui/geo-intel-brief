import unittest
from integration.site_parsers import sanews_listing,sanews_article
URL='https://www.sanews.gov.za/south-africa/trade-story'
HTML='<head><meta property="og:title" content="South Africa trade talks"><meta property="article:published_time" content="2026-10-01T12:00:00Z"></head><h1 class="page-title">South Africa trade talks</h1><article class="node node-detail"><time datetime="2026-10-01T12:00:00Z"></time><p>'+('Trade talks details. '*12)+'</p></article><article><p>Related story must not be included</p></article>'
class SiteParserTests(unittest.TestCase):
 def test_article_body_scope_and_date(self):
  r=sanews_article(HTML,URL,'2026-10-02T00:00:00Z','User-agent: *\nAllow: /',reviewed=True);self.assertEqual(r['published'],'2026-10-01T12:00:00+00:00');self.assertNotIn('Related story',r['summary']);self.assertEqual(r['attribution'],'SAnews')
 def test_no_date_invention(self):
  r=sanews_article(HTML.replace('<meta property="article:published_time" content="2026-10-01T12:00:00Z">',''),URL,'2026-10-02T00:00:00Z','User-agent: *\nAllow: /',reviewed=True);self.assertEqual(r['published'],'')
 def test_stub_and_wrong_site_rejected(self):
  with self.assertRaises(ValueError):sanews_article('<h1>Home</h1>',URL,'2026-10-02T00:00:00Z','User-agent: *\nAllow: /',reviewed=True)
  with self.assertRaises(ValueError):sanews_article(HTML,'https://evil.example/south-africa/a','2026-10-02T00:00:00Z','User-agent: *\nAllow: /',reviewed=True)
 def test_listing_disabled_and_robots(self):
  h='<a href="/south-africa/trade-story">South Africa trade talks</a><a href="/user/login">Login to this website</a>'
  self.assertEqual(sanews_listing(h,'User-agent: *\nAllow: /'),[])
  self.assertEqual(len(sanews_listing(h,'User-agent: *\nDisallow: /user/',reviewed=True)),1)
  self.assertEqual(sanews_listing(h,'User-agent: *\nDisallow: /south-africa/',reviewed=True),[])

 def test_article_robots_and_traversal(self):
  with self.assertRaises(ValueError):sanews_article(HTML,URL,'2026-10-02T00:00:00Z','User-agent: *\nDisallow: /',reviewed=True)
  with self.assertRaises(ValueError):sanews_article(HTML,'https://www.sanews.gov.za/south-africa/../user/login','2026-10-02T00:00:00Z','User-agent: *\nAllow: /',reviewed=True)
 def test_malformed_footer_and_multiple_title(self):
  h=HTML.replace('</p></article>','</p><div><li>bad nesting</article>')+'<h1>Second heading</h1><footer><p>Footer leak</p></footer>'
  r=sanews_article(h,URL,'2026-10-02T00:00:00Z','User-agent: *\nAllow: /',reviewed=True);self.assertNotIn('Footer leak',r['summary']);self.assertNotIn('Second heading',r['title'])

 def test_truncated_root_rejected(self):
  with self.assertRaises(ValueError):sanews_article(HTML.replace('</article>','',1),URL,'2026-10-02T00:00:00Z','User-agent: *\nAllow: /',reviewed=True)

 def test_site_banner_never_title(self):
  h='<h1>Site banner</h1>'+HTML
  r=sanews_article(h,URL,'2026-10-02T00:00:00Z','User-agent: *\nAllow: /',reviewed=True)
  self.assertEqual(r['title'],'South Africa trade talks')
 def test_page_title_and_metadata_must_agree(self):
  for title in ['Other story','']:
   h=HTML.replace('<head>','<head><meta property="og:title" content="'+title+'">')
   with self.assertRaises(ValueError):sanews_article(h,URL,'2026-10-02T00:00:00Z','User-agent: *\nAllow: /',reviewed=True)
 def test_plain_h1_stub_not_article_title(self):
  with self.assertRaises(ValueError):sanews_article(HTML.replace('class="page-title"',''),URL,'2026-10-02T00:00:00Z','User-agent: *\nAllow: /',reviewed=True)
 def test_multiple_page_titles_rejected(self):
  h='<h1 class="page-title">Banner</h1>'+HTML
  with self.assertRaises(ValueError):sanews_article(h,URL,'2026-10-02T00:00:00Z','User-agent: *\nAllow: /',reviewed=True)
 def test_hidden_title_content_excluded(self):
  h=HTML.replace('South Africa trade talks</h1>','South Africa trade talks<span hidden><span>Wrong</span>Still wrong</span><script>Bad</script></h1>')
  r=sanews_article(h,URL,'2026-10-02T00:00:00Z','User-agent: *\nAllow: /',reviewed=True)
  self.assertEqual(r['title'],'South Africa trade talks')

 def test_unclosed_title_refused(self):
  with self.assertRaises(ValueError):sanews_article(HTML.replace('</h1>',''),URL,'2026-10-02T00:00:00Z','User-agent: *\nAllow: /',reviewed=True)
 def test_hidden_title_ancestors_refused(self):
  for opening,closing in [('<div hidden>','</div>'),('<div aria-hidden="true">','</div>'),('<nav>','</nav>')]:
   h=HTML.replace('<h1',opening+'<h1').replace('</h1>','</h1>'+closing)
   with self.assertRaises(ValueError):sanews_article(h,URL,'2026-10-02T00:00:00Z','User-agent: *\nAllow: /',reviewed=True)
 def test_hidden_body_paragraphs_excluded(self):
  h=HTML.replace('</p></article>','</p><p hidden>SECRET ONE</p><div aria-hidden="true"><p>SECRET TWO</p></div><p aria-hidden="true">SECRET THREE</p></article>')
  r=sanews_article(h,URL,'2026-10-02T00:00:00Z','User-agent: *\nAllow: /',reviewed=True);self.assertNotIn('SECRET',r['summary'])
 def test_metadata_title_required(self):
  h=HTML.replace('<meta property="og:title" content="South Africa trade talks">','')
  with self.assertRaises(ValueError):sanews_article(h,URL,'2026-10-02T00:00:00Z','User-agent: *\nAllow: /',reviewed=True)

 def test_multiple_sibling_article_roots_refused(self):
  h=HTML+'<article class="node-detail"><p>UNRELATED SECOND ROOT</p></article>'
  with self.assertRaises(ValueError):sanews_article(h,URL,'2026-10-02T00:00:00Z','User-agent: *\nAllow: /',reviewed=True)
 def test_hidden_void_does_not_hide_following_text(self):
  for void in ['<img hidden>','<input hidden/>','<br aria-hidden="TRUE">']:
   h=HTML.replace('</p></article>','</p>'+void+'<p>VISIBLE FOLLOWING PARAGRAPH</p></article>')
   r=sanews_article(h,URL,'2026-10-02T00:00:00Z','User-agent: *\nAllow: /',reviewed=True)
   self.assertIn('VISIBLE FOLLOWING PARAGRAPH',r['summary']);self.assertFalse(r['body_truncated'])
 def test_uppercase_aria_hidden_suppressed(self):
  h=HTML.replace('</p></article>','</p><p aria-hidden="TRUE">SECRET</p></article>')
  r=sanews_article(h,URL,'2026-10-02T00:00:00Z','User-agent: *\nAllow: /',reviewed=True);self.assertNotIn('SECRET',r['summary'])

 def test_unclosed_hidden_container_refused(self):
  for hidden in ['<div hidden><p>SEC</div><p>VIS</p>','<ul hidden><li>SEC</ul><p>VIS</p>']:
   h=HTML.replace('</p></article>','</p>'+hidden+'</article>')
   with self.assertRaises(ValueError):sanews_article(h,URL,'2026-10-02T00:00:00Z','User-agent: *\nAllow: /',reviewed=True)
