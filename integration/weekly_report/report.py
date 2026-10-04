# Copyright (c) 2026 Push
"""Weekly intelligence report: supplied public news rows (+ optional supplied
tariff-evidence records) -> phone-readable PDF.

Pure functions: no network, no database, no application-file or configuration
reads, no clock reads (the caller supplies timezone-aware datetimes), no
import-time side effects. Time zone names are resolved by the standard library
zoneinfo (which reads the system tz database). The PDF is written by this
package's own writer (_pdf.py); there is no third-party runtime dependency.

Closed allowlists: only the fields named in NEWS_FIELDS / TARIFF_FIELDS are
ever copied. Unknown keys (telegram_*, emailed, _id, backup_url, ...) are
dropped, never echoed.
"""
import math
import re
import unicodedata
from collections import Counter
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from . import _pdf

NEWS_FIELDS = (
    "article_key", "project", "url", "title", "summary", "source",
    "original_country", "category", "published_at", "collected_at",
    "risk_level", "credibility", "score", "corroboration_count",
)
TARIFF_FIELDS = (
    "record_id", "country", "product_code", "measure", "rate_text",
    "effective_date", "source_name", "source_url", "captured_at", "note",
)
MAX_NEWS_INPUT = 2000      # rows read from input; the rest are counted, not read
MAX_TARIFF_INPUT = 300
MAX_TOP_ITEMS = 25         # items listed in the PDF
MAX_TARIFF_LISTED = 60
MIN_PERIOD = timedelta(days=1)
MAX_PERIOD = timedelta(days=31)
_NUM_LIMIT = 10 ** 12
_STR_CAPS = {"title": 200, "summary": 400, "source": 80, "original_country": 60,
             "category": 60, "project": 60, "article_key": 120, "risk_level": 30,
             "credibility": 30, "record_id": 80, "country": 60, "product_code": 24,
             "measure": 160, "rate_text": 80, "source_name": 80, "note": 300,
             "effective_date": 40}
_URL_MAX = 500
_DATE_MAX_LEN = 40
_YEAR_MIN, _YEAR_MAX = 1970, 2100
_BAD_CHARS = re.compile(r"[\u0000-\u001f\u007f-\u009f\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff\ud800-\udfff]")
_CREATOR = "Copyright (c) 2026 Push"


def _clean_text(value, cap):
    if not isinstance(value, str):
        return None
    if len(value) > cap * 8:      # bound work on hostile input before normalising
        value = value[: cap * 8]
    s = unicodedata.normalize("NFC", value)
    s = _BAD_CHARS.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        return None
    if len(s) > cap:
        s = s[: cap - 1].rstrip() + "\u2026"
    return s


def _clean_url(value):
    """Strict https only; no credentials, backslashes, control/invisible chars."""
    if not isinstance(value, str) or len(value) > _URL_MAX:
        return None
    if _BAD_CHARS.search(value) or "\\" in value or " " in value:
        return None
    try:
        p = urlsplit(value)
        host = p.hostname
        port = p.port
    except ValueError:
        return None
    if p.scheme != "https" or not host or p.username is not None or p.password is not None:
        return None
    if port not in (None, 443) or "." not in host or not value.isascii():
        return None
    return "https" + value[5:]  # scheme normalised to lowercase


def _parse_dt(value):
    """ISO-8601 with an explicit offset/Z. Naive, over-long, overflowing or
    implausible (outside 1970-2100) values return None."""
    if not isinstance(value, str) or len(value) > _DATE_MAX_LEN:
        return None
    s = value.strip()
    if s.endswith(("Z", "z")):
        s = s[:-1] + "+00:00"
    try:
        d = datetime.fromisoformat(s)
        if d.tzinfo is None or d.utcoffset() is None:
            return None
        u = d.astimezone(timezone.utc)
    except (ValueError, OverflowError, OSError):
        return None
    if not _YEAR_MIN <= u.year <= _YEAR_MAX:
        return None
    return u


