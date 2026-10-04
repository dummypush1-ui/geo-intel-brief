# Copyright (c) 2026 Push
import csv, io, importlib.util, os, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from integration.news_export import (snapshot_export, stream_export, guarded, csv_cell, parse_args, FIELDS, DEFAULT_CAPS,
                                     SNAPSHOT_MAX_ROWS, ExportRequestError, ExportUnavailable)

def row(i=1, project="geo", **kw):
    d = {"article_key": "k%s%d" % (project, i), "project": project, "url": "https://example.com/%s/%d" % (project, i), "title": "Title %d" % i,
         "summary": "S", "source": "Src", "original_country": "France", "category": "TRADE", "published_at": "2026-10-01T00:00:00+00:00",
         "collected_at": "2026-10-02T00:00:%02d+00:00" % (i % 60), "risk_level": "HIGH", "credibility": "HIGH", "score": 5, "corroboration_count": 2}
    d.update(kw); return d

def parse(b):
    return list(csv.reader(io.StringIO(b.decode("utf-8").lstrip("\ufeff"), newline="")))

class FixturePager:
    """Cursor pager over in-memory lists. Read-only; counts calls."""
    def __init__(self, data, fail_on_call=None, bad=None):
        self.data, self.calls, self.fail_on_call, self.bad = data, 0, fail_on_call, bad
    def __call__(self, project, cursor, limit):
        self.calls += 1
        if self.fail_on_call == self.calls: raise RuntimeError("secret connection string")
        if self.bad == "stuck": return [row(1, project)], "same"
        if self.bad == "toomany": return [row(i, project) for i in range(limit + 1)], None
        if self.bad == "shape": return [row(1, project)]
        rows = self.data.get(project, []); start = cursor or 0
        chunk = rows[start:start + limit]; end = start + len(chunk)
        return chunk, (end if end < len(rows) else None)

def run(pager, args=None, **kw):
    chunks, headers, state = stream_export(pager, args, **kw)
    return b"".join(chunks), headers, state

class Columns(unittest.TestCase):
    def test_fields_match_loaded_news(self):
        self.assertEqual(FIELDS, ('project', 'title', 'source', 'original_country', 'category', 'published_at', 'collected_at',
                                  'risk_level', 'credibility', 'score', 'corroboration_count', 'url', 'summary'))

class CellParity(unittest.TestCase):
    def test_same_as_existing_csv_cell(self):
        path = os.environ.get("A_LOADED_NEWS", str(Path(__file__).resolve().parents[2]/"integration/loaded_news.py"))
        pn = os.environ.get("A_PUBLIC_NEWS", str(Path(__file__).resolve().parents[2]/"integration/public_news.py"))
        if not (os.path.exists(path) and os.path.exists(pn)): self.skipTest("existing loaded_news.py not available")
        import types
        saved = {k: sys.modules.get(k) for k in ("integration.public_news",)}
        s1 = importlib.util.spec_from_file_location("a_public_news", pn); m1 = importlib.util.module_from_spec(s1); s1.loader.exec_module(m1)
        sys.modules["integration.public_news"] = m1
        try:
            s2 = importlib.util.spec_from_file_location("a_loaded_news", path); m2 = importlib.util.module_from_spec(s2); s2.loader.exec_module(m2)
        finally:
            if saved["integration.public_news"] is None: sys.modules.pop("integration.public_news", None)
            else: sys.modules["integration.public_news"] = saved["integration.public_news"]
        import random
        rnd = random.Random(5); pieces = ["=", "+", "-", "@", " ", "\t", "\r", "\n", "\u200b", "\x00", "a", "1", "\ud800", "\u2060", "é", "\u00a0", ",", '"']
        vals = ["".join(rnd.choice(pieces) for _ in range(rnd.randint(0, 6))) for _ in range(5000)] + [None, 0, -1, 5.5, "a" * 9000, True]
        self.assertEqual([m2.csv_cell(v) for v in vals], [csv_cell(v) for v in vals])
        self.assertEqual(m2.FIELDS, FIELDS)
        res = {"items": [row(1), row(2, title="=x", summary="a\nb")]}
        # same bytes as the existing sample for the same ordered rows
        expected = m2.sample_csv(res)
        got = b"".join(stream_export(FixturePager({"geo": res["items"]}), {"project": "geo"})[0]).decode()
        self.assertEqual(got, expected)

