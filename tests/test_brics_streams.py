import unittest
from integration.brics_streams import FixtureStreams,video_id
from integration.news_api import create_app
class BricsStreamsTests(unittest.TestCase):
 def test_original_mutation_semantics_fixture(self):
  f=FixtureStreams([]);r=f.add(' Test ','India','https://youtu.be/abcdefghijk');self.assertEqual(r['name'],'Test');self.assertIn('youtube-nocookie',r['embed_url'])
  with self.assertRaises(ValueError):f.add('test','India','abcdefghijk')
  copy=f.load();copy.clear();self.assertEqual(len(f.load()),1);self.assertTrue(f.remove(' TEST '));self.assertFalse(f.remove('test'))
 def test_url_forms_and_rejections(self):
  for url in ['abcdefghijk','https://www.youtube.com/watch?v=abcdefghijk','https://youtu.be/abcdefghijk','https://youtube.com/live/abcdefghijk','https://www.youtube.com/embed/abcdefghijk']:self.assertEqual(video_id(url),'abcdefghijk')
  for url in ['any','javascript:abcdefghijk','https://evil.com/watch?v=abcdefghijk','https://youtu.be/abcdefghijk?secret=x','https://youtube.com/watch?v=abcdefghijk&v=abcdefghijk','https://youtube.com/x/live/abcdefghijk']:self.assertIsNone(video_id(url))
 def test_guard_crud_and_unwired(self):
  c=create_app().test_client();self.assertEqual(c.get('/api/brics/streams').status_code,403)
  c=create_app(authorize=lambda r:True).test_client();self.assertEqual(c.get('/api/brics/streams').status_code,503)
  c=create_app(authorize=lambda r:True,brics_stream_fixture=FixtureStreams([]),allowed_origin='http://localhost').test_client()
  self.assertEqual(c.post('/api/brics/streams',json={'name':'x','link':'abcdefghijk'}).status_code,403)
  self.assertEqual(c.delete('/api/brics/streams',json={'name':'x'}).status_code,403)
  h={'Origin':'http://localhost'};self.assertEqual(c.post('/api/brics/streams',headers=h,json={'name':'x','link':'abcdefghijk'}).status_code,200)
  self.assertFalse(c.get('/api/brics/streams').json['persistence']);self.assertEqual(c.delete('/api/brics/streams',headers=h,json={'name':'x'}).status_code,200);self.assertEqual(c.delete('/api/brics/streams',headers=h,json={'name':'x'}).status_code,404)

 def test_bad_rows_and_labels(self):
  for rows in [[None],[{'name':'x','country':'India','type':'channel','channel_id':None}],[{'name':'\u200bx','country':'India','type':'video','video_id':'abcdefghijk'}],[{'name':'\u2800','country':'India','type':'video','video_id':'abcdefghijk'}]]:
   with self.assertRaises(ValueError):FixtureStreams(rows)

 def test_review_casefold_countries_scalars_and_names(self):
  f=FixtureStreams([]);f.add('Straße',None,'abcdefghijk')
  with self.assertRaises(ValueError):f.add('STRASSE','India','abcdefghijk')
  self.assertTrue(f.remove('STRASSE'))
  for country in [None,'','   ']:self.assertEqual(FixtureStreams([]).add('x',country,'abcdefghijk')['country'],'Custom')
  for country in [[],{},1,True]:
   with self.assertRaises(ValueError):FixtureStreams([]).add('x',country,'abcdefghijk')
  for url in ['https://youtube.com/live/unexpected/abcdefghijk','https://youtube.com/embed/a/b/abcdefghijk','https://you\ntube.com/watch?v=abcdefghijk','https://youtube.com/watch?v=abc\tdefghijk','https://youtu.be/watch?v=abcdefghijk',' https://youtu.be/abcdefghijk']:
   self.assertIsNone(video_id(url),url)
  for name in ['.','..','/leading','slash/a','percent%','what?','hash#','தமிழ்']:
   c=create_app(authorize=lambda r:True,brics_stream_fixture=FixtureStreams([]),allowed_origin='http://localhost').test_client();h={'Origin':'http://localhost'}
   self.assertEqual(c.post('/api/brics/streams',headers=h,json={'name':name,'link':'abcdefghijk'}).status_code,200,name)
   self.assertEqual(c.delete('/api/brics/streams',headers=h,json={'name':name}).status_code,200,name)
 def test_canonical_origin_not_host(self):
  c=create_app(authorize=lambda r:True,brics_stream_fixture=FixtureStreams([]),allowed_origin='https://preview.example').test_client()
  r=c.post('/api/brics/streams',base_url='https://evil.example',headers={'Origin':'https://evil.example'},json={'name':'x','link':'abcdefghijk'});self.assertEqual(r.status_code,403)
  with self.assertRaises(ValueError):create_app(brics_stream_fixture=FixtureStreams([]))

 def test_body_bound_before_parse(self):
  c=create_app(authorize=lambda r:True,brics_stream_fixture=FixtureStreams([]),allowed_origin='http://localhost').test_client();h={'Origin':'http://localhost'}
  for method in ['post','delete']:
   call=getattr(c,method)
   self.assertEqual(call('/api/brics/streams',headers=h,data='{}',content_type='text/plain').status_code,415)
   self.assertEqual(call('/api/brics/streams',headers=h,data='x'*4097,content_type='application/json').status_code,413)
   self.assertEqual(call('/api/brics/streams',headers=h,content_type='application/json',environ_overrides={'CONTENT_LENGTH':''}).status_code,413)

 def test_final_small_review_items(self):
  f=FixtureStreams([{'name':'channel','type':'channel','channel_id':'UC'+'a'*22,'video_id':{'nested':['bad']}}]);self.assertNotIn('video_id',f.load()[0])
  self.assertIsNone(video_id('https://youtube.com/watch?v=abcdefghijk&&'))
  for origin in ['null','https://preview.example/path','https://preview.example?x=y','https://preview.example#x']:
   with self.assertRaises(ValueError):create_app(brics_stream_fixture=FixtureStreams([]),allowed_origin=origin)
  f=FixtureStreams([]);c=create_app(authorize=lambda r:True,brics_stream_fixture=f,allowed_origin='http://localhost').test_client();h={'Origin':'http://localhost'}
  for body in ['{','[]','null','{"name":null}','{"name":{}}','{"name":""}','{"name":"x","name":"y"}']:
   self.assertEqual(c.delete('/api/brics/streams',headers=h,content_type='application/json',data=body).status_code,400,body)
  self.assertEqual(c.delete('/api/brics/streams',headers={'Origin':'https://evil.example'},json={'name':'x'}).status_code,403)
  self.assertEqual(c.post('/api/brics/streams',headers=h,data='{}',content_type='application/foo+json').status_code,415);self.assertEqual(f.load(),[])
