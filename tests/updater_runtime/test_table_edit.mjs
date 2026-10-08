import assert from 'node:assert/strict';import fs from 'node:fs';import {applyGst,appendAliases} from '../../updater_runtime/table-edit.mjs';
const G='export const GST_MAP: Record<string, [string, string]> = {\n  "1234": ["5%", "old"]\n};\n';const A="export const ALIASES: Record<string, string[][]> = {\n  'coffee': [['roasted']]\n};\n";
const proposal=description=>({changes:[{code:'1234',rate:'18%',description}],sources:['https://example.org/notice']});
for(const description of ['$&','$`',"$'",'$1','Unicode தமிழ் & quotes " \\']){
 const out=applyGst(G,proposal(description));assert.equal(out.applied,1);assert.ok(out.source.includes(JSON.stringify(description)));assert.equal(JSON.parse(out.source.match(/"1234": (\[[^\n]+\])/)[1])[1],description);
}
const p=proposal('new');p.changes[0].code='567890';const inserted=applyGst(G,p);assert.equal(inserted.applied,1);assert.ok(inserted.source.includes('"old"],\n'));assert.ok(inserted.source.includes('"567890"'));
for(const bad of [G.replace('};','}'),G+'};\n',G+G])assert.throws(()=>applyGst(bad,proposal('new')));
assert.throws(()=>applyGst(G.replace('  "1234"','    "1234"'),proposal('new')),/row format/);
assert.throws(()=>applyGst(G.replace('};','  "1234": ["5%", "dupe"]\n};'),proposal('new')),/Duplicate/);
for(const change of [{code:'123',rate:'5%',description:'x'},{code:'12x4',rate:'5%',description:'x'},{code:'1234',rate:'101%',description:'x'},{code:'1234',rate:'5%',description:''},{code:'1234',rate:'5%',description:'x\n'},{code:'1234',rate:'5%',description:'x',source:'https://other.org'}])assert.throws(()=>applyGst(G,{changes:[change],sources:['https://example.org/notice']}));
assert.throws(()=>applyGst(G,{...proposal('x'),changes:[...proposal('x').changes,...proposal('x').changes]}));
const alias=appendAliases(A,[{term:'test roast',sets:[['roasted']]}]);assert.equal(alias.added,1);assert.ok(alias.source.includes("'coffee': [['roasted']],\n"));assert.ok(alias.source.includes("'test roast'"));
for(const bad of [A.replace('};','}'),A+'};\n',A+A])assert.throws(()=>appendAliases(bad,[{term:'test roast',sets:[['roasted']]}]));
assert.throws(()=>appendAliases(A,[{term:'coffee',sets:[['roasted']]}]));assert.throws(()=>appendAliases(A,[{term:'bad $&',sets:[['roasted']]}]));assert.throws(()=>appendAliases(A,[{term:'new alias',sets:[['x']]}]));
// Distinguish report claim: $1 is literal without any regex capture group.
assert.equal('old'.replace(/old/,'$1'),'$1');assert.equal('old'.replace(/old/,'$&'),'old');
// Exercise real schema input without any file writes.
assert.equal(applyGst(fs.readFileSync('src/gstmap.ts','utf8'),proposal('$&')).applied,1);assert.equal(appendAliases(fs.readFileSync('src/aliases.ts','utf8'),[{term:'fixture roast',sets:[['roasted']]}]).added,1);
console.log('table edits: literal dollar forms, Unicode, exact terminators/declarations, insert/update/count/schema/alias validation PASS; no filesystem writes');
