import hashlib, json, sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from source_drift import drift_report


class SourceDriftTests(unittest.TestCase):
    def test_repo_manifest_matches_tree(self):
        rep = drift_report()
        self.assertEqual(rep['missing'], [])
        self.assertEqual(rep['local_drift'], [])
        self.assertEqual(rep['total'], len(json.loads((ROOT / 'preservation-manifest.json').read_text())['source_files']))
        self.assertGreater(rep['total'], 0)
        self.assertTrue(rep['ok'])

    def _tmp(self, body=b'x'):
        d = Path(tempfile.mkdtemp())
        (d / 'a.py').write_bytes(body)
        h = hashlib.sha256(b'x').hexdigest()
        m = {'source_files': [{'source_repo': 'geonews', 'source_path': 'a.py', 'path': 'a.py',
                               'source_sha256': h, 'sha256': h, 'changes': []}]}
        return d, m, h

    def test_detects_local_edit_and_missing(self):
        d, m, _ = self._tmp(b'edited')
        self.assertEqual(drift_report(d, m)['local_drift'], ['a.py'])
        (d / 'a.py').unlink()
        self.assertEqual(drift_report(d, m)['missing'], ['a.py'])

    def test_upstream_drift_only_when_supplied(self):
        d, m, h = self._tmp()
        self.assertFalse(drift_report(d, m)['upstream_checked'])
        self.assertEqual(drift_report(d, m, {'geonews/a.py': h})['upstream_drift'], [])
        r = drift_report(d, m, {'geonews/a.py': 'f' * 64})
        self.assertEqual(r['upstream_drift'], ['geonews/a.py']); self.assertFalse(r['ok'])
        self.assertEqual(drift_report(d, m, {})['upstream_unknown'], ['geonews/a.py'])


if __name__ == '__main__':
    unittest.main()
