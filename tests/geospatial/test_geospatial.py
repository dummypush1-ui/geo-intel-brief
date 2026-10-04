# Copyright (c) 2026 Push
import json, math, sys, unittest, socket, builtins
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from integration.geospatial import (validate_features, ship_view, map_payload, project, bbox_rects,
                                    MAX_FEATURES, INPUT_CAP, DISPLAY_CAP)
from integration.geospatial import fixtures as fx
from integration.geospatial._safe import safe_https_url, clean_text

NOW = datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc)
ISO = NOW.isoformat()

class Features(unittest.TestCase):
    def test_good(self):
        f, r = validate_features(fx.PORTS + fx.CHOKES)
        self.assertEqual(len(f), 6); self.assertEqual(r["accepted"], 6)
    def test_not_list_is_unavailable(self):
        f, r = validate_features(None); self.assertEqual(f, []); self.assertFalse(r["available"])
    def test_bad_coords(self):
        bad = [True, None, float("nan"), float("inf"), "5", 91, -91]
        rows = [fx.port(i + 10, v, 0) for i, v in enumerate(bad)] + [fx.port(30, 0, 181), fx.port(31, 0, True)]
        f, r = validate_features(rows)
        self.assertEqual(f, []); self.assertEqual(r["rejected"]["bad_coordinates"], 9)
    def test_zero_not_invented(self):
        row = fx.port(1, None, None); f, _ = validate_features([row]); self.assertEqual(f, [])
    def test_duplicates_and_junk(self):
        f, r = validate_features([fx.port(1, 1, 1), fx.port(1, 2, 2), "x", None, 5, {}])
        self.assertEqual(len(f), 1); self.assertEqual(r["rejected"]["duplicate"], 1)
    def test_same_id_other_kind_ok(self):
        f, _ = validate_features([fx.port(1, 1, 1), fx.choke(1, 1, 1, id="fx-port-1")]); self.assertEqual(len(f), 2)
    def test_unsafe_urls(self):
        for u in ["http://a.com/x", "javascript:alert(1)", "https://u:p@a.com/", "https://a.com\\evil", "https://a.com/\u200bx",
                  "https://a.com/ x", "//a.com", "https://", "data:text/html,x", "https://a.com:99999/"]:
            f, _ = validate_features([fx.port(1, 1, 1, source_url=u)]); self.assertEqual(f, [], u)
    def test_closed_shape(self):
        f, _ = validate_features([fx.port(1, 1, 1, telegram_chat="s", _id="x", extra={"a": 1})])
        self.assertNotIn("telegram_chat", f[0]); self.assertNotIn("_id", f[0]); self.assertNotIn("extra", f[0])
    def test_hostile_text_kept_as_text_stripped_of_controls(self):
        f, _ = validate_features([fx.port(1, 1, 1, name="<img onerror=x>\x00\u202eA")])
        self.assertNotIn("\x00", f[0]["name"]); self.assertNotIn("\u202e", f[0]["name"])
    def test_truncation(self):
        rows = [fx.port(i, 0, 0) for i in range(MAX_FEATURES + 5)]
        f, r = validate_features(rows); self.assertEqual(len(f), MAX_FEATURES); self.assertTrue(r["truncated"])
    def test_bad_bbox_dropped_not_fatal(self):
        f, _ = validate_features([fx.port(1, 1, 1, bbox={"south": 5, "north": 1, "west": 0, "east": 1})])
        self.assertEqual(len(f), 1); self.assertIsNone(f[0]["bbox"])
    def test_subclass_dict_rejected(self):
        class D(dict): pass
        f, _ = validate_features([D(fx.port(1, 1, 1))]); self.assertEqual(f, [])

