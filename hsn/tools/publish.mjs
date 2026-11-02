// Copies the freshly built hosted files into ../static (what the Flask service
// serves). Run after `node build.mjs` or `node automate.mjs`:
//     node build.mjs && node publish.mjs
import fs from 'fs';
import path from 'path';

const OUT = path.resolve(process.cwd(), '..', 'static');
if (!fs.existsSync(OUT)) throw new Error('publish: ' + OUT + ' not found - run from hsn/tools');
const data = fs.readdirSync('.').filter((f) => /^data\.[0-9a-f]{12}\.js$/.test(f));
if (data.length !== 1) throw new Error('publish: expected exactly one data.<hash>.js, found ' + data.length);
for (const f of fs.readdirSync(OUT)) if (/^data\.[0-9a-f]{12}\.js$/.test(f) && f !== data[0]) fs.rmSync(path.join(OUT, f));
for (const f of ['index.html', 'sw.js', data[0]]) fs.copyFileSync(f, path.join(OUT, f));
// offline.html (20 MB) is a download, not served by default; keep it out of git/static.
console.log('published', ['index.html', 'sw.js', data[0]].join(', '), '->', OUT);
