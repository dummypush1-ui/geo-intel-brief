# Copyright (c) 2026 Push
"""Server-side mirrors of the browser validators (live_channels.js, countries.js).
Rules as supplied by the project owner's code review; re-verify against the JS before landing."""
import re, unicodedata

CHANNEL_JSON_MAX = 10000
WATCH_JSON_MAX = 5000
MAX_EXTRA_CHANNELS = 20
MAX_WATCH = 20
_VID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_URLS = (re.compile(r"^https://www\.youtube\.com/watch\?v=([A-Za-z0-9_-]{11})$"),
         re.compile(r"^https://youtu\.be/([A-Za-z0-9_-]{11})$"))


def utf16_len(s):
    return len(s.encode("utf-16-le", "surrogatepass")) // 2


def clean_label(v, max_len):
    """Trimmed, 1..max_len UTF-16 units, no Unicode category C, at least one visible L/N/P/S."""
    if not isinstance(v, str) or len(v) > 4 * max_len + 64:   # bound before strip/encode
        raise ValueError("type")
    v = v.strip()
    if not v or utf16_len(v) > max_len:
        raise ValueError("length")
    if any(unicodedata.category(c).startswith("C") for c in v):
        raise ValueError("chars")
    if not any(unicodedata.category(c)[0] in "LNPS" for c in v):
        raise ValueError("invisible")
    return v


def video_id(v):
    """Bare 11-char id, or exact youtube watch / youtu.be URL (<=200 chars, no extra params)."""
    if not isinstance(v, str) or len(v) > 200 or any(c.isspace() or c in "\\%" for c in v):
        raise ValueError("video")
    if v.isascii() and _VID.match(v):
        return v
    for rx in _URLS:
        m = rx.match(v)
        if m and v.isascii():
            return m.group(1)
    raise ValueError("video")


def channel_validator(item):
    """Row has only name and video. Returns {name, video} with video canonicalised to the bare id."""
    if not isinstance(item, dict) or set(item) != {"name", "video"}:
        raise ValueError("shape")
    return {"name": clean_label(item["name"], 80), "video": video_id(item["video"])}


def watch_validator(item):
    return clean_label(item, 100)


def fold(name):
    return unicodedata.normalize("NFKC", name).casefold()
