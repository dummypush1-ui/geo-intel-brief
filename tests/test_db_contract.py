# Copyright (c) 2026 Push. All rights reserved.
import unittest
from integration.db_contract.plan import plan,retention_decision

MAPPING={'full_records':'fixture_full_records','collection_outbox':'fixture_outbox','collection_control':'fixture_control','backup_journal':'fixture_backup_journal'}


class Tests(unittest.TestCase):
    def test_roles_no_admin_or_delete(self):
        p=plan(MAPPING)
        for rows in p['roles'].values():
            for r in rows:
                self.assertEqual(r['resource']['db'],'geo_intel');self.assertTrue(r['resource']['collection']);self.assertTrue(set(r['actions']) <= {'find','insert','update'})
        self.assertEqual(p['inherited_roles'],[]);self.assertFalse(p['provision_allowed'])
    def test_public_articles_only(self):
        self.assertEqual(plan(MAPPING)['roles']['public_reader'],[{'resource':{'db':'geo_intel','collection':'articles'},'actions':['find']}])
    def test_mail_no_collection_send_journal(self):
        names={r['resource']['collection'] for r in plan(MAPPING)['roles']['mail_worker']}
        self.assertEqual(names,{'articles','events','mail_control','mail_receipts'})
    def test_backup_worker_no_article_access(self):
        names={r['resource']['collection'] for r in plan(MAPPING)['roles']['backup_journal_worker']}
        self.assertEqual(names,{MAPPING['full_records'],MAPPING['backup_journal'],MAPPING['collection_outbox']})
    def test_no_ttl_or_auto_delete(self):
        p=plan(MAPPING);self.assertEqual(p['ttl_indexes'],[]);self.assertFalse(p['automatic_deletion'])
        self.assertTrue(set(MAPPING.values()) <= set(p['no_ttl_resources']))
    def test_index_candidates_no_ttl(self):
        self.assertTrue(all('expireAfterSeconds' not in r['options'] for r in plan(MAPPING)['indexes']))
    def test_mapping_closed_and_distinct(self):
        for r in ({},dict(MAPPING,secret='x'),dict(MAPPING,full_records='articles'),dict(MAPPING,full_records='system_roles'),dict(MAPPING,full_records=MAPPING['collection_outbox'])):
            with self.assertRaises(ValueError):plan(r)
    def test_detached_mapping(self):
        p=plan(MAPPING);p['mapping']['full_records']='changed';self.assertEqual(MAPPING['full_records'],'fixture_full_records')
    def test_pending_unknown_always_hold(self):
        for state in ('pending','started','unknown'):
            r={'state':state,'full_record_present':True,'all_pieces_authenticated':True,'unknown_send':False,'export_verified':True}
            self.assertEqual(retention_decision(r)['decision'],'hold')
    def test_terminal_only_review_not_delete(self):
        r={'state':'terminal','full_record_present':True,'all_pieces_authenticated':True,'unknown_send':False,'export_verified':True}
        p=retention_decision(r);self.assertEqual(p['decision'],'eligible_for_owner_retention_review');self.assertFalse(p['delete_allowed']);self.assertFalse(p['ttl_allowed'])
    def test_incomplete_or_unknown_hold(self):
        r={'state':'terminal','full_record_present':True,'all_pieces_authenticated':True,'unknown_send':False,'export_verified':True}
        for k in ('full_record_present','all_pieces_authenticated','export_verified','unknown_send'):
            changed=dict(r);changed[k]=not changed[k];self.assertEqual(retention_decision(changed)['decision'],'hold')
    def test_retention_closed_types(self):
        with self.assertRaises(ValueError):retention_decision({'state':'terminal','full_record_present':1,'all_pieces_authenticated':True,'unknown_send':False,'export_verified':True})