class Ships(unittest.TestCase):
    def test_absent_vs_empty(self):
        self.assertEqual(ship_view(None, NOW)["status"], "absent")
        e = ship_view({"state": "connected", "captured_at": ISO, "vessels": []}, NOW)
        self.assertEqual(e["status"], "empty"); self.assertEqual(e["ships"], [])
    def test_fresh_and_stale(self):
        self.assertEqual(ship_view(fx.ships(ISO), NOW)["status"], "fresh")
        old = (NOW - timedelta(minutes=16)).isoformat()
        v = ship_view(fx.ships(old), NOW); self.assertEqual(v["status"], "stale"); self.assertTrue(v["stale"])
    def test_future_rejected(self):
        fut = (NOW + timedelta(hours=1)).isoformat()
        self.assertEqual(ship_view(fx.ships(fut), NOW)["status"], "invalid_clock")
    def test_naive_clock_rejected(self):
        self.assertEqual(ship_view(fx.ships("2026-10-05T11:59:00"), NOW)["status"], "invalid_clock")
        with self.assertRaises(ValueError): ship_view(None, datetime(2026, 1, 1))
    def test_missing_clock(self):
        o = fx.ships(ISO); del o["captured_at"]; self.assertEqual(ship_view(o, NOW)["status"], "invalid_clock")
    def test_connection_no_freshness(self):
        o = fx.ships(ISO, state="disconnected"); v = ship_view(o, NOW)
        self.assertEqual(v["status"], "disconnected"); self.assertEqual(v["ships"], [])
        self.assertEqual(ship_view(fx.ships(ISO, state="warming"), NOW)["status"], "warming")
    def test_bad_state(self):
        self.assertEqual(ship_view({"state": "ok"}, NOW)["status"], "invalid_state")
    def test_vessel_validation(self):
        o = fx.ships(ISO, n=1); o["vessels"] += [{"mmsi": "12", "latitude": 0, "longitude": 0},
            {"mmsi": "123456789", "latitude": True, "longitude": 0}, {"mmsi": "200000000", "latitude": 1, "longitude": 1},
            {"mmsi": "123456789", "latitude": float("nan"), "longitude": 0}, "x"]
        v = ship_view(o, NOW); self.assertEqual(len(v["ships"]), 1); self.assertEqual(v["rejected"], 5)
    def test_imo_validated_not_guessed(self):
        o = fx.ships(ISO, n=1); o["vessels"][0]["imo"] = "99"; self.assertIsNone(ship_view(o, NOW)["ships"][0]["imo"])
        o["vessels"][0]["imo"] = 9074729; self.assertEqual(ship_view(o, NOW)["ships"][0]["imo"], "9074729")
    def test_private_fields_absent(self):
        o = fx.ships(ISO, n=1); o["vessels"][0].update({"telegram_chat": "s", "_id": "x", "TELEGRAM_X": 1, "api_key": "k"})
        self.assertNotIn("telegram", json.dumps(ship_view(o, NOW)).lower()); self.assertNotIn('"k"', json.dumps(ship_view(o, NOW)))
    def test_truncation_visible(self):
        o = fx.ships(ISO, n=INPUT_CAP + 50)
        v = ship_view(o, NOW); self.assertTrue(v["truncated"]); self.assertEqual(len(v["ships"]), DISPLAY_CAP)
    def test_counts_are_observations(self):
        o = fx.ships(ISO, n=2); o["supplied_vessel_count"] = 99999
        v = ship_view(o, NOW); self.assertEqual(v["supplied_vessel_count"], 99999); self.assertIn("not proof", v["coverage_note"])
    def test_non_utc_zone(self):
        ist = timezone(timedelta(hours=5, minutes=30))
        self.assertEqual(ship_view(fx.ships(NOW.astimezone(ist).isoformat()), NOW.astimezone(ist))["status"], "fresh")

