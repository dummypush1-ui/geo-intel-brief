// AI proxy for the HSN finder. Provider keys live ONLY in Render environment
// variables here - browsers never see them. The static site calls these
// endpoints; this service forwards to Groq / Gemini / Mistral / NVIDIA and
// returns the provider's answer untouched. Zero dependencies (node >= 20).
//
// This one service also serves live ship positions near India ports: it holds
// the AISStream key server-side, keeps one WebSocket to aisstream.io open, and
// answers GET /ships with the latest vessels as JSON (same token + rate limit).
// Needs Node 22 or newer (built-in WebSocket client).
//
// Render setup: New Web Service on this repo, Start command `node proxy.js`.
// Environment variables:
//   AISSTREAM_KEY - free aisstream.io key for the live-ships feed (optional;
//                   without it /ships answers 503 and /health says keySet false)
//   APP_SECRET   - token the page sends as x-app-token. It is visible in the
//                  public bundle, so it is a speed bump, not a true secret:
//                  it stops drive-by abuse; the rate limit below caps the rest.
//   GEMINI_KEYS  - comma-separated Google AI Studio keys
//   GROQ_KEYS    - comma-separated Groq keys
//   MISTRAL_KEYS - comma-separated Mistral keys (optional)
//   NVIDIA_KEYS  - comma-separated NVIDIA NIM keys (optional)
const http = require('http');

const SECRET = process.env.APP_SECRET || '';
const POOLS = {};
for (const kind of ['gemini', 'groq', 'mistral', 'nvidia']) {
  POOLS[kind] = (process.env[kind.toUpperCase() + '_KEYS'] || '').split(',').map((k) => k.trim()).filter(Boolean);
}
const OFF = { gemini: 0, groq: 0, mistral: 0, nvidia: 0 };

// ---------------- live ships (AISStream) ----------------
const AIS_KEY = (process.env.AISSTREAM_KEY || '').trim();
const AIS_URL = process.env.AISSTREAM_URL || 'wss://stream.aisstream.io/v0/stream';