def _num(value):
    """Plain int/float only; bool, NaN/inf and |x| > 10**12 are rejected."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if value > _NUM_LIMIT or value < -_NUM_LIMIT:
        return None
    return value


def _check_aware(name, d):
    if not isinstance(d, datetime) or d.tzinfo is None or d.utcoffset() is None:
        raise ValueError("%s must be a timezone-aware datetime" % name)
    try:
        u = d.astimezone(timezone.utc)
    except (OverflowError, ValueError, OSError):
        raise ValueError("%s is out of range" % name)
    if not _YEAR_MIN <= u.year <= _YEAR_MAX:
        raise ValueError("%s is out of range" % name)
    return u


def sanitize_news_rows(rows, period_start, period_end, generated_at):
    """Return (clean_rows, stats). Rows outside [period_start, period_end) or
    published after generated_at are excluded and counted, never silently lost."""
    ps, pe, ga = (_check_aware("period_start", period_start),
                  _check_aware("period_end", period_end),
                  _check_aware("generated_at", generated_at))
    if not ps < pe:
        raise ValueError("period_start must be before period_end")
    if not MIN_PERIOD <= pe - ps <= MAX_PERIOD:
        raise ValueError("period must be between 1 and 31 days")
    stats = Counter()
    clean, seen = [], set()
    if not isinstance(rows, (list, tuple)):
        rows = []
        stats["input_not_a_list"] = 1
    stats["input_total"] = len(rows)
    if len(rows) > MAX_NEWS_INPUT:
        stats["input_truncated"] = len(rows) - MAX_NEWS_INPUT
        rows = rows[:MAX_NEWS_INPUT]
    for r in rows:
        if not isinstance(r, dict):
            stats["rejected_not_object"] += 1
            continue
        item = {}
        for k in NEWS_FIELDS:
            v = r.get(k)
            if k == "url":
                item[k] = _clean_url(v)
            elif k in ("published_at", "collected_at"):
                item[k] = _parse_dt(v)
            elif k in ("score", "corroboration_count"):
                item[k] = _num(v)
            else:
                item[k] = _clean_text(v, _STR_CAPS[k]) if k in _STR_CAPS else None
        if item["title"] is None:
            stats["rejected_no_title"] += 1
            continue
        if item["url"] is None:
            stats["rejected_bad_url"] += 1
            continue
        if item["published_at"] is None:
            stats["rejected_bad_or_naive_date"] += 1
            continue
        if item["published_at"] > ga:
            stats["rejected_future_date"] += 1
            continue
        if not ps <= item["published_at"] < pe:
            stats["outside_period"] += 1
            continue
        ident = item["article_key"] or item["url"]
        if ident in seen:
            stats["duplicate"] += 1
            continue
        seen.add(ident)
        c = item["corroboration_count"]
        if c is not None and (not isinstance(c, int) or c < 0):
            item["corroboration_count"] = None
        clean.append(item)
    stats["accepted"] = len(clean)
    return clean, dict(stats)


def sanitize_tariff_records(records, generated_at):
    ga = _check_aware("generated_at", generated_at)
    stats = Counter()
    clean, seen = [], set()
    if records is None:
        records = []
    if not isinstance(records, (list, tuple)):
        records, stats["input_not_a_list"] = [], 1
    stats["input_total"] = len(records)
    if len(records) > MAX_TARIFF_INPUT:
        stats["input_truncated"] = len(records) - MAX_TARIFF_INPUT
        records = records[:MAX_TARIFF_INPUT]
    for r in records:
        if not isinstance(r, dict):
            stats["rejected_not_object"] += 1
            continue
        item = {}
        for k in TARIFF_FIELDS:
            v = r.get(k)
            if k == "source_url":
                item[k] = _clean_url(v)
            elif k == "captured_at":
                item[k] = _parse_dt(v)
            else:
                item[k] = _clean_text(v, _STR_CAPS[k])
        if not item["country"] or not item["measure"]:
            stats["rejected_missing_country_or_measure"] += 1
            continue
        if item["source_url"] is None:
            stats["rejected_bad_source_url"] += 1
            continue
        if item["captured_at"] is None:
            stats["rejected_bad_or_naive_capture_date"] += 1
            continue
        if item["captured_at"] > ga:
            stats["rejected_future_capture"] += 1
            continue
        ident = item["record_id"] or (item["country"], item["product_code"], item["measure"], item["source_url"])
        if ident in seen:
            stats["duplicate"] += 1
            continue
        seen.add(ident)
        clean.append(item)
    stats["accepted"] = len(clean)
    return clean, dict(stats)


def _tz(name):
    try:
        return ZoneInfo(name)
    except Exception:
        raise ValueError("unknown display timezone")


def fmt_dt(d, tzname, with_time=True):
    """'05 Oct 2026, 14:30 IST (UTC+05:30)' - zone always stated."""
    z = _tz(tzname)
    L = d.astimezone(z)
    off = L.strftime("%z")
    off = "UTC%s:%s" % (off[:3], off[3:])
    abbr = L.tzname() or ""
    zone = "%s (%s)" % (abbr, off) if abbr and not abbr[0] in "+-" else off
    if with_time:
        return "%s, %s %s" % (L.strftime("%d %b %Y"), L.strftime("%H:%M"), zone)
    return "%s %s" % (L.strftime("%d %b %Y"), zone)


def summarize_week(news_rows, tariff_records, period_start, period_end,
                   generated_at, display_tz="Asia/Kolkata", title="Weekly intelligence report"):
    """Pure data summary used by render_pdf; also useful for tests."""
    news, nstats = sanitize_news_rows(news_rows, period_start, period_end, generated_at)
    tariffs, tstats = sanitize_tariff_records(tariff_records, generated_at)
    z = _tz(display_tz)
    by_country = Counter(r["original_country"] or "Not stated" for r in news)
    by_category = Counter(r["category"] or "Not stated" for r in news)
    by_source = Counter(r["source"] or "Not stated" for r in news)
    by_risk = Counter((r["risk_level"] or "not stated").lower() for r in news)
    by_day = Counter(r["published_at"].astimezone(z).date() for r in news)
    scores = [r["score"] for r in news if r["score"] is not None]
    ordered = sorted(
        news,
        key=lambda r: (r["score"] is None, -(r["score"] or 0), -(r["published_at"].timestamp()), r["url"]),
    )
    days = []
    d = period_start.astimezone(z).date()
    last = (period_end.astimezone(z) - timedelta(microseconds=1)).date()
    while d <= last:
        days.append((d, by_day.get(d, 0)))
        d += timedelta(days=1)
    return {
        "title": _clean_text(title, 100) or "Weekly intelligence report",
        "display_tz": display_tz,
        "period_start": period_start, "period_end": period_end, "generated_at": generated_at,
        "news": news, "news_stats": nstats, "tariffs": tariffs, "tariff_stats": tstats,
        "by_country": by_country.most_common(), "by_category": by_category.most_common(),
        "by_source": by_source.most_common(), "by_risk": by_risk.most_common(),
        "by_day": days,
        "score_count": len(scores),
        "score_min": min(scores) if scores else None,
        "score_max": max(scores) if scores else None,
        "top": ordered[:MAX_TOP_ITEMS],
        "top_omitted": max(0, len(ordered) - MAX_TOP_ITEMS),
    }


