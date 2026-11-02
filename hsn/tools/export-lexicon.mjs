// Exports a small HS lexicon (WCO HS, 4-digit headings + 6-digit subheadings) for
// the server-side news<->code matcher: node export-lexicon.mjs  ->  ../data/lexicon.json
import fs from 'fs';
import zlib from 'zlib';
import path from 'path';

const dir = path.resolve(process.cwd(), '..', 'static');
const f = fs.readdirSync(dir).find((x) => /^data\.[0-9a-f]{12}\.js$/.test(x));
if (!f) throw new Error('no data.<hash>.js in ' + dir);
const m = fs.readFileSync(path.join(dir, f), 'utf8').match(/DATA_B64 = "([^"]+)"/);
const rows = JSON.parse(zlib.gunzipSync(Buffer.from(m[1], 'base64')).toString());
const clean = (s) => String(s).replace(/\s+/g, ' ').replace(/[.;:\s]+$/, '').trim();
const GENERIC = /^(other|others|other:|-|--)$/i;
const headings = [];
const hs6 = [];
for (const [sys, code, desc] of rows) {
  if (sys !== 0) continue; // system 0 = WCO Harmonized System
  if (code.length === 4) headings.push([code, clean(desc)]);
  else if (code.length === 6 && !GENERIC.test(clean(desc))) hs6.push([code, clean(desc)]);
}
const out = path.resolve(process.cwd(), '..', 'data', 'lexicon.json');
fs.writeFileSync(out, JSON.stringify({ headings, hs6 }));
console.log('lexicon:', headings.length, 'headings,', hs6.length, 'subheadings ->', out, fs.statSync(out).size, 'bytes');
