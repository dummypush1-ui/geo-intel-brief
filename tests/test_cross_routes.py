import unittest
import hashlib
from integration.news_api import create_app
class CrossRouteTests(unittest.TestCase):
 def app(self,index=None):
  return create_app(reader=lambda:{'geo':[{'_id':'1','url':'https://example.com/a','title':'HS 123456 trade'}],'brics':[{'id':'1','url':'https://example.com/a','title':'BRICS story'}]},authorize=lambda r:True,finder_context_reader=index,finder_base='http://localhost/workspace/finder/index.html',finder_index_verified=True).test_client()
 def test_same_story_keeps_profiles(self):
  d=self.app().get('/api/story-groups').json;self.assertEqual(len(d['items']),1);self.assertEqual(len(d['items'][0]['profiles']),2)
 def test_reverse_exact_identity(self):
  d=self.app(lambda article:[{'code':'123456','system':'IN','system_index':0,'index_verified':True}]).post('/api/finder-context',headers={'Origin':'http://localhost'},json={'project':'geo','article_key':hashlib.sha256(b'geo\nhttps://example.com/a').hexdigest()}).json
  self.assertEqual(d['items'][0]['finder_url'],'http://localhost/workspace/finder/index.html#code=0:123456');self.assertFalse(d['items'][0]['match']['duty_change_verified'])
 def test_no_fabricated_index(self):
  d=self.app().post('/api/finder-context',headers={'Origin':'http://localhost'},json={'project':'geo','article_key':hashlib.sha256(b'geo\nhttps://example.com/a').hexdigest()}).json;self.assertEqual(d['items'],[])
 def test_guarded_and_bad_identity(self):
  self.assertEqual(create_app().test_client().get('/api/story-groups').status_code,403)
  self.assertEqual(self.app().post('/api/finder-context',headers={'Origin':'http://localhost'},json={'article_key':hashlib.sha256(b'geo\nhttps://example.com/a').hexdigest()}).status_code,400)
