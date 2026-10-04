// Copyright (c) 2026 Push
import { mountMap, dispose } from "../../../integration/geospatial/map_ui.js";
const q = new URLSearchParams(location.search);
const host = document.getElementById("host");
const r = await fetch(q.get("data") || "payload.json");  // local preview file only
const payload = JSON.parse(await r.text());
const real = q.get("real") === "1";
if (real) document.querySelector(".fx").textContent = "REAL reference data (Wikidata CC0), retrieved 2026-10-04. Offline preview.";
mountMap(host, payload, { title: real ? "Map (reference data)" : "Map (fixture)" });
if (q.get("dispose")) { dispose(host); mountMap(host, payload); dispose(host); }
document.title = "ready:" + host.querySelectorAll("circle").length + ":" + (window.PWNED ? "PWNED" : "clean") + ":" + ({}.polluted ? "POLLUTED" : "ok");
