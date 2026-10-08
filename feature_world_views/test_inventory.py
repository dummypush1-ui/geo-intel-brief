# Copyright (c) 2026 Push. All rights reserved.
"""Current exact-path world inventory, separate from immutable historical87."""
import ast
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'feature_world_views'
EXCLUDED = ['feature_world_views/inventory.json', 'feature_world_views/test_inventory.py']


def ast_record(path):
    imports = set()
    dynamic = False
    for node in ast.walk(ast.parse(path.read_bytes())):
        if isinstance(node, ast.Import):
            imports.update(n.name for n in node.names)
        if isinstance(node, ast.ImportFrom):
            imports.add('.' * node.level + (node.module or ''))
        if isinstance(node, ast.Call) and (
            isinstance(node.func, ast.Name) and node.func.id == '__import__' or
            isinstance(node.func, ast.Attribute) and node.func.attr in ('import_module', 'spec_from_file_location')):
            dynamic = True
    return {'imports': sorted(imports), 'dynamic_import': dynamic}


class InventoryTests(unittest.TestCase):
    def test_exact_paths_hashes_and_ast(self):
        data = json.loads((PACKAGE / 'inventory.json').read_text())
        self.assertEqual(data['excluded_exact'], EXCLUDED)
        actual = sorted(str(p.relative_to(ROOT)) for p in PACKAGE.rglob('*')
                        if p.is_file() and '__pycache__' not in p.parts and str(p.relative_to(ROOT)) not in EXCLUDED)
        self.assertEqual(actual, [row['path'] for row in data['files']])
        python_paths = []
        for row in data['files']:
            path = ROOT / row['path']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row['sha256'], row['path'])
            self.assertEqual(path.stat().st_size, row['bytes'])
            if path.suffix == '.py':
                python_paths.append(row['path'])
                self.assertEqual(ast_record(path), row['ast'], row['path'])
        self.assertEqual(python_paths, data['python_paths_exact'])
        historical = json.loads((ROOT / 'integration/dependency_audit/import-inventory.json').read_text())
        baseline_paths = {row['path'] for row in historical['source_baseline']['files']}
        self.assertTrue(set(python_paths).isdisjoint(baseline_paths))
        self.assertNotIn('feature_world_views', historical['source_baseline']['scopes'])
        audit = json.loads((ROOT / 'integration/dependency_audit/audit.json').read_text())
        canonical = json.dumps(historical['source_baseline']['files'], sort_keys=True, separators=(',', ':')).encode()
        self.assertEqual(hashlib.sha256(canonical).hexdigest(), audit['source_manifest_sha256'])

if __name__ == '__main__':
    unittest.main()
