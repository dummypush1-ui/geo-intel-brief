// Market data bake: top importing countries for EVERY 6-digit HS code.
// Strategy: pull each reporting country's full AG6 world-import table (one bulk
// call per reporter batch, same shape as the India trend pull), then rank per code.
// This inverts the naive one-call-per-code approach (5354 codes -> ~12 calls).
// State lives in state/comtrade-market.json so partial progress survives reruns;
// a 429 stops the run cleanly and the next run resumes.
import fs from 'fs';

const KEY = process.env.COMTRADE_KEY || '';
const DRY = process.env.RENDER_DRY === '1';
const STATE = 'state/comtrade-market.json';
const OUT = 'src/marketdata.ts';
const CHUNK = 15; // reporters per call; ~80k rows worst case, under the 100k record cap

const log = (...a) => console.log(new Date().toISOString(), ...a);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function tradeYear() {
  const src = fs.readFileSync('src/tradevalues.ts', 'utf8');
  const ym = src.match(/calendar year (\d{4})/);
  return ym ? parseInt(ym[1], 10) : new Date().getUTCFullYear() - 1;
}

async function fetchJson(url) {
  const res = await fetch(url, { headers: { 'Ocp-Apim-Subscription-Key': KEY } });
  if (!res.ok) throw new Error('HTTP ' + res.status + ' for ' + url.slice(0, 110));
  return res.json();
}

async function reporterList() {
  const res = await fetch('https://comtradeapi.un.org/files/v1/app/reference/partnerAreas.json');
  const d = await res.json();
  const out = {};
  for (const r of d.results || []) {
    const id = r.id ?? r.ReporterCode;
    const name = r.text ?? r.ReporterDesc;
    if (id > 0 && name && !(r.isGroup)) out[id] = name;
  }
  return out; // {code: name}
}

// One batched AG6 import pull for a list of reporters; returns rows.
async function pullBatch(ids, year) {
  const url = `https://comtradeapi.un.org/data/v1/get/C/A/HS?reporterCode=${ids.join('%2C')}&period=${year}&partnerCode=0&partner2Code=0&flowCode=M&cmdCode=AG6&customsCode=C00&motCode=0`;
  const d = await fetchJson(url);
  return d.data || [];
}

