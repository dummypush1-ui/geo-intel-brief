"""Legacy Geo HTTP entry point.

Protected routes require X-Trigger-Secret. Query-string keys are rejected;
mutations are POST-only. /health is public and does not initialize storage.
Cleanup remains disabled until a separately reviewed retention implementation.
No collectors, report senders or database clients load before authorization.
"""
import os
import io
import csv
import threading
import logging
import hmac
import importlib
from datetime import datetime, timezone
from flask import Flask, request, jsonify, Response

from intelligence.geo.config import (ENABLE_GNEWS, EXTRA_RSS_FEEDS, TRIGGER_SECRET,
                     UPCOMING_DAYS, ACTIVE_CATEGORIES,
                     ENABLE_CRITICAL_ALERTS, ENABLE_WEEKLY_REPORT,
                     ENABLE_METADATA_CLEANUP)
def _service(module, name, *args, **kwargs):
    return getattr(importlib.import_module("intelligence.geo." + module), name)(*args, **kwargs)

def init_db(*args, **kwargs):
    return _service('database', 'init_db', *args, **kwargs)

def recent_articles(*args, **kwargs):
    return _service('database', 'recent_articles', *args, **kwargs)

def upcoming_events(*args, **kwargs):
    return _service('database', 'upcoming_events', *args, **kwargs)

def collect_rss(*args, **kwargs):
    return _service('collectors.rss', 'collect', *args, **kwargs)

def collect_gnews(*args, **kwargs):
    return _service('collectors.gnews_search', 'collect', *args, **kwargs)

def seed_events(*args, **kwargs):
    return _service('collectors.events', 'seed_events', *args, **kwargs)

def send_email_smtp(*args, **kwargs):
    return _service('reports.email_report', 'send', *args, **kwargs)

def build_html(*args, **kwargs):
    return _service('reports.email_report', 'build_html', *args, **kwargs)

def build_digest(*args, **kwargs):
    return _service('reports.email_report', 'build_digest', *args, **kwargs)

def mark_sent(*args, **kwargs):
    return _service('reports.email_report', 'mark_sent', *args, **kwargs)

def send_if_critical(*args, **kwargs):
    return _service('reports.critical_alert', 'send_if_critical', *args, **kwargs)

def send_weekly(*args, **kwargs):
    return _service('reports.weekly_report', 'send', *args, **kwargs)

def build_dashboard_html(*args, **kwargs):
    return _service('reports.dashboard', 'build_dashboard_html', *args, **kwargs)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("web")

app = Flask(__name__)

_db_ready = False


def _db_check():
    global _db_ready
    if not _db_ready:
        try:
            init_db()
            _db_ready = True
        except Exception:
            log.error("Database initialization failed")
            return jsonify(error="Database unavailable"), 503
    return None


def _authorized():
    secret = TRIGGER_SECRET
    supplied = request.headers.get("X-Trigger-Secret", "")
    return (isinstance(secret, str) and bool(secret.strip())
            and "key" not in request.args
            and hmac.compare_digest(supplied.encode("utf-8"), secret.encode("utf-8")))


@app.before_request
def _protect_routes():
    if request.endpoint and request.endpoint != "health" and not _authorized():
        return jsonify(error="unauthorized"), 401
    return None


# Background job state for /collect. Collection (RSS + Google News +
# paused backup) can take longer than gunicorn's/Render's request
# timeout, so /collect now kicks the work off in a background thread and
# returns immediately instead of blocking the HTTP request until it's
# done. Poll /collect-status to see progress and the final result.
_collect_status = {
    "running": False,
    "last_started": None,
    "last_finished": None,
    "last_result": None,
}
_collect_lock = threading.Lock()


