# Copyright (c) 2026 Push
"""Port and chokepoint feature validation (supplied observations only)."""
from ._safe import clean_text, safe_https_url, finite_number, as_dict

MAX_FEATURES = 1000
KINDS = ("port", "chokepoint")
FEATURE_FIELDS = ("id", "kind", "name", "latitude", "longitude", "source_url",
                  "dataset", "license", "captured_version", "bbox")


def _bbox(raw):
    d = as_dict(raw)
    if d is None:
        return None
    s = finite_number(d.get("south"), -90, 90)
    n = finite_number(d.get("north"), -90, 90)
    w = finite_number(d.get("west"), -180, 180)
    e = finite_number(d.get("east"), -180, 180)
    if None in (s, n, w, e) or s > n:
        return None
    # west > east means the box crosses the antimeridian; kept as supplied.
    return {"south": s, "north": n, "west": w, "east": e}


def validate_features(items):
    """Return (features, report). features is a new list of closed-shape dicts.

    Input beyond MAX_FEATURES is dropped and reported as truncated.
    Rejected rows are counted by reason; nothing is invented.
    """
    report = {"input_count": 0, "accepted": 0, "truncated": False,
              "rejected": {}}
    if not isinstance(items, (list, tuple)):
        report["available"] = False
        return [], report
    report["available"] = True
    report["input_count"] = len(items)
    if len(items) > MAX_FEATURES:
        report["truncated"] = True
        items = items[:MAX_FEATURES]
    seen, out = set(), []

    def reject(reason):
        report["rejected"][reason] = report["rejected"].get(reason, 0) + 1

    for raw in items:
        d = as_dict(raw)
        if d is None:
            reject("not_object"); continue
        fid = clean_text(d.get("id"), 80)
        kind = d.get("kind")
        name = clean_text(d.get("name"), 120)
        if not fid or kind not in KINDS or not name:
            reject("missing_identity"); continue
        lat = finite_number(d.get("latitude"), -90, 90)
        lon = finite_number(d.get("longitude"), -180, 180)
        if lat is None or lon is None:
            reject("bad_coordinates"); continue
        url = safe_https_url(d.get("source_url"))
        dataset = clean_text(d.get("dataset"), 120)
        lic = clean_text(d.get("license"), 80)
        ver = clean_text(d.get("captured_version"), 80)
        if not url or not dataset or not lic or not ver:
            reject("missing_provenance"); continue
        key = (kind, fid)
        if key in seen:
            reject("duplicate"); continue
        seen.add(key)
        out.append({"id": fid, "kind": kind, "name": name, "latitude": lat,
                    "longitude": lon, "source_url": url, "dataset": dataset,
                    "license": lic, "captured_version": ver,
                    "bbox": _bbox(d.get("bbox"))})
    report["accepted"] = len(out)
    return out, report
