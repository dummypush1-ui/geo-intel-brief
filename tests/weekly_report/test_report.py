# Copyright (c) 2026 Push
import ast, io, pathlib, unittest
from datetime import datetime, timedelta, timezone

from integration import weekly_report as wr
from integration.weekly_report import report as rep

IST = timezone(timedelta(hours=5, minutes=30))
PS = datetime(2026, 9, 28, 0, 0, tzinfo=IST)
PE = datetime(2026, 10, 5, 0, 0, tzinfo=IST)
GA = datetime(2026, 10, 5, 8, 0, tzinfo=IST)


def row(i, **kw):
    d = {"article_key": "FIXTURE-%d" % i, "project": "fixture", "url": "https://example.com/a/%d" % i,
         "title": "FIXTURE headline %d" % i, "summary": "Fixture summary %d" % i, "source": "Fixture Wire",
         "original_country": "Exampleland", "category": "trade", "published_at": "2026-09-30T10:00:00+05:30",
         "collected_at": "2026-09-30T10:05:00+05:30", "risk_level": "medium", "credibility": "high",
         "score": 40 + i, "corroboration_count": 2}
    d.update(kw)
    return d


def tariff(i=1, **kw):
    d = {"record_id": "T%d" % i, "country": "Exampleland", "product_code": "7202", "measure": "Import duty",
         "rate_text": "10%", "effective_date": "2026-09-01", "source_name": "Fixture Gazette",
         "source_url": "https://example.org/t/%d" % i, "captured_at": "2026-10-01T09:00:00+05:30", "note": "fixture"}
    d.update(kw)
    return d


def S(rows, tr=None):
    return rep.summarize_week(rows, tr, PS, PE, GA)


