# Copyright (c) 2026 Push
"""Layout and rendering of a summarize_week() result with the own PDF writer.

The renderer does not trust the summary it is given: every text is cleaned
again, every number re-bounded, every link re-validated (https only) before
it can become a PDF link annotation.
"""
from datetime import datetime, timezone
from urllib.parse import urlsplit

from . import _pdf
from .report import (MAX_TARIFF_LISTED, MAX_TOP_ITEMS, _CREATOR, _clean_text, _clean_url,
                     _YEAR_MAX, _YEAR_MIN, _num, fmt_dt, summarize_week)

MM = _pdf.MM
LEFT = 12.0
RIGHT = _pdf.PAGE_W - 12.0
WIDTH = RIGHT - LEFT
TOP = _pdf.PAGE_H - 14.0
BOTTOM = 36.0
INK = (0, 0, 0)
NAVY = (0.07, 0.21, 0.36)
BLUE = (0.04, 0.34, 0.82)
GRID = (0.72, 0.76, 0.8)
HEAD_BG = (0.9, 0.93, 0.96)
NOTE_BG = (1, 0.96, 0.84)


def _s(v, cap=200, default="-"):
    return _clean_text(v, cap) or default


class _Flow:
    def __init__(self):
        self.pages = []
        self.y = 0
        self.new_page()

    def new_page(self):
        self.pages.append(_pdf.Page())
        self.y = TOP

    @property
    def page(self):
        return self.pages[-1]

    def ensure(self, h):
        if self.y - h < BOTTOM:
            self.new_page()

    def para(self, text, size=11.5, leading=None, bold=False, color=INK, after=5, bg=None,
             x=LEFT, width=WIDTH, before=0):
        leading = leading or size * 1.4
        pad = 6 if bg else 0
        lines = _pdf.wrap(text, size, bold, width - 2 * pad)
        self.y -= before
        if bg:
            h = len(lines) * leading + 2 * pad
            self.ensure(h)
            self.page.rect(x, self.y - h, width, h, fill=bg)
            self.y -= pad
        for ln in lines:
            self.ensure(leading)
            self.page.text(x + pad, self.y - leading + (leading - size) / 2 + size * 0.2, ln, size, bold, color)
            self.y -= leading
        self.y -= pad + after

    def link_line(self, url, size=10.5):
        """Host name, underlined and clickable; link only if the URL validates."""
        u = _clean_url(url)
        if u is None:
            return
        label = urlsplit(u).hostname or "link"
        leading = size * 1.4
        self.ensure(leading)
        base = self.y - leading + (leading - size) / 2 + size * 0.2
        w = _pdf.text_width(label, size)
        self.page.text(LEFT, base, label, size, False, BLUE)
        self.page.hline(LEFT, LEFT + w, base - 1.2, BLUE, 0.5)
        self.page.link(LEFT, base - 2, LEFT + w, base + size, u)
        self.y -= leading

    def table(self, rows, widths, header=True):
        """rows: list of list of (text, bold, url_or_None)."""
        size, lead, pad = 10.5, 13.5, 4
        xs = [LEFT]
        for w in widths:
            xs.append(xs[-1] + w)
        head = rows[0] if header else None

        def height(row):
            return max(len(_pdf.wrap(c[0], size, c[1], widths[i] - 2 * pad)) for i, c in enumerate(row)) * lead + 2 * pad - 2

        def draw(row, is_head):
            h = height(row)
            top = self.y
            for i, (text, bold, url) in enumerate(row):
                self.page.rect(xs[i], top - h, widths[i], h, fill=HEAD_BG if is_head else None, stroke=GRID, line=0.4)
                ty = top - pad - size + 1
                for ln in _pdf.wrap(text, size, bold, widths[i] - 2 * pad):
                    u = _clean_url(url) if url else None
                    if u:
                        w = _pdf.text_width(ln, size, bold)
                        self.page.text(xs[i] + pad, ty, ln, size, bold, BLUE)
                        self.page.hline(xs[i] + pad, xs[i] + pad + w, ty - 1.2, BLUE, 0.5)
                        self.page.link(xs[i] + pad, ty - 2, xs[i] + pad + w, ty + size, u)
                    else:
                        self.page.text(xs[i] + pad, ty, ln, size, bold, INK)
                    ty -= lead
            self.y -= h

        for idx, row in enumerate(rows):
            h = height(row)
            if header and idx == 0 and len(rows) > 1:
                h += height(rows[1])   # keep the header with its first data row
            if self.y - h < BOTTOM:
                self.new_page()
                if head is not None and idx != 0:
                    draw(head, True)
            draw(row, header and idx == 0)
        self.y -= 8

    def heading(self, text):
        self.ensure(40)
        self.para(text, size=14, bold=True, color=NAVY, after=4, before=8)


