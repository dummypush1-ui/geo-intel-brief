import ast
import copy
import hashlib
import json
from pathlib import Path
import socket
import unittest
from unittest.mock import patch
from integration import existing_schema215 as seam
from integration.native200_admission_preflight import VALIDATORS
from integration.native200_store import NAMES

HASHES = {
 'collector_checkpoints197': '30418819366c57ff94022a9c48a1f523d04657734742f33b4e83829ea1b32908',
 'collector_jobs197': '469c79d19b97ca62de7fd95e08bc389bbaec0859aea25a8956c3e0721dd7efc0',
 'collector_replay199': '69ebd996c2e89f48663b989a347f52bc119ad83b38612d76764d28a04ff63ac1',
 'finder_budget198': '94a4784b713672d2bac75935c8f195a76d1ca92d08c15389a00af112d3a38616',
 'finder_replay199': '69c63cc901f209064f29e4f8c330227abacc744d00d51bfedfa3b026e512d212',
 'native_guards200': '0da27ccab99710e2600bfa574803026f6d9849e96a54a1ada90cbd0e8f6aef3c',
 'native_operations200': 'ea886a74778e9249fb717db95068b870e20890eb973634895896d8d8c20ea410',
 'native_outcomes200': '8388ca6604731c32d858ac8467e54c64750a732dbf6b28c8fb885e510200cd7a',
}

def canonical(value):
 return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)

class Tests(unittest.TestCase):
 def test_exact_names_current_validator_hashes(self):
  self.assertEqual(set(HASHES), NAMES)
  self.assertEqual(set(HASHES), set(VALIDATORS))
  p=seam.optional_schema_review(validation_level='strict')
  rows=p['request_data_not_executable']
  self.assertEqual([r['collection_name'] for r in rows], sorted(HASHES))
  for r in rows:
   n=r['collection_name'];self.assertEqual(r['proposed_validator'],VALIDATORS[n])
   self.assertIsNot(r['proposed_validator'],VALIDATORS[n])
   self.assertEqual(hashlib.sha256(canonical(r['proposed_validator']).encode()).hexdigest(),HASHES[n])
 def test_explicit_validation_level_no_default(self):
  with self.assertRaises(TypeError):seam.optional_schema_review()
  class Text(str):pass
  for v in (None,True,1,{},Text('strict'),'STRICT','', 'warn'):
   with self.assertRaises(ValueError):seam.optional_schema_review(validation_level=v)
  for level in ('strict','moderate'):
   p=seam.optional_schema_review(validation_level=level)
   for r in p['request_data_not_executable']:
    self.assertEqual(r['validation_level_choice'],level)
    self.assertEqual(r['proposed_validation_action'],'error')
    self.assertEqual(r['proposed_write_concern_data'],{'w':'majority','j':True,'wtimeout':5000})
 def test_output_and_source_mutation_independent(self):
  source=copy.deepcopy(VALIDATORS);baseline=seam.optional_schema_review(validation_level='strict')
  p=seam.optional_schema_review(validation_level='strict');p['request_data_not_executable'][0]['proposed_validator'].clear()
  self.assertEqual(VALIDATORS,source)
  self.assertEqual(seam.optional_schema_review(validation_level='strict'),baseline)
  n=sorted(VALIDATORS)[0];original=VALIDATORS[n]
  try:
   VALIDATORS[n]={};self.assertEqual(seam.optional_schema_review(validation_level='strict'),baseline)
  finally:VALIDATORS[n]=original
  source[n].clear();self.assertEqual(seam.optional_schema_review(validation_level='strict'),baseline)
 def test_constant_missing_extra_held(self):
  for names in (seam._NAMES[:-1], seam._NAMES+('other',)):
   with patch.object(seam,'_NAMES',names):
    with self.assertRaises(ValueError):seam.optional_schema_review(validation_level='strict')
  for schemas in ({}, {**seam._SCHEMA,'other':{}}):
   with patch.object(seam,'_SCHEMA',schemas):
    with self.assertRaises(ValueError):seam.optional_schema_review(validation_level='strict')
 def test_plain_nonexecutable_data_only(self):
  p=seam.optional_schema_review(validation_level='moderate')
  self.assertEqual(set(p),{'state','ready','executable','live','collection_existence_verified','database','request_data_not_executable'})
  self.assertEqual(p['state'],'optional_review_data_only');self.assertEqual(p['database'],'geo_intel')
  for n in ('ready','executable','live','collection_existence_verified'):self.assertIs(p[n],False)
  prohibited={'collMod','create','insert','update','find','listCollections','listIndexes','genesis','empty_new_genesis_templates','role','upsert','writeConcern'}
  def walk(v):
   self.assertFalse(callable(v))
   self.assertIn(type(v),(dict,list,str,bool,int))
   if type(v)is dict:
    self.assertTrue(prohibited.isdisjoint(v))
    for child in v.values():walk(child)
   if type(v)is list:
    for child in v:walk(child)
  walk(p);self.assertEqual(json.loads(canonical(p)),p)
 def test_no_network_or_file_operations(self):
  with patch.object(socket,'socket',side_effect=AssertionError('socket')),patch('builtins.open',side_effect=AssertionError('open')),patch.object(Path,'open',side_effect=AssertionError('path open')),patch.object(Path,'write_text',side_effect=AssertionError('file write')),patch.object(Path,'write_bytes',side_effect=AssertionError('file write')):
   self.assertEqual(seam.optional_schema_review(validation_level='strict')['state'],'optional_review_data_only')
 def test_closed_ast_import_and_call_surface(self):
  tree=ast.parse(Path(seam.__file__).read_text())
  imports=[(n.module,tuple(a.name for a in n.names)) for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
  self.assertEqual(imports,[('copy',('deepcopy',)),('integration.native200_admission_preflight',('VALIDATORS',)),('integration.native200_store',('NAMES',))])
  self.assertFalse(any(isinstance(n,ast.Import) for n in ast.walk(tree)))
  names={n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
  self.assertEqual(names,{'deepcopy','tuple','sorted','type','ValueError'})
  self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) for n in ast.walk(tree)))
 def test_no_current_runtime_import_edge(self):
  root=Path(seam.__file__).parents[1]
  for parent in (root/'integration',root/'feature_mail_mount'):
   for p in parent.rglob('*.py'):
    if p.resolve()==Path(seam.__file__).resolve():continue
    tree=ast.parse(p.read_bytes())
    for node in ast.walk(tree):
     if isinstance(node,ast.ImportFrom):self.assertNotIn('existing_schema215',node.module or '',str(p))
     if isinstance(node,ast.Import):
      for a in node.names:self.assertNotIn('existing_schema215',a.name,str(p))