class Sanitize(unittest.TestCase):
    def test_private_and_unknown_fields_dropped(self):
        r = row(1, telegram_chat="x", telegram_id=5, emailed=True, _id="m", backup_url="https://e.com/b",
                original_url="https://e.com/o", Telegram_X="y", mongo_id="1", secret="s")
        clean, _ = rep.sanitize_news_rows([r], PS, PE, GA)
        self.assertEqual(set(clean[0]), set(wr.NEWS_FIELDS))
        blob = repr(clean)
        for bad in ("telegram", "emailed", "backup", "mongo", "secret", "original_url"):
            self.assertNotIn(bad, blob.lower())

    def test_pdf_has_no_private_text(self):
        r = row(1, telegram_chat="PRIVATECHAT", backup_url="https://e.com/PRIVBACKUP", emailed="PRIVMAIL", _id="PRIVID")
        text = pdf_text(wr.build_weekly_report([r], period_start=PS, period_end=PE, generated_at=GA))
        for bad in ("PRIVATECHAT", "PRIVBACKUP", "PRIVMAIL", "PRIVID"):
            self.assertNotIn(bad, text)

    def test_bad_urls_rejected(self):
        bads = ["http://e.com/x", "javascript:alert(1)", "https://u:p@e.com/x", "https://e.com\\x",
                "https://e.com/\u200bx", "https://e.com/a b", "https://localhost/x", "//e.com/x", None, 5,
                "https://e.com:8443/x", "https://e.com/" + "a" * 600, "https://\u00e9.com/x", "https://e.com/\nx"]
        clean, st = rep.sanitize_news_rows([row(i, url=u) for i, u in enumerate(bads)], PS, PE, GA)
        self.assertEqual(clean, [])
        self.assertEqual(st["rejected_bad_url"], len(bads))

    def test_dates(self):
        rows = [row(1, published_at="2026-09-30T10:00:00"),          # naive
                row(2, published_at="2026-10-05T09:00:00+05:30"),    # after generated_at
                row(3, published_at="2026-09-20T10:00:00+05:30"),    # outside period
                row(4, published_at="garbage"), row(5, published_at=None),
                row(6, published_at="2026-09-30T04:30:00Z"),         # ok
                row(7, published_at="2026-10-04T23:59:59+05:30")]    # ok edge
        clean, st = rep.sanitize_news_rows(rows, PS, PE, GA)
        self.assertEqual([r["article_key"] for r in clean], ["FIXTURE-6", "FIXTURE-7"])
        self.assertEqual(st["rejected_bad_or_naive_date"], 3)
        self.assertEqual(st["rejected_future_date"], 1)
        self.assertEqual(st["outside_period"], 1)

    def test_period_end_exclusive_and_dateline(self):
        z = timezone(timedelta(hours=-12))
        e = row(1, published_at="2026-10-05T00:00:00+05:30")
        clean, st = rep.sanitize_news_rows([e], PS, PE, datetime(2026, 10, 6, tzinfo=timezone.utc))
        self.assertEqual(st["outside_period"], 1)
        # same instant expressed in UTC-12 still lands on the right side
        f = row(2, published_at="2026-09-27T12:00:00-12:00")  # = 2026-09-28 00:00 UTC+0 -> 05:30 IST
        clean, _ = rep.sanitize_news_rows([f], PS, PE, GA)
        self.assertEqual(len(clean), 1)

    def test_naive_arguments_rejected(self):
        with self.assertRaises(ValueError):
            rep.sanitize_news_rows([], datetime(2026, 9, 28), PE, GA)
        with self.assertRaises(ValueError):
            rep.sanitize_news_rows([], PE, PS, GA)
        with self.assertRaises(ValueError):
            rep.sanitize_tariff_records([], datetime(2026, 10, 5))

    def test_numbers(self):
        rows = [row(1, score=True), row(2, score=float("nan")), row(3, score=float("inf")), row(4, score="9"),
                row(5, corroboration_count=-3), row(6, corroboration_count=True), row(7, corroboration_count=2.5)]
        clean, _ = rep.sanitize_news_rows(rows, PS, PE, GA)
        self.assertTrue(all(r["score"] is None or r["score"] == 45 + 0 or isinstance(r["score"], (int, float)) for r in clean))
        self.assertEqual([r["score"] for r in clean[:4]], [None, None, None, None])
        self.assertEqual([r["corroboration_count"] for r in clean[4:]], [None, None, None])

    def test_duplicates_and_hostile_text(self):
        rows = [row(1), row(1), row(2, article_key=None, url="https://e.com/same"), row(3, article_key=None, url="https://e.com/same"),
                row(4, title="<script>alert(1)</script>\u202e\x00 bad\n\tline")]
        clean, st = rep.sanitize_news_rows(rows, PS, PE, GA)
        self.assertEqual(st["duplicate"], 2)
        t = [r for r in clean if r["article_key"] == "FIXTURE-4"][0]["title"]
        self.assertNotIn("\u202e", t)
        self.assertNotIn("\x00", t)
        self.assertNotIn("\n", t)

    def test_caps_and_truncation_visible(self):
        rows = [row(i) for i in range(rep.MAX_NEWS_INPUT + 50)]
        clean, st = rep.sanitize_news_rows(rows, PS, PE, GA)
        self.assertEqual(st["input_truncated"], 50)
        self.assertEqual(len(clean), rep.MAX_NEWS_INPUT)
        long, _ = rep.sanitize_news_rows([row(1, title="x" * 5000)], PS, PE, GA)
        self.assertLessEqual(len(long[0]["title"]), 200)

    def test_bad_inputs_do_not_raise(self):
        for bad in (None, 5, "x", {"a": 1}):
            clean, st = rep.sanitize_news_rows(bad, PS, PE, GA)
            self.assertEqual(clean, [])
        clean, st = rep.sanitize_news_rows([None, 5, [], "x"], PS, PE, GA)
        self.assertEqual(st["rejected_not_object"], 4)

    def test_tariff(self):
        recs = [tariff(1), tariff(1), tariff(2, source_url="http://x.com/a"), tariff(3, captured_at="2026-10-01T09:00:00"),
                tariff(4, captured_at="2026-10-06T09:00:00+05:30"), tariff(5, country=None), tariff(6, evil="x", telegram_x="y")]
        clean, st = rep.sanitize_tariff_records(recs, GA)
        self.assertEqual([r["record_id"] for r in clean], ["T1", "T6"])
        self.assertEqual(set(clean[1]), set(wr.TARIFF_FIELDS))
        self.assertEqual(st["duplicate"], 1)
        self.assertEqual(st["rejected_future_capture"], 1)


