"""Fast, dependency-light contract tests for the production entry boundary.

These tests use an injected public builder so they do not need Flask, network
access, credentials, or a database. They verify default-off behavior and
fail-closed switch parsing without enabling optional integrations.
"""
from pathlib import Path
import sys
import unittest

# Running this file directly puts tests/ on sys.path, not the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from production_entry import build_production_app


class FakeApp:
    def __init__(self):
        self.extensions = {}
        self.wsgi_app = lambda environ, start_response: []


class ProductionEntryContractTests(unittest.TestCase):
    def setUp(self):
        self.app = FakeApp()
        self.received = {}

    def builder(self, environ, **bindings):
        self.received["environ"] = dict(environ)
        self.received["bindings"] = dict(bindings)
        return self.app

    def test_optional_components_are_off_by_default(self):
        app = build_production_app({}, self.builder)
        self.assertIs(app, self.app)
        components = app.extensions["production_components"]
        self.assertEqual(components["collector"]["gate_state"], "false")
        self.assertEqual(components["mail"]["gate_state"], "false")
        self.assertEqual(components["scraper"]["gate_state"], "false")
        self.assertEqual(self.received["environ"]["PUBLIC_NEWS_FULL_PAGES_ENABLED"], "false")
        self.assertEqual(self.received["environ"]["PUBLIC_NEWS_SEARCH_PROGRESS_ENABLED"], "false")

    def test_unwired_scraper_cannot_be_enabled(self):
        with self.assertRaisesRegex(ValueError, "not wired"):
            build_production_app({"SCRAPER_ENABLED": "true"}, self.builder)

    def test_collection_switch_requires_exact_boolean_text(self):
        with self.assertRaisesRegex(ValueError, "Exact collection switch"):
            build_production_app({"COLLECTION_ENABLED": "yes"}, self.builder)

    def test_mail_switch_requires_exact_boolean_text(self):
        with self.assertRaisesRegex(ValueError, "Exact merged mail switch"):
            build_production_app({"MERGED_MAIL_ENABLED": "1"}, self.builder)

    def test_environment_must_be_plain_string_mapping(self):
        with self.assertRaisesRegex(ValueError, "Plain environment strings"):
            build_production_app({"COLLECTION_ENABLED": True}, self.builder)


    def test_host_probe_switch_requires_exact_boolean_text(self):
        with self.assertRaisesRegex(ValueError, "Exact host probe switch"):
            build_production_app({"COLLECTOR_HOST_PROBE_ENABLED": "yes"}, self.builder)

    def test_collection_requires_runtime_evidence_before_building(self):
        with self.assertRaisesRegex(Exception, "Verified runtime evidence required"):
            build_production_app({"COLLECTION_ENABLED": "true"}, self.builder)
        self.assertEqual(self.received, {})

    def test_public_builder_errors_propagate(self):
        def broken_builder(environ, **bindings):
            raise RuntimeError("intentional builder failure")

        with self.assertRaisesRegex(RuntimeError, "intentional builder failure"):
            build_production_app({}, broken_builder)


if __name__ == "__main__":
    unittest.main()