// Major India container/bulk gateways. Boxes about +/-0.35 deg around each
// anchorage; Haldia/Kolkata wider to cover the Hooghly approach.
const AIS_PORTS = [
  { code: 'INNSA', name: 'Nhava Sheva (JNPT)', lat: 18.95, lon: 72.95 },
  { code: 'INBOM', name: 'Mumbai', lat: 18.9, lon: 72.82 },
  { code: 'INMUN', name: 'Mundra', lat: 22.74, lon: 69.7 },
  { code: 'INIXY', name: 'Kandla (Deendayal)', lat: 23.02, lon: 70.22 },
  { code: 'INMAA', name: 'Chennai', lat: 13.09, lon: 80.3 },
  { code: 'INENR', name: 'Kamarajar (Ennore)', lat: 13.25, lon: 80.35 },
  { code: 'INCOK', name: 'Kochi', lat: 9.97, lon: 76.27 },
  { code: 'INTUT', name: 'Tuticorin (V.O.C.)', lat: 8.79, lon: 78.2 },
  { code: 'INNML', name: 'New Mangalore', lat: 12.93, lon: 74.8 },
  { code: 'INVTZ', name: 'Visakhapatnam', lat: 17.69, lon: 83.29 },
  { code: 'INPRT', name: 'Paradip', lat: 20.3, lon: 86.62 },
  { code: 'INHAL', name: 'Haldia / Kolkata', lat: 21.75, lon: 87.95, wide: true },
];
// Major world gateways (top container/bulk hubs), same box style as India.
const AIS_PORTS_WORLD = [
  { code: 'SGSIN', name: 'Singapore', lat: 1.26, lon: 103.82 },
  { code: 'CNSHA', name: 'Shanghai', lat: 31.22, lon: 121.5 },
  { code: 'CNNGB', name: 'Ningbo-Zhoushan', lat: 29.87, lon: 121.9 },
  { code: 'CNSZX', name: 'Shenzhen', lat: 22.5, lon: 114.3 },
  { code: 'CNTSN', name: 'Tianjin', lat: 38.98, lon: 117.75 },
  { code: 'CNTAO', name: 'Qingdao', lat: 36.05, lon: 120.32 },
  { code: 'HKHKG', name: 'Hong Kong', lat: 22.3, lon: 114.15 },
  { code: 'KRPUS', name: 'Busan', lat: 35.08, lon: 129.08 },
  { code: 'JPYOK', name: 'Tokyo / Yokohama', lat: 35.55, lon: 139.72 },
  { code: 'TWKHH', name: 'Kaohsiung', lat: 22.6, lon: 120.28 },
  { code: 'MYPKG', name: 'Port Klang', lat: 3.0, lon: 101.37 },
  { code: 'MYTPP', name: 'Tanjung Pelepas', lat: 1.35, lon: 103.55 },
  { code: 'LKCMB', name: 'Colombo', lat: 6.95, lon: 79.84 },
  { code: 'AEJEA', name: 'Jebel Ali (Dubai)', lat: 25.0, lon: 55.05 },
  { code: 'NLRTM', name: 'Rotterdam', lat: 51.95, lon: 4.05 },
  { code: 'BEANR', name: 'Antwerp', lat: 51.3, lon: 4.35 },
  { code: 'DEHAM', name: 'Hamburg', lat: 53.9, lon: 9.95 },
  { code: 'DEBRV', name: 'Bremerhaven', lat: 53.57, lon: 8.56 },
  { code: 'ESVLC', name: 'Valencia', lat: 39.45, lon: -0.32 },
  { code: 'ESALG', name: 'Algeciras', lat: 36.1, lon: -5.43 },
  { code: 'GRPIR', name: 'Piraeus', lat: 37.94, lon: 23.64 },
  { code: 'GBFXT', name: 'Felixstowe / London', lat: 51.95, lon: 1.32 },
  { code: 'USLAX', name: 'Los Angeles', lat: 33.72, lon: -118.27 },
  { code: 'USLGB', name: 'Long Beach', lat: 33.75, lon: -118.2 },
  { code: 'USNYC', name: 'New York / New Jersey', lat: 40.64, lon: -74.02 },
  { code: 'USSAV', name: 'Savannah', lat: 32.08, lon: -81.06 },
  { code: 'USHOU', name: 'Houston', lat: 29.7, lon: -95.2 },
  { code: 'BRSSZ', name: 'Santos', lat: -23.97, lon: -46.3 },
  { code: 'ZADUR', name: 'Durban', lat: -29.87, lon: 31.06 },
  { code: 'EGSUZ', name: 'Suez Canal (both ends)', lat: 30.4, lon: 32.35, wide: true },
];
const AIS_PORTS_ALL = AIS_PORTS.concat(AIS_PORTS_WORLD);
const AIS_BOXES = AIS_PORTS_ALL.map((p) => {
  const d = p.wide ? 0.6 : 0.35;
  return [[p.lat - d, p.lon - d], [p.lat + d, p.lon + d]];
});

// MMSI first three digits (MID) -> flag, covering the common registries.
const AIS_MID = { 209: 'Cyprus', 210: 'Cyprus', 211: 'Germany', 212: 'Cyprus', 215: 'Malta', 219: 'Denmark', 220: 'Denmark', 224: 'Spain', 225: 'Spain', 226: 'France', 227: 'France', 229: 'Malta', 232: 'United Kingdom', 233: 'United Kingdom', 234: 'United Kingdom', 235: 'United Kingdom', 237: 'Greece', 239: 'Greece', 240: 'Greece', 241: 'Greece', 244: 'Netherlands', 245: 'Netherlands', 246: 'Netherlands', 247: 'Italy', 248: 'Malta', 255: 'Portugal', 256: 'Malta', 257: 'Norway', 258: 'Norway', 259: 'Norway', 265: 'Sweden', 266: 'Sweden', 273: 'Russia', 306: 'Curacao', 308: 'Bahamas', 309: 'Bahamas', 310: 'Bermuda', 311: 'Bahamas', 312: 'Belize', 314: 'Barbados', 316: 'Canada', 319: 'Cayman Is.', 338: 'USA', 351: 'Panama', 352: 'Panama', 353: 'Panama', 354: 'Panama', 355: 'Panama', 356: 'Panama', 357: 'Panama', 366: 'USA', 367: 'USA', 368: 'USA', 369: 'USA', 370: 'Panama', 371: 'Panama', 372: 'Panama', 373: 'Panama', 375: 'St Vincent', 376: 'St Vincent', 403: 'Saudi Arabia', 405: 'Bangladesh', 408: 'Bahrain', 412: 'China', 413: 'China', 414: 'China', 416: 'Taiwan', 417: 'Sri Lanka', 419: 'India', 422: 'Iran', 428: 'Israel', 431: 'Japan', 432: 'Japan', 440: 'South Korea', 441: 'South Korea', 447: 'Kuwait', 453: 'Macao', 455: 'Maldives', 461: 'Oman', 463: 'Pakistan', 466: 'Qatar', 469: 'UAE', 470: 'UAE', 471: 'UAE', 477: 'Hong Kong', 503: 'Australia', 515: 'Cambodia', 525: 'Indonesia', 533: 'Malaysia', 538: 'Marshall Is.', 548: 'Philippines', 563: 'Singapore', 564: 'Singapore', 565: 'Singapore', 566: 'Singapore', 567: 'Thailand', 574: 'Vietnam', 576: 'Vanuatu', 577: 'Vanuatu', 601: 'South Africa', 636: 'Liberia', 637: 'Liberia', 645: 'Mauritius', 677: 'Tanzania', 710: 'Brazil' };