def _item_block(flow, i, r, tz):
    meta = "%s | %s | %s" % (r["source"], r["country"], r["when"])
    extra = "Category: %s | Risk label: %s | Score: %s | Corroboration: %s" % (
        r["category"], r["risk"], r["score"], r["corr"])
    size = 11.5
    h = (len(_pdf.wrap("%d. %s" % (i, r["title"]), size, True, WIDTH)) * size * 1.4 + 2
         + len(_pdf.wrap(meta, 10.5, False, WIDTH)) * 14.7
         + (len(_pdf.wrap(r["summary"], 10.5, False, WIDTH)) * 14.7 if r["summary"] else 0)
         + len(_pdf.wrap(extra, 10.5, False, WIDTH)) * 14.7 + 14.7 + 8)
    flow.ensure(h)  # keep one item together
    flow.para("%d. %s" % (i, r["title"]), size=size, bold=True, after=2)
    flow.para(meta, size=10.5, after=0)
    if r["summary"]:
        flow.para(r["summary"], size=10.5, after=0)
    flow.para(extra, size=10.5, after=0)
    flow.link_line(r["url"])
    flow.y -= 8


def _dt_ok(d):
    """Aware datetime whose UTC year is within 1970-2100 (no overflow)."""
    try:
        if not isinstance(d, datetime) or d.tzinfo is None or d.utcoffset() is None:
            return False
        return _YEAR_MIN <= d.astimezone(timezone.utc).year <= _YEAR_MAX
    except (OverflowError, ValueError, OSError):
        return False


def _fmt_num(n):
    n = _num(n)
    if n is None:
        return "-"
    return ("%d" % n) if isinstance(n, int) else ("%.2f" % n).rstrip("0").rstrip(".")


def _pairs(v, limit=1000):
    out = []
    for item in (v if isinstance(v, (list, tuple)) else [])[:limit]:
        try:
            k, n = item
            n = _num(n)
            if isinstance(n, int) and n >= 0:
                out.append((_s(k, 80), n))
        except (TypeError, ValueError):
            continue
    return out


def _top_n(pairs, n=5):
    return ", ".join("%s (%d)" % (k, v) for k, v in pairs[:n])