class Payload(unittest.TestCase):
    def test_project_corners(self):
        self.assertEqual(project(90, -180), (0.0, 0.0)); self.assertEqual(project(-90, 180), (1000.0, 500.0))
        self.assertIsNone(project(float("nan"), 0)); self.assertIsNone(project(True, 0))
    def test_dateline_features(self):
        self.assertEqual(project(0, 180)[0], 1000.0); self.assertEqual(project(0, -180)[0], 0.0)
    def test_bbox_antimeridian_two_rects(self):
        r = bbox_rects({"south": 64.5, "north": 67, "west": 170, "east": -168})
        self.assertEqual(len(r), 2); self.assertAlmostEqual(r[0]["x"] + r[0]["w"], 1000.0); self.assertEqual(r[1]["x"], 0.0)
        self.assertEqual(len(bbox_rects({"south": 0, "north": 1, "west": 10, "east": 20})), 1)
    def test_layers_and_availability(self):
        p = map_payload(None, None, None, None, NOW)
        for k, L in p["layers"].items(): self.assertFalse(L["available"], k); self.assertEqual(L["count"], 0)
        p = map_payload(fx.NEWS, fx.PORTS, fx.CHOKES, fx.ships(ISO), NOW)
        self.assertEqual([p["layers"][k]["count"] for k in ("news", "ports", "chokepoints", "ships")], [1, 4, 2, 3])
        self.assertTrue(p["layers"]["ports"]["provenance"])
    def test_news_private_fields_and_no_inference(self):
        p = map_payload(fx.NEWS + [{"title": "no coords", "original_country": "France"}], [], [], None, NOW)
        self.assertEqual(p["layers"]["news"]["count"], 1)
        s = json.dumps(p).lower()
        for bad in ("telegram", "backup_url", "secret", "_id", "mongo"): self.assertNotIn(bad, s)
    def test_news_case_variants(self):
        n = dict(fx.NEWS[0]); n.update({"Telegram_Chat": "s", "BACKUP_URL": "u", "Original_URL": "u", "Emailed": True})
        s = json.dumps(map_payload([n], [], [], None, NOW)).lower()
        for bad in ("telegram", "backup", "original_url", "emailed"): self.assertNotIn(bad, s)
    def test_no_score_inferred(self):
        s = json.dumps(map_payload(None, fx.PORTS, fx.CHOKES, fx.ships(ISO), NOW))
        for bad in ("risk", "threat", "congestion", "closed"): self.assertNotIn(bad, s.lower().replace("not operational", ""))
    def test_hostile_news_url_dropped(self):
        n = dict(fx.NEWS[0], url="javascript:alert(1)"); self.assertIsNone(map_payload([n], [], [], None, NOW)["layers"]["news"]["items"][0]["url"])
    def test_json_serialisable(self): json.dumps(map_payload(fx.NEWS, fx.PORTS, fx.CHOKES, fx.ships(ISO), NOW))

class NoSideEffects(unittest.TestCase):
    def test_import_and_calls_no_network_or_writes(self):
        import importlib, integration.geospatial as g
        orig_sock, orig_open = socket.socket, builtins.open
        def boom(*a, **k): raise AssertionError("forbidden")
        socket.socket = boom
        def guard(f, mode="r", *a, **k):
            if any(c in mode for c in "wax+"): raise AssertionError("write")
            return orig_open(f, mode, *a, **k)
        builtins.open = guard
        try:
            importlib.reload(g); map_payload(fx.NEWS, fx.PORTS, fx.CHOKES, fx.ships(ISO), NOW)
        finally:
            socket.socket, builtins.open = orig_sock, orig_open
    def test_source_has_no_forbidden_apis(self):
        import re
        for f in (Path(__file__).resolve().parents[2] / "integration" / "geospatial").glob("*"):
            if f.suffix not in (".py", ".js"): continue
            t = f.read_text()
            for pat in ("innerHTML", "eval(", "outerHTML", "document.write", "postMessage", "fetch(", "XMLHttpRequest", "WebSocket", "EventSource", "setInterval", "import requests", "urllib.request", "os.environ", "threading"):
                if f.name == "test_geospatial.py": continue
                self.assertNotIn(pat, t, "%s in %s" % (pat, f.name))
            if f.name != "fixtures.py": self.assertNotRegex(t, r"(?i)worldmonitor|koala73|agpl")
            self.assertIn("Copyright (c) 2026 Push", t)

