"""Public read-only JSON for the news <-> HS-code link (mounted at /api/links)."""
import threading
import time

from flask import Blueprint, jsonify, request

from . import crosslink

bp = Blueprint("links", __name__)
_HITS, _L = {}, threading.Lock()


def _limited():
    ip, now = request.remote_addr or "?", time.time()
    with _L:
        t, n = _HITS.get(ip, (now, 0))
        if now - t > 600:
            t, n = now, 0
        _HITS[ip] = (t, n + 1)
        if len(_HITS) > 5000:
            _HITS.clear()
        return n + 1 > 120


def _json(payload, status=200):
    r = jsonify(payload)
    r.status_code = status
    r.headers["Cache-Control"] = "public, max-age=60"
    return r


@bp.get("/news-for-code")
def news_for_code():
    if _limited():
        return _json({"ok": False, "error": "rate limit exceeded"}, 429)
    days = request.args.get("days", 30, type=int)
    limit = request.args.get("limit", 12, type=int)
    days = 30 if days is None else max(1, min(days, 180))
    limit = 12 if limit is None else max(1, min(limit, 30))
    res = crosslink.news_for_code(request.args.get("code", ""), days=days, limit=limit)
    return _json(res, 200 if res.get("ok") else 400)


@bp.get("/codes-for-article")
def codes_for_article():
    if _limited():
        return _json({"ok": False, "error": "rate limit exceeded"}, 429)
    text = (request.args.get("text") or "")[:2000]
    return _json({"ok": True, "codes": crosslink.tag_text(text)})