def render_pdf(summary):
    """Render a summarize_week() result to PDF bytes. Revalidates everything."""
    tz = summary["display_tz"]
    for k in ("period_start", "period_end", "generated_at"):
        if not _dt_ok(summary.get(k)):
            raise ValueError("%s must be a timezone-aware datetime between %d and %d" % (k, _YEAR_MIN, _YEAR_MAX))
    f = lambda d, t=True: fmt_dt(d, tz, t)
    ga = summary["generated_at"]
    flow = _Flow()
    title = _s(summary.get("title"), 100, "Weekly intelligence report")

    dt_ok = _dt_ok

    news = []
    for r in (summary.get("news") or [])[:2000]:
        if not isinstance(r, dict) or not dt_ok(r.get("published_at")):
            continue
        news.append(r)
    top = []
    for r in (summary.get("top") or [])[:MAX_TOP_ITEMS]:
        if not isinstance(r, dict) or not dt_ok(r.get("published_at")):
            continue
        top.append({"title": _s(r.get("title"), 200), "summary": _s(r.get("summary"), 400, ""),
                    "source": _s(r.get("source"), 80, "source not stated"),
                    "country": _s(r.get("original_country"), 60, "country not stated"),
                    "category": _s(r.get("category"), 60), "risk": _s(r.get("risk_level"), 30),
                    "score": _fmt_num(r.get("score")), "corr": _fmt_num(r.get("corroboration_count")),
                    "when": f(r["published_at"]), "url": r.get("url")})
    by_country = _pairs(summary.get("by_country"))
    by_category = _pairs(summary.get("by_category"))
    by_source = _pairs(summary.get("by_source"))
    by_risk = _pairs(summary.get("by_risk"))
    nst = summary.get("news_stats") or {}
    tst = summary.get("tariff_stats") or {}

    scope = ("Scope: this report covers only the supplied data listed here. It is not complete coverage "
             "of world events, and it is not legal, customs or tariff advice. Check official sources "
             "before acting. Risk labels and scores are those supplied with each item, not judged here.")
    flow.para(title, size=19, bold=True, leading=23, after=6)
    flow.para("Period: %s to %s" % (f(summary["period_start"]), f(summary["period_end"])))
    flow.para("Generated: %s" % f(ga))
    flow.para(scope, size=11, bg=NOTE_BG, after=10, before=4)

    flow.heading("Summary in numbers")
    if news:
        known = len([c for c, _ in by_country if c != "Not stated"])
        lines = ["%d news items were supplied and accepted for this period." % len(news),
                 "They come from %d source(s) and mention %d country label(s) (as labelled in the data)." % (
                     len(by_source), known),
                 "Most items by country: %s." % _top_n(by_country),
                 "Most items by category: %s." % _top_n(by_category),
                 "Supplied risk labels: %s." % _top_n(by_risk, 6)]
        if summary.get("score_count"):
            lines.append("Supplied scores range from %s to %s across %d items." % (
                _fmt_num(summary.get("score_min")), _fmt_num(summary.get("score_max")),
                _num(summary.get("score_count")) or 0))
    else:
        lines = ["No supplied news items fall in this period. This does not mean nothing happened."]
    for ln in lines:
        flow.para("\u2022 " + ln)

    flow.heading("Items per day (%s)" % tz)
    rows = [[("Day", True, None), ("Items", True, None)]]
    for d, n in (summary.get("by_day") or [])[:31]:
        try:
            rows.append([(d.strftime("%a %d %b %Y"), False, None), (str(_num(n) or 0), False, None)])
        except (AttributeError, ValueError):
            continue
    flow.table(rows, [WIDTH * 0.6, WIDTH * 0.4])

    for label, pairs in (("Country", by_country), ("Category", by_category), ("Source", by_source)):
        if not pairs:
            continue
        # Reserve heading, table header and first wrapped data row together.
        first = pairs[0]
        first_h = max(len(_pdf.wrap(str(first[0]), 10.5, False, WIDTH * .75 - 8)), len(_pdf.wrap(str(first[1]), 10.5, False, WIDTH * .25 - 8))) * 13.5 + 6
        flow.ensure(32 + 19.5 + first_h)
        flow.heading("By %s%s" % (label.lower(), " (top 12)" if len(pairs) > 12 else ""))
        rows = [[(label, True, None), ("Items", True, None)]] + [[(k, False, None), (str(v), False, None)] for k, v in pairs[:12]]
        flow.table(rows, [WIDTH * 0.75, WIDTH * 0.25])

    flow.heading("Top items by supplied score")
    if top:
        flow.para("Sorted by the supplied score, highest first; items without a score come last. "
                  "Tap a source link to open the original article.", size=10.5, after=4)
        for i, r in enumerate(top, 1):
            _item_block(flow, i, r, tz)
        omitted = max(0, len(news) - len(top))
        if omitted:
            flow.para("%d further accepted items are counted above but not listed." % omitted, size=10.5)
    else:
        flow.para("No items to list.")

    flow.heading("Supplied tariff evidence")
    tar = [r for r in (summary.get("tariffs") or []) if isinstance(r, dict) and dt_ok(r.get("captured_at"))]
    if tar:
        flow.para("These records were supplied as evidence with their own source and capture date. "
                  "Rates and rules change; this is not tariff or legal advice and may be out of date.", size=10.5, after=4)
        rows = [[(x, True, None) for x in ("Country / code", "Measure and rate", "Captured", "Source")]]
        for r in tar[:MAX_TARIFF_LISTED]:
            code = _s(r.get("product_code"), 24, "")
            rate = _s(r.get("rate_text"), 80, "")
            eff = _s(r.get("effective_date"), 40, "")
            url = _clean_url(r.get("source_url"))
            host = (urlsplit(url).hostname if url else None) or "no valid link"
            rows.append([
                ("%s%s" % (_s(r.get("country"), 60), (" / " + code) if code else ""), False, None),
                ("%s%s%s" % (_s(r.get("measure"), 160), (": " + rate) if rate else "",
                             (" (effective " + eff + ")") if eff else ""), False, None),
                (f(r["captured_at"], False), False, None),
                (host, False, url)])
        flow.table(rows, [WIDTH * 0.22, WIDTH * 0.38, WIDTH * 0.22, WIDTH * 0.18])
        if len(tar) > MAX_TARIFF_LISTED:
            flow.para("%d further accepted records not listed." % (len(tar) - MAX_TARIFF_LISTED), size=10.5)
    else:
        flow.para("No tariff evidence was supplied for this report. Nothing here implies tariffs are unchanged.")

    flow.heading("Data checks")
    rows = [[("Check", True, None), ("Count", True, None)]]
    names = {"input_total": "News rows supplied", "accepted": "News rows accepted",
             "input_truncated": "News rows beyond input limit (not read)",
             "outside_period": "Outside this period", "duplicate": "Duplicates dropped",
             "rejected_future_date": "Dated after generation time", "rejected_bad_url": "Missing or unsafe link",
             "rejected_no_title": "No title", "rejected_bad_or_naive_date": "Missing, unusable or no-timezone date",
             "rejected_not_object": "Not a valid row"}
    tnames = {"input_total": "Tariff records supplied", "accepted": "Tariff records accepted",
              "input_truncated": "Tariff records beyond input limit", "duplicate": "Tariff duplicates",
              "rejected_bad_source_url": "Tariff: missing or unsafe source link",
              "rejected_bad_or_naive_capture_date": "Tariff: missing, unusable or no-timezone capture date",
              "rejected_future_capture": "Tariff: capture after generation time",
              "rejected_missing_country_or_measure": "Tariff: missing country or measure",
              "rejected_not_object": "Tariff: not a valid record"}
    for src, nm in ((nst, names), (tst, tnames)):
        for k, label in nm.items():
            n = _num(src.get(k))
            if n:
                rows.append([(label, False, None), (str(n), False, None)])
    flow.table(rows, [WIDTH * 0.75, WIDTH * 0.25])
    flow.para("Fields other than the public news fields and the tariff evidence fields are never read or printed. "
              "Text outside the Western European character set prints as \"?\".", size=10.5)

    total = len(flow.pages)
    for n, pg in enumerate(flow.pages, 1):
        grey = (0.33, 0.33, 0.33)
        pg.text(LEFT, 20.0, "Supplied data only. Not complete coverage. Not legal or tariff advice.", 9, False, grey)
        pg.text(LEFT, 9.0, _CREATOR, 9, False, grey)
        label = "Page %d of %d" % (n, total)
        pg.text(RIGHT - _pdf.text_width(label, 9), 9.0, label, 9, False, grey)
    return _pdf.build_pdf(flow.pages, title, "Supplied-data weekly report. " + _CREATOR, _CREATOR, ga)


def build_weekly_report(news_rows, tariff_records=None, *, period_start, period_end,
                        generated_at, display_tz="Asia/Kolkata", title="Weekly intelligence report"):
    """Return PDF bytes. Pure: caller supplies rows and aware datetimes."""
    return render_pdf(summarize_week(news_rows, tariff_records, period_start, period_end,
                                     generated_at, display_tz, title))
