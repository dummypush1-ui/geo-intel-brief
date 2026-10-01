// Applies state/gst-proposal.json to src/gstmap.ts and writes the PR description.
import fs from 'fs';
const P = JSON.parse(fs.readFileSync('state/gst-proposal.json', 'utf8'));
let g = fs.readFileSync('src/gstmap.ts', 'utf8'); const lines = [];
for (const c of P.changes) {
  const re = new RegExp('^  "' + c.code + '": \\[[^\\n]*\\],?$', 'm'), row = `  "${c.code}": ["${c.rate}", ${JSON.stringify(c.description || 'See notification')}],`;
  const m = g.match(re);
  lines.push(`- \`${c.code}\`: ${m ? m[0].match(/\["([^"]+)"/)[1] + ' -> ' : 'NEW -> '}**${c.rate}** (${c.description})`);
  g = m ? g.replace(re, row) : g.replace(/\n\};\s*$/, '\n' + row + '\n};\n');
}
fs.writeFileSync('src/gstmap.ts', g);
fs.writeFileSync('/tmp/pr-body.md', '## AI-drafted GST changes - REVIEW BEFORE MERGING\nEvery code and rate below was found literally in the official notification text, but AI may still mis-read context (exemptions, conditions).\n\n' + lines.join('\n') + '\n\nSources:\n' + P.sources.map((s) => '- ' + s).join('\n') + '\n');
console.log(lines.length + ' changes applied');
