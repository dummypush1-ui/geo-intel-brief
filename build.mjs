// Builds a hosted shell, versioned dataset, and offline single-file finder from src/.
// Node port of the original build script - plain concatenation, no dependencies.
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';

const SRC = path.join(process.cwd(), 'src');
const PAKO = fs.readFileSync(path.join(process.cwd(), 'vendor', 'pako-inflate.min.js'), 'utf8');
const OUT = path.join(process.cwd(), 'index.html');

const read = (p) => fs.readFileSync(path.join(SRC, p), 'utf8');

// 1. data chunks -> one base64 string
const parts = [];
for (let n = 0; ; n++) {
  if (!fs.existsSync(path.join(SRC, `datachunk${n}.ts`))) break;
  const t = read(`datachunk${n}.ts`);
  const m = t.match(/export const CHUNK\d+ = "([A-Za-z0-9+/=]+)";/);
  if (!m) throw new Error(`chunk ${n} not found`);
  parts.push(m[1]);
}
const dataB64 = parts.join('');

// 2. maps: strip TS types + export - every strip MUST match, or the build dies loudly.
const must = (text, from, to, label) => {
  const out = text.replace(from, to);
  if (out === text) throw new Error('build: strip did not match - ' + label);
  return out;
};
const plain = (file, name) => must(read(file), new RegExp('export const ' + name + '\\s*:\\s*[^=]+='), 'const ' + name + ' =', file + ':' + name);

const gst = plain('gstmap.ts', 'GST_MAP');
const trade = plain('trademap.ts', 'TRADE_CH');
const trade6 = plain('tradevalues.ts', 'TRADE6');
const tradepartners = must(plain('tradepartners.ts', 'TRADE_PARTNERS'), 'export const TRADE_PARTNERS_YEAR =', 'const TRADE_PARTNERS_YEAR =', 'TRADE_PARTNERS_YEAR');
const marketdata = must(must(plain('marketdata.ts', 'MARKET_IMPORTERS'), 'export const MARKET_DATA_YEAR =', 'const MARKET_DATA_YEAR =', 'MARKET_DATA_YEAR'), /export const MARKET_WORLD: Record<string, number> =/, 'const MARKET_WORLD =', 'MARKET_WORLD');
const marketexp = must(must(plain('marketexp.ts', 'MARKET_EXPORTERS'), 'export const MARKET_EXP_YEAR =', 'const MARKET_EXP_YEAR =', 'MARKET_EXP_YEAR'), /export const MARKET_WORLD_X: Record<string, number> =/, 'const MARKET_WORLD_X =', 'MARKET_WORLD_X');
const sancgap = must(plain('sancgap.ts', 'SANCGAP'), 'export const SANCGAP_YEAR =', 'const SANCGAP_YEAR =', 'SANCGAP_YEAR');
const tradetrend = must(plain('tradetrend.ts', 'TRADE_TREND'), 'export const TRADE_TREND_YEARS =', 'const TRADE_TREND_YEARS =', 'TRADE_TREND_YEARS');
const tradeseason = must(plain('tradeseson.ts', 'TRADE_SEASON'), 'export const TRADE_SEASON_YEARS =', 'const TRADE_SEASON_YEARS =', 'TRADE_SEASON_YEARS');
const docs = must(read('docs.ts'), /export const (DOC_BASE_OUT|DOC_BASE_IN|DOC_EXTRA|PORTS|DOC_SRC) =/g, 'const $1 =', 'docs exports');
const sancz = must(must(read('sanc.ts'), 'export const SANC_ZONES =', 'const SANC_ZONES =', 'SANC_ZONES'), 'export const SANC_SRC =', 'const SANC_SRC =', 'SANC_SRC');
const add = must(must(must(read('add.ts'), 'export const ADD_MEASURES =', 'const ADD_MEASURES =', 'ADD_MEASURES'), 'export const ADD_ONGOING =', 'const ADD_ONGOING =', 'ADD_ONGOING'), 'export const ADD_SRC =', 'const ADD_SRC =', 'ADD_SRC');
const certs = must(must(read('certs.ts'), 'export const CERT_RULES =', 'const CERT_RULES =', 'CERT_RULES'), 'export const CERT_SRC =', 'const CERT_SRC =', 'CERT_SRC');
const fta = must(must(plain('fta.ts', 'FTA_UAE'), 'export const FTA_UAE_UNPARSED: string[] =', 'const FTA_UAE_UNPARSED =', 'FTA_UAE_UNPARSED'), 'export const FTA_AU: Record<string, string[]> =', 'const FTA_AU =', 'FTA_AU');
const rodtep = must(must(read('rodtep.ts'), 'export const RODTEP_DTA: Record<string, [string, string, string]> =', 'const RODTEP_DTA =', 'RODTEP_DTA'), 'export const RODTEP_SEZ: Record<string, [string, string, string]> =', 'const RODTEP_SEZ =', 'RODTEP_SEZ');
const scomet = plain('scomet.ts', 'SCOMET');
const alias = plain('aliases.ts', 'ALIASES');
const worldports = plain('worldports.ts', 'WORLD_PORTS');
const hscorr = must(must(read('hscorr.ts'), 'export const HS22_FWD: Record<string, string[]> =', 'const HS22_FWD =', 'HS22_FWD'), 'export const HS22_REV: Record<string, string[]> =', 'const HS22_REV =', 'HS22_REV');
const sanc = must(must(read('sanctions.ts'), 'export const SANCTIONS_META =', 'const SANCTIONS_META =', 'SANCTIONS_META'), 'export const SANCTIONS: [string, string, string][] =', 'const SANCTIONS =', 'SANCTIONS');

