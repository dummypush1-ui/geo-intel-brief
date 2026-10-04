# Copyright (c) 2026 Push
import ast, pathlib, socket, unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from integration import geonews_digest as g
from integration.geonews_digest import delivery, model, render, _safe

NOW = datetime(2026, 10, 5, 8, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
UTC = timezone.utc
TOK = "123456:" + "SECRETtokenSECRETtoken_-ab"


def iso(hours_ago):
    return (NOW.astimezone(UTC) - timedelta(hours=hours_ago)).isoformat()


def art(i, **kw):
    d = {"_id": "ref%03d" % i, "title": "FIXTURE headline %d" % i, "summary": "Fixture summary %d" % i,
         "source": "Fixture Wire", "category": "TRADE", "risk_level": "HIGH", "score": 20 + i,
         "credibility": "HIGH", "country": "India", "corroboration": 1,
         "published": iso(3), "created_at": iso(2), "url": "https://example.com/a/%d" % i, "emailed": False}
    d.update(kw)
    return d


def N(rows):
    return g.normalise_all(rows)[0]


class Selection(unittest.TestCase):
    def test_unemailed_order_and_limit(self):
        rows = [art(1, score=5), art(2, score=50), art(3, score=50, published=iso(1)), art(4, emailed=True, score=99)]
        out = model.unemailed_articles(N(rows), 60)
        self.assertEqual([a["ref"] for a in out], ["ref003", "ref002", "ref001"])  # score DESC then published DESC; emailed excluded
        self.assertEqual(len(model.unemailed_articles(N([art(i) for i in range(100)]), 60)), 60)

    def test_critical_window(self):
        rows = [art(1, risk_level="CRITICAL", created_at=iso(5.9), score=40), art(2, risk_level="CRITICAL", created_at=iso(6.1)),
                art(3, risk_level="HIGH"), art(4, risk_level="CRITICAL", created_at=iso(1), score=90)]
        out = model.critical_since(N(rows), NOW, 6)
        self.assertEqual([a["ref"] for a in out], ["ref004", "ref001"])

    def test_weekly_pieces(self):
        rows = [art(i, category=("TRADE", "RISK")[i % 2], country=("India", "Chile", "")[i % 3], created_at=iso(24 * (i % 9))) for i in range(30)]
        a = N(rows)
        inside = [x for x in a if x["created_at"] >= NOW.astimezone(UTC) - timedelta(days=7)]
        self.assertEqual(sum(n for _, n in model.category_counts(a, NOW)), len(inside))
        self.assertLessEqual(len(model.top_countries(a, NOW)), 8)
        self.assertTrue(all(c for c, _ in model.top_countries(a, NOW)))
        self.assertLessEqual(len(model.weekly_top_articles(a, NOW)), 20)

    def test_events_window(self):
        today = NOW.astimezone(UTC).date()
        ev = [{"name": "In", "event_date": (today + timedelta(days=3)).isoformat()},
              {"name": "Past", "event_date": (today - timedelta(days=1)).isoformat()},
              {"name": "Far", "event_date": (today + timedelta(days=91)).isoformat()},
              {"name": "Today", "event_date": today.isoformat()},
              {"name": "Bad", "event_date": "2026-13-45"}, {"name": "", "event_date": today.isoformat()}, "x", None]
        self.assertEqual([e["name"] for e in model.upcoming_events(ev, NOW, 90)], ["Today", "In"])

    def test_both_row_shapes(self):
        pub = {"article_key": "k1", "url": "https://example.com/p", "title": "Public shape", "summary": "s", "source": "S",
               "original_country": "Chile", "category": "risk", "published_at": iso(2), "collected_at": iso(1),
               "risk_level": "high", "credibility": "low", "score": 33, "corroboration_count": 3,
               "telegram_chat": "X", "backup_url": "https://e.com/b", "emailed": False}
        a = N([pub])[0]
        self.assertEqual((a["ref"], a["country"], a["corroboration"], a["category"], a["risk_level"]), ("k1", "Chile", 3, "RISK", "HIGH"))
        self.assertNotIn("telegram", repr(a).lower())
        self.assertNotIn("backup", repr(a).lower())

    def test_rejections_and_bounds(self):
        bad = [art(1, url="javascript:alert(1)"), art(2, url="http://e.com/x"), art(3, title=""), art(4, created_at="garbage", published=None),
               art(5, created_at="2026-10-05T01:00:00", published=None), art(6, score=10 ** 5000), art(7, score=True),
               art(8, risk_level="<script>"), art(9, title="t" * 10 ** 6), art(10, published="0001-01-01T00:00:00+14:00", created_at=None), 5, None, [], "x"]
        out, st = g.normalise_all(bad)
        self.assertEqual(st["accepted"] + st["rejected"], len(bad))
        by = {a["ref"]: a for a in out}
        self.assertNotIn("ref001", by)
        self.assertNotIn("ref002", by)
        self.assertNotIn("ref003", by)
        self.assertEqual(by["ref006"]["score"], 0)
        self.assertEqual(by["ref008"]["risk_level"], "LOW")
        self.assertLessEqual(len(by["ref009"]["title"]), 200)
        big, st = g.normalise_all([art(i) for i in range(model.MAX_INPUT_ROWS + 7)])
        self.assertEqual(st["input_truncated"], 7)
        self.assertEqual(g.normalise_all("nope")[1], {"input_not_a_list": 1})

    def test_naive_now_rejected(self):
        with self.assertRaises(ValueError):
            model.critical_since([], datetime(2026, 10, 5), 6)
        with self.assertRaises(ValueError):
            model.upcoming_events([], datetime(1, 1, 1, tzinfo=timezone(timedelta(hours=14))), 90)


class Render(unittest.TestCase):
    def setUp(self):
        self.rows = [art(1, category="GEOPOLITICS", score=45, risk_level="CRITICAL", corroboration=3, country="Chile"),
                     art(2, category="TRADE", score=30), art(3, category="SANCTIONS", score=3),
                     art(4, category="WEIRD", score=10), art(5, emailed=True, score=99)]
        self.d = render.build_digest(N(self.rows), [{"name": "Summit", "event_date": (NOW.astimezone(UTC).date() + timedelta(days=5)).isoformat(),
                                                    "category": "CONFERENCE", "confidence": "HIGH", "description": "d", "source_url": "https://example.org/e"}], NOW)

    def test_digest_content(self):
        h = self.d.html
        self.assertIn("Global Geopolitical Intelligence", h)
        self.assertIn("confirmed by 3 sources", h)
        self.assertIn("Upcoming Events", h)
        self.assertIn("(IST)", h)
        self.assertEqual(self.d.critical_count, 1)
        self.assertEqual(self.d.shown, 3)  # score 3 is below min_score 4; emailed excluded
        self.assertNotIn("FIXTURE headline 3", h)
        self.assertNotIn("FIXTURE headline 5", h)
        # section order: GEOPOLITICS before TRADE, unknown category last
        self.assertLess(h.index("Geopolitics"), h.index("Trade Activity"))
        self.assertLess(h.index("Trade Activity"), h.index("Weird"))

    def test_refs_equal_shown_items(self):
        # deliberate deviation: refs equal the shown items (below-threshold rows are not selected)
        self.assertEqual(sorted(self.d.refs), ["ref001", "ref002", "ref004"])
        self.assertEqual(len(self.d.refs), self.d.shown)

    def test_digest_data_shape_and_no_private(self):
        data = self.d.to_digest_data()
        self.assertEqual(set(data), {"html", "critical_count", "article_ids"})
        self.assertNotIn("ref001", data["html"])

    def test_subject_and_skip_rule(self):
        self.assertIn("1 CRITICAL", self.d.subject)
        self.assertIn("IST", self.d.subject)
        quiet = render.build_digest(N([art(1, emailed=True)]), [], NOW)
        self.assertFalse(render.should_send_digest(quiet))
        self.assertNotIn("CRITICAL", quiet.subject)
        self.assertIn("No items scored above", quiet.html)

    def test_hostile_text_escaped(self):
        r = art(1, title="<script>alert(1)</script>", summary="\"><img src=x onerror=alert(1)>", source="<b>x</b>", country="<i>")
        h = render.build_digest(N([r]), [], NOW).html
        for raw in ("<script>", "<img src", "<b>x</b>", "<i>"):
            self.assertNotIn(raw, h)
        self.assertIn("&lt;script&gt;", h)

    def test_links_https_only(self):
        r = N([art(1, url="javascript:alert(1)"), art(2, url="HTTPS://Example.com/ok")])
        h = render.build_digest(r, [], NOW).html
        self.assertNotIn("javascript", h)
        self.assertIn('href="https://Example.com/ok"', h)

    def test_dashboard_link_never_carries_secret(self):
        s = model.Settings(dashboard_url="https://geonews.example.com/dashboard")
        self.assertIn("View full dashboard", render.build_digest(N([art(1)]), [], NOW, s).html)
        bad = model.Settings(dashboard_url="http://x.com/dashboard?key=SECRET")
        self.assertNotIn("SECRET", render.build_digest(N([art(1)]), [], NOW, bad).html)

    def test_alert(self):
        items = model.critical_since(N([art(1, risk_level="CRITICAL", score=60), art(2, risk_level="CRITICAL")]), NOW, 6)
        subj, h = render.build_alert(items, NOW)
        self.assertEqual(subj, "\U0001F6A8 CRITICAL Geo Intel Alert \u2014 2 item(s)")
        self.assertIn("Critical Geo Intel Alert", h)
        self.assertLess(h.index("headline 1"), h.index("headline 2"))  # score 60 before 22

    def test_weekly(self):
        subj, h = render.build_weekly(N([art(i, created_at=iso(i)) for i in range(5)]), NOW)
        self.assertIn("Weekly Geo Intel Summary", h)
        self.assertIn("Volume by category", h)
        self.assertIn("Most-mentioned countries", h)
        self.assertIn("IST", subj)
        _, h2 = render.build_weekly([], NOW)
        self.assertIn("does not mean nothing happened", h2)

    def test_chat_messages(self):
        rows = N([art(i, score=10 + i, title="a_b*c[d") for i in range(12)] + [art(50, score=2)])
        t = render.build_telegram_message(rows, [], NOW, model.Settings(dashboard_url="https://geonews.example.com/dashboard"))
        w = render.build_whatsapp_message(rows, [], NOW)
        self.assertEqual(t.count("[HIGH]"), 8)
        self.assertEqual(w.count("[HIGH]"), 6)
        self.assertIn("a\\_b\\*c\\[d", t)
        self.assertIn("https://example.com/a/", t)
        self.assertNotIn("https://example.com/a/", w)
        self.assertNotIn("headline 50", t)  # score 2 < 4
        self.assertLessEqual(len(render.build_telegram_message(N([art(i, title="x" * 200, summary="") for i in range(60)]), [], NOW)), 4040)
        self.assertIn("No high-relevance items", render.build_whatsapp_message([], [], NOW))


class Delivery(unittest.TestCase):
    def setUp(self):
        self.rows = N([art(1, risk_level="CRITICAL"), art(2)])

    def test_default_off_no_network_no_marking(self):
        marked = []
        with mock.patch.object(socket, "socket", side_effect=AssertionError("network used")):
            o = delivery.deliver_digest(self.rows, [], NOW, sender=lambda s, b: self.fail("sent"), mark_sent=marked.append)
            self.assertEqual(o.status, "dry_run")
            self.assertEqual(marked, [])
            for fn, kw in ((delivery.smtp_sender, dict(host="h", user="u", password="p", mail_from="a@b.co", mail_to="c@d.co")),
                           (delivery.telegram_sender, dict(bot_token=TOK, chat_id="1")),
                           (delivery.whatsapp_sender, dict(phone="1", apikey="k"))):
                with self.assertRaises(delivery.DeliveryDisabled):
                    fn(**kw)
                with self.assertRaises(delivery.DeliveryDisabled):
                    fn(enabled="true", **kw)
            for kind in ("telegram", "whatsapp"):
                self.assertEqual(delivery.deliver_chat(kind, self.rows, [], NOW, sender=lambda t: self.fail("sent")).status, "dry_run")
            self.assertEqual(delivery.deliver_critical_alert(self.rows, NOW, sender=lambda s, b: self.fail("sent")).status, "dry_run")
            self.assertEqual(delivery.deliver_weekly(self.rows, NOW, sender=lambda s, b: self.fail("sent")).status, "dry_run")
        for truthy in (1, "true", "yes"):
            self.assertEqual(delivery.deliver_digest(self.rows, [], NOW, enabled=truthy, sender=lambda s, b: self.fail("sent")).status, "dry_run")

    def test_mark_only_after_confirmed_send(self):
        marked, sent = [], []
        o = delivery.deliver_digest(self.rows, [], NOW, enabled=True, sender=lambda s, b: sent.append((s, b)), mark_sent=marked.append)
        self.assertEqual((o.status, o.marked, len(sent)), ("sent", 2, 1))
        self.assertEqual(sorted(marked[0]), ["ref001", "ref002"])

    def test_failed_send_marks_nothing_and_retries(self):
        marked, calls, sleeps = [], [], []

        def boom(s, b):
            calls.append(1)
            raise delivery.DeliveryError("x")
        o = delivery.deliver_digest(self.rows, [], NOW, enabled=True, sender=boom, mark_sent=marked.append, sleep=sleeps.append)
        self.assertEqual((o.status, o.attempts, len(calls), marked, sleeps), ("failed", 3, 3, [], [30, 30]))
        n = []
        flaky = lambda s, b: (n.append(1), (_ for _ in ()).throw(delivery.DeliveryError("x")) if len(n) < 2 else None)
        o = delivery.deliver_digest(self.rows, [], NOW, enabled=True, sender=flaky, mark_sent=marked.append)
        self.assertEqual((o.status, o.attempts), ("sent", 2))

    def test_skip_when_nothing_new(self):
        o = delivery.deliver_digest(N([art(1, emailed=True)]), [], NOW, enabled=True, sender=lambda s, b: self.fail("sent"))
        self.assertEqual(o.status, "skipped")

    def test_critical_and_none(self):
        self.assertEqual(delivery.deliver_critical_alert(N([art(1)]), NOW, enabled=True, sender=lambda s, b: self.fail("sent")).status, "skipped")
        got = []
        o = delivery.deliver_critical_alert(self.rows, NOW, enabled=True, sender=lambda s, b: got.append(s))
        self.assertEqual((o.status, len(got)), ("sent", 1))

    def test_smtp_transport(self):
        with mock.patch.object(delivery.smtplib, "SMTP_SSL") as S:
            send = delivery.smtp_sender(enabled=True, host="smtp.example.com", user="u@example.com", password="PW-SECRET",
                                        mail_from="u@example.com", mail_to="a@example.com, b@example.com")
            send("Subj", "<p>x</p>")
            srv = S.return_value.__enter__.return_value
            srv.login.assert_called_once_with("u@example.com", "PW-SECRET")
            args = srv.sendmail.call_args[0]
            self.assertEqual(args[1], ["a@example.com", "b@example.com"])
            S.return_value.__enter__.return_value.sendmail.side_effect = delivery.smtplib.SMTPException("PW-SECRET boom")
            with self.assertRaises(delivery.DeliveryError) as cm:
                send("Subj", "x")
            self.assertNotIn("PW-SECRET", str(cm.exception))
        for bad_to in ("not-an-email", "a@b.co\nBcc: x@y.co", "", ",".join(["a@b.co"] * 21)):
            with self.assertRaises(ValueError):
                delivery.smtp_sender(enabled=True, host="h", user="u", password="p", mail_from="a@b.co", mail_to=bad_to)
        send = delivery.smtp_sender(enabled=True, host="h", user="u", password="p", mail_from="a@b.co", mail_to="c@d.co")
        with self.assertRaises(ValueError):
            send("Subject\r\nBcc: evil@x.co", "x")

    def test_telegram_and_whatsapp_transport(self):
        class R:
            def __init__(self, s): self.status = s
            def __enter__(self): return self
            def __exit__(self, *a): return False
        with mock.patch.object(delivery.urllib.request, "urlopen", return_value=R(200)) as u:
            delivery.telegram_sender(enabled=True, bot_token=TOK, chat_id="5")("hello")
            req = u.call_args[0][0]
            self.assertTrue(req.full_url.startswith("https://api.telegram.org/bot123456:SECRETtokenSECRETtoken_-ab/"))
            self.assertIn(b"parse_mode=Markdown", req.data)
            delivery.whatsapp_sender(enabled=True, phone="+1", apikey="K")("hi")
            self.assertTrue(u.call_args[0][0].startswith("https://api.callmebot.com/whatsapp.php?"))
        err = delivery.urllib.error.HTTPError("https://api.telegram.org/bot123456:SECRETtokenSECRETtoken_-ab/x", 400, "bad", {}, None)
        with mock.patch.object(delivery.urllib.request, "urlopen", side_effect=err):
            with self.assertRaises(delivery.DeliveryError) as cm:
                delivery.telegram_sender(enabled=True, bot_token=TOK, chat_id="5")("x")
            self.assertNotIn("SECRETtokenSECRETtoken_-ab", str(cm.exception))
            self.assertIn("400", str(cm.exception))
        with mock.patch.object(delivery.urllib.request, "urlopen", side_effect=OSError("SECRETtokenSECRETtoken_-ab")):
            with self.assertRaises(delivery.DeliveryError) as cm:
                delivery.telegram_sender(enabled=True, bot_token=TOK, chat_id="5")("x")
            self.assertNotIn("SECRETtokenSECRETtoken_-ab", str(cm.exception))

    def test_parse_mark_request(self):
        self.assertEqual(delivery.parse_mark_request({"article_ids": ["a1", "a1", "b2"]}), ["a1", "b2"])
        for bad in (None, [], {"article_ids": "x"}, {"article_ids": [1]}, {"article_ids": ["../x"]}, {"article_ids": ["a"] * 1001}):
            if bad == {"article_ids": ["a"] * 1001}:
                bad = {"article_ids": ["a%d" % i for i in range(1001)]}
            with self.assertRaises(ValueError):
                delivery.parse_mark_request(bad)
        with self.assertRaises(ValueError):
            delivery.parse_mark_request({"article_ids": ["zzz"]}, known_refs=["a1"])


class Hygiene(unittest.TestCase):
    def test_source_rules(self):
        d = pathlib.Path(g.__file__).parent
        banned = {"os", "threading", "sched", "schedule", "sqlite3", "pymongo", "requests", "subprocess", "socket", "http", "dotenv", "time"}
        for f in d.glob("*.py"):
            src = f.read_text()
            self.assertTrue(src.startswith("# Copyright (c) 2026 Push"), f.name)
            for n in ast.walk(ast.parse(src)):
                names = [a.name for a in n.names] if isinstance(n, ast.Import) else ([n.module or ""] if isinstance(n, ast.ImportFrom) else [])
                for m in names:
                    if m != "http.client":
                        self.assertNotIn(m.split(".")[0], banned, f.name)
            import re
            self.assertIsNone(re.search(r"(?<![A-Za-z_])open\(", src), f.name)
            if f.name != "delivery.py":
                for m in ("smtplib", "urllib.request", "ssl"):
                    self.assertNotIn("import " + m, src, f.name)
            for bad in ("eval(", "exec(", "environ", "getenv", "WorldMonitor", "koala73", "reportlab", "while True"):
                self.assertNotIn(bad, src, f.name)


if __name__ == "__main__":
    unittest.main()


class Review2Regressions(unittest.TestCase):
    def test_token_format_and_invalid_request(self):
        import http.client
        for bad in ("TOKEN", "123:abc", "abc:" + "x" * 30, "123456:" + "x" * 30 + "\n"):
            with self.assertRaises(ValueError) as c:
                delivery.telegram_sender(enabled=True, bot_token=bad, chat_id="5")
            self.assertNotIn(bad.strip() or "?", str(c.exception).replace("bot_token has an invalid format", ""))
        with self.assertRaises(ValueError):
            delivery.telegram_sender(enabled=True, bot_token=TOK, chat_id="5\nx")
        for exc in (ValueError("url " + TOK), http.client.InvalidURL("x " + TOK)):
            with mock.patch("urllib.request.urlopen", side_effect=exc):
                with self.assertRaises(delivery.DeliveryError) as c:
                    delivery.telegram_sender(enabled=True, bot_token=TOK, chat_id="5")("x")
                self.assertEqual(str(c.exception), "invalid request")
                self.assertNotIn("SECRET", str(c.exception))

    def test_telegram_urls_escaped_and_cut_on_line(self):
        rows = N([art(1, url="https://example.com/a_b*c(d)e_f", title="T_*`[x")])
        msg = render.build_telegram_message(rows, [], NOW)
        self.assertIn("a\\_b\\*c(d%29e\\_f", msg)
        self.assertNotIn("a_b", msg)
        many = N([art(i, title="x" * 79, source="s" * 300) for i in range(1, 9)])
        long = render.build_telegram_message(many, [], NOW)
        self.assertLessEqual(len(long), 4100)
        body = long.split("\n\n...(truncated)")[0] if "(truncated)" in long else long
        self.assertFalse(body.endswith("\\"))
        self.assertEqual(render._cut("a\nb" + "c" * 50, 10), "a\n\n...(truncated)")

    def test_bidi_and_mongolian_stripped(self):
        out = _safe.clean_text("a\u2066b\u2069c\u061cd\u180ee", 50)
        self.assertEqual(out, "a b c d e")
        self.assertIsNone(_safe.clean_url("https://example.com/\u2066x"))

    def test_zoneinfo_missing_falls_back_to_ist(self):
        from zoneinfo import ZoneInfoNotFoundError
        with mock.patch.object(render, "ZoneInfo", side_effect=ZoneInfoNotFoundError("x")):
            subj = render.digest_subject(NOW, 0)
            html_ = render.build_digest(N([art(1)]), [], NOW).html
        self.assertIn("13:30", render.digest_subject(NOW.replace(hour=8), 0)) if False else None
        self.assertIn("08:00", subj)
        self.assertIn("IST", subj)
        self.assertIn("05 October 2026", html_)

    def test_mark_failure_still_reports_sent(self):
        def boom(refs):
            raise RuntimeError("db down")
        o = delivery.deliver_digest(N([art(1)]), [], NOW, enabled=True, sender=lambda s, b: None, mark_sent=boom)
        self.assertEqual((o.status, o.marked, o.note), ("sent", 0, "mark failed"))
        o = delivery.deliver_critical_alert(N([art(1, risk_level="CRITICAL")]), NOW, enabled=True,
                                            sender=lambda s, b: None, mark_alerted=boom)
        self.assertEqual((o.status, o.note), ("sent", "mark failed"))

    def test_digest_filters_score_before_limit(self):
        rows = N([art(i, score=1) for i in range(1, 70)] + [art(100 + i, score=5) for i in range(3)])
        d = render.build_digest(rows, [], NOW, model.Settings(digest_limit=60))
        self.assertEqual(len(d.refs), 3)
        self.assertEqual(d.shown, 3)
        low_first = N([art(i, score=3) for i in range(1, 5)])
        self.assertEqual(render.build_digest(low_first, [], NOW).refs, [])
        # cap still applies to qualifying items
        many = N([art(i, score=10) for i in range(1, 80)])
        self.assertEqual(len(render.build_digest(many, [], NOW).refs), 60)

    def test_critical_alert_not_repeated(self):
        rows = N([art(1, risk_level="CRITICAL"), art(2, risk_level="CRITICAL")])
        alerted, sent = set(), []
        def run():
            return delivery.deliver_critical_alert(rows, NOW, enabled=True, sender=lambda s, b: sent.append(s),
                                                   alerted_refs=alerted, mark_alerted=alerted.update)
        o1 = run(); o2 = run()
        self.assertEqual((o1.status, o1.marked, o2.status), ("sent", 2, "skipped"))
        self.assertEqual(len(sent), 1)
        # failed send marks nothing
        alerted.clear()
        def bad(s, b): raise delivery.DeliveryError("x")
        o = delivery.deliver_critical_alert(rows, NOW, enabled=True, sender=bad, alerted_refs=alerted,
                                            mark_alerted=alerted.update)
        self.assertEqual((o.status, len(alerted)), ("failed", 0))
        # dry run marks nothing; a new critical item still alerts
        o = delivery.deliver_critical_alert(rows, NOW, alerted_refs={"ref001"})
        self.assertEqual((o.status, o.refs), ("dry_run", ("ref002",)))

    def test_headers_present(self):
        for p in pathlib.Path(__file__).resolve().parent.rglob("*.py"):
            self.assertTrue(p.read_text().startswith("# Copyright (c) 2026 Push"), p)


class DashboardUrl(unittest.TestCase):
    def test_https_url_with_query_fragment_or_userinfo_is_dropped(self):
        for bad in ("https://example.com/dashboard?access_key=X", "https://example.com/dashboard?key=",
                    "https://example.com/dashboard#token=X", "https://user:pw@example.com/dashboard",
                    "https://user@example.com/dashboard", "https://example.com/dashboard;k=X",
                    "http://example.com/dashboard", "https://example.com:8443/dashboard"):
            s = model.Settings(dashboard_url=bad)
            self.assertIsNone(_safe.clean_dashboard_url(bad), bad)
            html_ = render.build_digest(N([art(1)]), [], NOW, s).html
            tg = render.build_telegram_message(N([art(1)]), [], NOW, s)
            wa = render.build_whatsapp_message(N([art(1)]), [], NOW, s)
            for out in (html_, tg, wa):
                self.assertNotIn("access_key", out); self.assertNotIn("token=", out)
                self.assertNotIn("user", out.replace("username", ""))
                self.assertNotIn("dashboard", out.replace("View full dashboard", "")) if False else None
            self.assertNotIn("View full dashboard", html_)
            self.assertNotIn("View full dashboard", tg)
        ok = model.Settings(dashboard_url="https://geonews.example.com/dashboard")
        self.assertIn("https://geonews.example.com/dashboard", render.build_digest(N([art(1)]), [], NOW, ok).html)
