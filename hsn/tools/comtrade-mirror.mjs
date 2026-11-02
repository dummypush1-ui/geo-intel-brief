// Mirror pull: sanctioned countries stopped self-reporting to UN Comtrade, so their
// trade is reconstructed from PARTNER records - every other reporter's imports from
// and exports to the sanctioned country. One AG6 call per country per flow direction
// pair, chapter-chunked only if the 100k record cap bites (detected via count field).
// Output: src/mirrordata.ts - per red-zone country, per 6-digit code, [importsByCountry, exportsByCountry]
// as seen by the rest of the world. Rows under $1M dropped (noise floor).
import fs from 'fs';

const KEY = process.env.COMTRADE_KEY || '';
const STATE = 'state/comtrade-mirror.json';
const OUT = 'src/mirrordata.ts';
const FLOOR = 1000000; // $1M
const log = (...a) => console.log(new Date().toISOString(), ...a);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Red-zone countries from sanc.ts (zone 1) mapped to M49 codes.
const RED = { 'Russia': 643, 'Iran': 364, 'Cuba': 192, 'North Korea': 408, 'Belarus': 112, 'Syria': 760, 'Venezuela': 862, 'Myanmar': 104, 'Afghanistan': 4, 'Iraq': 368, 'Lebanon': 422, 'Libya': 434, 'Somalia': 706, 'Sudan': 729, 'South Sudan': 728, 'Yemen': 887, 'Nicaragua': 558, 'Zimbabwe': 716, 'Haiti': 332, 'Mali': 466, 'Congo (DRC)': 180, 'Central African Republic': 140, 'Guinea-Bissau': 624 };

async function fetchJson(url) {
  const res = await fetch(url, { headers: { 'Ocp-Apim-Subscription-Key': KEY } });
  if (!res.ok) throw new Error('HTTP ' + res.status + ' for ' + url.slice(0, 110));
  return res.json();
}

async function pull(partnerCode, year, cmd) {
  const url = `https://comtradeapi.un.org/data/v1/get/C/A/HS?period=${year}&partnerCode=${partnerCode}&flowCode=M%2CX&cmdCode=${cmd}&partner2Code=0&customsCode=C00&motCode=0`;
  return fetchJson(url);
}

export async function bakeMirror() {
  if (!KEY) { log('COMTRADE_KEY not set - skipping mirror bake'); return { skipped: 'no key' }; }
  const year = parseInt((fs.readFileSync('src/marketdata.ts', 'utf8').match(/MARKET_DATA_YEAR = (\d{4})/) || [])[1], 10);
  let st = fs.existsSync(STATE) ? JSON.parse(fs.readFileSync(STATE, 'utf8')) : null;
  if (!st || st.year !== year) st = { year, data: {}, failures: {} };
  let pulled = 0, failed = 0;
  for (const [name, code] of Object.entries(RED)) {
    if (st.data[name] && Object.keys(st.data[name]).length) continue;
    if ((st.failures[name] || 0) >= 3) continue;
    try {
      let d = await pull(code, year, 'AG6');
      let rows = d.data || [];
      if ((d.count && d.count > rows.length) || rows.length >= 100000) {
        // Chunk by 2-digit chapter.
        rows = [];
        for (let ch = 1; ch <= 97; ch++) {
          const cc = String(ch).padStart(2, '0');
          await sleep(450);
          const dc = await pull(code, year, cc);
          rows = rows.concat(dc.data || []);
        }
      }
      const rec = {};
      for (const r of rows) {
        if (!r.cmdCode || r.cmdCode.length !== 6) continue;
        const v = Math.round(r.primaryValue || 0);
        if (v < FLOOR) continue;
        if (!rec[r.cmdCode]) rec[r.cmdCode] = [0, 0];
        if (r.flowCode === 'M') rec[r.cmdCode][0] += v; // world imports FROM this country = its exports
        else if (r.flowCode === 'X') rec[r.cmdCode][1] += v; // world exports TO it = its imports
      }
      st.data[name] = rec;
      delete st.failures[name];
      pulled++;
      log('mirror ok:', name, Object.keys(rec).length, 'codes');
      fs.mkdirSync('state', { recursive: true });
      fs.writeFileSync(STATE, JSON.stringify(st) + '\n');
      await sleep(450);
    } catch (e) {
      if (/HTTP 429/.test(e.message)) { log('rate limited - resumes next run'); break; }
      st.failures[name] = (st.failures[name] || 0) + 1;
      failed++;
      log('mirror failed', name, e.message);
    }
  }
  // Render
  const year2 = st.year;
  let out = `// Sanctioned-country trade reconstructed from partner (mirror) records, calendar ${year2}.\n` +
    `// These countries stopped self-reporting to UN Comtrade; rows are what the rest of the world\n` +
    `// reported trading WITH them: [their exports (world imports from them), their imports (world\n` +
    `// exports to them)], USD, rows under $1M dropped. Source: UN Comtrade mirror flow.\n` +
    `// Baked ${new Date().toISOString().slice(0, 10)}.\n` +
    `export const MIRROR_YEAR = ${year2};\n` +
    `export const MIRROR: Record<string, Record<string, [number, number]>> = {\n`;
  for (const name of Object.keys(st.data).sort()) {
    const rec = st.data[name];
    const cells = Object.keys(rec).sort().map((c) => `'${c}': [${rec[c][0]}, ${rec[c][1]}]`).join(', ');
    out += `  ${JSON.stringify(name)}: { ${cells} },\n`;
  }
  fs.writeFileSync(OUT, out + '};\n');
  log('mirror bake:', pulled, 'pulled,', failed, 'failed, countries', Object.keys(st.data).length);
  return { pulled, failed, countries: Object.keys(st.data).length, year: year2 };
}

if (process.argv[1] && process.argv[1].endsWith('comtrade-mirror.mjs')) {
  bakeMirror().then((r) => console.log('[ok] comtrade-mirror', JSON.stringify(r))).catch((e) => { console.error('[fail] comtrade-mirror', e.message); process.exit(1); });
}
