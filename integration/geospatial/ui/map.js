// Copyright (c) 2026 Push
// Page controller: one manual click loads /api/map-data (same origin, GET) and mounts the map.
// No polling, no timers, no other network. Stale responses are ignored.
import { mountMap, dispose } from "./geo_map_ui.js";

const ENDPOINT = "/api/map-data";
const host = document.getElementById("map-host");
const btn = document.getElementById("map-load");
const msg = document.getElementById("map-msg");
let seq = 0, ctl = null;

function say(text, isErr) {
  msg.textContent = text;
  msg.setAttribute("class", isErr ? "map-msg map-err" : "map-msg");
}

async function load() {
  const mine = ++seq;
  if (ctl) ctl.abort();
  ctl = new AbortController();
  btn.disabled = true;
  say("Loading map data...", false);
  try {
    const res = await fetch(ENDPOINT, { method: "GET", credentials: "same-origin", cache: "no-store",
      headers: { Accept: "application/json" }, signal: ctl.signal });
    if (mine !== seq) return;
    if (!res.ok) { say(res.status === 503 ? "Map data is unavailable right now (503)." : "Could not load map data (" + res.status + ").", true); return; }
    const text = await res.text();
    if (mine !== seq) return;
    if (text.length > 2000000) { say("Map data response was too large to show.", true); return; }
    const payload = JSON.parse(text);
    dispose(host);
    mountMap(host, payload, { title: "Reference map" });
    say("Loaded " + (typeof payload.generated_at === "string" ? payload.generated_at.slice(0, 40) : "just now") + ". Load again to refresh; nothing updates by itself.", false);
  } catch (e) {
    if (mine === seq && !(e && e.name === "AbortError")) say("Could not load map data.", true);
  } finally {
    if (mine === seq) btn.disabled = false;
  }
}
btn.addEventListener("click", load);
window.addEventListener("pagehide", () => { seq++; if (ctl) ctl.abort(); dispose(host); });