function aisFlag(mmsi) {
  return AIS_MID[Number(String(mmsi).slice(0, 3))] || null;
}
function aisType(t) {
  if (t >= 60 && t <= 69) return 'Passenger';
  if (t >= 70 && t <= 79) return 'Cargo';
  if (t >= 80 && t <= 89) return 'Tanker';
  if (t === 30) return 'Fishing';
  if (t === 52 || t === 31 || t === 32) return 'Tug';
  if (t === 50) return 'Pilot boat';
  if (t === 35) return 'Military';
  if (t === 36) return 'Sailing';
  if (t === 37) return 'Pleasure';
  if (t === 51) return 'SAR';
  if (t === 53 || t === 55 || t === 58 || t === 59) return 'Service';
  if (t === 33 || t === 34) return 'Work boat';
  if (t >= 40 && t <= 49) return 'High-speed';
  if (t >= 90) return 'Other';
  return null;
}
function aisDistKm(aLat, aLon, bLat, bLon) {
  const r = Math.PI / 180;
  const h = Math.sin((bLat - aLat) * r / 2) ** 2 + Math.cos(aLat * r) * Math.cos(bLat * r) * Math.sin((bLon - aLon) * r / 2) ** 2;
  return 12742 * Math.asin(Math.sqrt(h));
}
function aisNearestPort(lat, lon) {
  let best = null, bd = 1e9;
  for (const p of AIS_PORTS_ALL) {
    const d = aisDistKm(lat, lon, p.lat, p.lon);
    if (d < bd) { bd = d; best = p; }
  }
  return bd <= (best.wide ? 70 : 45) ? best.code : null;
}
function aisEtaText(e) {
  if (!e || !e.Month || e.Month < 1 || e.Month > 12 || !e.Day) return null;
  const now = new Date();
  const y = now.getUTCFullYear();
  let d = new Date(Date.UTC(y, e.Month - 1, e.Day, e.Hour && e.Hour < 24 ? e.Hour : 0, e.Minute && e.Minute < 60 ? e.Minute : 0));
  if (d.getTime() < now.getTime() - 45 * 864e5) d = new Date(Date.UTC(y + 1, e.Month - 1, e.Day, e.Hour && e.Hour < 24 ? e.Hour : 0, e.Minute && e.Minute < 60 ? e.Minute : 0));
  if (d.getTime() < now.getTime() - 864e5 || d.getTime() > now.getTime() + 400 * 864e5) return null;
  return d.toISOString().slice(0, 16).replace('T', ' ') + ' UTC';
}

const aisShips = new Map(); // mmsi -> record
let aisMsgCount = 0, aisLastMsgAt = 0, aisConnected = false;
let aisErrFrames = 0, aisLastFrameType = '', aisLastFrameNote = '';
let aisCloseCount = 0, aisLastCloseAt = 0, aisLastCloseCode = 0, aisErrCount = 0, aisLastErrAt = 0;
const aisBootedAt = Date.now();