class Summary(unittest.TestCase):
    def test_counts(self):
        rows = [row(1, original_country="A"), row(2, original_country="A"), row(3, original_country=None, score=None)]
        s = S(rows)
        self.assertEqual(s["by_country"][0], ("A", 2))
        self.assertIn(("Not stated", 1), s["by_country"])
        self.assertEqual(sum(n for _, n in s["by_day"]), 3)
        self.assertEqual(len(s["by_day"]), 7)
        self.assertEqual(s["score_count"], 2)
        self.assertIsNone(s["top"][-1]["score"])  # unscored last

    def test_no_risk_inference(self):
        s = S([row(1, risk_level=None)])
        self.assertEqual(s["by_risk"], [("not stated", 1)])


def pdf_text(b):
    import pypdf
    r = pypdf.PdfReader(io.BytesIO(b))
    return "\n".join(p.extract_text() for p in r.pages)


class Pdf(unittest.TestCase):
    def setUp(self):
        self.rows = [row(i, original_country=("A", "B", "C")[i % 3]) for i in range(40)]
        self.pdf = wr.build_weekly_report(self.rows, [tariff(1), tariff(2)], period_start=PS, period_end=PE, generated_at=GA)
        self.text = pdf_text(self.pdf)

    def test_valid_pdf_and_scope(self):
        self.assertTrue(self.pdf.startswith(b"%PDF-"))
        t = " ".join(self.text.split())
        for s in ("supplied data", "not complete coverage", "not legal", "tariff advice", "IST (UTC+05:30)"):
            self.assertIn(s.lower(), t.lower())
        self.assertIn("40 news items", t)

    def test_links_present_and_https(self):
        import pypdf
        r = pypdf.PdfReader(io.BytesIO(self.pdf))
        uris = [a.get_object()["/A"]["/URI"] for p in r.pages for a in (p.get("/Annots") or [])]
        self.assertTrue(uris)
        self.assertTrue(all(u.startswith("https://") for u in uris))

    def test_no_third_party_name_in_output(self):
        low = self.pdf.lower()
        for x in (b"reportlab", b"worldmonitor", b"koala73", b"python", b"liberation"):
            self.assertFalse(x in low, x)
        import pypdf
        m = pypdf.PdfReader(io.BytesIO(self.pdf), strict=True).metadata
        self.assertIn("Copyright (c) 2026 Push", m.creator)
        self.assertIn("Copyright (c) 2026 Push", pdf_text(self.pdf))

    def test_phone_page_text_size(self):
        import pypdf
        r = pypdf.PdfReader(io.BytesIO(self.pdf))
        self.assertGreater(len(r.pages), 1)
        self.assertEqual(round(float(r.pages[0].mediabox.width)), 390)

    def test_metadata_date_is_generated_at(self):
        import pypdf
        m = pypdf.PdfReader(io.BytesIO(self.pdf)).metadata
        self.assertEqual(m.creation_date.astimezone(timezone.utc), GA.astimezone(timezone.utc))

    def test_output_independent_of_environment(self):
        import os
        old = os.environ.get("SOURCE_DATE_EPOCH")
        try:
            for v in ("123", "notanumber", None):
                if v is None:
                    os.environ.pop("SOURCE_DATE_EPOCH", None)
                else:
                    os.environ["SOURCE_DATE_EPOCH"] = v
                again = wr.build_weekly_report(self.rows, [tariff(1), tariff(2)], period_start=PS, period_end=PE, generated_at=GA)
                self.assertEqual(again, self.pdf)
        finally:
            if old is None:
                os.environ.pop("SOURCE_DATE_EPOCH", None)
            else:
                os.environ["SOURCE_DATE_EPOCH"] = old

    def test_deterministic(self):
        again = wr.build_weekly_report(self.rows, [tariff(1), tariff(2)], period_start=PS, period_end=PE, generated_at=GA)
        self.assertEqual(again, self.pdf)

    def test_empty_inputs(self):
        b = wr.build_weekly_report([], None, period_start=PS, period_end=PE, generated_at=GA)
        t = " ".join(pdf_text(b).split())
        self.assertIn("does not mean nothing happened", t)
        self.assertIn("No tariff evidence was supplied", t)

    def test_hostile_and_non_latin_text(self):
        r = row(1, title="<b>Bold</b> & <a href='javascript:x'>x</a> \u0b87\u0ba8\u0bcd\u0ba4\u0bbf\u0baf\u0bbe", summary="</para><br/>")
        b = wr.build_weekly_report([r], period_start=PS, period_end=PE, generated_at=GA)
        t = pdf_text(b)
        self.assertIn("<b>Bold</b>", t)
        self.assertNotIn("javascript", " ".join(a.get_object()["/A"]["/URI"] for p in __import__("pypdf").PdfReader(io.BytesIO(b)).pages for a in (p.get("/Annots") or [])))

    def test_unknown_timezone(self):
        with self.assertRaises(ValueError):
            rep.summarize_week([], None, PS, PE, GA, display_tz="Nowhere/Land")

    def test_other_display_tz_stated(self):
        b = wr.build_weekly_report([row(1)], period_start=PS, period_end=PE, generated_at=GA, display_tz="America/Los_Angeles")
        self.assertIn("UTC-07:00", pdf_text(b))


