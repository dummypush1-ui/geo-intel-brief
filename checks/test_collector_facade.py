import ast, importlib, sys, unittest
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import collector


class CollectorFacadeTests(unittest.TestCase):
    def test_reexports_are_the_stage_objects(self):
        pairs = {
            'select_installed_source': 'collector130_prep.network_selection',
            'compile_installed_profile': 'collector130_prep.extra_profile',
            'compile_profile': 'collector130_prep.base_profile',
            'run_fetch': 'collector124_prep.runner',
            'parse_supplied_bytes': 'collector128_prep.parser_runner',
            'prepare_supplied_feed': 'collector129_prep.supplied_feed',
            'capture': 'collector110_prep.input_budget',
            'endpoint_plan': 'collector113_prep.transport_policy',
            'original_catalog': 'collector113_prep.feed_composition',
        }
        for name, mod in pairs.items():
            self.assertIs(getattr(collector, name), getattr(importlib.import_module(mod), name), name)
        for name in collector.__all__:
            self.assertTrue(hasattr(collector, name), name)

    def test_chain_covers_stage130_imports(self):
        # Every collector1NN import reachable from stage 130 sources must be a chain module
        # (stage 109/110 helpers excepted: only the names re-exported above are in scope).
        listed = set(collector.CHAIN_MODULES)
        for f in (ROOT / 'collector130_prep').glob('*.py'):
            if f.name.startswith('test_'):
                continue
            for n in ast.walk(ast.parse(f.read_text())):
                if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith('collector1') and n.level == 0:
                    if n.module == 'collector109_prep.fetch_stage':
                        continue
                    self.assertIn(n.module, listed, f.name)

    def test_unchanged_refusals_through_facade(self):
        clock = datetime(2026, 10, 8, tzinfo=timezone.utc)
        with self.assertRaises(collector.SelectionRefused):
            collector.select_installed_source({}, 'https://example.invalid/none', clock=clock)
        with self.assertRaises(collector.ProfileRefused):
            collector.compile_profile({'UNKNOWN': 'x'})
        with self.assertRaises(collector.SelectionRefused):
            collector.select_installed_source({}, 'x', clock='not a clock')


if __name__ == '__main__':
    unittest.main()
