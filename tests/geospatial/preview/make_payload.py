# Copyright (c) 2026 Push
"""Regenerates payload.json (synthetic FIXTURE data) from the shipped code.
Run from the repository root: python3 tests/geospatial/preview/make_payload.py
The per-item fixture flag is added here, not by the package."""
import json, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root))
from integration.geospatial import map_payload, fixtures as fx
now = datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc)
p = map_payload(fx.NEWS, fx.PORTS, fx.CHOKES, fx.ships((now - timedelta(minutes=3)).isoformat(), n=40), now)
for layer in p["layers"].values():
    for it in layer["items"]:
        it["fixture"] = True
(Path(__file__).parent / "payload.json").write_text(json.dumps(p))
