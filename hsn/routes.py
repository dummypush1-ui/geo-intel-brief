"""HSN finder: static single-page app at /hsn/ + same-origin AI / ships API at
/hsn/api/*  (replaces the separate Render static site and proxy.js service)."""
import gzip
import hmac
import logging
import os
import re
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from flask import Blueprint, Response, abort, jsonify, request, send_file, send_from_directory

from core.paths import DATA_DIR
from .ais import AisFeed

log = logging.getLogger("hsn")
bp = Blueprint("hsn", __name__)

STATIC = Path(__file__).parent / "static"
GZ_DIR = DATA_DIR / "hsn_gz"
_GZ_LOCK = threading.Lock()

# ------------------------------------------------------------------ config
APP_SECRET = os.getenv("APP_SECRET", "")           # optional: for non-browser / cross-origin callers
ALLOWED_ORIGINS = {o.strip().rstrip("/") for o in os.getenv("HSN_ALLOWED_ORIGINS", "").split(",") if o.strip()}
POOLS = {k: [x.strip() for x in os.getenv(k.upper() + "_KEYS", "").split(",") if x.strip()]
         for k in ("gemini", "groq", "mistral", "nvidia")}
_OFF = {k: 0 for k in POOLS}
_OFF_LOCK = threading.Lock()
ROUTES = {
    "gemini": (lambda model: f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
               lambda k: {"x-goog-api-key": k}),
    "groq": (lambda _=None: "https://api.groq.com/openai/v1/chat/completions", lambda k: {"Authorization": "Bearer " + k}),
    "mistral": (lambda _=None: "https://api.mistral.ai/v1/chat/completions", lambda k: {"Authorization": "Bearer " + k}),
    "nvidia": (lambda _=None: "https://integrate.api.nvidia.com/v1/chat/completions", lambda k: {"Authorization": "Bearer " + k}),
}
RATE_WINDOW, RATE_MAX = 10 * 60, 60            # 60 calls / 10 min / IP (same cap as the old proxy)
_HITS, _HITS_LOCK = {}, threading.Lock()
MAX_BODY = 2_000_000

ais = AisFeed(os.getenv("AISSTREAM_KEY", ""))


def init_app(app):
    ais.start()
    app.config.setdefault("MAX_CONTENT_LENGTH", 64 * 1024 * 1024)


# ------------------------------------------------------------------ static
def _gz_variant(path: Path):
    with _GZ_LOCK:
        return _build_gz_variant(path)


def _build_gz_variant(path: Path):
    """Pre-gzip big text assets once (19 MB data file -> a few MB). The old
    Render static site did this at its CDN; Flask does not."""
    GZ_DIR.mkdir(parents=True, exist_ok=True)
    out = GZ_DIR / f"{path.name}.{int(path.stat().st_mtime)}.gz"
    if not out.exists():
        for old in GZ_DIR.glob(path.name + ".*.gz"):
            old.unlink(missing_ok=True)
        tmp = out.with_suffix(".tmp")
        with open(path, "rb") as src, gzip.open(tmp, "wb", compresslevel=6) as dst:
            dst.write(src.read())
        tmp.replace(out)
    return out


def _serve(name: str):
    path = (STATIC / name).resolve()
    if STATIC.resolve() not in path.parents and path != STATIC.resolve():
        abort(404)
    if not path.is_file():
        abort(404)
    suffix = path.suffix.lower()
    if re.fullmatch(r"data\.[0-9a-f]{12}\.js", path.name):
        cache = "public, max-age=31536000, immutable"          # content-hashed
    elif path.name in ("index.html", "sw.js", "manifest.webmanifest"):
        cache = "no-cache"
    else:
        cache = "public, max-age=86400"
    if suffix in (".js", ".html", ".css", ".json", ".svg", ".webmanifest") and path.stat().st_size > 20_000 \
            and request.accept_encodings["gzip"] > 0:
        gz = _gz_variant(path)
        resp = send_file(gz, mimetype={".js": "text/javascript", ".html": "text/html"}.get(suffix) or None,
                         conditional=True, max_age=None, etag=True)
        resp.headers["Content-Encoding"] = "gzip"
        resp.vary.add("Accept-Encoding")
    else:
        resp = send_from_directory(STATIC, name, conditional=True, max_age=None)
    if suffix in (".js", ".html", ".css", ".json", ".svg", ".webmanifest") and path.stat().st_size > 20_000:
        resp.vary.add("Accept-Encoding")
    resp.headers["Cache-Control"] = cache
    if path.name == "sw.js":
        resp.headers["Service-Worker-Allowed"] = "/hsn/"
    return resp


@bp.get("/")
def index():
    return _serve("index.html")


@bp.get("/<path:name>")
def static_files(name):
    return _serve(name)


