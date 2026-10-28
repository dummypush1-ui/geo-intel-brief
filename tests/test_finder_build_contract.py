"""Contract checks for the generated hosted and offline Finder artifacts.

Run after `npm run build`. These checks catch stale/mismatched generated files
without changing source data or enabling any guarded integration.
"""
import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSIONED_DATA = re.compile(r"^data\.([0-9a-f]{12})\.js$")


class FinderBuildContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.offline = (ROOT / "offline.html").read_text(encoding="utf-8")
        cls.worker = (ROOT / "sw.js").read_text(encoding="utf-8")
        cls.data_files = sorted(
            path for path in ROOT.iterdir()
            if path.is_file() and VERSIONED_DATA.fullmatch(path.name)
        )

    def test_exactly_one_versioned_dataset_is_present(self):
        self.assertEqual(
            len(self.data_files), 1,
            "Build must leave exactly one current versioned data bundle",
        )

    def test_version_hash_matches_dataset_contents(self):
        data_path = self.data_files[0]
        match = VERSIONED_DATA.fullmatch(data_path.name)
        digest = hashlib.sha256(data_path.read_bytes()).hexdigest()[:12]
        self.assertEqual(match.group(1), digest)
        self.assertIn(f"./{data_path.name}", self.index)
        self.assertIn(f"./{data_path.name}", self.worker)
        self.assertIn(f"hsn-data-{digest}", self.worker)

    def test_hosted_and_offline_outputs_share_app_and_data(self):
        data_path = self.data_files[0]
        data_text = data_path.read_text(encoding="utf-8")
        self.assertIn("function boot(", self.index)
        self.assertIn("function boot(", self.offline)
        self.assertIn(f"./{data_path.name}", self.index)
        self.assertNotIn("data.src =", self.offline)
        self.assertIn("var DATA_B64 =", self.offline)
        self.assertIn("var DATA_B64 =", data_text)

    def test_hosted_failure_state_and_offline_shell_exist(self):
        self.assertIn('id="root"', self.index)
        self.assertIn("Code data did not load", self.index)
        self.assertIn('id="root"', self.offline)
        self.assertIn("Worldwide HSN Code Finder", self.index)
        self.assertIn("Worldwide HSN Code Finder", self.offline)


if __name__ == "__main__":
    unittest.main()