class Review2(unittest.TestCase):
    def uris(self, b):
        import pypdf
        r = pypdf.PdfReader(io.BytesIO(b), strict=True)
        return [a.get_object()["/A"]["/URI"] for p in r.pages for a in (p.get("/Annots") or [])]

    def test_renderer_revalidates_links(self):
        s = S([row(1), row(2)], [tariff(1)])
        evil = ["javascript:alert(1)", "data:text/html,x", "http://e.com/x", "file:///etc/passwd", "https://u:p@e.com/", None, 7]
        for u in evil:
            s2 = dict(s)
            s2["top"] = [dict(r, url=u) for r in s["top"]]
            s2["tariffs"] = [dict(r, source_url=u) for r in s["tariffs"]]
            self.assertEqual(self.uris(wr.render_pdf(s2)), [], u)
        good = self.uris(wr.render_pdf(s))
        self.assertTrue(good and all(x.startswith("https://") for x in good))

    def test_renderer_survives_tampered_summary(self):
        s = S([row(1)], [tariff(1)])
        s["top"][0].update(title="x" * 100000, score=10 ** 5000, corroboration_count="a", summary=5)
        s["by_country"] = [("a", 10 ** 5000), 5, ("b",), ("ok", 3)]
        s["news_stats"] = {"accepted": 10 ** 5000, "duplicate": "x"}
        s["by_day"] = [("notadate", 1), (None, 2)]
        b = wr.render_pdf(s)
        self.assertTrue(b.startswith(b"%PDF-"))
        s["generated_at"] = datetime(2026, 1, 1)
        with self.assertRaises(ValueError):
            wr.render_pdf(s)

    def test_extreme_dates_do_not_crash(self):
        for d in ("0001-01-01T00:00:00+14:00", "9999-12-31T23:59:59-12:00", "0001-01-01T00:00:00+00:00",
                  "2026-09-30T10:00:00+99:99", "1969-12-31T23:59:59Z", "2101-01-01T00:00:00Z", "9" * 5000):
            clean, st = rep.sanitize_news_rows([row(1, published_at=d)], PS, PE, GA)
            self.assertEqual(clean, [], d)
        clean, st = rep.sanitize_tariff_records([tariff(1, captured_at="0001-01-01T00:00:00+14:00"),
                                                 tariff(2, captured_at="9999-12-31T23:59:59-12:00")], GA)
        self.assertEqual(clean, [])
        for bad in (datetime(1, 1, 1, tzinfo=timezone(timedelta(hours=14))), datetime(9999, 12, 31, tzinfo=timezone(timedelta(hours=-12)))):
            with self.assertRaises(ValueError):
                rep.sanitize_tariff_records([], bad)

    def test_huge_numbers_and_strings(self):
        import time
        t0 = time.time()
        r = row(1, score=10 ** 5000, corroboration_count=10 ** 5000, title="y" * 5_000_000, summary="z" * 5_000_000)
        r2 = row(2, score=1e300, corroboration_count=-10 ** 20)
        clean, _ = rep.sanitize_news_rows([r, r2], PS, PE, GA)
        self.assertEqual(len(clean), 2)
        self.assertIsNone(clean[0]["score"])
        self.assertIsNone(clean[0]["corroboration_count"])
        self.assertIsNone(clean[1]["score"])
        self.assertLessEqual(len(clean[0]["title"]), 200)
        self.assertLess(time.time() - t0, 5)

    def test_period_length(self):
        for ps, pe in ((PS, PS + timedelta(hours=5)), (PS, PS + timedelta(days=45)), (PS, PS + timedelta(days=400))):
            with self.assertRaises(ValueError):
                rep.sanitize_news_rows([], ps, pe, pe)
        pe = PS + timedelta(days=31)
        s = rep.summarize_week([], None, PS, pe, pe)
        self.assertEqual(len(s["by_day"]), 31)
        s = rep.summarize_week([], None, PS, PS + timedelta(days=1), GA)
        self.assertEqual(len(s["by_day"]), 1)