class Cell(unittest.TestCase):
    def test_formula_variants(self):
        for v in ["=1", "+cmd", "-1", "@x", "  =SUM(1)", "\u200b=1", "\x00=1", "\ttext", "\rtext", "\ntext"]:
            self.assertTrue(csv_cell(v).startswith("'"), repr(v))
        self.assertEqual(csv_cell("normal"), "normal"); self.assertEqual(csv_cell(None), ""); self.assertEqual(csv_cell("a\ud800"), "a\ufffd")
        self.assertEqual(len(csv_cell("a" * 9000)), 8000)

class Args(unittest.TestCase):
    def test_bad_args(self):
        for bad in ({"project": "x"}, {"category": "../etc"}, {"category": "a" * 61}, {"category": ["a"]}, {"foo": "1"}, {"path": "/etc/passwd"}, {"project": 5}, {"category": "T;D"}, "str", {"file": "x.csv"}):
            with self.assertRaises(ExportRequestError): parse_args(bad)
        self.assertEqual(parse_args({"project": "", "category": ""}), {"project": None, "category": None})
    def test_filename_closed_pattern(self):
        h = snapshot_export([], {"project": "geo", "category": "Trade Co"})[1]["Content-Disposition"]
        self.assertEqual(h, 'attachment; filename="geo-intel-news-snapshot-geo-trade-co.csv"')
        self.assertRegex(stream_export(FixturePager({}), {"category": "A_b-c 9"})[1]["Content-Disposition"], r'filename="[a-z0-9_.-]+"$')

class Snapshot(unittest.TestCase):
    def test_basic(self):
        body, h, m = snapshot_export([row(1), row(2, summary='he said "hi", then\nleft')])
        t = parse(body); self.assertEqual(tuple(t[0]), FIELDS); self.assertEqual(len(t), 3)
        self.assertIn(b"\r\n", body); self.assertEqual(h["Content-Type"], "text/csv; charset=utf-8")
        self.assertEqual(h["X-Export-Truncated"], "false"); self.assertEqual(h["X-Export-Scope"], "loaded_read_view_not_full_database")
        self.assertIn('he said "hi", then\nleft', [c for r in t for c in r])
    def test_utf8_bom(self):
        r = [row(1, title="நாள் é 日本")]
        self.assertFalse(snapshot_export(r)[0].startswith(b"\xef\xbb\xbf")); self.assertTrue(snapshot_export(r, bom=True)[0].startswith(b"\xef\xbb\xbf"))
        self.assertEqual(parse(snapshot_export(r)[0])[1][1], "நாள் é 日本")
    def test_filters_dupes_order_trunc(self):
        rows = [row(1), row(1), row(2, project="brics", category="SANCTIONS"), row(3, category=None), row(4, category="")]
        self.assertEqual(snapshot_export(rows, {"project": "brics"})[2]["rows"], 1)
        self.assertEqual(snapshot_export(rows, {"category": "GENERAL"})[2]["rows"], 2)
        self.assertEqual(snapshot_export(rows)[2]["duplicates_omitted"], 1)
        new = [row(i) for i in range(30)]
        keys = [r[FIELDS.index("title")] for r in parse(snapshot_export(new)[0])[1:]]
        self.assertEqual(keys[0], "Title 29")
        b, h, m = snapshot_export([row(i) for i in range(50)], max_rows=10); self.assertEqual((m["rows"], h["X-Export-Truncated"]), (10, "true"))
        self.assertEqual(snapshot_export([row(i) for i in range(SNAPSHOT_MAX_ROWS + 5)])[2]["rows"], SNAPSHOT_MAX_ROWS)
    def test_bad_inputs(self):
        for bad in (None, {"geo": []}):
            with self.assertRaises(ValueError): snapshot_export(bad)
        for bad in (0, True, 10001, "5"):
            with self.assertRaises(ValueError): snapshot_export([], max_rows=bad)
        class D(dict): pass
        self.assertEqual(snapshot_export([row(1), "x", None, D(row(2))])[2]["non_object_rows_skipped"], 3)
    def test_private_fields_never_exported(self):
        r = row(1, telegram_url="https://t.me/x", backup_url="https://b", original_url="o", emailed=True, _id="abc", mongo_id="m", legacy_id="l", api_key="k")
        for b in (snapshot_export([r])[0], run(FixturePager({"geo": [r]}), {"project": "geo"})[0]):
            s = b.decode()
            for bad in ("t.me", "backup", "abc", "mongo", "emailed", "legacy", "api_key", "https://b"): self.assertNotIn(bad, s)
    def test_big_cells_bounded_fast(self):
        import time
        t0 = time.time(); b = snapshot_export([row(1, summary="a" * 5_000_000, title="=" + "b" * 100000)])[0]
        self.assertLess(time.time() - t0, 1.0); self.assertLessEqual(len(parse(b)[1][FIELDS.index("summary")]), 8000)

