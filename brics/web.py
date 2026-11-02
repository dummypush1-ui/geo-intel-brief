"""Unified dashboard + cloud trigger routes.
Works in BOTH deploy modes:
  - DEPLOY_MODE=local  -> scheduler.py runs the 24/7 collect/report loop
                          in the background; run this file too (or use
                          `python run_all.py`) just to view the dashboard
                          at http://localhost:5000
  - DEPLOY_MODE=cloud  -> this is the single process Render runs; an
                          external scheduler hits /trigger-collect and
                          /trigger-report to drive the 24/7 loop
"""
import csv
import io
import datetime
from flask import Blueprint, request, jsonify, render_template, Response
from . import config as C
from .app import cmd_collect, cmd_report
from .database import get_store
from .collectors.rss import load_sources, get_source_status
from .video import load_streams, add_stream, remove_stream
from .processing.classifier import is_critical, filter_brics
from core import auth, crosslink

bp = Blueprint("brics", __name__, template_folder="templates")

CRITICAL_WINDOW = datetime.timedelta(hours=24)


def _auth_ok():
    return auth.authorized()


def _dashboard_key_ok(req):
    """Checks the key from either the query string or a submitted form/JSON
    body, so the on-page 'add stream' form works without extra JS wiring."""
    key = req.args.get("key") or req.form.get("key")
    if key is None and req.is_json:
        key = (req.get_json(silent=True) or {}).get("key")
    # Fail closed: the shipped default "changeme" used to unlock stream
    # add/remove for anyone. Fall back to the shared TRIGGER_SECRET when no
    # dedicated DASHBOARD_KEY is configured.
    import hmac
    expected = C.DASHBOARD_KEY
    if auth.is_weak_secret(expected):
        expected = C.TRIGGER_SECRET
    if auth.is_weak_secret(expected):
        return False
    return hmac.compare_digest(str(key or "").encode(), expected.encode())


def _is_within_window(article, now, window):
    """Parses `collected_at` (an ISO 8601 string written by database.py) and
    returns True if it falls within `window` of `now`. Articles with a
    missing/unparseable timestamp are treated as NOT recent, rather than
    crashing the whole request — a single bad row shouldn't take down the
    dashboard."""
    raw = article.get("collected_at")
    if not raw:
        return False
    try:
        collected = datetime.datetime.fromisoformat(raw)
    except (ValueError, TypeError):
        return False
    utc = datetime.timezone.utc
    now = now.replace(tzinfo=utc) if now.tzinfo is None else now.astimezone(utc)
    collected = collected.replace(tzinfo=utc) if collected.tzinfo is None else collected.astimezone(utc)
    return datetime.timedelta(0) <= (now - collected) <= window


def _sources_with_status():
    """BUG FIX: the dashboard's "Sources in use" panel previously just
    echoed config/sources.yaml verbatim — every source looked identical
    whether it was returning 60 fresh articles or had been silently dead
    for weeks (CCTV, G1/Globo, Ahram Online, etc. — see collectors/rss.py).
    This merges in the last collection cycle's per-source result so that's
    finally visible on the page instead of only in the console."""
    sources = load_sources()
    status_map = get_source_status()
    for s in sources:
        st = status_map.get(s.get("name"))
        if st:
            s["last_status"] = st.get("status")
            s["last_count"] = st.get("count")
            s["last_message"] = st.get("message")
            s["last_checked"] = st.get("checked_at")
        else:
            # Never run yet this session, or a scrape/tier-3 source (which
            # doesn't go through rss.py's status tracking at all).
            s["last_status"] = None
    return sources


def _critical_recent(articles, now):
    """BUG FIX: previously `critical = [a for a in articles if is_critical(a)]`
    was labeled "Critical (24h)" on the dashboard but never actually checked
    the timestamp — it just kept-word-matched over whatever `store.recent()`
    happened to return, so week-old critical items would show up as if they
    were from the last day. This actually applies the 24h window."""
    return [a for a in articles if is_critical(a) and _is_within_window(a, now, CRITICAL_WINDOW)]


@bp.get("/health")
def health():
    return jsonify({"status": "ok", "app": "brics", "deploy_mode": C.DEPLOY_MODE, "storage": C.STORAGE_BACKEND})


@bp.get("/")
@bp.get("/dashboard")
def dashboard():
    store = get_store()
    articles = _with_hsn(filter_brics(store.recent(300)))  # safety filter for older/mixed data
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    critical = _critical_recent(articles, now)
    sources = _sources_with_status()
    streams = load_streams()
    # Powers the category/country filter dropdowns on the dashboard —
    # built from whatever's actually present in the current article batch
    # rather than a hardcoded list, so it never shows an empty option for
    # a category/country with zero articles, and never misses a country
    # that config/sources.yaml didn't anticipate.
    categories = sorted({a.get("category") for a in articles if a.get("category")})
    countries = sorted({a.get("country") for a in articles if a.get("country")})
    return render_template(
        "dashboard.html",
        articles=articles,
        critical=critical,
        critical_count=len(critical),
        sources=sources,
        streams=streams,
        categories=categories,
        countries=countries,
        total=len(articles),
        refreshed=now.strftime("%d %b %Y, %H:%M UTC"),
    )