class Phone(unittest.TestCase):
    def test_min_font_size_at_phone_width(self):
        # pages are 390 pt wide: a 390 px phone view is 1:1, so pt == px.
        import re, zlib, pypdf
        rows = [row(i) for i in range(30)]
        b = wr.build_weekly_report(rows, [tariff(1)], period_start=PS, period_end=PE, generated_at=GA)
        r = pypdf.PdfReader(io.BytesIO(b))
        sizes = set()
        for pg in r.pages:
            data = pg.get_contents().get_data().decode("latin-1")
            sizes |= {float(x) for x in re.findall(r"/F[12] ([0-9.]+) Tf", data)}
        self.assertTrue(sizes)
        self.assertGreaterEqual(min(sizes), 9.0)
        self.assertEqual(r.pages[0].mediabox.width, 390)

    def test_no_text_beyond_margins(self):
        import re, pypdf
        from integration.weekly_report import _pdf
        b = wr.build_weekly_report([row(i, title="longword" * 30) for i in range(10)], [tariff(1)], period_start=PS, period_end=PE, generated_at=GA)
        for pg in pypdf.PdfReader(io.BytesIO(b)).pages:
            data = pg.get_contents().get_data().decode("latin-1")
            for m in re.finditer(r"/F([12]) ([0-9.]+) Tf ([0-9.]+) ([0-9.]+) Td \((.*?)\) Tj", data):
                x = float(m.group(3)); w = _pdf.text_width(re.sub(r"\\(.)", r"\1", m.group(5)), float(m.group(2)), m.group(1) == "2")
                self.assertLessEqual(x + w, 390 - 11.9, m.group(5)[:30])


class Review3(unittest.TestCase):
    def test_lone_surrogates(self):
        r = row(1, title="a\ud800b\udfff c", source="\ud83d")
        b = wr.build_weekly_report([r], period_start=PS, period_end=PE, generated_at=GA, title="T\ud800")
        self.assertTrue(b.startswith(b"%PDF-"))
        clean, _ = rep.sanitize_news_rows([r], PS, PE, GA)
        self.assertNotIn("\ud800", clean[0]["title"])

    def test_render_extreme_summary_dates(self):
        s = S([row(1)], [tariff(1)])
        for k, v in (("generated_at", datetime(1, 1, 1, tzinfo=timezone(timedelta(hours=14)))),
                     ("period_end", datetime(9999, 12, 31, 23, tzinfo=timezone(timedelta(hours=-12)))),
                     ("period_start", datetime(1969, 1, 1, tzinfo=timezone.utc))):
            with self.assertRaises(ValueError):
                wr.render_pdf(dict(s, **{k: v}))
        s2 = dict(s)
        s2["top"] = [dict(s["top"][0], published_at=datetime(1, 1, 1, tzinfo=timezone(timedelta(hours=14))))]
        s2["tariffs"] = [dict(s["tariffs"][0], captured_at=datetime(9999, 12, 31, 23, tzinfo=timezone(timedelta(hours=-12))))]
        self.assertTrue(wr.render_pdf(s2).startswith(b"%PDF-"))

    def test_pairs_capped(self):
        s = S([row(1)])
        s["by_country"] = [("c%d" % i, 1) for i in range(50000)]
        self.assertTrue(wr.render_pdf(s).startswith(b"%PDF-"))
        from integration.weekly_report import _render
        self.assertEqual(len(_render._pairs(s["by_country"])), 1000)
        self.assertEqual(_render._pairs("notalist"), [])

    def test_scheme_normalised_and_port(self):
        self.assertEqual(rep._clean_url("HTTPS://Example.com/a"), "https://Example.com/a")
        self.assertEqual(rep._clean_url("hTtPs://example.com:443/a"), "https://example.com:443/a")
        self.assertIsNone(rep._clean_url("https://example.com:444/a"))
        self.assertIsNone(rep._clean_url("HTTP://example.com/a"))

    def test_table_header_kept_with_first_row(self):
        import pypdf
        for n in range(20, 60):   # sweep so some run breaks right after a heading/table start
            rows = [row(i) for i in range(n)]
            b = wr.build_weekly_report(rows, [tariff(i) for i in range(n % 9 + 1)], period_start=PS, period_end=PE, generated_at=GA)
            for pg in pypdf.PdfReader(io.BytesIO(b)).pages:
                lines = [l.strip() for l in pg.extract_text().splitlines() if l.strip()]
                body = [l for l in lines if not l.startswith(("Supplied data only", "Copyright", "Page "))]
                # a page must not end with a table header row alone
                self.assertFalse(body and body[-1] in ("Day Items", "Country Items", "Category Items", "Source Items", "Check Count"), (n, body[-2:]))


