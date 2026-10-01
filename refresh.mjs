// Daily refresh pipeline for the HSN finder dataset.
// What it refreshes automatically:
//   - India per-code trade values (src/tradevalues.ts) from UN Comtrade,
//     using the COMTRADE_KEY environment variable (free key, 2 API calls).
// What it deliberately does NOT touch:
//   - GST rates (CBIC publishes no stable machine-readable feed; manual update)
//   - sanctions lists (formats vary; manual update - see README)
// If trade values change, it rebuilds the hosted shell, versioned dataset and offline copy, then commits them back
// to this repo via the GitHub API, which auto-redeploys the Render static site.
import fs from 'fs';
import zlib from 'zlib';
import { cleanDescriptions } from './gemini.mjs';

const KEY = process.env.COMTRADE_KEY || '';
const GEMINI = process.env.GEMINI_API_KEY || '';
const TOKEN = process.env.GITHUB_TOKEN || '';
const REPO = process.env.GITHUB_REPO || ''; // e.g. "push/hsn-finder"
const BRANCH = process.env.GITHUB_BRANCH || 'main';
const DRY = process.env.RENDER_DRY === '1';

const log = (...a) => console.log(new Date().toISOString(), ...a);

async function fetchComtrade(flow, year) {
  const url = `https://comtradeapi.un.org/data/v1/get/C/A/HS?reporterCode=699&period=${year}&partnerCode=0&partner2Code=0&flowCode=${flow}&cmdCode=AG6&customsCode=C00&motCode=0`;
  const res = await fetch(url, { headers: { 'Ocp-Apim-Subscription-Key': KEY } });
  if (!res.ok) throw new Error('Comtrade ' + flow + ' ' + year + ' -> HTTP ' + res.status);
  const d = await res.json();
  return d.data || [];
}

function renderTradevalues(m, x, year) {
  const mm = {}, xx = {};
  for (const r of m) mm[r.cmdCode] = Math.round(r.primaryValue || 0);
  for (const r of x) xx[r.cmdCode] = Math.round(r.primaryValue || 0);
  const codes = [...new Set([...Object.keys(mm), ...Object.keys(xx)])].sort();
  let out = `// India merchandise trade by 6-digit HS code, calendar year ${year}.\n` +
    `// Source: UN Comtrade API (comtradeapi.un.org), reporter 699 (India), partner World,\n` +
    `// flows M (imports, CIF) and X (exports), values in USD. Baked ${new Date().toISOString().slice(0, 10)}.\n` +
    `export const TRADE6: Record<string, [number, number]> = {\n`;
  for (const c of codes) {
    const imp = mm[c] || 0, exp = xx[c] || 0;
    if (imp || exp) out += `  '${c}': [${imp}, ${exp}],\n`;
  }
  return out + '};\n';
}