class Robust(unittest.TestCase):
    BIG = 10 ** 400
    def test_huge_ints_no_crash(self):
        f, r = validate_features([fx.port(1, self.BIG, 0), fx.port(2, 0, -self.BIG)])
        self.assertEqual(f, []); self.assertEqual(r["rejected"]["bad_coordinates"], 2)
        self.assertIsNone(project(self.BIG, 0))
        n = dict(fx.NEWS[0], latitude=self.BIG)
        self.assertEqual(map_payload([n], [], [], None, NOW)["layers"]["news"]["count"], 0)
        o = fx.ships(ISO, n=1); o["vessels"][0]["latitude"] = self.BIG; o["vessels"][0]["speed_knots"] = self.BIG
        self.assertEqual(ship_view(o, NOW)["ships"], [])
        o["vessels"][0].update(latitude=1, speed_knots=self.BIG); self.assertIsNone(ship_view(o, NOW)["ships"][0]["speed_knots"])
    def test_giant_string_bounded_fast(self):
        import time
        t = time.time(); clean_text("a" * 50_000_000, 100)
        self.assertLess(time.time() - t, 1.0)
    def test_wrong_kind_reported(self):
        p = map_payload(None, fx.PORTS + fx.CHOKES[:1], [], None, NOW)
        self.assertEqual(p["layers"]["ports"]["count"], 4); self.assertEqual(p["layers"]["ports"]["report"]["wrong_kind_dropped"], 1)
    def test_url_unicode_host(self):
        self.assertIsNone(safe_https_url("https://exаmple.com/"))  # cyrillic a
        self.assertIsNone(safe_https_url("https://example.com/\u2060x")); self.assertIsNone(safe_https_url("https://example.com/\u00adx"))

class Round2(unittest.TestCase):
    def test_huge_mmsi_imo(self):
        o = fx.ships(ISO, n=1); o["vessels"][0]["imo"] = 10 ** 5000
        self.assertIsNone(ship_view(o, NOW)["ships"][0]["imo"])
        o["vessels"][0]["mmsi"] = 10 ** 5000; self.assertEqual(ship_view(o, NOW)["ships"], [])
        o["vessels"][0]["mmsi"] = -5; self.assertEqual(ship_view(o, NOW)["ships"], [])
    def test_prov_groups_not_lost(self):
        rows = [fx.port(i, 0, 0, source_url="https://example.com/p/%d" % i) for i in range(30)]
        rows.append(fx.port(99, 1, 1, dataset="OTHER", license="OTHER-LICENCE"))
        L = map_payload(None, rows, [], None, NOW)["layers"]["ports"]
        self.assertEqual(len(L["provenance"]), 2); self.assertEqual(L["provenance_groups_dropped"], 0)
        a = [g for g in L["provenance"] if g[0] == "FIXTURE dataset"][0]; self.assertEqual(a[4], 30)
        self.assertTrue(any(g[1] == "OTHER-LICENCE" for g in L["provenance"]))
    def test_prov_group_cap_flagged(self):
        rows = [fx.port(i, 0, 0, dataset="D%d" % i) for i in range(25)]
        L = map_payload(None, rows, [], None, NOW)["layers"]["ports"]
        self.assertEqual(len(L["provenance"]), 20); self.assertEqual(L["provenance_groups_dropped"], 5)
    def test_old_empty_is_stale(self):
        old = (NOW - timedelta(hours=1)).isoformat()
        v = ship_view({"state": "connected", "captured_at": old, "vessels": []}, NOW)
        self.assertEqual(v["status"], "stale"); self.assertEqual(v["ships"], [])

