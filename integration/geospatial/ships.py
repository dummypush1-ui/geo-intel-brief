# Copyright (c) 2026 Push
"""AIS display adapter for supplied observations. No network, no stream."""
from datetime import datetime, timedelta
from ._safe import clean_text, finite_number, as_dict

INPUT_CAP = 1000
DISPLAY_CAP = 500
# Proposed threshold: AIS position reports from moving ships arrive every few
# seconds to minutes, so a snapshot older than 15 minutes is no longer a
# reasonable "current position". Callers may override; value is a proposal.
STALE_AFTER = timedelta(minutes=15)
SHIP_FIELDS = ("mmsi", "imo", "name", "latitude", "longitude", "speed_knots",
               "course_deg", "reported_at")
MAX_FUTURE_SKEW = timedelta(seconds=60)


def _zoned(value):
    """Parse an ISO-8601 string or datetime; must carry a timezone."""
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str) and len(value) < 64:
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    return dt if dt.tzinfo is not None and dt.utcoffset() is not None else None


def _digits(value, lengths):
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        if not 0 <= value < 10 ** 9:
            return None  # bound before str(): huge ints must not reach conversion
        value = str(value)
    if isinstance(value, str) and value.isascii() and value.isdigit() and len(value) in lengths:
        return value
    return None


def _ship(raw):
    d = as_dict(raw)
    if d is None:
        return None
    mmsi = _digits(d.get("mmsi"), (9,))
    lat = finite_number(d.get("latitude"), -90, 90)
    lon = finite_number(d.get("longitude"), -180, 180)
    if not mmsi or lat is None or lon is None:
        return None
    imo = _digits(d.get("imo"), (7,))
    return {"mmsi": mmsi, "imo": imo, "name": clean_text(d.get("name"), 60),
            "latitude": lat, "longitude": lon,
            "speed_knots": finite_number(d.get("speed_knots"), 0, 110),
            "course_deg": finite_number(d.get("course_deg"), 0, 360),
            "reported_at": None}


def ship_view(observation, now, stale_after=STALE_AFTER):
    """Turn one supplied observation into a public, bounded ship view.

    observation: None (absent) or dict with keys state ('connected',
    'warming', 'disconnected'), captured_at (zoned ISO), vessels (list),
    optional supplied_vessel_count / supplied_message_count (observations
    only, never proof of worldwide coverage).
    Result "status": absent | disconnected | warming | invalid_clock |
    stale | fresh | empty. "empty" = fresh snapshot with zero vessels; it is
    distinct from absent (no data supplied).
    """
    now = _zoned(now)
    if now is None:
        raise ValueError("now must be a timezone-aware datetime")
    base = {"status": "absent", "ships": [], "captured_at": None,
            "age_seconds": None, "stale": None, "truncated": False,
            "input_count": 0, "displayed": 0, "rejected": 0,
            "supplied_vessel_count": None, "supplied_message_count": None,
            "coverage_note": "Supplied snapshot only; not proof of worldwide AIS coverage."}
    obs = as_dict(observation)
    if obs is None:
        return base
    state = obs.get("state")
    if state not in ("connected", "warming", "disconnected"):
        base["status"] = "invalid_state"
        return base
    for k in ("supplied_vessel_count", "supplied_message_count"):
        v = obs.get(k)
        if isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 10**9:
            base[k] = v
    cap = _zoned(obs.get("captured_at"))
    if cap is not None:
        if cap - now > MAX_FUTURE_SKEW:
            base["status"] = "invalid_clock"
            return base
        age = max(0.0, (now - cap).total_seconds())
        base["captured_at"] = cap.isoformat()
        base["age_seconds"] = age
        base["stale"] = age > stale_after.total_seconds()
    if state in ("warming", "disconnected"):
        base["status"] = state
        return base  # connection state alone gives no freshness guarantee
    if cap is None:
        base["status"] = "invalid_clock"
        return base
    vessels = obs.get("vessels")
    if not isinstance(vessels, (list, tuple)):
        base["status"] = "absent"
        return base
    base["input_count"] = len(vessels)
    seen, ships, rejected = set(), [], 0
    for raw in vessels[:INPUT_CAP]:
        s = _ship(raw)
        if s is None or s["mmsi"] in seen:
            rejected += 1
            continue
        seen.add(s["mmsi"])
        ships.append(s)
    base["rejected"] = rejected + max(0, len(vessels) - INPUT_CAP)
    if len(ships) > DISPLAY_CAP or len(vessels) > INPUT_CAP:
        base["truncated"] = True
    ships = ships[:DISPLAY_CAP]
    for s in ships:
        s["reported_at"] = cap.isoformat()
    base["ships"] = ships
    base["displayed"] = len(ships)
    if base["stale"]:
        base["status"] = "stale"  # an old snapshot is stale even when it holds zero vessels
    else:
        base["status"] = "empty" if not ships and not base["rejected"] else "fresh"
    return base