export async function bakeMarket() {
  if (!KEY) { log('COMTRADE_KEY not set - skipping market bake'); return { skipped: 'no key' }; }
  const year = tradeYear();
  const reporters = await reporterList();
  const ids = Object.keys(reporters).map(Number).sort((a, b) => a - b);
  log('reporters:', ids.length, 'year:', year);
  let st = fs.existsSync(STATE) ? JSON.parse(fs.readFileSync(STATE, 'utf8')) : null;
  if (!st || st.year !== year || st.v !== 1) st = { v: 1, year, rows: {}, done: [], failures: {} };
  // rows: {code: {reporterId: value}} accumulated from pulled batches
  const doneSet = new Set(st.done);
  const todo = ids.filter((i) => !doneSet.has(i) && (st.failures[i] || 0) < 3);
  if (!todo.length) {
    writeOutputs(st, reporters, year);
    return { complete: true, reporters: st.done.length, year };
  }
  const chunks = [];
  if (DRY) chunks.push(todo.slice(0, 2));
  else for (let i = 0; i < todo.length; i += CHUNK) chunks.push(todo.slice(i, i + CHUNK));
  let pulled = 0, failed = 0, throttled = false;
  for (const chunk of chunks) {
    try {
      const rows = await pullBatch(chunk, year);
      for (const r of rows) {
        if (!(r.primaryValue > 0) || !r.cmdCode || r.cmdCode.length !== 6) continue;
        if (!st.rows[r.cmdCode]) st.rows[r.cmdCode] = {};
        st.rows[r.cmdCode][r.reporterCode] = Math.round(r.primaryValue);
      }
      for (const i of chunk) { if (!st.done.includes(i)) st.done.push(i); delete st.failures[i]; }
      pulled += chunk.length;
      log('batch ok:', chunk.length, 'reporters, rows:', rows.length);
    } catch (e) {
      if (/HTTP 429/.test(e.message)) { throttled = true; log('rate limited - stopping, resumes next run'); break; }
      log('batch failed (' + e.message + ') - falling back to per-reporter');
      for (const id of chunk) {
        try {
          await sleep(450);
          const rows = await pullBatch([id], year);
          for (const r of rows) {
            if (!(r.primaryValue > 0) || !r.cmdCode || r.cmdCode.length !== 6) continue;
            if (!st.rows[r.cmdCode]) st.rows[r.cmdCode] = {};
            st.rows[r.cmdCode][r.reporterCode] = Math.round(r.primaryValue);
          }
          if (!st.done.includes(id)) st.done.push(id);
          delete st.failures[id];
          pulled++;
        } catch (e2) {
          if (/HTTP 429/.test(e2.message)) { throttled = true; break; }
          st.failures[id] = (st.failures[id] || 0) + 1;
          failed++;
          log('reporter failed', id, e2.message);
        }
      }
      if (throttled) break;
    }
    await sleep(450);
    // Checkpoint after every batch so a killed run loses at most one batch.
    fs.mkdirSync('state', { recursive: true });
    fs.writeFileSync(STATE, JSON.stringify(st) + '\n');
  }
  writeOutputs(st, reporters, year);
  const coverage = Object.keys(st.rows).length;
  log('market bake:', pulled, 'reporters pulled,', failed, 'failed, coverage', coverage, 'codes, year', year);
  return { pulled, failed, throttled, reporters: st.done.length, totalReporters: ids.length, coverage, year };
}

function writeOutputs(st, reporters, year) {
  // Rank per code: top 8 importing countries by value.
  const top = {};
  for (const [code, byRep] of Object.entries(st.rows)) {
    const arr = Object.entries(byRep)
      .map(([id, v]) => [reporters[id] || String(id), v])
      .filter((a) => a[0] && a[1] > 0)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8);
    if (arr.length) top[code] = arr;
  }
  const world = {};
  for (const [code, byRep] of Object.entries(st.rows)) {
    const t = Object.values(byRep).reduce((a, b) => a + b, 0);
    if (t > 0) world[code] = Math.round(t);
  }
  const codes = Object.keys(top).sort();
  let out = `// Top importing countries by 6-digit HS code, calendar year ${year}.\n` +
    `// Source: UN Comtrade API (comtradeapi.un.org), every reporting country's world-import\n` +
    `// table (flow M, partner World, values USD), ranked per code, top 8 kept. MARKET_WORLD is the\n` +
    `// sum of all reporting countries' imports of the code (approximates world imports).\n` +
    `// Baked ${new Date().toISOString().slice(0, 10)} - coverage ${codes.length} codes from ${st.done.length} reporters.\n` +
    `export const MARKET_DATA_YEAR = ${year};\n` +
    `export const MARKET_IMPORTERS: Record<string, [string, number][]> = {\n`;
  for (const c of codes) {
    out += `  '${c}': [${top[c].map((p) => '[' + JSON.stringify(p[0]) + ', ' + p[1] + ']').join(', ')}],\n`;
  }
  out += `};\nexport const MARKET_WORLD: Record<string, number> = {\n`;
  for (const c of Object.keys(world).sort()) out += `  '${c}': ${world[c]},\n`;
  fs.mkdirSync('state', { recursive: true });
  fs.writeFileSync(STATE, JSON.stringify(st) + '\n');
  fs.writeFileSync(OUT, out + '};\n');
}

if (process.argv[1] && process.argv[1].endsWith('comtrade-market.mjs')) {
  bakeMarket().then((r) => console.log('[ok] comtrade-market', JSON.stringify(r))).catch((e) => { console.error('[fail] comtrade-market', e.message); process.exit(1); });
}
