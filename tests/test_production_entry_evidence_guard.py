"""Missing runtime evidence refuses before importing the collector HTTP stack."""
import builtins
import unittest
from unittest.mock import patch
from integration.collector197_runtime_evidence import EvidenceRefused
from production_entry import build_production_app

class ProductionEvidenceGuardTests(unittest.TestCase):
    def test_none_evidence_refuses_before_collector_http_import(self):
        original_import = builtins.__import__
        touched = []
        def import_trap(name, *args, **kwargs):
            if name in ('integration.collector197_http', 'integration.collector197_dispatcher'):
                touched.append(name)
                raise AssertionError('collector stack imported without evidence')
            return original_import(name, *args, **kwargs)
        def public_builder(_):
            self.fail('public builder touched before evidence refusal')
        def client_factory(_):
            self.fail('client factory touched before evidence refusal')
        with patch('builtins.__import__', side_effect=import_trap):
            with self.assertRaises(EvidenceRefused):
                build_production_app({'COLLECTION_ENABLED':'true'}, public_builder,
                                     runtime_evidence=None, collector_client_factory=client_factory)
        self.assertEqual(touched, [])

if __name__ == '__main__':
    unittest.main()