function aisUpsert(m) {
  const md = m.MetaData || {};
  const body = m.Message && (m.Message.PositionReport || m.Message.ShipStaticData);
  const mmsi = String(md.MMSI || (body && body.UserID) || '');
  if (!mmsi || mmsi === '0') return;
  let r = aisShips.get(mmsi);
  if (!r) {
    r = { mmsi, name: '', type: null, dest: '', eta: null, imo: null, lat: null, lon: null, sog: null, cog: null, seen: 0, port: null };
    aisShips.set(mmsi, r);
    if (aisShips.size > 6000) {
      let oldK = null, oldT = Infinity;
      for (const [k, v] of aisShips) if (v.seen < oldT) { oldT = v.seen; oldK = k; }
      if (oldK) aisShips.delete(oldK);
    }
  }
  if (md.ShipName && String(md.ShipName).trim()) r.name = String(md.ShipName).trim();
  if (m.MessageType === 'PositionReport' && m.Message && m.Message.PositionReport) {
    const p = m.Message.PositionReport;
    const la = typeof p.Latitude === 'number' ? p.Latitude : (typeof md.latitude === 'number' ? md.latitude : null);
    const lo = typeof p.Longitude === 'number' ? p.Longitude : (typeof md.longitude === 'number' ? md.longitude : null);
    if (la !== null && la >= -90 && la <= 90 && la !== 91) r.lat = la;
    if (lo !== null && lo >= -180 && lo <= 180 && lo !== 181) r.lon = lo;
    if (typeof p.Sog === 'number' && p.Sog >= 0 && p.Sog < 102.3) r.sog = Math.round(p.Sog * 10) / 10;
    if (typeof p.Cog === 'number' && p.Cog >= 0 && p.Cog < 360) r.cog = Math.round(p.Cog);
    r.seen = Date.now();
  } else if (m.MessageType === 'ShipStaticData' && m.Message && m.Message.ShipStaticData) {
    const sd = m.Message.ShipStaticData;
    if (sd.Name && String(sd.Name).trim()) r.name = String(sd.Name).trim();
    if (typeof sd.Type === 'number') r.type = sd.Type;
    if (sd.Destination && String(sd.Destination).trim()) r.dest = String(sd.Destination).trim();
    if (sd.ImoNumber) r.imo = sd.ImoNumber;
    const et = aisEtaText(sd.Eta);
    if (et) r.eta = et;
    r.seen = Date.now();
  }
  if (r.lat !== null && r.lon !== null) r.port = aisNearestPort(r.lat, r.lon);
}

setInterval(() => {
  const cut = Date.now() - 2 * 3600e3;
  for (const [k, v] of aisShips) if (v.seen < cut) aisShips.delete(k);
}, 300e3);

let aisBackoff = 1000;
let aisLiveWs = null;
process.on('SIGTERM', () => { try { if (aisLiveWs) aisLiveWs.close(1000, 'shutdown'); } catch (e) { } setTimeout(() => process.exit(0), 500); });
function aisConnect() {
  if (!AIS_KEY || typeof WebSocket !== 'function') return;
  let ws;
  try { ws = new WebSocket(AIS_URL); aisLiveWs = ws; } catch (e) { return aisRetry(); }
  ws.onopen = () => {
    aisBackoff = 1000;
    aisConnected = true;
    console.log('aisstream connected, subscribing to', AIS_BOXES.length, 'port boxes');
    ws.send(JSON.stringify({ APIKey: AIS_KEY, BoundingBoxes: AIS_BOXES, MessageTypes: ['PositionReport', 'ShipStaticData'] }));
  };
  ws.onmessage = async (ev) => {
    aisLastMsgAt = Date.now();
    aisMsgCount++;
    try {
      let d = ev.data;
      if (typeof d !== 'string') {
        if (d && typeof d.text === 'function') d = await d.text();
        else if (d instanceof ArrayBuffer) d = Buffer.from(d).toString('utf8');
        else if (ArrayBuffer.isView(d)) d = Buffer.from(d.buffer, d.byteOffset, d.byteLength).toString('utf8');
        else d = String(d);
      }
      const m = JSON.parse(d);
      aisLastFrameType = m.MessageType || 'unknown';
      if (!m.MetaData || !m.MetaData.MMSI) {
        aisErrFrames++;
        aisLastFrameNote = String(d).replace(/[A-Za-z0-9]{20,}/g, '[redacted]').slice(0, 160);
      }
      aisUpsert(m);
    } catch (e) { aisErrFrames++; aisLastFrameNote = 'unparseable ' + Object.prototype.toString.call(ev.data); }
  };
  ws.onclose = (ev) => { aisConnected = false; aisCloseCount++; aisLastCloseAt = Date.now(); aisLastCloseCode = ev && ev.code ? ev.code : 0; console.log('aisstream closed', aisLastCloseCode, 'attempt', aisCloseCount); aisRetry(); };
  ws.onerror = () => { aisErrCount++; aisLastErrAt = Date.now(); try { ws.close(); } catch (e) { } };
}
function aisRetry() {
  aisConnected = false;
  setTimeout(aisConnect, aisBackoff);
  aisBackoff = Math.min(aisBackoff * 2, 60000);
}
// Watchdog: a quiet socket is a dead socket - reconnect after 6 silent minutes.
setInterval(() => {
  if (aisConnected && aisLastMsgAt && Date.now() - aisLastMsgAt > 6 * 60e3) {
    console.log('aisstream quiet for 6 min - reconnecting');
    aisConnected = false;
    aisConnect();
  }
}, 60e3);
aisConnect();

