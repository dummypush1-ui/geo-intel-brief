"""MongoDB-backed storage layer.

Same function names/signatures as the original SQLite version, so nothing
in collectors/, processing/, or reports/ needs to change — they just call
save_article(), recent_articles(), etc. as before. Records behave like
dicts (a["title"], a["score"], ...) exactly like the old sqlite3.Row did.
"""
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, BulkWriteError
from intelligence.geo.config import MONGODB_URI, MONGODB_DB_NAME
from intelligence.geo.bounded_reads import bounded_limit, cursor_rows, article_pages

_client = None
_db = None


def connect():
    global _client, _db
    if _db is None:
        # Explicit timeouts: without these, a bad/unreachable MONGODB_URI
        # (wrong password, IP not allow-listed in Atlas, typo'd cluster
        # host) hangs the request for minutes instead of failing fast with
        # a clear error.
        _client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=8000,
            connectTimeoutMS=8000,
        )
        _db = _client[MONGODB_DB_NAME]
    return _db


def init_db():
    db = connect()
    db.articles.create_index([("url", ASCENDING)], unique=True)
    db.articles.create_index([("score", DESCENDING)])
    db.events.create_index([("name", ASCENDING), ("event_date", ASCENDING)], unique=True)
    db.events.create_index([("event_date", ASCENDING)])


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def save_article(a):
    db = connect()
    doc = dict(a)
    doc.setdefault("created_at", _now_iso())
    try:
        db.articles.insert_one(doc)
        return True
    except DuplicateKeyError:
        return False


class ArticleWriteOutcomeError(RuntimeError):
    """A partial or unknown batch is not a general-success count or retry permit."""
    def __init__(self, outcome):
        self.outcome = dict(outcome)
        super().__init__("Article write requires reconciliation; automatic retry is unsafe")


def save_articles_bulk(articles):
    """Return only driver-confirmed all-success or URL-duplicate-only inserts.

    Validation errors raise with a redacted partial outcome. Network,
    write-concern and malformed receipts raise unknown, never inferred success.
    Caller records are copied; no driver retry or caller mutation occurs here.
    """
    if type(articles) is not list or any(type(a) is not dict for a in articles):
        raise ValueError("Plain article batch required")
    if not articles:
        return 0
    from copy import deepcopy
    from integration.geo_article_writer import GeoArticleWriter
    documents = deepcopy(articles)
    stamp = _now_iso()
    for doc in documents:
        doc.setdefault("created_at", stamp)
    attempted = len(documents)
    try:
        db = connect()
        insert = db.articles.insert_many
    except Exception:
        raise ArticleWriteOutcomeError(GeoArticleWriter._uncertain(attempted)) from None
    try:
        result = insert(documents, ordered=False)
    except BulkWriteError as exc:
        try:
            outcome = GeoArticleWriter._bulk_outcome(exc.details, attempted)
        except Exception:
            outcome = GeoArticleWriter._uncertain(attempted)
        if outcome["state"] == "duplicates":
            return outcome["inserted_count"]
        raise ArticleWriteOutcomeError(outcome) from None
    except Exception:
        raise ArticleWriteOutcomeError(GeoArticleWriter._uncertain(attempted)) from None
    # Exceptions while reading a receipt are not command-error proof.
    try:
        acknowledged = result.acknowledged
        ids = result.inserted_ids
        if acknowledged is not True or type(ids) is not list or len(ids) != attempted:
            raise ValueError()
    except Exception:
        raise ArticleWriteOutcomeError(GeoArticleWriter._uncertain(attempted)) from None
    return attempted


def update_telegram_refs(articles):
    """Attaches telegram_message_id/telegram_url to already-saved articles,
    matched by url. Used by the background Telegram-backup thread (see
    collectors/rss.py) so that posting to Telegram never has to happen
    before /collect can respond -- this runs afterward, in the background,
    and just patches the docs once Telegram confirms the post. Safe to
    call with articles that have no telegram_url yet (skipped)."""
    db = connect()
    updated = 0
    for a in articles:
        if not a.get("telegram_url"):
            continue
        result = db.articles.update_one(
            {"url": a["url"]},
            {"$set": {"telegram_message_id": a.get("telegram_message_id"),
                      "telegram_url": a.get("telegram_url")}},
        )
        updated += result.modified_count
    return updated


def save_event(e):
    db = connect()
    doc = dict(e)
    doc.setdefault("created_at", _now_iso())
    try:
        db.events.insert_one(doc)
        return True
    except DuplicateKeyError:
        return False


