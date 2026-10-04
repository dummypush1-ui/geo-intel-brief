# Copyright (c) 2026 Push
"""SYNTHETIC FIXTURES for tests and offline preview. Not live evidence and
not verified geography; names are marked FIXTURE."""
SRC = "https://example.invalid/fixture"
def port(i, lat, lon, **kw):
    d = {"id": "fx-port-%d" % i, "kind": "port", "name": "FIXTURE Port %d" % i, "latitude": lat,
         "longitude": lon, "source_url": "https://example.com/fixture/%d" % i,
         "dataset": "FIXTURE dataset", "license": "fixture-only", "captured_version": "fixture-0"}
    d.update(kw); return d
def choke(i, lat, lon, **kw):
    d = port(i, lat, lon, kind="chokepoint", id="fx-choke-%d" % i, name="FIXTURE Chokepoint %d" % i); d.update(kw); return d
PORTS = [port(1, 51.9, 4.5), port(2, -33.9, 18.4), port(3, 1.26, 103.8), port(4, 35.0, 179.9)]
CHOKES = [choke(1, 26.5, 56.3, bbox={"south": 25.5, "north": 27.5, "west": 55.5, "east": 57.5}),
          choke(2, 65.8, -169.0, bbox={"south": 64.5, "north": 67, "west": 170, "east": -168})]
NEWS = [{"latitude": 48.8, "longitude": 2.3, "title": "FIXTURE headline <b>x</b>", "url": "https://example.com/n1",
         "source": "FIXTURE", "category": "fixture", "score": 3, "corroboration_count": 1,
         "telegram_chat": "SECRET", "backup_url": "https://x.example/b", "_id": "abc"}]
def ships(now_iso, state="connected", n=3):
    return {"state": state, "captured_at": now_iso, "supplied_vessel_count": n,
            "vessels": [{"mmsi": "%09d" % (200000000 + i), "name": "FIXTURE VESSEL %d" % i,
                         "latitude": -60 + (i * 7) % 120, "longitude": -170 + (i * 37) % 340, "speed_knots": 8.5, "course_deg": 90}
                        for i in range(n)]}