def _with_hsn(articles):
    """Attach HS-code tags (news -> code link). Never lets tagging break the feed."""
    for a in articles:
        try:
            a["hsn"] = crosslink.tag_text(a.get("title", ""), max_codes=2)
        except Exception:  # noqa: BLE001
            a["hsn"] = []
    return articles


@bp.get("/api/articles")
def api_articles():
    store = get_store()
    articles = _with_hsn(filter_brics(store.recent(300)))
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    critical = _critical_recent(articles, now)
    return jsonify({
        "articles": articles,
        "critical": critical,
        "total": len(articles),
        "critical_count": len(critical),
        "refreshed": now.strftime("%d %b %Y, %H:%M:%S UTC"),
    })


@bp.get("/api/sources")
def api_sources():
    return jsonify(_sources_with_status())


@bp.get("/api/streams")
def api_streams():
    return jsonify(load_streams())


@bp.post("/api/streams")
def api_add_stream():
    if not _dashboard_key_ok(request):
        return jsonify({"error": "unauthorized — wrong dashboard key"}), 401
    payload = request.get_json(silent=True) or request.form
    try:
        stream = add_stream(
            name=payload.get("name", ""),
            country=payload.get("country", ""),
            link=payload.get("link") or payload.get("video_id", ""),
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"status": "added", "stream": stream})


@bp.delete("/api/streams/<path:name>")
def api_delete_stream(name):
    if not _dashboard_key_ok(request):
        return jsonify({"error": "unauthorized — wrong dashboard key"}), 401
    removed = remove_stream(name)
    if not removed:
        return jsonify({"error": f'No stream named "{name}"'}), 404
    return jsonify({"status": "removed", "name": name})


@bp.get("/export.csv")
def export_csv():
    """BUG FIX: previously built the CSV by hand-concatenating strings and
    only quoted `title` — any comma in `source`, `published`, etc. silently
    shifted every column after it. Using the stdlib `csv` module quotes and
    escapes every field correctly, including embedded quotes/newlines.

    Optional query params let the dashboard export exactly what's currently
    on screen instead of always dumping everything:
      ?category=TRADE     — case-insensitive exact match on category
      ?country=India       — case-insensitive exact match on country
      ?q=some+text          — substring match against title/source/country
      ?critical_only=1      — only rows classifier.is_critical() flags
      ?limit=500             — cap row count fetched from the store (default 1000)
    """
    store = get_store()
    try:
        limit = max(1, min(int(request.args.get("limit", 1000)), 5000))
    except ValueError:
        limit = 1000
    rows = store.recent(limit)

    category = (request.args.get("category") or "").strip().lower()
    country = (request.args.get("country") or "").strip().lower()
    q = (request.args.get("q") or "").strip().lower()
    critical_only = request.args.get("critical_only") in ("1", "true", "yes")

    if category:
        rows = [r for r in rows if (r.get("category") or "").lower() == category]
    if country:
        rows = [r for r in rows if (r.get("country") or "").lower() == country]
    if q:
        rows = [r for r in rows if q in ((r.get("title") or "") + " " +
                                          (r.get("source") or "") + " " +
                                          (r.get("country") or "")).lower()]
    if critical_only:
        rows = [r for r in rows if is_critical(r)]

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["title", "url", "source", "country", "category",
                      "published", "collected_at", "corroborated_by"])
    for r in rows:
        corroborated = r.get("corroborated_by") or []
        writer.writerow([
            r.get("title", ""), r.get("url", ""), r.get("source", ""),
            r.get("country", ""), r.get("category", ""), r.get("published", ""),
            r.get("collected_at", ""),
            "; ".join(corroborated) if isinstance(corroborated, list) else corroborated,
        ])

    stamp = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).strftime("%Y%m%d_%H%M%S")
    filename = "brics_articles_" + stamp + ".csv"
    return Response(buf.getvalue(), mimetype="text/csv",
                     headers={"Content-Disposition": f"attachment;filename={filename}"})


@bp.post("/trigger-collect")
def trigger_collect():
    if not _auth_ok():
        return auth.deny()
    new_items = cmd_collect()
    return jsonify({"new_items": len(new_items)})


@bp.post("/trigger-report")
def trigger_report():
    if not _auth_ok():
        return auth.deny()
    cmd_report()
    return jsonify({"status": "report cycle complete"})


