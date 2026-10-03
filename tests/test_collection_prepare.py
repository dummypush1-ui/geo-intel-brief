import unittest
from copy import deepcopy
from unittest.mock import patch
from integration.collection_prepare import prepare_candidates
CATS=['GEOPOLITICS','TRADE','SANCTIONS','RISK','CONFERENCE','GENERAL']
def row(title,source='Source',summary=''):
 return {'title':title,'url':'https://example.com/'+source,'source':source,'summary':summary}
class OfflineCollectionTests(unittest.TestCase):
 def test_geo_processing_without_network_store_or_delivery(self):
  rows=[row('Trade agreement and tariff notification','A','x'*400),row('Trade agreement and tariff notification','B','x'*400)];before=deepcopy(rows)
  with patch('socket.socket',side_effect=AssertionError('Network forbidden')):
   d=prepare_candidates('geo',rows,CATS,.85)
  self.assertEqual(rows,before);self.assertEqual(d['prepared_count'],1);self.assertEqual(d['items'][0]['corroboration'],2);self.assertEqual(len(d['items'][0]['summary']),300);self.assertFalse(d['writes']);self.assertNotIn('created_at',d['items'][0])
 def test_brics_order_corroboration_and_topic_filter(self):
  rows=[row('BRICS summit joint declaration','A'),row('BRICS summit joint declaration','B'),row('Local sports final results','C')];before=deepcopy(rows)
  with patch('socket.socket',side_effect=AssertionError('Network forbidden')):
   d=prepare_candidates('brics',rows,CATS,.8)
  self.assertEqual(d['deduped_count'],2);self.assertEqual(d['prepared_count'],1);self.assertEqual(d['items'][0]['corroborated_by'],['A','B']);self.assertEqual(rows,before);self.assertNotIn('collected_at',d['items'][0]);self.assertFalse(d['delivery'])
 def test_explicit_configuration_and_bounded_inputs(self):
  for project,rows,cats,threshold in [('all',[],CATS,.8),('geo',[{}],CATS,.8),('geo',[],[],.8),('geo',[],CATS,True),('geo',[],CATS,0),('geo',[row('x')]*1001,CATS,.8)]:
   with self.assertRaises(ValueError):prepare_candidates(project,rows,cats,threshold)
  self.assertEqual(prepare_candidates('geo',[],CATS,.85)['prepared_count'],0)

 def test_brics_does_not_import_config_or_read_environment(self):
  import subprocess,sys
  code="""
import builtins,os
original=builtins.__import__
def guarded(name,*a,**kw):
 if name.startswith('intelligence.brics') or name=='dotenv':raise AssertionError(name)
 return original(name,*a,**kw)
builtins.__import__=guarded
from integration.collection_prepare import prepare_candidates
prepare_candidates('brics',[{'title':'BRICS summit','url':'https://example.com','source':'x','summary':''}],['GEOPOLITICS'],.8)
assert 'intelligence.brics.config' not in __import__('sys').modules
"""
  subprocess.run([sys.executable,'-c',code],check=True)