def recent_articles(limit=60, sort_by="score"):
    bounded_limit(limit)
    db = connect()
    sort_spec = {
        "score": [("score", DESCENDING), ("published", DESCENDING), ("_id", DESCENDING)],
        "newest": [("published", DESCENDING), ("_id", DESCENDING)],
        "title": [("title", ASCENDING), ("_id", ASCENDING)],
    }.get(sort_by, [("score", DESCENDING), ("published", DESCENDING), ("_id", DESCENDING)])
    cur = db.articles.find().sort(sort_spec).limit(limit+1)
    return cursor_rows(cur, limit)


def total_article_count():
    """Total documents in the articles collection, ignoring any limit --
    used so the dashboard can show 'X shown of Y total' instead of quietly
    capping the count with no indication more data exists."""
    db = connect()
    return db.articles.count_documents({})


def latest_collection_time():
    """created_at of the single most recently saved article -- used for a
    'last collected' stat on the dashboard so it's obvious at a glance
    whether /collect is still running on schedule."""
    db = connect()
    doc = db.articles.find_one(sort=[("created_at", DESCENDING)])
    return doc.get("created_at") if doc else None


def unemailed_articles(limit=60):
    """Same as recent_articles(), but excludes anything already included in
    a previous digest — this is what stops the 10pm email repeating the
    same stories the 10am one already sent."""
    bounded_limit(limit)
    db = connect()
    cur = db.articles.find({"emailed": {"$ne": True}}) \
        .sort([("score", DESCENDING), ("published", DESCENDING), ("_id", DESCENDING)]).limit(limit+1)
    return cursor_rows(cur, limit)


def mark_emailed(article_ids):
    """Flags the given articles (by their MongoDB _id) as already sent in
    a digest, so the next digest won't repeat them."""
    if not article_ids:
        return
    db = connect()
    db.articles.update_many({"_id": {"$in": list(article_ids)}}, {"$set": {"emailed": True}})


def get_articles_older_than(days, limit=2000):
    """Articles older than N days (by created_at), oldest first — used by
    the Telegram archive/purge job to keep MongoDB from filling up over a
    long deployment lifetime."""
    db = connect()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    cur = db.articles.find({"created_at": {"$lt": cutoff}}).sort("created_at", ASCENDING)
    return cursor_rows(cur, bounded_limit(limit), require_complete=True)


def delete_articles(article_ids):
    """Fail closed: no authenticated retention implementation exists yet.

    This low-level boundary blocks callers bypassing metadata_cleanup. Caller
    IDs, Telegram links and a feature flag cannot authorize destructive work.
    """
    raise PermissionError("Article deletion disabled: retention policy not implemented")


def upcoming_events(days=90, limit=2000):
    db = connect()
    today = datetime.now(timezone.utc).date()
    end = today + timedelta(days=days)
    cur = db.events.find({
        "event_date": {"$gte": today.isoformat(), "$lte": end.isoformat()}
    }).sort("event_date", ASCENDING)
    return cursor_rows(cur, bounded_limit(limit), require_complete=True)


def critical_since(hours=6, limit=2000):
    db = connect()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    cur = db.articles.find({
        "risk_level": "CRITICAL",
        "created_at": {"$gte": cutoff}
    }).sort("score", DESCENDING)
    return cursor_rows(cur, bounded_limit(limit), require_complete=True)


def weekly_top_articles(days=7, limit=20):
    db = connect()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    cur = db.articles.find({
        "created_at": {"$gte": cutoff}
    }).sort("score", DESCENDING).limit(limit+1)
    return cursor_rows(cur, bounded_limit(limit))


def category_counts(days=7):
    db = connect()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    pipeline = [
        {"$match": {"created_at": {"$gte": cutoff}}},
        {"$group": {"_id": "$category", "cnt": {"$sum": 1}}},
        {"$sort": {"cnt": -1}},
    ]
    return [{"category": r["_id"], "cnt": r["cnt"]} for r in db.articles.aggregate(pipeline)]


def top_countries(days=7, limit=8):
    db = connect()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    pipeline = [
        {"$match": {"created_at": {"$gte": cutoff}, "country": {"$nin": [None, ""]}}},
        {"$group": {"_id": "$country", "cnt": {"$sum": 1}}},
        {"$sort": {"cnt": -1}},
        {"$limit": limit},
    ]
    return [{"country": r["_id"], "cnt": r["cnt"]} for r in db.articles.aggregate(pipeline)]


def export_article_pages(category=None, max_rows=2000):
    """Bounded page primitive, not a snapshot or full backup certificate."""
    yield from article_pages(connect().articles, category=category, max_rows=max_rows)
