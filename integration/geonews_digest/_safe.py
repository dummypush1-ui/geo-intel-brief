# Copyright (c) 2026 Push
"""Small input-hardening helpers (self-contained copy; no shared imports)."""
import math
import re
import unicodedata
from datetime import datetime, timezone
from urllib.parse import urlsplit

BAD_CHARS = re.compile(r"[\u0000-\u001f\u007f-\u009f\u200b-\u200f\u202a-\u202e\u2060-\u2064\u2066-\u2069\u061c\u180e\ufeff\ud800-\udfff]")
YEAR_MIN, YEAR_MAX = 1970, 2100
NUM_LIMIT = 10 ** 12
URL_MAX = 500


def clean_text(value, cap):
    if not isinstance(value, str):
        return None
    if len(value) > cap * 8:
        value = value[: cap * 8]
    s = BAD_CHARS.sub(" ", unicodedata.normalize("NFC", value))
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        return None
    return s if len(s) <= cap else s[: cap - 1].rstrip() + "\u2026"


def clean_url(value):
    """https only, default port only, no credentials/backslash/space/control/non-ASCII."""
    if not isinstance(value, str) or len(value) > URL_MAX:
        return None
    if BAD_CHARS.search(value) or "\\" in value or " " in value or not value.isascii():
        return None
    try:
        p = urlsplit(value)
        host, port = p.hostname, p.port
    except ValueError:
        return None
    if p.scheme != "https" or not host or "." not in host or p.username is not None or p.password is not None:
        return None
    if port not in (None, 443):
        return None
    return "https" + value[5:]


def clean_dashboard_url(value):
    """clean_url plus: no query, fragment, params or '?'/'#'/'@'/'=' anywhere, so a
    secret/access key cannot ride along in a dashboard link. Rejected -> None
    (the link is simply left out)."""
    u = clean_url(value)
    if u is None or any(c in u for c in "?#;@"):
        return None
    p = urlsplit(u)
    if p.query or p.fragment:
        return None
    return u


def parse_dt(value):
    """Aware ISO-8601 (explicit offset/Z) -> UTC datetime within 1970-2100, else None."""
    if not isinstance(value, str) or len(value) > 40:
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
    return u if YEAR_MIN <= u.year <= YEAR_MAX else None


def num(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value if -NUM_LIMIT <= value <= NUM_LIMIT else None


def aware(name, d):
    """Caller-supplied clock value: aware, 1970-2100, else ValueError."""
    try:
        if not isinstance(d, datetime) or d.tzinfo is None or d.utcoffset() is None:
            raise ValueError
        u = d.astimezone(timezone.utc)
        if not YEAR_MIN <= u.year <= YEAR_MAX:
            raise ValueError
    except (ValueError, OverflowError, OSError):
        raise ValueError("%s must be a timezone-aware datetime between %d and %d" % (name, YEAR_MIN, YEAR_MAX))
    return u
