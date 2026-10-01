import unittest
from integration.news_view import views
from integration.news_api import create_app
from integration.story_links import groups,possible_related
from integration.relevance import match
from integration.finder_links import finder_link
from integration.site_scraper import collect_site
ROWS={'geo':[{'_id':'old','title':'India tariff news HS 22029921','url':'https://example.invalid/a','summary':'protein powder trade','category':'TRADE','country':'India','emailed':True,'published':None,'created_at':'2026-10-01T12:00:00Z'}],'brics':[{'id':'hash','title':'India tariff news HS 22029921','url':'https://example.invalid/a','category':'GEOPOLITICS','country':'Russia','emailed':False,'collected_at':'2026-10-01T12:00:00'}]}
class BridgeTests(unittest.TestCase):
 def test_same_story_profiles_intact(self):
  rows=views(ROWS);self.assertEqual(len(groups(rows)),1);self.assertEqual({r['category'] for r in rows},{'TRADE','GEOPOLITICS'});self.assertTrue(rows[0]['emailed']);self.assertIsNone(rows[0]['published_at'])
 def test_no_original_rewrite(self):
  views(ROWS);self.assertNotIn('project',ROWS['geo'][0])
 def test_country_mention_not_publisher(self):
  self.assertEqual(match({'country':'RU'},views(ROWS)[1])['reasons'],[])
 def test_explicit_code_only(self):
  self.assertTrue(match({'code':'22029921','system':'IN','edition':'2026'},views(ROWS)[0])['precise'])
  self.assertFalse(match({'code':'22029921'},{'title':'Order number 22029921','summary':''})['precise'])
 def test_never_tariff_proof(self):self.assertFalse(match({'code':'22029921'},views(ROWS)[0])['duty_change_verified'])
 def test_product_boundary(self):self.assertEqual(match({'product_terms':['rice']},{'title':'price rise'})['reasons'],[])
 def test_link_requires_verified_index(self):
  self.assertIsNone(finder_link('https://finder-hsn-codee.onrender.com',1,2))
  self.assertEqual(finder_link('https://finder-hsn-codee.onrender.com',1,2,True),'https://finder-hsn-codee.onrender.com/#code=1:2')
 def test_default_access_closed(self):
  c=create_app(lambda:ROWS).test_client();self.assertEqual(c.get('/api/news').status_code,403)
  for route in ['/collect','/send-digest','/cleanup-old','/mark-emailed']:self.assertEqual(c.post(route).status_code,403)
 def test_fixture_authorized_search(self):
  c=create_app(lambda:ROWS,lambda r:True).test_client();self.assertEqual(len(c.get('/api/news?q=India').json['items']),2)
  self.assertEqual(len(c.post('/api/related-news',headers={'Origin':'http://localhost'},json={'country':'India'}).json['items']),2)
 def test_bad_context(self):
  c=create_app(lambda:ROWS,lambda r:True).test_client();self.assertEqual(c.post('/api/related-news',headers={'Origin':'http://localhost'},json={'product_terms':'x'}).status_code,400)
 def test_scraper_off(self):self.assertEqual(collect_site('anything')['state'],'disabled')
 def test_no_unsafe_urls(self):self.assertEqual(views({'geo':[{'title':'x','url':'javascript:alert(1)'}]}),[])
