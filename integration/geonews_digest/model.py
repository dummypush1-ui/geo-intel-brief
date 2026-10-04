# Copyright (c) 2026 Push
"""Row normalisation and the selection rules ported from geonews database.py.

geonews ran these as MongoDB queries. Here they are pure functions over
supplied rows (no database, no clock reads: `now` is passed in), with the
same ordering, limits and thresholds.

Accepted row shapes: the legacy geonews document (title, summary, source,
category, risk_level, score, credibility, country, corroboration, published,
created_at, url, emailed, _id) and the public news shape (original_country,
corroboration_count, published_at, collected_at, article_key). Anything else
is ignored. `ref` is an opaque handle (article_key, else str(_id)) used only
to mark items as sent; it is never printed in any output.
"""
from collections import Counter
from dataclasses import dataclass, field
from datetime import timedelta

from . import _safe

MAX_INPUT_ROWS = 20000
CATEGORIES = ("GEOPOLITICS", "CONFERENCE", "TRADE", "SANCTIONS", "RISK", "RESEARCH", "GENERAL")
RISK_LEVELS = ("CRITICAL", "HIGH", "MODERATE", "LOW")
CREDIBILITY = ("HIGH", "MEDIUM", "LOW")


@dataclass(frozen=True)
class Settings:
    """Defaults equal geonews config.py / email_report.py defaults."""
    min_score: int = 4                      # email_report.MIN_SCORE
    upcoming_days: int = 90                 # UPCOMING_DAYS
    digest_limit: int = 60                  # unemailed_articles(limit=60)
    active_categories: tuple = CATEGORIES   # ACTIVE_CATEGORIES default, in this order
    critical_lookback_hours: int = 6        # CRITICAL_ALERT_LOOKBACK_HOURS
    weekly_days: int = 7
    weekly_limit: int = 20                  # weekly_top_articles(limit=20)
    weekly_countries: int = 8               # top_countries(limit=8)
    chat_telegram_limit: int = 8            # telegram_report.build_message(limit=8)
    chat_whatsapp_limit: int = 6            # whatsapp_report.build_message(limit=6)
    chat_min_score: int = 4
    display_tz: str = "Asia/Kolkata"        # zone stated in every printed date
    dashboard_url: str = ""                 # plain https URL, never with a secret


def _s(row, key, cap):
    return _safe.clean_text(row.get(key), cap)


def normalise_article(row):
    """-> clean dict or None (no title / no safe https url / no usable date)."""
    if not isinstance(row, dict):
        return None
    title = _s(row, "title", 200)
    url = _safe.clean_url(row.get("url"))
    if title is None or url is None:
        return None
    published = _safe.parse_dt(row.get("published_at") if row.get("published_at") is not None else row.get("published"))
    created = _safe.parse_dt(row.get("collected_at") if row.get("collected_at") is not None else row.get("created_at"))
    if created is None and published is None:
        return None
    ref = _s(row, "article_key", 120)
    if ref is None and row.get("_id") is not None:
        ref = _safe.clean_text(str(row.get("_id")), 120)
    risk = (_s(row, "risk_level", 30) or "LOW").upper()
    cred = (_s(row, "credibility", 30) or "MEDIUM").upper()
    score = _safe.num(row.get("score"))
    corr = _safe.num(row.get("corroboration_count") if row.get("corroboration_count") is not None else row.get("corroboration"))
    category = (_s(row, "category", 40) or "GENERAL").upper()
    return {
        "ref": ref,
        "title": title,
        "summary": _s(row, "summary", 600) or "",
        "source": _s(row, "source", 80) or "",
        "category": category,
        "risk_level": risk if risk in RISK_LEVELS else "LOW",
        "credibility": cred if cred in CREDIBILITY else "MEDIUM",
        "score": score if isinstance(score, int) else (int(score) if score is not None else 0),
        "corroboration": corr if isinstance(corr, int) and corr >= 1 else 1,
        "country": _s(row, "original_country", 60) or _s(row, "country", 60) or "",
        "url": url,
        "published": published,
        "created_at": created or published,
        "emailed": row.get("emailed") is True,
    }