def _collection_outcome(value):
    """Closed status, never a partial dictionary masquerading as insert count."""
    if type(value) is int and value >= 0:
        return {"state": "confirmed", "inserted_count": value}
    keys = {"state", "attempted", "inserted_count", "duplicate_count",
            "failed_count", "uncertain_count", "retry_safe"}
    if type(value) is not dict or set(value) != keys:
        raise ValueError("Invalid collection outcome")
    if value["state"] not in ("partial", "uncertain") or value["retry_safe"] is not False:
        raise ValueError("Invalid collection state")
    if type(value["attempted"]) is not int or value["attempted"] < 0:
        raise ValueError("Invalid attempted count")
    if value["state"] == "uncertain":
        if any(value[k] is not None for k in ("inserted_count", "duplicate_count", "failed_count")) or type(value["uncertain_count"]) is not int or value["uncertain_count"] != value["attempted"]:
            raise ValueError("Unknown counts must not be inferred")
    else:
        counts = [value[k] for k in ("inserted_count", "duplicate_count", "failed_count", "uncertain_count")]
        if any(type(n) is not int or n < 0 for n in counts) or sum(counts) != value["attempted"] or counts[-1] != 0:
            raise ValueError("Invalid partial counts")
    return dict(value)


def _publication_holds(value):
    # Closed process-cumulative diagnostic, not durable quarantine storage.
    keys = {'missing', 'invalid', 'incomplete', 'naive_timezone', 'unknown_timezone', 'future'}
    if type(value) is not dict or set(value) != keys or any(type(n) is not int or n < 0 for n in value.values()):
        raise ValueError('Invalid publication hold counters')
    return {'scope': 'cumulative_since_process_start', 'counts': dict(value)}


def _run_collect_job():
    try:
        rss = _collection_outcome(collect_rss(EXTRA_RSS_FEEDS))
        gnews = _collection_outcome(collect_gnews()) if ENABLE_GNEWS else {"state": "disabled", "inserted_count": 0}
        new_events = seed_events()
        if type(new_events) is not int or new_events < 0:
            raise ValueError("Invalid event count")
        states = {rss["state"], gnews["state"]}
        state = "uncertain" if "uncertain" in states else "partial" if "partial" in states else "confirmed"
        _collect_status["last_result"] = {
            "state": state, "rss": rss, "gnews": gnews, "new_events": new_events,
            "backup": "held_pending_durable_adapter", "error": None,
        }
    except Exception:
        # Do not expose provider/driver credentials or raw exception text.
        log.error("Background collection failed")
        _collect_status["last_result"] = {"state": "failed", "error": "collection_failed",
                                          "backup": "held_pending_durable_adapter"}
    finally:
        try:
            diagnostic = _publication_holds(_service('collectors.rss', 'date_hold_counts'))
        except Exception:
            diagnostic = {'scope': 'unavailable'}
        if type(_collect_status.get('last_result')) is dict:
            _collect_status['last_result']['publication_date_holds'] = diagnostic
        _collect_status["running"] = False
        _collect_status["last_finished"] = datetime.now(timezone.utc).isoformat()


@app.route("/health")
def health():
    return jsonify(status="ok")


@app.route("/collect", methods=["POST"])
def collect():
    if not _authorized():
        return jsonify(error="unauthorized"), 401
    if (err := _db_check()):
        return err
    with _collect_lock:
        if _collect_status["running"]:
            return jsonify(status="already_running",
                            started=_collect_status["last_started"]), 202
        _collect_status["running"] = True
        _collect_status["last_started"] = datetime.now(timezone.utc).isoformat()
    threading.Thread(target=_run_collect_job, daemon=True).start()
    return jsonify(status="started",
                    note="Collection runs in the background now -- poll /collect-status for the result."), 202


@app.route("/collect-status")
def collect_status():
    if not _authorized():
        return jsonify(error="unauthorized"), 401
    return jsonify(_collect_status)


@app.route("/send-digest", methods=["POST"])
def send_digest():
    """Sends the email directly from Render via SMTP (Option B: keep it
    simple). If Render's SMTP keeps failing, use /digest-data instead and
    let Apps Script send it via Gmail."""
    if not _authorized():
        return jsonify(error="unauthorized"), 401
    if (err := _db_check()):
        return err
    send_email_smtp()
    return jsonify(status="sent")


