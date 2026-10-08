"""No live routes, storage or senders: legacy safety boundaries with fakes."""
import ast
import importlib
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]

class LegacyGeoP0(unittest.TestCase):
    def setUp(self):
        self.web = importlib.import_module('intelligence.geo.web')
        self.client = self.web.app.test_client()
        self.web._db_ready = False

    def test_health_no_storage(self):
        with patch.object(self.web, '_service', side_effect=AssertionError('service loaded')):
            self.assertEqual(self.client.get('/health').status_code, 200)

    def test_protected_route_inventory_denies_before_services(self):
        routes = [r for r in self.web.app.url_map.iter_rules() if r.endpoint not in ('health','static')]
        self.assertEqual(len(routes), 10)
        for secret in ('', ' ', 'known'):
            with patch.object(self.web, 'TRIGGER_SECRET', secret), patch.object(self.web, '_service', side_effect=AssertionError('service loaded')):
                for rule in routes:
                    method = 'post' if 'POST' in rule.methods else 'get'
                    self.assertEqual(getattr(self.client, method)(rule.rule).status_code, 401, rule.rule)

    def test_wrong_header_and_query_denied(self):
        with patch.object(self.web, 'TRIGGER_SECRET', 'known'), patch.object(self.web, '_service', side_effect=AssertionError('service loaded')):
            for headers, suffix in [({'X-Trigger-Secret':'bad'},''), ({},'?key=known'), ({'X-Trigger-Secret':'known'},'?key=known')]:
                self.assertEqual(self.client.get('/digest-data'+suffix, headers=headers).status_code, 401)

    def test_correct_header_status_no_service(self):
        with patch.object(self.web, 'TRIGGER_SECRET', 'known'), patch.object(self.web, '_service', side_effect=AssertionError('service loaded')):
            self.assertEqual(self.client.get('/collect-status', headers={'X-Trigger-Secret':'known'}).status_code,200)

    def test_mutation_get_removed(self):
        for path in ('/collect','/send-digest','/critical','/weekly','/cleanup-old'):
            self.assertEqual(self.client.get(path).status_code,405)

    def test_cleanup_never_reads_or_deletes(self):
        cleanup = importlib.import_module('intelligence.geo.reports.metadata_cleanup')
        for days in (None,0,1,999,'fabricated-complete-receipt'):
            self.assertEqual(cleanup.cleanup(days)['deleted'],0)
        with patch.object(self.web,'TRIGGER_SECRET','known'), patch.object(self.web,'ENABLE_METADATA_CLEANUP',True), patch.object(self.web,'_service',side_effect=AssertionError('service loaded')):
            r=self.client.post('/cleanup-old',headers={'X-Trigger-Secret':'known'})
            self.assertEqual(r.status_code,403)
            self.assertEqual(r.json['deleted'],0)

    def test_low_level_delete_cannot_bypass(self):
        tree=ast.parse((ROOT/'intelligence/geo/database.py').read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='delete_articles')
        scope={'connect':lambda: self.fail('storage touched')}
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'delete','exec'),scope)
        for ids in ([],['no-backup'],['partial'],['unknown'],['daemon-restart'],['all-piece-ack'],['fabricated-receipt']):
            with self.assertRaises(PermissionError):scope['delete_articles'](ids)

    def test_no_eager_service_imports_or_init(self):
        tree=ast.parse((ROOT/'intelligence/geo/web.py').read_text())
        for node in tree.body:
            if isinstance(node,ast.ImportFrom):
                self.assertNotIn(node.module, ['intelligence.geo.database','intelligence.geo.reports.email_report'])
            self.assertNotIsInstance(node,ast.Try)

    def test_web_config_missing_secret_rejected(self):
        check=importlib.import_module('intelligence.geo.config_check')
        with patch.object(check.cfg,'TRIGGER_SECRET',''),patch.object(check.cfg,'MONGODB_URI','fixture'),patch.object(check.cfg,'ENABLE_GNEWS',False),patch.object(check.cfg,'ENABLE_FULL_TEXT',False),patch.object(check.cfg,'ENABLE_METADATA_CLEANUP',False),patch.object(check.cfg,'ENABLE_WHATSAPP',False),patch.object(check.cfg,'ENABLE_TELEGRAM',False),patch.object(check.cfg,'ENABLE_TELEGRAM_BACKUP',False):
            self.assertFalse(check.check_config(require_email=False,require_web=True))
            self.assertTrue(check.check_config(require_email=False,require_web=False))
