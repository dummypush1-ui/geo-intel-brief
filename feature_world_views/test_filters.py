# Copyright (c) 2026 Push. All rights reserved.
import unittest
from werkzeug.datastructures import MultiDict
from .model import snapshot
from .filters import apply_filters
from .fixtures import RAW, INDEX
from .fixtures import app

class FilterTests(unittest.TestCase):
 def test_combined_exact_filters(self):
  data=apply_filters(snapshot(RAW, INDEX), {'country':'India','category':'TRADE','q':'coffee','code':'090111','project':'geo'})
  self.assertEqual(data['count'],1)
  self.assertEqual(data['options']['original_country'],['India'])
 def test_zero_and_reset(self):
  data=snapshot(RAW,INDEX)
  self.assertEqual(apply_filters(data,{'country':'india'})['count'],0)
  self.assertEqual(apply_filters(data,{'code':'0901'})['count'],0)
  self.assertEqual(apply_filters(data,{})['count'],1)
 def test_validation(self):
  for args in ({'q':'x'*201},{'q':'\x00'},{'code':'９０１１'},{'code':'1'},{'project':'other'},{'other':'x'},MultiDict([('q','a'),('q','b')])):
   with self.assertRaises(ValueError): apply_filters(snapshot(RAW), args)
 def test_optional_fields_and_validate_before_read(self):
  data={'items':[{'title':'coffee','summary':None,'source':None,'original_country':None}], 'count':1}
  self.assertEqual(apply_filters(data,{'q':'coffee'})['count'],1)
  def fail(): raise AssertionError('Must not read')
  client=app(reader=fail)
  for path in ('/data?unknown=x','/export.csv?q=x&q=y'):
   self.assertEqual(client.get('/workspace/world'+path).status_code,400)
 def test_route(self):
  client=app()
  self.assertEqual(client.get('/workspace/world/data?country=India').json['count'],1)
  self.assertEqual(client.get('/workspace/world/data?q=x&q=y').status_code,400)
