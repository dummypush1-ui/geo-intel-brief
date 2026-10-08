// Apply a reviewed proposal locally for a PR; never commits rates automatically.
import fs from 'node:fs';
import {applyGst} from './updater_runtime/table-edit.mjs';
const proposal=JSON.parse(fs.readFileSync('state/gst-proposal.json','utf8'));
const result=applyGst(fs.readFileSync('src/gstmap.ts','utf8'),proposal);
const lines=result.lines.map(c=>`- \`${c.code}\`: ${c.previous===null?'NEW':c.previous} -> **${c.rate}** (${c.description})`);
const body='## AI-drafted GST changes - REVIEW BEFORE MERGING\nLiteral code/rate matches do not prove tax context or scope. Manually check exemptions and conditions before merging.\n\n'+lines.join('\n')+'\n\nSources:\n'+proposal.sources.map(s=>'- '+s).join('\n')+'\n';
// All table/description/schema/count checks complete before any output write.
fs.writeFileSync('src/gstmap.ts',result.source);
fs.writeFileSync('/tmp/pr-body.md',body);
console.log(result.applied+' changes applied');
