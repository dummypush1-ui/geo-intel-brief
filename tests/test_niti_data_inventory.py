# Copyright (c) 2026 Push. All rights reserved.
import ast
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    'integration/india_open_data/__init__.py',
    'integration/india_open_data/core.py',
    'integration/india_open_data/transport.py',
    'integration/india_open_data/data_layer.py',
    'integration/india_open_data/README.md',
    'integration/india_open_data/SOURCES.md',
    'tests/india_open_data/__init__.py',
    'tests/india_open_data/fixtures.py',
    'tests/india_open_data/test_core.py',
    'tests/india_open_data/test_data_layer.py',
    'tests/india_open_data/test_transport.py',
}
EXCLUDED = [
    'tests/india_open_data/__init__.py',
    'tests/india_open_data/fixtures.py',
    'tests/india_open_data/test_core.py',
    'tests/india_open_data/test_data_layer.py',
    'tests/india_open_data/test_transport.py',
    'tests/test_niti_data_inventory.py',
]


class InventoryTests(unittest.TestCase):
    def test_exact_paths_and_hashes(self):
        inv = json.loads((ROOT/'integration/india_open_data/inventory.json').read_text())
        self.assertEqual(set(inv['files']), EXPECTED)
        self.assertEqual(inv['historical87_excluded_exact'], EXCLUDED)
        for path, digest in inv['files'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), digest)

    def test_ast_no_new_third_party_imports(self):
        import sys
        for path in EXPECTED:
            if not path.endswith('.py'): continue
            tree=ast.parse((ROOT/path).read_text())
            for node in ast.walk(tree):
                if isinstance(node,ast.Import):
                    for name in node.names:
                        self.assertIn(name.name.split('.')[0],sys.stdlib_module_names)
                if isinstance(node,ast.ImportFrom) and not node.level:
                    self.assertIn(node.module.split('.')[0],set(sys.stdlib_module_names)|{'integration','tests'})

if __name__=='__main__':unittest.main()
