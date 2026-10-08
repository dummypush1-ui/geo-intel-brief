// One command does everything: node automate.mjs
// trade data -> sanctions -> source watch -> rebuild -> safety checks. Exits 1 if any check fails.
import fs from 'fs';
import zlib from 'zlib';
import { execSync } from 'child_process';
import { runRefresh } from './refresh.mjs';
import { bakePartners } from './comtrade-partners.mjs';
import { refreshSanctions } from './sanctions-refresh.mjs';
import { monitor, issue } from './monitor.mjs';
import vm from 'vm';
import { expandAliases, draftGst } from './ai-agent.mjs';
const step = async (n, f) => { try { const r = await f(); console.log('[ok]', n, JSON.stringify(r)); return r; } catch (e) { console.log('[skip]', n, e.message); return null; } };
await step('trade+cleanup', runRefresh);
await step('comtrade-partners', bakePartners);
await step('comtrade-market', (await import('./comtrade-market.mjs')).bakeMarket);
const sr = await step('sanctions', refreshSanctions);
if (sr) {
  const HP = 'state/health.json', h = fs.existsSync(HP) ? JSON.parse(fs.readFileSync(HP, 'utf8')) : {};
  for (const [l, v] of Object.entries(sr)) {
    h[l] = v.state === 'updated' ? 0 : Math.min((h[l] || 0) + 1, 8);
    if (h[l] >= 7) {const notification=await issue('Sanctions ' + l + ' not refreshing for 7 attempts', JSON.stringify(v));console.log('[sanctions-issue-health]',l,JSON.stringify(notification));}
  }
  fs.writeFileSync(HP, JSON.stringify(h) + '\n');
}
await step('source-watch', monitor);
await step('ai-aliases', expandAliases);
await step('ai-gst-draft', draftGst);
execSync('node build.mjs', { stdio: 'inherit' });
// ---- safety checks (nothing is committed if these fail) ----
const fail = (m) => { console.error('CHECK FAILED:', m); process.exit(1); };
let b = ''; for (let n = 0; fs.existsSync(`src/datachunk${n}.ts`); n++) b += fs.readFileSync(`src/datachunk${n}.ts`, 'utf8').match(/"([A-Za-z0-9+/=]+)"/)[1]; // chunk count grows with the dataset - was hardcoded 66 and broke the daily run when it crossed
const rows = JSON.parse(zlib.gunzipSync(Buffer.from(b, 'base64')).toString());
if (rows.length < 250000) fail('dataset rows ' + rows.length);
if (rows.some((r) => /<[a-z/][^>]*>/i.test(r[2] || ''))) fail('HTML artifacts in descriptions');
const g = fs.readFileSync('src/gstmap.ts', 'utf8');
const rates = [...g.matchAll(/\["([^"]+)",/g)].map((m) => m[1]);
if (rates.length < 1000 || rates.some((r) => !/^\d+(\.\d+)?%$/.test(r))) fail('GST map malformed');
if (fs.readFileSync('src/sanctions.ts', 'utf8').length < 3e6) fail('sanctions file too small');
const tp = fs.readFileSync('src/tradepartners.ts', 'utf8');
const tpCount = (tp.match(/^  '\d{6}':/gm) || []).length;
const tpClaim = parseInt((tp.match(/coverage (\d+) codes/) || [0, '-1'])[1], 10);
if (tpCount < 20 || tpCount !== tpClaim) fail('tradepartners malformed: entries ' + tpCount + ' vs header ' + tpClaim);
const tt = fs.readFileSync('src/tradetrend.ts', 'utf8');
const ttCount = (tt.match(/^  '\d{6}':/gm) || []).length;
if (ttCount < 3000 || !/TRADE_TREND_YEARS = \[\d{4}, \d{4}, \d{4}, \d{4}, \d{4}\]/.test(tt)) fail('tradetrend malformed: entries ' + ttCount);
// SHIP_SANC program tags must be clean ("IRAN, SDGT"), never bracket-corrupted ("IRAN] [SDGT") - the bake script once mangled multi-tag OFAC programs.
const shipLine = (fs.readFileSync('src/app.js', 'utf8').match(/const SHIP_SANC = \[.*\];/) || [''])[0];
if (!shipLine) fail('SHIP_SANC table missing');
if (/[A-Z]\] \[[A-Z]/.test(shipLine)) fail('SHIP_SANC bracket-corrupted program tags');
const idx = fs.readFileSync('index.html', 'utf8');
const offline = fs.readFileSync('offline.html', 'utf8');
const dataFiles = fs.readdirSync('.').filter((f) => /^data\.[0-9a-f]{12}\.js$/.test(f));
if (idx.length < 100000 || idx.length > 2000000 || !idx.includes('data.src =') || dataFiles.length !== 1 || !idx.includes(dataFiles[0])) fail('hosted shell or dataset incomplete');
if (fs.statSync(dataFiles[0]).size < 5000000 || offline.length < 8000000 || !offline.includes('boot(document') || !offline.includes('var DATA_B64 =')) fail('offline copy or code dataset incomplete');
for (const f of [idx, offline]) for (const m of f.matchAll(/<script>([\s\S]*?)<\/script>/g)) { try { new vm.Script(m[1]); } catch (e) { fail('JS syntax error in built page: ' + e.message); } }
try { new vm.Script(fs.readFileSync(dataFiles[0], 'utf8')); new vm.Script(fs.readFileSync('sw.js', 'utf8')); } catch (e) { fail('JS syntax error in data or service worker: ' + e.message); }
fs.writeFileSync('state/heartbeat.txt', new Date().toISOString().slice(0, 7) + '\n'); // monthly commit keeps the schedule alive
console.log('ALL CHECKS PASSED');