// 3. app.js: drop ES imports/exports
const app0 = read('app.js');
const appImports = (app0.match(/^import [^\n]+\n/gm) || []).length;
const app = must(must(app0, /^import [^\n]+\n/gm, '', 'app.js import lines'), 'export function boot(', 'function boot(', 'boot export');
if (!appImports) throw new Error('build: app.js import lines not found');

const css = read('style.css');

const dataJs = `var DATA_B64 = ${JSON.stringify(dataB64)};\n${gst}\n${trade}\n${trade6}\n${tradepartners}\n${marketexp}\n${marketdata}\n${worldports}\n${sancgap}\n${tradetrend}\n${tradeseason}\n${docs}\n${sancz}\n${add}\n${certs}\n${fta}\n${rodtep}\n${scomet}\n${alias}\n${hscorr}\n${sanc}\n`;
const dataVersion = crypto.createHash('sha256').update(dataJs).digest('hex').slice(0, 12);
const dataName = 'data.' + dataVersion + '.js';
fs.writeFileSync(path.join(process.cwd(), dataName), dataJs);
for (const f of fs.readdirSync(process.cwd())) if (/^data\.[0-9a-f]{12}\.js$/.test(f) && f !== dataName) fs.rmSync(f);
// Network-first HTML, immutable versioned code data. Old deployments never pin stale UI.
const sw = `/* Copyright (c) 2026 Push. */
const CACHE = 'hsn-data-${dataVersion}';
self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.add('./data.${dataVersion}.js')).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (event) => {
  event.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((key) => key.startsWith('hsn-data-') && key !== CACHE).map((key) => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET' || new URL(event.request.url).origin !== self.location.origin) return;
  const url = new URL(event.request.url);
  if (url.pathname.endsWith('/data.${dataVersion}.js')) {
    event.respondWith(caches.match(event.request).then((hit) => hit || fetch(event.request)));
  }
});
`;
fs.writeFileSync(path.join(process.cwd(), 'sw.js'), sw);

const doc = `<!doctype html>
<!--
  Worldwide HSN Code Finder - hosted app and offline build
  Copyright (c) 2026 Push. All rights reserved.
  Plain HTML/CSS/JavaScript. No frameworks.
  Tariff descriptions and duty rates are compiled from the official public
  government and WCO sources credited in the app's Sources section.
-->
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Worldwide HSN Code Finder</title>
<meta name="description" content="Search 340,000+ official customs tariff codes across 22 national systems - India HSN, US HTS, EU CN, UK, Korea, Canada, Japan, Australia, Brazil and more. Duty rates, export incentives, trade data, documents and AI reports in one free file.">
<meta property="og:title" content="Worldwide HSN Code Finder">
<meta property="og:description" content="Find the right customs code for any product across 22 official tariff systems, with duty rates, trade data and export documents.">
<meta property="og:type" content="website">
<link rel="canonical" href="https://finder-hsn-codee.onrender.com/">
<link rel="manifest" href="./manifest.webmanifest">
<meta name="theme-color" content="#edf1f7">
<style>
${css}
</style>
<link rel="icon" href="/branding/favicon.ico" sizes="16x16 32x32 48x48">
<link rel="icon" type="image/png" sizes="48x48" href="/branding/icon-48.png">
<link rel="apple-touch-icon" sizes="180x180" href="/branding/apple-touch-icon.png">
<meta property="og:image" content="https://finder-hsn-codee.onrender.com/branding/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Worldwide HSN Code Finder">
<meta name="twitter:description" content="Trade-code finder with official code descriptions and duty context.">
<meta name="twitter:image" content="https://finder-hsn-codee.onrender.com/branding/og-image.png">
</head>
<body>
<div id="root"></div>
<script>
${PAKO}
</script>
<script>
${app}
</script>
<script>
// Show the interface immediately; fetch the large code database only when needed.
(function () {
  const root = document.getElementById('root');
  root.innerHTML = '<div class="app-shell"><div class="app-head"><h1 class="app-title">Worldwide HSN Code Finder</h1><p class="muted">Loading trade codes... The first visit may take a moment.</p></div></div>';
  const data = document.createElement('script');
  data.src = './data.${dataVersion}.js';
  data.onload = function () { boot(root); };
  data.onerror = function () {
    root.innerHTML = '<div class="app-shell"><div class="app-head"><h1 class="app-title">Worldwide HSN Code Finder</h1><p>Code data did not load. Check your connection and reload this page.</p></div></div>';
  };
  document.head.appendChild(data);
  if ('serviceWorker' in navigator && location.protocol === 'https:' && location.hostname === 'finder-hsn-codee.onrender.com') {
    window.addEventListener('load', function () { navigator.serviceWorker.register('./sw.js').catch(function () {}); });
  }
})();
</script>
</body>
</html>
`;
// Final leak check: no TS export/import syntax may survive into the bundle.
if (/export (const|function)/.test(doc)) throw new Error('build: TS export leaked into bundle');
if (/^import /m.test(app)) throw new Error('build: import line leaked into bundle');
// Preserve the original downloadable single-file workflow separately from the
// faster hosted shell. Both are generated from the same app source and dataset.
const offlineDoc = doc.replace('<link rel="manifest" href="./manifest.webmanifest">', '')
  .replace(/<script>\n\/\/ Show the interface immediately;[\s\S]*?\n<\/script>/, `<script>\n${dataJs}\nboot(document.getElementById('root'));\n</script>`);
if (offlineDoc.includes('data.src =')) throw new Error('offline build still depends on data.js');
fs.writeFileSync(path.join(process.cwd(), 'offline.html'), offlineDoc);
fs.writeFileSync(OUT, doc);
console.log('written', OUT, fs.statSync(OUT).size, dataName, fs.statSync(dataName).size, 'version', dataVersion);
