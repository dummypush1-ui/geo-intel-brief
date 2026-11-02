"""Live ship positions near major ports (AISStream) - Python port of the AIS
half of the original proxy.js. One background WebSocket; /hsn/api/ships reads
the in-memory table. Needs AISSTREAM_KEY and the `websockets` package;
without either the feed stays off and /ships answers 503."""
import asyncio
import json
import logging
import math
import os
import threading
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

log = logging.getLogger("hsn.ais")

_T = json.loads((Path(__file__).parent / "data" / "ais_ports.json").read_text())
PORTS_ALL = _T["india"] + _T["world"]
MID = {int(k): v for k, v in _T["mid"].items()}
BOXES = [[[p["lat"] - (0.6 if p.get("wide") else 0.35), p["lon"] - (0.6 if p.get("wide") else 0.35)],
          [p["lat"] + (0.6 if p.get("wide") else 0.35), p["lon"] + (0.6 if p.get("wide") else 0.35)]]
         for p in PORTS_ALL]
URL = os.getenv("AISSTREAM_URL", "wss://stream.aisstream.io/v0/stream")
MAX_SHIPS = 6000


def flag_of(mmsi):
    try:
        return MID.get(int(str(mmsi)[:3]))
    except ValueError:
        return None


def type_label(t):
    if t is None:
        return None
    if 60 <= t <= 69: return "Passenger"
    if 70 <= t <= 79: return "Cargo"
    if 80 <= t <= 89: return "Tanker"
    if t == 30: return "Fishing"
    if t in (52, 31, 32): return "Tug"
    if t == 50: return "Pilot boat"
    if t == 35: return "Military"
    if t == 36: return "Sailing"
    if t == 37: return "Pleasure"
    if t == 51: return "SAR"
    if t in (53, 55, 58, 59): return "Service"
    if t in (33, 34): return "Work boat"
    if 40 <= t <= 49: return "High-speed"
    if t >= 90: return "Other"
    return None