# ------------------------------------------------------------------ guards
def _client_ip():
    return request.remote_addr or "?"            # ProxyFix (app.py) makes this the real client


def _rate_ok(ip):
    now = time.time()
    with _HITS_LOCK:
        t, n = _HITS.get(ip, (now, 0))
        if now - t > RATE_WINDOW:
            t, n = now, 0
        n += 1
        _HITS[ip] = (t, n)
        if len(_HITS) > 5000:
            _HITS.clear()
        return n <= RATE_MAX


def _origin_ok():
    """Same-origin browser calls pass with no token. Anything else needs
    APP_SECRET (x-app-token) or an origin listed in HSN_ALLOWED_ORIGINS."""
    if request.headers.get("Sec-Fetch-Site") in ("same-origin",):
        return True
    host = request.host
    for h in ("Origin", "Referer"):
        v = request.headers.get(h)
        if v:
            pu = urlparse(v)
            if pu.netloc == host:
                return True
            if f"{pu.scheme}://{pu.netloc}" in ALLOWED_ORIGINS:
                return True
    tok = request.headers.get("x-app-token", "")
    return bool(APP_SECRET) and hmac.compare_digest(tok.encode(), APP_SECRET.encode())


def _guard():
    if not _origin_ok():
        return jsonify(error={"message": "forbidden origin"}), 403
    if not _rate_ok(_client_ip()):
        return jsonify(error={"message": "rate limit exceeded. try again later."}), 429
    return None


@bp.after_request
def _cors(resp):
    o = request.headers.get("Origin", "").rstrip("/")
    if o and o in ALLOWED_ORIGINS:
        resp.headers["Access-Control-Allow-Origin"] = o
        resp.vary.add("Origin")
        # Flask may answer OPTIONS automatically for a more specific API route.
        if request.method == "OPTIONS":
            resp.headers["Access-Control-Allow-Methods"] = "POST, GET"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type, x-app-token"
            resp.headers["Access-Control-Max-Age"] = "86400"
    return resp


@bp.route("/api/<path:_any>", methods=["OPTIONS"])
def _preflight(_any):
    o = request.headers.get("Origin", "").rstrip("/")
    if o not in ALLOWED_ORIGINS:
        return ("", 204)
    return ("", 204, {"Access-Control-Allow-Origin": o, "Access-Control-Allow-Methods": "POST, GET",
                      "Access-Control-Allow-Headers": "Content-Type, x-app-token", "Access-Control-Max-Age": "86400"})


# ------------------------------------------------------------------ API
@bp.get("/api/health")
def health():
    return jsonify(ok=True, service="hsn ai + ais", providers=[k for k, v in POOLS.items() if v], ais=ais.health())


@bp.get("/api/ships")
def ships():
    if (g := _guard()):
        return g
    if not ais.key:
        return jsonify(error={"message": "AISSTREAM_KEY not configured on the server"}), 503
    want = re.sub(r"[^A-Za-z]", "", request.args.get("port", "ALL")).upper() or "ALL"
    return jsonify(ais.snapshot(want))


def _forward(kind, model=None):
    if (g := _guard()):
        return g
    pool = POOLS[kind]
    if not pool:
        return jsonify(error={"message": f"{kind} keys not configured on the server"}), 503
    body = request.get_data(cache=False)
    if len(body) > MAX_BODY:
        return jsonify(error={"message": "request too large"}), 413
    url_fn, hdr_fn = ROUTES[kind]
    url = url_fn(model) if kind == "gemini" else url_fn()
    with _OFF_LOCK:
        start = _OFF[kind]
    for i in range(len(pool)):
        ki = (start + i) % len(pool)
        last = i == len(pool) - 1
        try:
            up = requests.post(url, data=body, timeout=150,
                               headers={"Content-Type": "application/json", **hdr_fn(pool[ki])})
        except requests.RequestException:
            if not last:
                continue
            return jsonify(error={"message": "upstream unreachable - try again in a minute"}), 502
        if up.status_code in (401, 403, 429) and len(pool) > 1 and not last:
            continue                                  # rotate to the next key
        with _OFF_LOCK:
            _OFF[kind] = ki
        return Response(up.content, status=up.status_code,
                        content_type=up.headers.get("content-type", "application/json"))
    return jsonify(error={"message": "no key available"}), 502


@bp.post("/api/gemini/v1beta/models/<model>:generateContent")
def gemini(model):
    if not re.fullmatch(r"[A-Za-z0-9._-]+", model):
        return jsonify(error={"message": "unknown endpoint"}), 404
    return _forward("gemini", model)


@bp.post("/api/groq/openai/v1/chat/completions")
def groq():
    return _forward("groq")


@bp.post("/api/mistral/v1/chat/completions")
def mistral():
    return _forward("mistral")


@bp.post("/api/nvidia/v1/chat/completions")
def nvidia():
    return _forward("nvidia")
