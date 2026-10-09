import unittest,copy
from integration.native200_owner_package import owner_package
from integration.native200_admission_preflight import VALIDATORS
from integration.native200_store import NAMES
from integration.replay199_schema import source,validate_manifest
class Tests(unittest.TestCase):
 def test_exact_schema_role_readonly_commands(self):
  p=owner_package(fingerprint='a'*64,clock=100);self.assertFalse(p['ready']);self.assertEqual(len(p['schema_requests']),8)
  for r in p['schema_requests']:self.assertEqual(r['modify_if_existing_owner_reviewed']['validator'],VALIDATORS[r['collection']]);self.assertEqual(r['create_if_verified_absent']['validator'],VALIDATORS[r['collection']])
  role=p['role'];self.assertEqual(role['inheritedRoles'],[]);self.assertEqual({a['action']for a in role['actions']},{'FIND','INSERT','UPDATE','LIST_INDEXES','LIST_COLLECTIONS'})
  for a in role['actions']:
   if a['action']!='LIST_COLLECTIONS':self.assertEqual({r['collection']for r in a['resources']},NAMES)
  self.assertEqual(len(p['readonly_verification_commands']),16)
 def test_genesis_templates_valid_newempty_only(self):
  p=owner_package(fingerprint='a'*64,clock=100);rows=p['empty_new_genesis_templates'];self.assertEqual(len(rows),6)
  for r in rows:
   d=r['empty_new_install_only']
   if r['collection']=='collector_jobs197':source('collector',d,'a'*64)
   elif r['collection']=='finder_budget198':source('broker',d)
   elif 'replay199'in r['collection']:validate_manifest(d['family'],d)
   else:self.assertEqual(d['serial'],0);self.assertEqual(d['phase'],'idle')
 def test_invalid_scope_no_sideeffects_or_sharedmutable_data(self):
  for f,c in [('bad',100),('a'*64,True),('a'*64,-1)]:
   with self.assertRaises(ValueError):owner_package(fingerprint=f,clock=c)
  p=owner_package(fingerprint='a'*64,clock=100);p['schema_requests'][0]['create_if_verified_absent']['validator'].clear();self.assertTrue(owner_package(fingerprint='a'*64,clock=100)['schema_requests'][0]['create_if_verified_absent']['validator'])
 def test_honest_no_creation_no_reset_no_activation(self):
  p=owner_package(fingerprint='a'*64,clock=100);text=' '.join(p['mandatory_holds']);self.assertIn('INSERT itself',text);self.assertIn('ONE-write',text);self.assertIn('NO genesis',text);self.assertIn('NO activation',text)
