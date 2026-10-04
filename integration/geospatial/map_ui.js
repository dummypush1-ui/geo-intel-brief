// Copyright (c) 2026 Push
// Offline SVG map surface plus table fallback. No network, no HTML-string insertion,
// no inline script. All text goes through textContent.
const W = 1000, H = 500, CAP = 1000, SVGNS = "http://www.w3.org/2000/svg";
const LAYERS = [
  ["news", "News"], ["ports", "Ports"], ["chokepoints", "Chokepoints"], ["ships", "Ships"],
];
const mounted = new WeakMap();

const own = (o, k) => (o !== null && typeof o === "object" && Object.prototype.hasOwnProperty.call(o, k)) ? o[k] : undefined;
const num = (v, lo, hi) => (typeof v === "number" && Number.isFinite(v) && v >= lo && v <= hi) ? v : null;
const str = (v, n) => {
  if (typeof v !== "string") return "";
  return v.replace(/[\u0000-\u001f\u007f-\u009f\u00ad\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff]/g, " ").trim().slice(0, n);
};
// Mirrors _safe.safe_https_url (Python) exactly: printable ASCII only (0x21-0x7e),
// https scheme (case-insensitive), no "@" in the authority, hostname [a-z0-9.-]
// starting/ending alphanumeric with no "..", last label not all digits, optional
// numeric port <= 65535. The final new URL() call may reject additional hosts (for
// example malformed xn-- punycode); guarantee: JS accepts => Python accepts.
function safeUrl(v) {
  if (typeof v !== "string" || v.length === 0 || v.length > 2000 || /[^\x21-\x7e]/.test(v)) return "";
  const m = /^https:\/\/([^\/?#]*)/i.exec(v);
  if (!m || m[1].indexOf("@") !== -1) return "";
  const hp = /^([^:]*)(?::([0-9]*))?$/.exec(m[1]);
  if (!hp) return "";
  const host = hp[1].toLowerCase();
  if (!/^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$/.test(host) || host.indexOf("..") !== -1) return "";
  if (/^[0-9]+$/.test(host.slice(host.lastIndexOf(".") + 1))) return "";
  if (hp[2] && Number(hp[2]) > 65535) return "";
  try { new URL(v); } catch (e) { return ""; }
  return v;
}
function el(doc, tag, attrs, text) {
  const e = doc.createElement(tag);
  if (attrs) for (const k of Object.keys(attrs)) e.setAttribute(k, attrs[k]);
  if (text !== undefined) e.textContent = text;
  return e;
}
function svg(doc, tag, attrs, text) {
  const e = doc.createElementNS(SVGNS, tag);
  if (attrs) for (const k of Object.keys(attrs)) e.setAttribute(k, String(attrs[k]));
  if (text !== undefined) e.textContent = text;
  return e;
}
function ageText(s) {
  if (s === null || s === undefined || !Number.isFinite(s)) return "age unknown";
  if (s < 90) return Math.round(s) + " s old";
  if (s < 5400) return Math.round(s / 60) + " min old";
  return Math.round(s / 3600) + " h old";
}

// Re-validate whatever the caller passed; never trust payload shape.
function cleanLayer(payload, name) {
  const layers = own(payload, "layers");
  const L = own(layers, name);
  const out = { available: false, items: [], note: "", status: "", age: null, stale: null,
                truncated: false, provDropped: 0, vessels: null, messages: null, captured: "", prov: [] };
  if (!L || own(L, "available") !== true) return out;
  out.available = true;
  out.note = str(own(L, "note"), 200);
  out.status = str(own(L, "status"), 30);
  out.captured = str(own(L, "captured_at"), 40);
  const age = own(L, "age_seconds");
  out.age = typeof age === "number" && Number.isFinite(age) ? age : null;
  out.stale = own(L, "stale") === true;
  out.truncated = own(L, "truncated") === true || own(own(L, "report"), "truncated") === true;
  out.vessels = num(own(L, "supplied_vessel_count"), 0, 1e9);
  out.messages = num(own(L, "supplied_message_count"), 0, 1e9);
  out.provDropped = num(own(L, "provenance_groups_dropped"), 0, 1e9) || 0;
  const prov = own(L, "provenance");
  if (Array.isArray(prov)) for (const p of prov.slice(0, 20))
    if (Array.isArray(p)) out.prov.push([str(p[0], 120), str(p[1], 80), str(p[2], 80), safeUrl(p[3]), num(p[4], 1, 1e9) || 1]);
  const items = own(L, "items");
  if (Array.isArray(items)) for (const it of items.slice(0, CAP)) {
    const x = num(own(it, "x"), 0, W), y = num(own(it, "y"), 0, H);
    if (x === null || y === null) continue;
    const lat = num(own(it, "latitude"), -90, 90), lon = num(own(it, "longitude"), -180, 180);
    if (lat === null || lon === null) continue;
    let label = "";
    if (name === "ships") label = str(own(it, "name"), 60) || ("MMSI " + str(String(own(it, "mmsi") ?? ""), 12));
    else label = str(own(it, name === "news" ? "title" : "name"), 120);
    if (!label) continue;
    const rects = [];
    const rr = own(it, "rects");
    if (Array.isArray(rr)) for (const r of rr.slice(0, 2)) {
      const rx = num(own(r, "x"), 0, W), ry = num(own(r, "y"), 0, H), rw = num(own(r, "w"), 0, W), rh = num(own(r, "h"), 0, H);
      if (rx !== null && ry !== null && rw !== null && rh !== null) rects.push([rx, ry, rw, rh]);
    }
    out.items.push({ x, y, lat, lon, label, rects,
      url: safeUrl(own(it, "url") || own(it, "source_url")),
      detail: str(own(it, "source") || own(it, "dataset") || own(it, "category") || "", 120),
      fixture: own(it, "fixture") === true });
  }
  return out;
}

export function mountMap(element, payload, options) {
  if (!element || typeof element.ownerDocument !== "object") throw new TypeError("element required");
  dispose(element);
  const doc = element.ownerDocument;
  const opts = options && typeof options === "object" ? options : {};
  const token = { live: true, listeners: [] };
  mounted.set(element, token);
  const root = el(doc, "div", { class: "geo-map" });
  const layers = {};
  for (const [k] of LAYERS) layers[k] = cleanLayer(payload, k);
  const visible = {};
  for (const [k] of LAYERS) visible[k] = true;

  // Styles live in geo_map.css (caller links it); no inline style element, so no style-src unsafe-inline.
  root.appendChild(el(doc, "h3", null, str(opts.title, 80) || "Map"));

  const status = el(doc, "div", { class: "geo-status", role: "status" });
  root.appendChild(status);
  const bar = el(doc, "div", { class: "geo-bar", role: "group", "aria-label": "Map layers" });
  root.appendChild(bar);

  const s = svg(doc, "svg", { viewBox: "-12 -12 " + (W + 24) + " " + (H + 24), role: "img",
    "aria-label": "Offline world map without base tiles. Markers are positioned by latitude and longitude." });
  for (let lon = -180; lon <= 180; lon += 30) s.appendChild(svg(doc, "line", { class: "grat", x1: (lon + 180) / 360 * W, y1: 0, x2: (lon + 180) / 360 * W, y2: H }));
  for (let lat = -90; lat <= 90; lat += 30) s.appendChild(svg(doc, "line", { class: "grat", x1: 0, y1: (90 - lat) / 180 * H, x2: W, y2: (90 - lat) / 180 * H }));
  root.appendChild(s);
  root.appendChild(el(doc, "div", { class: "geo-status" }, "No base map is loaded in offline preview; grid lines are 30 degrees."));

  const groups = {};
  for (const [k, label] of LAYERS) {
    const L = layers[k];
    const g = svg(doc, "g", { "data-layer": k });
    groups[k] = g;
    s.appendChild(g);
    for (const it of L.items) {
      for (const r of it.rects) g.appendChild(svg(doc, "rect", { class: "bx", x: r[0], y: r[1], width: r[2], height: r[3] }));
      const c = svg(doc, "circle", { class: "dot m-" + k + (k === "ships" && layers.ships.stale ? " stale" : ""), cx: it.x, cy: it.y, r: k === "ships" ? 3 : 5, tabindex: 0, role: "img",
        "aria-label": label + ": " + it.label + ", " + it.lat.toFixed(2) + ", " + it.lon.toFixed(2) });
      c.appendChild(svg(doc, "title", null, it.label));
      g.appendChild(c);
    }
    const lab = el(doc, "label");
    const cb = el(doc, "input", { type: "checkbox" });
    cb.checked = true;
    cb.disabled = !L.available;
    const onChange = () => { visible[k] = cb.checked; g.setAttribute("display", cb.checked ? "inline" : "none"); renderTable(); };
    cb.addEventListener("change", onChange);
    token.listeners.push([cb, "change", onChange]);
    lab.appendChild(cb);
    lab.appendChild(el(doc, "span", { class: "key k-" + k }));
    lab.appendChild(doc.createTextNode(label + " (" + (L.available ? L.items.length : "unavailable") + ")"));
    bar.appendChild(lab);
  }

  // Coverage / age / source labels, always visible.
  const sh = layers.ships;
  const lines = [];
  if (!sh.available) lines.push("Ships: no data supplied (absent, not an empty sea).");
  else {
    let t = "Ships: " + sh.status + (sh.captured ? ", captured " + sh.captured + " (" + ageText(sh.age) + ")" : "");
    if (sh.stale) t += ", STALE";
    if (sh.truncated) t += ", display truncated";
    if (sh.items.length === 0) t += ", no vessels in snapshot";
    if (sh.vessels !== null) t += ", supplied vessel count " + sh.vessels;
    lines.push(t + ". " + sh.note);
  }
  for (const [k, label] of LAYERS) {
    const L = layers[k];
    if (k === "ships") continue;
    if (!L.available) lines.push(label + ": unavailable.");
    else if (L.truncated) lines.push(label + ": truncated.");
    if (L.note) lines.push(label + ": " + L.note);
    for (const p of L.prov) {
      const n = p[4];
      const d = el(doc, "div", { class: "geo-status" }, label + " source: " + p[0] + ", licence " + p[1] + ", " + p[2] + " ");
      if (p[3]) d.appendChild(el(doc, "a", { href: p[3], target: "_blank", rel: "noopener noreferrer" }, "source"));
      if (n > 1) d.appendChild(doc.createTextNode(" (+" + (n - 1) + " more source links in the table)"));
      root.appendChild(d);
    }
    if (L.provDropped > 0) root.appendChild(el(doc, "div", { class: "geo-status geo-warn" }, label + ": " + L.provDropped + " more dataset/licence groups not shown."));
  }
  status.textContent = lines.join(" | ");
  if (sh.stale || !sh.available) status.setAttribute("class", "geo-status geo-warn");

  const wrap = el(doc, "div", { class: "scroll" });
  root.appendChild(wrap);
  function renderTable() {
    if (!token.live) return;
    while (wrap.firstChild) wrap.removeChild(wrap.firstChild);
    const table = el(doc, "table");
    const cap = el(doc, "caption", null, "Map items (table view)");
    table.appendChild(cap);
    const head = el(doc, "tr");
    for (const h of ["Layer", "Name", "Lat, Lon", "Link"]) head.appendChild(el(doc, "th", { scope: "col" }, h));
    table.appendChild(head);
    let rows = 0;
    for (const [k, label] of LAYERS) {
      if (!visible[k]) continue;
      for (const it of layers[k].items) {
        if (rows++ >= CAP) break;
        const tr = el(doc, "tr");
        tr.appendChild(el(doc, "td", null, label));
        tr.appendChild(el(doc, "td", null, it.label + (it.fixture ? " (fixture)" : "")));
        tr.appendChild(el(doc, "td", null, it.lat.toFixed(3) + ", " + it.lon.toFixed(3)));
        const td = el(doc, "td");
        if (it.url) td.appendChild(el(doc, "a", { href: it.url, target: "_blank", rel: "noopener noreferrer" }, "open"));
        tr.appendChild(td);
        table.appendChild(tr);
      }
    }
    if (rows === 0) { const tr = el(doc, "tr"); const td = el(doc, "td", { colspan: 4 }, "Nothing to show."); tr.appendChild(td); table.appendChild(tr); }
    wrap.appendChild(table);
  }
  renderTable();
  element.appendChild(root);
  token.root = root;
  return { dispose: () => dispose(element) };
}

export function dispose(element) {
  const t = element && mounted.get(element);
  if (!t) return;
  t.live = false;  // guards any late render
  for (const [n, ev, fn] of t.listeners) n.removeEventListener(ev, fn);
  t.listeners.length = 0;
  if (t.root && t.root.parentNode) t.root.parentNode.removeChild(t.root);
  mounted.delete(element);
}

// Exposed for the parity test only.
export const _test = { safeUrl };
