# Copyright (c) 2026 Push
"""Route tests for A's venv, after PATCH.md is applied. Skips when the app cannot be imported
(for example Flask missing here). Run from the repository root:
  /tmp/phase1-venv/bin/python -m unittest tests.geospatial.test_map_route"""
import json, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
try:
    from integration.news_api import create_app
except Exception as exc:  # pragma: no cover
    create_app = None; WHY = repr(exc)

ROOT = Path(__file__).resolve().parents[2]

@unittest.skipIf(create_app is None, "news_api not importable here")
class MapRoutes(unittest.TestCase):
    def client(self, reader=None, allow=True):
        app = create_app(reader=reader, authorize=lambda r: allow)
        return app.test_client()
    def test_unauthorised_is_403(self):
        c = self.client(allow=False)
        self.assertEqual(c.get("/api/map-data").status_code, 403)
        self.assertEqual(c.get("/workspace/map").status_code, 403)
    def test_page_and_assets(self):
        c = self.client()
        r = c.get("/workspace/map"); self.assertEqual(r.status_code, 200)
        self.assertIn(b"map-load", r.data); self.assertNotIn(b"<script>", r.data)
        for name in ("map.js", "map.css", "geo_map_ui.js", "geo_map.css"):
            self.assertEqual(c.get("/workspace/assets/" + name).status_code, 200, name)
        self.assertEqual(c.get("/workspace/assets/map.mjs").status_code, 404)
    def test_map_data_default(self):
        r = self.client().get("/api/map-data"); self.assertEqual(r.status_code, 200)
        body = r.get_json(); L = body["layers"]
        self.assertEqual(L["chokepoints"]["count"], 12)
        self.assertFalse(L["ports"]["available"]); self.assertFalse(L["ships"]["available"])
        self.assertEqual(L["news"]["count"], 0)
        self.assertEqual(r.headers["Cache-Control"], "no-store")
        s = json.dumps(body).lower()
        for bad in ("telegram", "backup_url", "original_url", "mongo", "emailed", "_id"): self.assertNotIn(bad, s)
    def test_query_rejected(self):
        self.assertEqual(self.client().get("/api/map-data?x=1").status_code, 400)
    def test_post_not_allowed(self):
        self.assertEqual(self.client().post("/api/map-data",headers={"Origin":"http://localhost"}).status_code, 405)
    def test_news_reader_failure_does_not_break_map(self):
        def boom(): raise RuntimeError("db down")
        r = self.client(reader=boom).get("/api/map-data")
        self.assertEqual(r.status_code, 200); self.assertEqual(r.get_json()["layers"]["chokepoints"]["count"], 12)
    def test_assets_in_sync_with_package(self):
        pairs = [("integration/geospatial/map_ui.js", "integration/ui/geo_map_ui.js"), ("integration/geospatial/geo_map.css", "integration/ui/geo_map.css"),
                 ("integration/geospatial/ui/map.js", "integration/ui/map.js"), ("integration/geospatial/ui/map.css", "integration/ui/map.css"),
                 ("integration/geospatial/ui/map.html", "integration/ui/map.html")]
        for a, b in pairs:
            self.assertEqual((ROOT / a).read_bytes(), (ROOT / b).read_bytes(), b)
    def test_workspace_links_map(self):
        self.assertIn(b'href="/workspace/map"', self.client().get("/workspace").data)

if __name__ == "__main__": unittest.main()

class MapLoaderBounds(unittest.TestCase):
    def test_stale_stat_cannot_bypass_read_cap(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from types import SimpleNamespace
        from integration.geospatial.response import load_chokepoints,MAX_FILE_BYTES
        with TemporaryDirectory() as d:
            p=Path(d)/'data.json';p.write_bytes(b' '* (MAX_FILE_BYTES+1))
            with patch.object(Path,'stat',return_value=SimpleNamespace(st_size=1)):
                rows,status=load_chokepoints(p)
            self.assertEqual(rows,[]);self.assertFalse(status['ok']);self.assertEqual(status['reason'],'file_too_large')
    def test_deep_json_is_unavailable(self):
        from tempfile import TemporaryDirectory
        from integration.geospatial.response import load_chokepoints
        with TemporaryDirectory() as d:
            p=Path(d)/'data.json';p.write_text('['*2000+'0'+']'*2000)
            rows,status=load_chokepoints(p)
            self.assertEqual(rows,[]);self.assertFalse(status['ok']);self.assertEqual(status['reason'],'unreadable')
