# Copyright (c) 2026 Push
"""Layer payload for the map surface. Equirectangular projection, 1000x500."""
from ._safe import clean_text, safe_https_url, finite_number, as_dict
from .features import validate_features
from .ships import ship_view

WIDTH, HEIGHT = 1000, 500
NEWS_CAP = 200
MAX_PROV_GROUPS = 20
NEWS_FIELDS = ("article_key", "project", "url", "title", "summary", "source",
               "original_country", "category", "published_at", "collected_at",
               "risk_level", "credibility", "score", "corroboration_count")
_TEXT_LIMITS = {"article_key": 120, "project": 60, "title": 200, "summary": 400,
                "source": 80, "original_country": 60, "category": 60,
                "published_at": 40, "collected_at": 40, "risk_level": 30,
                "credibility": 30}


def project(lat, lon):
    """Return (x, y) in 0..WIDTH, 0..HEIGHT; None for invalid input."""
    la = finite_number(lat, -90, 90)
    lo = finite_number(lon, -180, 180)
    if la is None or lo is None:
        return None
    return (round((lo + 180.0) / 360.0 * WIDTH, 2),
            round((90.0 - la) / 180.0 * HEIGHT, 2))


def bbox_rects(bbox):
    """Projected rectangles for a bbox; two when it crosses the antimeridian."""
    if not bbox:
        return []
    top = project(bbox["north"], bbox["west"])[1]
    bot = project(bbox["south"], bbox["west"])[1]
    x_w = project(0, bbox["west"])[0]
    x_e = project(0, bbox["east"])[0]
    if bbox["west"] <= bbox["east"]:
        return [{"x": x_w, "y": top, "w": round(x_e - x_w, 2), "h": round(bot - top, 2)}]
    return [{"x": x_w, "y": top, "w": round(WIDTH - x_w, 2), "h": round(bot - top, 2)},
            {"x": 0.0, "y": top, "w": x_e, "h": round(bot - top, 2)}]


def _news(items):
    """Public news fields only. Items need explicit lat/lon from a geolocated
    source; coordinates are never inferred from country or category."""
    if not isinstance(items, (list, tuple)):
        return [], {"available": False}
    out, rejected = [], 0
    for raw in items[:NEWS_CAP]:
        d = as_dict(raw)
        if d is None:
            rejected += 1; continue
        pt = project(d.get("latitude"), d.get("longitude"))
        url = safe_https_url(d.get("url"))
        title = clean_text(d.get("title"), 200)
        if pt is None or not title:
            rejected += 1; continue
        rec = {"x": pt[0], "y": pt[1], "latitude": float(d["latitude"]),
               "longitude": float(d["longitude"]), "url": url}  # coords already range-checked by project()
        for k in NEWS_FIELDS:
            if k in _TEXT_LIMITS:
                rec[k] = clean_text(d.get(k), _TEXT_LIMITS[k])
        rec["title"] = title
        for k in ("score", "corroboration_count"):
            rec[k] = finite_number(d.get(k), -1e6, 1e6)
        out.append(rec)
    return out, {"available": True, "input_count": len(items), "rejected": rejected,
                 "truncated": len(items) > NEWS_CAP}


def _feature_layer(items, kind):
    feats, rep = validate_features(items)
    other = sum(1 for f in feats if f["kind"] != kind)
    feats = [f for f in feats if f["kind"] == kind]
    rep["wrong_kind_dropped"] = other
    for f in feats:
        f["x"], f["y"] = project(f["latitude"], f["longitude"])
        f["rects"] = bbox_rects(f["bbox"])
    return feats, rep


def map_payload(news_features, ports, chokepoints, ships, now):
    """Build layers. Each layer: available, count, items, provenance/notes.
    No risk or threat score is derived from positions or routes."""
    n_items, n_rep = _news(news_features)
    p_items, p_rep = _feature_layer(ports, "port")
    c_items, c_rep = _feature_layer(chokepoints, "chokepoint")
    sv = ship_view(ships, now)
    for s in sv["ships"]:
        s["x"], s["y"] = project(s["latitude"], s["longitude"])
    def prov(items):
        """Group by dataset/licence/version; first URL + URL count per group.
        At most MAX_PROV_GROUPS groups; dropped groups are counted."""
        groups = {}
        for f in items:
            key = (f["dataset"], f["license"], f["captured_version"])
            g = groups.setdefault(key, [f["source_url"], set()])
            g[1].add(f["source_url"])
        rows = [[k[0], k[1], k[2], v[0], len(v[1])] for k, v in sorted(groups.items())]
        return rows[:MAX_PROV_GROUPS], max(0, len(rows) - MAX_PROV_GROUPS)
    p_prov, p_drop = prov(p_items)
    c_prov, c_drop = prov(c_items)
    return {
        "projection": {"name": "equirectangular", "width": WIDTH, "height": HEIGHT},
        "layers": {
            "news": {"available": n_rep["available"], "count": len(n_items),
                     "items": n_items, "report": n_rep,
                     "note": "Only items with supplied coordinates; none inferred from country."},
            "ports": {"available": p_rep["available"], "count": len(p_items),
                      "items": p_items, "report": p_rep,
                      "provenance": p_prov, "provenance_groups_dropped": p_drop,
                      "note": "Reference positions only; not operational status."},
            "chokepoints": {"available": c_rep["available"], "count": len(c_items),
                            "items": c_items, "report": c_rep,
                            "provenance": c_prov, "provenance_groups_dropped": c_drop,
                            "note": "Display centre points; not navigation routes."},
            "ships": {"available": sv["status"] != "absent", "count": sv["displayed"],
                      "items": sv["ships"], "status": sv["status"],
                      "captured_at": sv["captured_at"], "age_seconds": sv["age_seconds"],
                      "stale": sv["stale"], "truncated": sv["truncated"],
                      "input_count": sv["input_count"],
                      "supplied_vessel_count": sv["supplied_vessel_count"],
                      "supplied_message_count": sv["supplied_message_count"],
                      "note": sv["coverage_note"]},
        },
    }