def normalise_all(rows):
    """-> (articles, stats). Input beyond MAX_INPUT_ROWS is counted, not read."""
    stats = Counter()
    out = []
    if not isinstance(rows, (list, tuple)):
        stats["input_not_a_list"] = 1
        return out, dict(stats)
    stats["input_total"] = len(rows)
    if len(rows) > MAX_INPUT_ROWS:
        stats["input_truncated"] = len(rows) - MAX_INPUT_ROWS
        rows = rows[:MAX_INPUT_ROWS]
    for r in rows:
        a = normalise_article(r)
        if a is None:
            stats["rejected"] += 1
        else:
            out.append(a)
    stats["accepted"] = len(out)
    return out, dict(stats)


def _epoch(d):
    return d.timestamp() if d else 0.0


def by_score_then_published(a):
    # geonews sort: score DESC, published DESC (ties keep input order: sort is stable)
    return (-a["score"], -_epoch(a["published"]))


def unemailed_articles(articles, limit=60, min_score=0):
    """port of database.unemailed_articles: not yet emailed, best first, capped.
    DELIBERATE DEVIATION: items below min_score are dropped BEFORE the cap, so
    what is selected (and later marked sent) is exactly what the digest shows.
    geonews capped first and marked unseen low-score items as sent."""
    pool = [a for a in articles if not a["emailed"] and a["score"] >= min_score]
    return sorted(pool, key=by_score_then_published)[: max(0, limit)]


def critical_since(articles, now, hours=6):
    """port of database.critical_since: CRITICAL and created_at >= now-hours, score DESC."""
    now_u = _safe.aware("now", now)
    cutoff = now_u - timedelta(hours=hours)
    pool = [a for a in articles if a["risk_level"] == "CRITICAL" and a["created_at"] >= cutoff]
    return sorted(pool, key=lambda a: -a["score"])


def weekly_window(articles, now, days=7):
    now_u = _safe.aware("now", now)
    cutoff = now_u - timedelta(days=days)
    return [a for a in articles if a["created_at"] >= cutoff]


def weekly_top_articles(articles, now, days=7, limit=20):
    return sorted(weekly_window(articles, now, days), key=lambda a: -a["score"])[: max(0, limit)]


def category_counts(articles, now, days=7):
    c = Counter(a["category"] for a in weekly_window(articles, now, days))
    return sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))   # ties by name (Mongo leaves ties unordered)


def top_countries(articles, now, days=7, limit=8):
    c = Counter(a["country"] for a in weekly_window(articles, now, days) if a["country"])
    return sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[: max(0, limit)]


def normalise_event(row):
    if not isinstance(row, dict):
        return None
    name = _safe.clean_text(row.get("name"), 160)
    date = _safe.clean_text(row.get("event_date"), 10)
    if not name or not date or len(date) != 10:
        return None
    try:
        from datetime import date as _d
        d = _d.fromisoformat(date)
    except ValueError:
        return None
    return {"name": name, "event_date": d,
            "category": _safe.clean_text(row.get("category"), 40) or "",
            "confidence": _safe.clean_text(row.get("confidence"), 30) or "",
            "description": _safe.clean_text(row.get("description"), 400) or "",
            "source_url": _safe.clean_url(row.get("source_url"))}


def upcoming_events(rows, now, days=90):
    """port of database.upcoming_events: today <= event_date <= today+days (UTC date), date ASC."""
    now_u = _safe.aware("now", now)
    today = now_u.date()
    end = today + timedelta(days=days)
    evs = []
    if isinstance(rows, (list, tuple)):
        for r in rows[:5000]:
            e = normalise_event(r)
            if e and today <= e["event_date"] <= end:
                evs.append(e)
    return sorted(evs, key=lambda e: e["event_date"])