class Stream(unittest.TestCase):
    def data(self, n=250, m=30): return {"geo": [row(i) for i in range(n)], "brics": [row(i, "brics") for i in range(m)]}
    def test_both_projects_paged(self):
        p = FixturePager(self.data()); b, h, s = run(p, page_size=100)
        t = parse(b); self.assertEqual(len(t), 1 + 250 + 30); self.assertEqual(tuple(t[0]), FIELDS)
        self.assertEqual({r[0] for r in t[1:]}, {"geo", "brics"}); self.assertEqual(s["rows"], 280)
        self.assertEqual(p.calls, 3 + 1); self.assertFalse(s["stopped"]); self.assertIn("paged_read_view_capped", h["X-Export-Scope"])
        self.assertEqual(h["X-Export-Limit"], "geo=1000000,brics=5000")
    def test_page_size_bounds_requests(self):
        seen = []
        def pager(pr, cur, limit): seen.append(limit); return [], None
        run(pager, page_size=50); self.assertTrue(seen and max(seen) <= 50)
        for bad in (0, 1001, True): 
            with self.assertRaises(ValueError): stream_export(pager, page_size=bad)
    def test_project_filter_and_category(self):
        d = {"geo": [row(i, category="TRADE" if i % 2 else "RISK") for i in range(40)]}
        t = parse(run(FixturePager(d), {"project": "geo", "category": "TRADE"})[0]); self.assertEqual(len(t) - 1, 20)
    def test_cap_truncation_trailer(self):
        b, h, s = run(FixturePager(self.data(300, 0)), {"project": "geo"}, caps={"geo": 120}, page_size=50)
        t = parse(b); self.assertEqual(len(t), 1 + 120 + 1); self.assertTrue(t[-1][0].startswith("EXPORT_TRUNCATED: row cap 120")); self.assertTrue(s["stopped"])
        self.assertEqual(s["read"], 120)
    def test_exact_cap_no_false_truncation(self):
        b, h, s = run(FixturePager(self.data(100, 0)), {"project": "geo"}, caps={"geo": 100}, page_size=50)
        self.assertNotIn(b"EXPORT_", b); self.assertFalse(s["stopped"])
    def test_cap_bounds_reads_even_with_unmatched_filter(self):
        p = FixturePager({"geo": [row(i, category="RISK") for i in range(1000)]})
        b, h, s = run(p, {"project": "geo", "category": "NOPE"}, caps={"geo": 200}, page_size=100)
        self.assertLessEqual(s["read"], 200); self.assertEqual(len(parse(b)) - 1 - 1, 0)
    def test_first_page_failure_is_503_before_bytes(self):
        with self.assertRaises(ExportUnavailable) as cm: stream_export(FixturePager({}, fail_on_call=1), {"project": "geo"})
        self.assertNotIn("secret", str(cm.exception))
    def test_mid_stream_failure_trailer_no_leak(self):
        b, h, s = run(FixturePager(self.data(300, 0), fail_on_call=2), {"project": "geo"}, page_size=100)
        t = parse(b); self.assertTrue(t[-1][0].startswith("EXPORT_INCOMPLETE: source error after 100 rows")); self.assertNotIn(b"secret", b); self.assertEqual(len(t), 1 + 100 + 1)
    def test_pager_contract_violations(self):
        for bad in ("toomany", "shape"):
            with self.assertRaises(ExportUnavailable): stream_export(FixturePager({}, bad=bad), {"project": "geo"})
        b, h, s = run(FixturePager({}, bad="stuck"), {"project": "geo"}, caps={"geo": 1000}, page_size=10)
        self.assertTrue(parse(b)[-1][0].startswith("EXPORT_INCOMPLETE: pager cursor did not advance"))
    def test_wrong_project_rows_dropped(self):
        d = {"geo": [row(1), row(2, "brics")]}
        t = parse(run(FixturePager(d), {"project": "geo"})[0]); self.assertEqual(len(t) - 1, 1)
    def test_byte_and_time_limits(self):
        big = {"geo": [row(i, summary="x" * 3000) for i in range(300)]}
        b, h, s = run(FixturePager(big), {"project": "geo"}, max_bytes=100000, page_size=100)
        self.assertLessEqual(len(b), 100000 + 200); self.assertIn(b"EXPORT_TRUNCATED: byte limit", b)
        ticks = iter(range(0, 10**6, 100))
        b, h, s = run(FixturePager(self.data(500, 0)), {"project": "geo"}, max_seconds=250, clock=lambda: next(ticks), page_size=100)
        self.assertIn(b"EXPORT_TRUNCATED: time limit", b)
    def test_formula_cells_protected_in_stream(self):
        r = row(1, title="=HYPERLINK(\"x\")", source="\u200b@s", summary="  +cmd")
        t = parse(run(FixturePager({"geo": [r]}), {"project": "geo"})[0])
        for f in ("title", "source", "summary"): self.assertTrue(t[1][FIELDS.index(f)].startswith("'"))
    def test_caps_validation(self):
        for bad in ({"x": 5}, {"geo": 0}, {"geo": True}, {}, {"geo": 6000000}):
            with self.assertRaises(ValueError): stream_export(FixturePager({}), caps=bad)
        with self.assertRaises(ExportRequestError): stream_export(FixturePager({}), {"project": "brics"}, caps={"geo": 5})
        self.assertEqual(DEFAULT_CAPS, {"geo": 1000000, "brics": 5000})
    def test_not_callable(self):
        with self.assertRaises(ValueError): stream_export(None)
    def test_guarded_releases_once_even_on_disconnect(self):
        rel = []; ch, _, _ = stream_export(FixturePager(self.data()), {"project": "geo"}, page_size=10)
        g = guarded(ch, lambda: rel.append(1)); next(g); g.close(); self.assertEqual(rel, [1])
        rel2 = []; list(guarded(stream_export(FixturePager(self.data(5, 0)), {"project": "geo"})[0], lambda: rel2.append(1))); self.assertEqual(rel2, [1])
    def test_generator_is_lazy(self):
        p = FixturePager(self.data(1000, 0)); ch, _, _ = stream_export(p, {"project": "geo"}, page_size=100)
        self.assertEqual(p.calls, 1); next(ch); next(ch); self.assertLessEqual(p.calls, 2)
    def test_large_streaming_memory_shape(self):
        n = 50000; data = {"geo": [row(i) for i in range(n)]}
        ch, _, s = stream_export(FixturePager(data), {"project": "geo"}, page_size=1000)
        biggest = max(len(c) for c in ch); self.assertEqual(s["rows"], n); self.assertLess(biggest, 400000)

class Safety(unittest.TestCase):
    def test_no_io_in_calls(self):
        import builtins, socket
        o1, o2 = builtins.open, socket.socket
        def boom(*a, **k): raise AssertionError("io")
        builtins.open, socket.socket = boom, boom
        try: snapshot_export([row(1)]); run(FixturePager({"geo": [row(1)]}), {"project": "geo"})
        finally: builtins.open, socket.socket = o1, o2
    def test_source_scan(self):
        t = (Path(__file__).resolve().parents[2] / "integration" / "news_export" / "export.py").read_text()
        for pat in ("open(", "requests", "urllib", "os.environ", "threading", "eval(", "subprocess", "socket", "pathlib", "pymongo", "sleep(", "Timer"):
            self.assertNotIn(pat, t, pat)
        self.assertIn("Copyright (c) 2026 Push", t)

if __name__ == "__main__": unittest.main()