class RealData(unittest.TestCase):
    def test_chokepoint_file_valid(self):
        f = Path(__file__).resolve().parents[2] / "integration" / "geospatial" / "data" / "chokepoints_wikidata.json"
        doc = json.loads(f.read_text(encoding="utf-8"))
        rows = doc["features"]
        feats, rep = validate_features(rows)
        self.assertEqual(len(rows), 12); self.assertEqual(len(feats), 12, rep)
        self.assertTrue(all(x["source_url"].startswith("https://www.wikidata.org/wiki/Q") for x in feats))
        self.assertTrue(all("CC0" in x["license"] and "retrieved 2026-10-04" in x["captured_version"] for x in feats))
        self.assertNotIn("fixture", json.dumps(doc["features"]).lower())
        self.assertTrue(all(not x["id"].startswith("fx-") for x in feats))
        p = map_payload(None, [], rows, None, NOW)["layers"]["chokepoints"]
        self.assertEqual(p["count"], 12)

class UrlParity(unittest.TestCase):
    def _run_js(self, vectors):
        import shutil, subprocess, tempfile, os
        node = shutil.which("node")
        if not node: self.skipTest("node not installed")
        here = Path(__file__).resolve().parent
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(vectors, fh, ensure_ascii=True); name = fh.name
        try:
            out = subprocess.run([node, str(here / "url_parity.mjs"), name], capture_output=True, text=True, timeout=60)
        finally:
            os.unlink(name)
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout)
    def _diffs(self, vectors):
        js = self._run_js(vectors)
        py = [safe_https_url(u) is not None for u in vectors]
        return py, [(u, p, j) for u, p, j in zip(vectors, py, js) if p != j]
    def test_fixed_vectors(self):
        vectors = json.loads((Path(__file__).resolve().parent / "url_vectors.json").read_text(encoding="utf-8"))
        py, diffs = self._diffs(vectors)
        self.assertEqual(diffs, []); self.assertTrue(any(py) and not all(py))
        for u in ["https://@a.com/", "https://a.com1.2.3.4/", "https://a.com/\u180ex", "https://a.com/\ud800"]:
            self.assertIsNone(safe_https_url(u), u)
    def test_seeded_fuzz(self):
        import random
        rnd = random.Random(20261005)
        pieces = ["https://", "HTTPS://", "http://", "a", "b", "Z", "0", "9", ".", "..", "-", "_", "@", ":", ":443", ":0", ":65536", "/", "?", "#", "%", "%41", "[", "]", "::1",
                  "com", "example.com", "1.2.3.4", " ", "\t", "\n", "\\", "\u00ad", "\u180e", "\u200b", "\u2060", "\u202e", "\ue000", "\u0378", "\ufdd0", "\uffff",
                  "\U000e0001", "\ud800", "\u00e9", "\u0430", "\u3002", "\u20ac", "\x7f", "\x00", "~", "!", "&", "="]
        vectors = []
        for _ in range(4000):
            vectors.append("".join(rnd.choice(pieces) for _ in range(rnd.randint(1, 9))))
        for _ in range(2000):  # mostly-valid shapes with one mutation
            u = "https://" + rnd.choice(["a.com", "x-y.org", "a.b.c.io", "1.2.3.4", "a.com1.2.3.4"]) + rnd.choice(["", ":443", ":", ":70000"]) + rnd.choice(["/", "/p?q=1", "?a", "#f", ""])
            i = rnd.randint(0, len(u)); u = u[:i] + rnd.choice(pieces) + u[i:]
            vectors.append(u)
        py, diffs = self._diffs(vectors)
        # JS may additionally reject via new URL(); it must never accept what Python rejects.
        self.assertEqual([d for d in diffs if d[2] and not d[1]][:5], [])
        self.assertTrue(100 < sum(py) < len(py) - 500, sum(py))

class Safe(unittest.TestCase):
    def test_ok(self): self.assertTrue(safe_https_url("https://example.com/a?b=1")); self.assertIsNone(safe_https_url("https://ex ample.com"))
    def test_host_policy(self): self.assertIsNone(safe_https_url("https://evil.com", {"example.com"}))
    def test_clean(self): self.assertEqual(clean_text(" a\u200b b\n"), "a b"); self.assertIsNone(clean_text(5))

if __name__ == "__main__": unittest.main()
