# Copyright (c) 2026 Push. All rights reserved.
import unittest
from .detail import detail
from .model import snapshot
from .fixtures import RAW, INDEX
from .fixtures import app

class DetailTests(unittest.TestCase):
 def test_exact_key_and_absent(self):
  data=snapshot(RAW,INDEX);key=data['items'][0]['article_key']
  self.assertEqual(detail(data,key)['item']['title'],RAW['geo'][0]['title'])
  self.assertIsNone(detail(data,'a'*64))
  with self.assertRaises(ValueError): detail(data,'../../etc/passwd')
 def test_related_basis_and_private_boundary(self):
  rows={'geo':RAW['geo']+[dict(RAW['geo'][0],url='https://example.com/other',title='Other India story',summary='')]}
  data=snapshot(rows,INDEX); result=detail(data,data['items'][0]['article_key'])
  self.assertEqual(result['related'][0]['basis'],'exact_country_label')
  self.assertNotIn('PRIVATE',str(result))
 def test_route(self):
  c=app();key=c.get('/workspace/world/data').json['items'][0]['article_key']
  self.assertEqual(c.get('/workspace/world/article/'+key).status_code,200)
  self.assertEqual(c.get('/workspace/world/article/'+'a'*64).status_code,404)
  self.assertEqual(c.get('/workspace/world/article/invalid').status_code,400)
  self.assertEqual(c.get('/workspace/world/article/'+key+'?url=x').status_code,400)