function aisPublicShip(r) {
  return {
    mmsi: r.mmsi, name: r.name || null, type: r.type !== null ? aisType(r.type) : null,
    flag: aisFlag(r.mmsi), sog: r.sog, dest: r.dest || null, eta: r.eta,
    lat: r.lat, lon: r.lon, port: r.port, seenAgoSec: Math.max(0, Math.round((Date.now() - r.seen) / 1000)),
  };
}
function aisPerPort() {
  const c = {};
  for (const r of aisShips.values()) if (r.port) c[r.port] = (c[r.port] || 0) + 1;
  return c;
}
const aisWarming = () => (Date.now() - aisBootedAt < 10 * 60e3) || aisShips.size === 0;
// Stalled: up >10 min, never connected, no frames - the upstream key/feed is dead, not warming.
const aisStalled = () => !aisConnected && aisMsgCount === 0 && (Date.now() - aisBootedAt > 10 * 60e3);
// ---------------- end live ships ----------------

const ROUTES = [
  { kind: 'gemini', match: /^\/gemini\/v1beta\/models\/[A-Za-z0-9._-]+:generateContent$/, upstream: (p) => 'https://generativelanguage.googleapis.com' + p.replace(/^\/gemini/, ''), header: (k) => ({ 'x-goog-api-key': k }) },
  { kind: 'groq', match: /^\/groq\/openai\/v1\/chat\/completions$/, upstream: () => 'https://api.groq.com/openai/v1/chat/completions', header: (k) => ({ Authorization: 'Bearer ' + k }) },
  { kind: 'mistral', match: /^\/mistral\/v1\/chat\/completions$/, upstream: () => 'https://api.mistral.ai/v1/chat/completions', header: (k) => ({ Authorization: 'Bearer ' + k }) },
  { kind: 'nvidia', match: /^\/nvidia\/v1\/chat\/completions$/, upstream: () => 'https://integrate.api.nvidia.com/v1/chat/completions', header: (k) => ({ Authorization: 'Bearer ' + k }) },
];

// Lean abuse cap: 60 AI calls per 10 minutes per IP (a full report is 1-3 calls).
const HITS = new Map();
const WINDOW = 10 * 60 * 1000, MAX = 60;
function rateOk(ip) {
  const now = Date.now();
  let a = HITS.get(ip);
  if (!a || now - a.t > WINDOW) { a = { t: now, n: 0 }; HITS.set(ip, a); }
  a.n++;
  if (HITS.size > 5000) HITS.clear();
  return a.n <= MAX;
}

function send(res, status, body, extra) {
  const headers = Object.assign({ 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }, extra || {});
  res.writeHead(status, headers);
  res.end(typeof body === 'string' ? body : JSON.stringify(body));
}

