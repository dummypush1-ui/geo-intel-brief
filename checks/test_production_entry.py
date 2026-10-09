import sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import production_entry as pe


class Fake:
    def __init__(self): self.extensions = {}


class ProductionEntryTests(unittest.TestCase):
    def test_import_builds_nothing(self):
        import subprocess
        code = 'import sys; import production_entry; sys.exit(1 if "public_live107" in sys.modules else 0)'
        r = subprocess.run([sys.executable, '-c', code], cwd=str(ROOT), capture_output=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_delegates_unchanged_and_records_components(self):
        seen = []
        env = {'PUBLIC_NEWS_READ_ENABLED': 'false'}
        app = pe.build_production_app(env, lambda e: (seen.append(e), Fake())[1])
        self.assertIs(seen[0], env)
        self.assertTrue(app.extensions['production_components']['collector']['wired'])
        geo = app.extensions['production_components']['geo_news_read']
        self.assertTrue(geo['wired'])
        self.assertEqual(geo['gate_state'], 'false')
        env2 = {'PUBLIC_NEWS_READ_ENABLED': 'true'}
        app2 = pe.build_production_app(env2, lambda e: Fake())
        self.assertEqual(app2.extensions['production_components']['geo_news_read']['gate_state'], 'true')
        self.assertEqual(app2.extensions['production_components']['collector']['gate_state'], 'false')

    def test_unwired_switches_fail_closed(self):
        for k in ('COLLECTION_ENABLED', 'MERGED_MAIL_ENABLED', 'SCRAPER_ENABLED'):
            with self.assertRaises(ValueError):
                pe.build_production_app({k: 'true'}, lambda e: Fake())
            pe.build_production_app({k: 'false'}, lambda e: Fake())

    def test_env_shape_checked(self):
        with self.assertRaises(ValueError):
            pe.build_production_app({'A': 1}, lambda e: Fake())


if __name__ == '__main__':
    unittest.main()
