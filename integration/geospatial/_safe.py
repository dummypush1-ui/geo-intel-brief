# Copyright (c) 2026 Push
"""Shared sanitising helpers. Pure functions, no I/O."""
import math
import re
import unicodedata
from urllib.parse import urlsplit

MAX_TEXT = 300
_HOST_RE = re.compile(r"^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$")


def clean_text(value, limit=MAX_TEXT):
    """Return a bounded string without control/invisible characters, or None."""
    if not isinstance(value, str):
        return None
    out = []
    for ch in value[:limit * 4]:  # bound work before scanning huge input
        cat = unicodedata.category(ch)
        if cat in ("Cc", "Cf", "Cs", "Co", "Cn", "Zl", "Zp"):
            if ch in "\n\t ":
                out.append(" ")
            continue
        out.append(ch)
    text = " ".join("".join(out).split())
    return text[:limit] if text else None


def safe_https_url(value, allowed_hosts=None):
    """Strict https URL or None.

    Rule (mirrored exactly by safeUrl in map_ui.js): printable ASCII only
    (0x21-0x7e; callers must percent-encode anything else), scheme https
    (case-insensitive), no "@" in the authority, hostname [a-z0-9.-] starting
    and ending alphanumeric with no "..", last label not all digits (so no IP
    literals or IPv4-lookalikes), optional port digits <= 65535.
    The JS side additionally calls new URL(), which can reject more (for example
    malformed xn-- punycode labels). Guarantee: JS accepts => Python accepts.
    """
    if not isinstance(value, str) or not value or len(value) > 2000:
        return None
    if any(not 0x21 <= ord(ch) <= 0x7e for ch in value):
        return None
    try:
        parts = urlsplit(value)
        host = parts.hostname
        parts.port  # raises on bad port
    except ValueError:
        return None
    if parts.scheme != "https" or not host or "@" in parts.netloc:
        return None
    if not _HOST_RE.match(host) or ".." in host or host.rsplit(".", 1)[-1].isdigit():
        return None
    if allowed_hosts is not None and host not in allowed_hosts:
        return None
    return value


def finite_number(value, lo, hi):
    """float in [lo, hi] or None. Rejects bool, NaN, inf, non-numbers."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        if isinstance(value, int) and not (lo <= value <= hi):
            return None  # compare ints exactly; huge ints never reach float()
        f = float(value)
    except (OverflowError, ValueError):
        return None
    if not math.isfinite(f) or f < lo or f > hi:
        return None
    return f


def as_dict(item):
    """Plain dict view of a mapping; non-dicts return None."""
    return item if type(item) is dict else None