async function gh(method, path, body) {
  const res = await fetch('https://api.github.com' + path, {
    method,
    headers: {
      Authorization: 'Bearer ' + TOKEN,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'hsn-finder-updater',
      'Content-Type': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error('GitHub ' + method + ' ' + path + ' -> HTTP ' + res.status + ' ' + (await res.text()).slice(0, 200));
  return res.json();
}

async function commitFiles(files, message) {
  const ref = await gh('GET', `/repos/${REPO}/git/ref/heads/${BRANCH}`);
  const baseSha = ref.object.sha;
  const baseCommit = await gh('GET', `/repos/${REPO}/git/commits/${baseSha}`);
  const tree = [];
  for (const f of files) {
    const blob = await gh('POST', `/repos/${REPO}/git/blobs`, { content: Buffer.from(f.content, 'utf8').toString('base64'), encoding: 'base64' });
    tree.push({ path: f.path, mode: '100644', type: 'blob', sha: blob.sha });
  }
  const newTree = await gh('POST', `/repos/${REPO}/git/trees`, { base_tree: baseCommit.tree.sha, tree });
  const commit = await gh('POST', `/repos/${REPO}/git/commits`, { message, tree: newTree.sha, parents: [baseSha] });
  await gh('PATCH', `/repos/${REPO}/git/refs/heads/${BRANCH}`, { sha: commit.sha });
  return commit.sha;
}


function readDataset() {
  let b64 = '';
  const files = fs.readdirSync('src').filter((f) => /^datachunk\d+\.ts$/.test(f)).length;
  for (let n = 0; n < files; n++) {
    const t = fs.readFileSync(`src/datachunk${n}.ts`, 'utf8');
    const m = t.match(/"([A-Za-z0-9+/=]+)"/);
    if (!m) throw new Error(`datachunk${n}.ts unreadable`);
    b64 += m[1];
  }
  return JSON.parse(zlib.gunzipSync(Buffer.from(b64, 'base64')).toString('utf8'));
}

function writeDataset(rows) {
  const b64 = zlib.gzipSync(Buffer.from(JSON.stringify(rows), 'utf8'), { level: 9 }).toString('base64');
  const CHUNKS = Math.max(66, fs.readdirSync('src').filter((f) => /^datachunk\d+\.ts$/.test(f)).length);
  const step = Math.ceil(b64.length / CHUNKS);
  const files = [];
  for (let n = 0; n < CHUNKS; n++) {
    const content = `export const CHUNK${n} = "${b64.slice(n * step, (n + 1) * step)}";\n`;
    const file = `src/datachunk${n}.ts`;
    if (!fs.existsSync(file) || fs.readFileSync(file, 'utf8') !== content) {
      fs.writeFileSync(file, content);
      files.push({ path: file, content });
    }
  }
  return files;
}

// AI-assisted cleanup of description markup artifacts (e.g. Brazil NCM rows
// with literal "<i>...</i>"). Returns { changedFiles, report } or null.
async function cleanupDescriptions() {
  const rows = readDataset();
  const dirtySet = new Set();
  for (const r of rows) if (typeof r[2] === 'string' && /<[a-zA-Z/][^>]*>/.test(r[2])) dirtySet.add(r[2]);
  if (!dirtySet.size) return null;
  const dirty = [...dirtySet];
  const { cleaned, ai, note } = await cleanDescriptions(GEMINI, dirty);
  let applied = 0;
  for (const r of rows) {
    if (dirtySet.has(r[2]) && cleaned[r[2]] && cleaned[r[2]] !== r[2]) { r[2] = cleaned[r[2]]; applied++; }
  }
  if (!applied) return null;
  const report = `${applied} descriptions cleaned (${dirty.length} distinct; ${ai} AI-proposed and content-verified). ${note}`;
  return { changedFiles: writeDataset(rows), report };
}

export async function runRefresh() {
  if (!KEY) { log('COMTRADE_KEY not set - skipping trade refresh'); return { skipped: 'no key' }; }
  const thisYear = new Date().getFullYear();
  let year = null, m = null, x = null;
  for (const y of [thisYear - 1, thisYear - 2]) {
    try {
      const tm = await fetchComtrade('M', y);
      const tx = await fetchComtrade('X', y);
      if (tm.length > 3000 && tx.length > 3000) { year = y; m = tm; x = tx; break; }
      log('year', y, 'looks partial (M=' + tm.length + ', X=' + tx.length + ') - trying older');
    } catch (e) { log('year', y, 'failed:', e.message); }
  }
  if (!year && !GEMINI) return { skipped: 'no complete Comtrade year' };
  const commitQueue = [];
  const messages = [];
  let tradeChanged = false;
  if (year) {
    const next = renderTradevalues(m, x, year);
    const prev = fs.readFileSync('src/tradevalues.ts', 'utf8');
    const same = (a, b) => a.replace(/Baked [\d-]+\./, '') === b.replace(/Baked [\d-]+\./, '');
    if (same(next, prev)) log('trade values unchanged (year ' + year + ')');
    else {
      tradeChanged = true;
      log('trade values CHANGED (baking year ' + year + ')');
      fs.writeFileSync('src/tradevalues.ts', next);
      commitQueue.push({ path: 'src/tradevalues.ts', content: next });
      const appPath = 'src/app.js';
      let app = fs.readFileSync(appPath, 'utf8');
      const appNext = app.replace(/const TRADE_YEAR = \d+;/, 'const TRADE_YEAR = ' + year + ';');
      if (appNext !== app) { fs.writeFileSync(appPath, appNext); commitQueue.push({ path: appPath, content: appNext }); log('TRADE_YEAR label updated to ' + year); }
      messages.push('India trade values ' + year + ' (UN Comtrade)');
    }
  }
  let cleanReport = null;
  try {
    const c = await cleanupDescriptions();
    if (c) { cleanReport = c.report; commitQueue.push(...c.changedFiles); messages.push('AI-assisted description cleanup (Gemini, content-verified)'); }
  } catch (e) { log('description cleanup failed (skipping):', e.message); }
  if (!commitQueue.length) return { changed: false, year, cleanup: cleanReport };
  if (DRY) { log('RENDER_DRY=1 - not writing'); return { changed: true, year, dry: true, tradeChanged, cleanup: cleanReport }; }
  const { execSync } = await import('child_process');
  execSync('node build.mjs', { stdio: 'inherit' });
  for (const path of ['index.html', 'offline.html', ...fs.readdirSync('.').filter((f) => /^data\.[0-9a-f]{12}\.js$/.test(f))]) {
    commitQueue.push({ path, content: fs.readFileSync(path, 'utf8') });
  }
  if (!TOKEN || !REPO) { log('GITHUB_TOKEN/GITHUB_REPO not set - rebuilt locally only'); return { changed: true, year, committed: false, cleanup: cleanReport }; }
  const sha = await commitFiles(commitQueue, 'Data refresh: ' + messages.join('; '));
  log('committed', sha, '- Render will auto-redeploy');
  return { changed: true, year, committed: true, sha, tradeChanged, cleanup: cleanReport };
}

if (process.argv[1] && process.argv[1].endsWith('refresh.mjs')) {
  runRefresh().then((r) => { log('result:', JSON.stringify(r)); process.exit(0); })
    .catch((e) => { console.error('refresh failed:', e); process.exit(1); });
}