const port = process.env.PORT || 3000;
http.createServer(async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  if (req.method === 'OPTIONS') {
    res.writeHead(204, { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'POST, GET', 'Access-Control-Allow-Headers': 'Content-Type, x-app-token', 'Access-Control-Max-Age': '86400' });
    return res.end();
  }
  const path = req.url.split('?')[0];
  if (req.method === 'GET' && (path === '/' || path === '/health')) {
    return send(res, 200, {
      ok: true, service: 'hsn ai + ais proxy',
      providers: Object.keys(POOLS).filter((k) => POOLS[k].length),
      ais: {
        keySet: !!AIS_KEY, connected: aisConnected, messages: aisMsgCount, vessels: aisShips.size,
        perPort: aisPerPort(), uptimeSec: Math.round((Date.now() - aisBootedAt) / 1000), warming: aisWarming(), stalled: aisStalled(),
        lastFrameType: aisLastFrameType || undefined, errorFrames: aisErrFrames || undefined,
        closes: aisCloseCount || undefined, lastCloseCode: aisLastCloseCode || undefined,
        lastCloseAgoSec: aisLastCloseAt ? Math.round((Date.now() - aisLastCloseAt) / 1000) : undefined,
        wsErrors: aisErrCount || undefined,
        lastFrameNote: aisLastFrameNote || undefined,
        note: typeof WebSocket !== 'function' ? 'node >= 22 required for the ais feed' : undefined,
      },
    });
  }
  if (req.method === 'GET' && path === '/ships') {
    if (!SECRET || req.headers['x-app-token'] !== SECRET) return send(res, 401, { error: { message: 'bad app token' } });
    const ip2 = String(req.headers['cf-connecting-ip'] || req.headers['x-forwarded-for'] || req.socket.remoteAddress || '?').split(',')[0].trim();
    if (!rateOk(ip2)) return send(res, 429, { error: { message: 'rate limit exceeded. try again later.' } });
    if (!AIS_KEY) return send(res, 503, { error: { message: 'AISSTREAM_KEY not configured on the server' } });
    const want = ((req.url.split('?')[1] || '').match(/port=([A-Za-z]+)/) || [, 'ALL'])[1].toUpperCase();
    const out = [];
    for (const r of aisShips.values()) {
      if (!r.port || r.lat === null) continue;
      if (want !== 'ALL' && r.port !== want) continue;
      out.push(aisPublicShip(r));
    }
    out.sort((a, b) => a.seenAgoSec - b.seenAgoSec);
    const counts = aisPerPort();
    return send(res, 200, {
      ok: true, warming: aisWarming(), stalled: aisStalled(), updated: new Date().toISOString(), count: out.length,
      ports: AIS_PORTS_ALL.map((p) => ({ code: p.code, name: p.name, count: counts[p.code] || 0 })),
      vessels: out.slice(0, 150),
    });
  }
  if (req.method !== 'POST') return send(res, 405, { error: { message: 'method not allowed' } });
  if (!SECRET || req.headers['x-app-token'] !== SECRET) return send(res, 401, { error: { message: 'bad app token' } });
  const route = ROUTES.find((r) => r.match.test(path));
  if (!route) return send(res, 404, { error: { message: 'unknown endpoint' } });
  const ip = req.headers['cf-connecting-ip'] || req.headers['x-forwarded-for'] || req.socket.remoteAddress || '?';
  if (!rateOk(String(ip).split(',')[0].trim())) return send(res, 429, { error: { message: 'rate limit exceeded. try again later.' } });
  const pool = POOLS[route.kind];
  if (!pool.length) return send(res, 503, { error: { message: route.kind + ' keys not configured on the server' } });
  let body = '';
  req.on('data', (c) => { body += c; if (body.length > 2e6) req.destroy(); });
  req.on('end', async () => {
    for (let i = 0; i < pool.length; i++) {
      const ki = (OFF[route.kind] + i) % pool.length;
      const key = pool[ki];
      try {
        const ctrl = new AbortController();
        const timer = setTimeout(() => ctrl.abort(), 150000);
        const up = await fetch(route.upstream(path), {
          method: 'POST',
          headers: Object.assign({ 'Content-Type': 'application/json' }, route.header(key)),
          body,
          signal: ctrl.signal,
        });
        clearTimeout(timer);
        const text = await up.text();
        if ((up.status === 401 || up.status === 403 || up.status === 429) && pool.length > 1 && i < pool.length - 1) continue; // next key
        OFF[route.kind] = ki;
        res.writeHead(up.status, { 'Content-Type': up.headers.get('content-type') || 'application/json', 'Access-Control-Allow-Origin': '*' });
        return res.end(text);
      } catch (e) {
        if (i < pool.length - 1) continue;
        return send(res, 502, { error: { message: 'upstream unreachable - try again in a minute' } });
      }
    }
  });
}).listen(port, () => console.log('ai+ais proxy listening on ' + port + ' - providers: ' + Object.keys(POOLS).filter((k) => POOLS[k].length).join(', ') + ' - ais key ' + (AIS_KEY ? 'set' : 'MISSING')));
