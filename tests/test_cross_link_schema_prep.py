import unittest
from unittest.mock import patch
from integration.cross_link_schema_prep import *
class Tests(unittest.TestCase):
 def test_relative_registered_GET(self):
  for node in ('workspace','countries','map'):self.assertEqual(link(node,{})['url'],REGISTRY[node][0])
  for node in ('https://evil','//evil','/workspace','unknown'):
   with self.assertRaises(Refused):link(node,{})
  for method in ('POST','PUT','DELETE','HEAD','OPTIONS'):
   with self.assertRaises(Refused):link('workspace',{},method=method)
 def test_extra_private_not_echoed(self):
  for key in ['question','tabs','notes','account','keys','token','url','origin','password','saved_tabs']:
   with self.assertRaises(Refused)as exc:link('workspace',{key:'PRIVATE_SECRET'})
   self.assertNotIn('PRIVATE',str(exc.exception));self.assertNotIn(key,str(exc.exception))
 def test_plain_types_and_exact_fields(self):
  for params in [[],None,{'system':0,'code':'8517'},{'system':'0'},{'system':'0','code':'8517','extra':'x'}]:
   with self.assertRaises(Refused):link('code',params,verified_identity=True)
 def test_catalogue_requires_validation(self):
  for node in ('code','code_news'):
   with self.assertRaises(Refused):link(node,{'system':'HS','edition':'2022','code':'8517'})
  self.assertEqual(link('code',{'system':'HS','edition':'2022','code':'8517'},verified_identity=True)['url'],'/workspace/finder/offline.html#code=0:8517')
 def test_field_100_boundary(self):
  p={'system':'HS','code':'8517','edition':'x'*100};self.assertEqual(link('code_news',p,verified_identity=True)['state'],'ready')
  p['edition']+='x'
  with self.assertRaises(Refused):link('code_news',p,verified_identity=True)
 def test_encoding_querycap(self):
  # Temporary fixture registry isolates query-byte boundary from field schema.
  schema={str(i):r'.{1,100}'for i in range(6)}
  with patch.dict(REGISTRY,{'fixture':('/workspace/fixture',schema)}):
   p={str(i):'a'*80 for i in range(6)};self.assertLessEqual(len(link('fixture',p)['url'].split('?')[1].encode()),512)
   p={str(i):'a'*100 for i in range(6)}
   with self.assertRaises(Refused):link('fixture',p)
   p={str(i):'x'for i in range(6)};p['0']='&< >'
   url=link('fixture',p)['url'];self.assertIn('%26%3C+%3E',url);self.assertNotIn('<',url)
 def test_ephemeral_news(self):
  p={'capability':'A'*43}
  self.assertEqual(link('news_context',p,now=0,expires_at=1)['state'],'ready')
  for expiry in [None,0,-1]:
   out=link('news_context',p,now=0,expires_at=expiry);self.assertIsNone(out['url']);self.assertEqual(out['message'],'Refresh news to open this context')
 def test_capability_format_noMongoID(self):
  for capability in ['x'*42,'x'*44,'507f1f77bcf86cd799439011','x'*42+'?']:
   with self.assertRaises(Refused):link('news_context',{'capability':capability},expires_at=1)
 def test_unavailable_no_broken_href(self):
  for node,p in [('workspace',{}),('code',{'system':'HS','edition':'2022','code':'8517'}),('code_news',{'system':'HS','edition':'2022','code':'8517'})]:
   out=view(node,p,verified_identity=True);self.assertIsNone(out['url']);self.assertEqual(out['state'],'unavailable')
 def test_country_not_relevance(self):
  with self.assertRaises(Refused):link('code_news',{'system':'HS','edition':'2022','code':'8517','country':'IN'},verified_identity=True)
 def test_cross_surface_identity_adapter(self):
  from urllib.parse import urlsplit,parse_qs
  context={'system':'HS','edition':'2022','code':'8517'}
  code=link('code',context,verified_identity=True)['url'];news=link('code_news',context,verified_identity=True)['url']
  self.assertEqual(code,'/workspace/finder/offline.html#code=0:8517')
  self.assertEqual(urlsplit(news).path,'/api/code-news-context')
  self.assertEqual(parse_qs(urlsplit(news).query),{'query':['8517'],'system':['HS'],'edition':['2022']})
  context['system']='IN';self.assertIn('#code=1:8517',link('code',context,verified_identity=True)['url'])
 def test_double_slash_registry_refused(self):
  with patch.dict(REGISTRY,{'bad':('//evil',{})}):
   with self.assertRaises(Refused):link('bad',{})
 def test_unmapped_system_clean_refused(self):
  with self.assertRaises(Refused):link('code',{'system':'US','edition':'2026','code':'8517'},verified_identity=True)
if __name__=='__main__':unittest.main()
