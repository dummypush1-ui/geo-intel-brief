import unittest,json
from pathlib import Path
from integration.scraper_policy import can_fetch,response_policy,ArticleLinks
RULE={'url':'https://example.invalid/news/','name':'Fixture','country':'India','enabled':True,'reviewed':True,'article_path_prefix':'/news/story/'}
class ScraperTests(unittest.TestCase):
 def test_policy_denies_unreviewed(self):self.assertFalse(can_fetch({**RULE,'reviewed':False},'https://example.invalid/news/story/1','User-agent: *\nAllow: /'))
 def test_robots_denied(self):self.assertFalse(can_fetch(RULE,'https://example.invalid/news/story/1','User-agent: *\nDisallow: /news/'))
 def test_unknown_robots_denied(self):self.assertFalse(can_fetch(RULE,'https://example.invalid/news/story/1',None))
 def test_cross_site_denied(self):self.assertFalse(can_fetch(RULE,'https://attacker.invalid/news/story/1','User-agent: *\nAllow: /'))
 def test_challenge_rate_stop(self):
  for status in [401,403,429]:self.assertEqual(response_policy(status,'text/html','x')['state'],'stopped')
  self.assertEqual(response_policy(200,'text/html','Verify you are human')['state'],'stopped')
 def test_fixture_articles_not_homepages(self):
  parser=ArticleLinks();parser.feed('<a href="/">Homepage news title</a><a href="/news/story/1">India announces trade talks</a><a href="/news/story/1">Duplicate long title</a><a href="javascript:alert(1)">Unsafe long title</a>')
  rows=parser.articles(RULE,'User-agent: *\nAllow: /');self.assertEqual(len(rows),1);self.assertEqual(rows[0]['title'],'India announces trade talks');self.assertEqual(rows[0]['published'],'')
 def test_all_site_configs_off(self):
  rules=json.loads((Path(__file__).resolve().parents[1]/'integration/scraper_rules.json').read_text());self.assertFalse(rules['enabled']);self.assertEqual(len(rules['sites']),10);self.assertTrue(all(not r['enabled'] and not r['reviewed'] for r in rules['sites']))
