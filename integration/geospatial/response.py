# Copyright (c) 2026 Push
"""Builds the /api/map-data body from supplied news rows plus the packaged
chokepoint reference file. No network, no DB, no config reads, no threads.
Reading the packaged file happens only when load_chokepoints() is called."""
import json
from datetime import datetime
from pathlib import Path

from .payload import map_payload
from ._safe import as_dict

DATA_FILE = Path(__file__).resolve().parent / "data" / "chokepoints_wikidata.json"
MAX_FILE_BYTES = 256 * 1024
MAX_NEWS_ROWS = 1000  # rows inspected; payload shows at most payload.NEWS_CAP


def load_chokepoints(path=None):
    """Return (rows, status). rows is [] when the file is missing/oversized/malformed;
    status says why, so the layer shows as unavailable instead of crashing."""
    p = Path(path) if path is not None else DATA_FILE
    try:
        with p.open("rb") as stream:
            data = stream.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            return [], {"ok": False, "reason": "file_too_large"}
        doc = json.loads(data.decode("utf-8"))
    except FileNotFoundError:
        return [], {"ok": False, "reason": "missing"}
    except (OSError, ValueError, RecursionError):
        return [], {"ok": False, "reason": "unreadable"}
    d = as_dict(doc)
    rows = d.get("features") if d else None
    if not isinstance(rows, list):
        return [], {"ok": False, "reason": "bad_shape"}
    return rows, {"ok": True, "retrieved_utc": str(d.get("retrieved_utc", ""))[:40]}


def bounded_snapshot(raw, per_project=100, total=2000):
    """Validate the reader snapshot shape before any normalisation (same bounds as the
    weekly PDF handler). Returns {project: list} or raises ValueError."""
    if type(raw) is not dict or len(raw) > 2 or any(k not in ("geo", "brics") for k in raw):
        raise ValueError("Invalid snapshot")
    if any(type(v) not in (list, tuple) for v in raw.values()) or sum(len(v) for v in raw.values()) > total:
        raise ValueError("Snapshot work bound")
    return {k: list(v[:per_project]) for k, v in raw.items()}


def _news_with_coordinates(rows):
    """Keep only dict rows that carry explicit latitude and longitude keys.
    Rows without them are counted, never located from country or category."""
    if not isinstance(rows, (list, tuple)):
        return None, 0, 0
    kept, without = [], 0
    for r in rows[:MAX_NEWS_ROWS]:
        d = as_dict(r)
        if d is not None and "latitude" in d and "longitude" in d:
            kept.append(d)
        else:
            without += 1
    return kept, without, len(rows)


def map_data_response(news_rows, now, chokepoints=None):
    """JSON-safe dict for GET /api/map-data.

    news_rows: list of public-news dicts (or None if unavailable).
    chokepoints: optional (rows, status) from load_chokepoints(); loaded if omitted.
    Ports and ships are always reported as absent here: there is no verified port
    dataset and no ship supply reader yet."""
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError("now must be a timezone-aware datetime")
    if chokepoints is None:
        chokepoints = load_chokepoints()
    choke_rows, choke_status = chokepoints
    news, without, total = _news_with_coordinates(news_rows)
    payload = map_payload(news, None, choke_rows if choke_status.get("ok") else None, None, now)
    payload["generated_at"] = now.isoformat()
    payload["status"] = {
        "news": {"rows_seen": total, "rows_without_coordinates": without,
                 "note": "Only rows with supplied coordinates are placed; none are located from country."},
        "chokepoints": dict(choke_status, note="Wikidata CC0 reference points; display centres only."),
        "ports": {"available": False, "note": "No verified port dataset loaded."},
        "ships": {"available": False, "note": "No ship data supplied; live tracking not wired."},
    }
    return payload