@app.route("/digest-data")
def digest_data():
    """Returns the digest as raw HTML, for Apps Script to send via GmailApp
    instead of Render's SMTP. Does NOT mark articles as sent here -- that
    only happens once Apps Script confirms GmailApp.sendEmail actually
    succeeded, via a follow-up call to /mark-emailed. This is what stops
    articles disappearing from every future digest if the Gmail send fails
    after this call (e.g. Gmail daily quota, bad EMAIL_TO address)."""
    if not _authorized():
        return jsonify(error="unauthorized"), 401
    if (err := _db_check()):
        return err
    html_content, critical_count, article_ids = build_digest()
    return jsonify(html=html_content, critical_count=critical_count,
                    article_ids=[str(i) for i in article_ids])


@app.route("/mark-emailed", methods=["POST"])
def mark_emailed_route():
    """Apps Script calls this right after GmailApp.sendEmail succeeds,
    passing back the article_ids it got from /digest-data. Only then do
    those articles stop appearing in future digests."""
    if not _authorized():
        return jsonify(error="unauthorized"), 401
    if (err := _db_check()):
        return err
    from bson import ObjectId
    ids = request.get_json(silent=True) or {}
    raw_ids = ids.get("article_ids", [])
    try:
        object_ids = [ObjectId(i) for i in raw_ids]
    except Exception:
        return jsonify(error="invalid article_ids"), 400
    mark_sent(object_ids)
    return jsonify(marked=len(object_ids))


@app.route("/critical", methods=["POST"])
def critical():
    if not _authorized():
        return jsonify(error="unauthorized"), 401
    if (err := _db_check()):
        return err
    if not ENABLE_CRITICAL_ALERTS:
        return jsonify(skipped="ENABLE_CRITICAL_ALERTS is false")
    n = send_if_critical()
    return jsonify(sent=bool(n), count=n or 0)


@app.route("/weekly", methods=["POST"])
def weekly():
    if not _authorized():
        return jsonify(error="unauthorized"), 401
    if (err := _db_check()):
        return err
    if not ENABLE_WEEKLY_REPORT:
        return jsonify(skipped="ENABLE_WEEKLY_REPORT is false")
    send_weekly()
    return jsonify(status="sent")


@app.route("/dashboard")
def dashboard():
    if not _authorized():
        return "Unauthorized", 401
    if (err := _db_check()):
        return err
    limit = request.args.get("limit", default=100000, type=int)
    category = request.args.get("category") or None
    sort_by = request.args.get("sort_by", default="score")
    html_out = build_dashboard_html(limit=limit, category=category, trigger_key="", sort_by=sort_by)
    return Response(html_out, mimetype="text/html")


@app.route("/export.csv")
def export_csv():
    """Downloads every article in MongoDB as a CSV file -- a portable full
    backup you can keep locally, independent of both the dashboard view
    and the Telegram archive. Pass &category=X to export just one category."""
    if not _authorized():
        return jsonify(error="unauthorized"), 401
    if (err := _db_check()):
        return err
    category = request.args.get("category") or None
    articles = recent_articles(limit=1000000)
    if category:
        articles = [a for a in articles if (a.get("category") or "GENERAL") == category]
    buf = io.StringIO()
    fields = ["title", "source", "category", "risk_level", "score", "credibility",
              "country", "corroboration", "published", "created_at", "url", "summary"]
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for a in articles:
        writer.writerow(a)
    fname = f"geonews_export{'_' + category if category else ''}.csv"
    return Response(buf.getvalue(), mimetype="text/csv",
                     headers={"Content-Disposition": f"attachment; filename={fname}"})


@app.route("/cleanup-old", methods=["POST"])
def cleanup_old():
    """Deletion is blocked even with a valid trigger secret and enabled flag."""
    return jsonify(deleted=0, held=True,
                   reason="retention_policy_not_implemented"), 403


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