def dist_km(a_lat, a_lon, b_lat, b_lon):
    r = math.pi / 180
    h = math.sin((b_lat - a_lat) * r / 2) ** 2 + math.cos(a_lat * r) * math.cos(b_lat * r) * math.sin((b_lon - a_lon) * r / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


def nearest_port(lat, lon):
    best, bd = None, 1e9
    for p in PORTS_ALL:
        d = dist_km(lat, lon, p["lat"], p["lon"])
        if d < bd:
            bd, best = d, p
    return best["code"] if best and bd <= (70 if best.get("wide") else 45) else None


def eta_text(e):
    if not e or not e.get("Month") or not 1 <= e["Month"] <= 12 or not e.get("Day"):
        return None
    now = datetime.now(timezone.utc)
    hh = e["Hour"] if e.get("Hour") is not None and e["Hour"] < 24 else 0
    mm = e["Minute"] if e.get("Minute") is not None and e["Minute"] < 60 else 0
    try:
        d = datetime(now.year, e["Month"], e["Day"], hh, mm, tzinfo=timezone.utc)
        if d < now - timedelta(days=45):
            d = datetime(now.year + 1, e["Month"], e["Day"], hh, mm, tzinfo=timezone.utc)
    except ValueError:
        return None
    if d < now - timedelta(days=1) or d > now + timedelta(days=400):
        return None
    return d.strftime("%Y-%m-%d %H:%M") + " UTC"


class AisFeed:
    def __init__(self, key):
        self.key = (key or "").strip()
        self.ships = {}
        self.lock = threading.Lock()
        self.booted = time.time()
        self.connected = False
        self.msgs = self.err_frames = self.closes = self.ws_errors = 0
        self.last_msg = 0.0
        self.last_frame_type = ""
        self.last_note = ""
        self.last_error = ""
        self._thread = None

    # ---- ingestion (pure, unit-testable) ----
    def upsert(self, m):
        md = m.get("MetaData") or {}
        msg = m.get("Message") or {}
        body = msg.get("PositionReport") or msg.get("ShipStaticData")
        mmsi = str(md.get("MMSI") or (body or {}).get("UserID") or "")
        if not mmsi or mmsi == "0":
            return
        with self.lock:
            r = self.ships.get(mmsi)
            if r is None:
                r = dict(mmsi=mmsi, name="", type=None, dest="", eta=None, imo=None,
                         lat=None, lon=None, sog=None, cog=None, seen=0.0, port=None)
                self.ships[mmsi] = r
            nm = md.get("ShipName")
            if nm and str(nm).strip():
                r["name"] = str(nm).strip()
            if m.get("MessageType") == "PositionReport" and msg.get("PositionReport"):
                p = msg["PositionReport"]
                la = p["Latitude"] if isinstance(p.get("Latitude"), (int, float)) else md.get("latitude")
                lo = p["Longitude"] if isinstance(p.get("Longitude"), (int, float)) else md.get("longitude")
                if isinstance(la, (int, float)) and -90 <= la <= 90 and la != 91:
                    r["lat"] = la
                if isinstance(lo, (int, float)) and -180 <= lo <= 180 and lo != 181:
                    r["lon"] = lo
                if isinstance(p.get("Sog"), (int, float)) and 0 <= p["Sog"] < 102.3:
                    r["sog"] = round(p["Sog"], 1)
                if isinstance(p.get("Cog"), (int, float)) and 0 <= p["Cog"] < 360:
                    r["cog"] = round(p["Cog"])
                r["seen"] = time.time()
            elif m.get("MessageType") == "ShipStaticData" and msg.get("ShipStaticData"):
                sd = msg["ShipStaticData"]
                if sd.get("Name") and str(sd["Name"]).strip():
                    r["name"] = str(sd["Name"]).strip()
                if isinstance(sd.get("Type"), int):
                    r["type"] = sd["Type"]
                if sd.get("Destination") and str(sd["Destination"]).strip():
                    r["dest"] = str(sd["Destination"]).strip()
                if sd.get("ImoNumber"):
                    r["imo"] = sd["ImoNumber"]
                et = eta_text(sd.get("Eta"))
                if et:
                    r["eta"] = et
                r["seen"] = time.time()
            if r["lat"] is not None and r["lon"] is not None:
                r["port"] = nearest_port(r["lat"], r["lon"])
            if len(self.ships) > MAX_SHIPS:
                oldest = min(self.ships, key=lambda k: self.ships[k]["seen"])
                self.ships.pop(oldest, None)

    def _handle(self, raw):
        self.last_msg = time.time()
        self.msgs += 1
        try:
            m = json.loads(raw)
            self.last_frame_type = m.get("MessageType") or "unknown"
            if not (m.get("MetaData") or {}).get("MMSI"):
                self.err_frames += 1
                import re
                self.last_note = re.sub(r"[A-Za-z0-9]{20,}", "[redacted]", str(raw))[:160]
            self.upsert(m)
        except Exception:
            self.err_frames += 1
            self.last_note = "unparseable frame"

    def prune(self):
        cut = time.time() - 2 * 3600
        with self.lock:
            for k in [k for k, v in self.ships.items() if v["seen"] < cut]:
                del self.ships[k]

    # ---- websocket thread ----
    async def _run(self):
        import websockets  # lazy: only needed when the feed is enabled
        backoff = 1
        last_prune = time.time()
        while True:
            try:
                async with websockets.connect(URL, ping_interval=20, max_size=2 ** 22) as ws:
                    await ws.send(json.dumps({"APIKey": self.key, "BoundingBoxes": BOXES,
                                              "MessageTypes": ["PositionReport", "ShipStaticData"]}))
                    self.connected = True
                    backoff = 1
                    log.info("aisstream connected, %d port boxes", len(BOXES))
                    while True:
                        raw = await asyncio.wait_for(ws.recv(), timeout=360)  # quiet socket = dead socket
                        if isinstance(raw, bytes):
                            raw = raw.decode("utf-8", "replace")
                        self._handle(raw)
                        if time.time() - last_prune > 300:
                            self.prune()
                            last_prune = time.time()
            except asyncio.TimeoutError:
                log.warning("aisstream quiet for 6 min - reconnecting")
            except Exception as e:
                self.ws_errors += 1
                self.last_error = type(e).__name__
                log.warning("aisstream error: %s", type(e).__name__)
            finally:
                if self.connected:
                    self.closes += 1
                self.connected = False
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)

    def start(self):
        if not self.key or self._thread:
            return False
        try:
            import websockets  # noqa: F401
        except ImportError:
            self.last_error = "websockets package not installed"
            log.warning("AISSTREAM_KEY set but `websockets` is not installed; live ships disabled")
            return False
        self._thread = threading.Thread(target=lambda: asyncio.run(self._run()), daemon=True, name="ais-feed")
        self._thread.start()
        return True

    # ---- views ----
    def warming(self):
        return (time.time() - self.booted < 600) or not self.ships

    def stalled(self):
        return (not self.connected) and self.msgs == 0 and (time.time() - self.booted > 600)

    def per_port(self):
        c = {}
        with self.lock:
            for r in self.ships.values():
                if r["port"]:
                    c[r["port"]] = c.get(r["port"], 0) + 1
        return c

    def public(self, r):
        return dict(mmsi=r["mmsi"], name=r["name"] or None, type=type_label(r["type"]), flag=flag_of(r["mmsi"]),
                    sog=r["sog"], dest=r["dest"] or None, eta=r["eta"], lat=r["lat"], lon=r["lon"], port=r["port"],
                    seenAgoSec=max(0, round(time.time() - r["seen"])))

    def snapshot(self, want="ALL"):
        with self.lock:
            rows = [dict(v) for v in self.ships.values() if v["port"] and v["lat"] is not None
                    and (want == "ALL" or v["port"] == want)]
        out = sorted((self.public(r) for r in rows), key=lambda x: x["seenAgoSec"])
        counts = self.per_port()
        return dict(ok=True, warming=self.warming(), stalled=self.stalled(),
                    updated=datetime.now(timezone.utc).isoformat(), count=len(out),
                    ports=[dict(code=p["code"], name=p["name"], count=counts.get(p["code"], 0)) for p in PORTS_ALL],
                    vessels=out[:150])

    def health(self):
        return dict(keySet=bool(self.key), connected=self.connected, messages=self.msgs, vessels=len(self.ships),
                    perPort=self.per_port(), uptimeSec=round(time.time() - self.booted),
                    warming=self.warming(), stalled=self.stalled(),
                    errorFrames=self.err_frames or None, closes=self.closes or None,
                    wsErrors=self.ws_errors or None, lastError=self.last_error or None)