class Writer(unittest.TestCase):
    def test_valid_structure_many_pages(self):
        import pypdf
        rows = [row(i, title="word " * 40 + str(i)) for i in range(200)]
        b = wr.build_weekly_report(rows, [tariff(i) for i in range(80)], period_start=PS, period_end=PE, generated_at=GA)
        r = pypdf.PdfReader(io.BytesIO(b), strict=True)
        self.assertGreater(len(r.pages), 5)
        self.assertIn("Page 1 of %d" % len(r.pages), r.pages[0].extract_text())
        for pg in r.pages:  # all content stays inside the page
            self.assertEqual(round(float(pg.mediabox.width)), 390)
            for a in pg.get("/Annots") or []:
                x0, y0, x1, y1 = [float(v) for v in a.get_object()["/Rect"]]
                self.assertTrue(0 <= x0 < x1 <= 390.1 and 0 <= y0 < y1 <= 780.1, (x0, y0, x1, y1))

    def test_escaping_and_long_words(self):
        r = row(1, title="caf\u00e9 \u20ac a(b)c\\d " + "W" * 300)
        b = wr.build_weekly_report([r], period_start=PS, period_end=PE, generated_at=GA)
        t = pdf_text(b)
        self.assertIn("a(b)c", t)
        self.assertIn("caf\u00e9", t)

    def test_wrap_respects_width(self):
        from integration.weekly_report import _pdf
        for line in _pdf.wrap("lorem ipsum " * 50 + "X" * 200, 11.5, True, 300):
            self.assertLessEqual(_pdf.text_width(line, 11.5, True), 300.01)

    def test_external_validators(self):
        try:
            import pikepdf
        except ImportError:
            self.skipTest("pikepdf not installed")
        b = wr.build_weekly_report([row(i) for i in range(30)], [tariff(1)], period_start=PS, period_end=PE, generated_at=GA)
        with pikepdf.open(io.BytesIO(b)) as pdf:
            self.assertEqual(list(pdf.check()), [])


class Hygiene(unittest.TestCase):
    def test_no_network_or_io_imports_and_header(self):
        d = pathlib.Path(rep.__file__).parent
        banned = {"socket", "http", "urllib.request", "requests", "subprocess", "os", "threading", "sched", "smtplib", "sqlite3"}
        for f in d.glob("*.py"):
            src = f.read_text()
            self.assertTrue(src.startswith("# Copyright (c) 2026 Push"), f.name)
            for n in ast.walk(ast.parse(src)):
                names = []
                if isinstance(n, ast.Import):
                    names = [a.name for a in n.names]
                elif isinstance(n, ast.ImportFrom):
                    names = [n.module or ""]
                for m in names:
                    self.assertNotIn(m, banned, f.name)
            for bad in ("open(", "eval(", "exec(", "environ", "WorldMonitor", "koala73", "reportlab"):
                self.assertNotIn(bad, src, f.name)


if __name__ == "__main__":
    unittest.main()
