import assert from 'node:assert/strict';import fs from 'node:fs';import os from 'node:os';import path from 'node:path';import {spawnSync} from 'node:child_process';
// Child test uses fake pdftotext on PATH, never an external PDF/site/provider.
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'gst-reject-test-'));const bin=path.join(dir,'bin');fs.mkdirSync(bin);fs.mkdirSync(path.join(dir,'state'));
fs.writeFileSync(path.join(bin,'pdftotext'),'#!/bin/sh\nif [ \"$1\" = -v ]; then printf \"pdftotext version 22.02.0\\n\"; exit 0; fi\nprintf \'1234 goods 18%%\\n\'\n');fs.chmodSync(path.join(bin,'pdftotext'),0o700);
fs.writeFileSync(path.join(dir,'state/gst-seen.json'),JSON.stringify({seen:[]}));
const module=path.resolve('ai-agent.mjs');
const script=`import {draftGst} from ${JSON.stringify(module)};import fs from 'node:fs';import assert from 'node:assert/strict';
const ask=async()=>[null,{code:'123',rate:'101%',description:''},{code:'1234',rate:'18%',description:'goods'}];
const fetcher=async u=>u.endsWith('.pdf')?{arrayBuffer:async()=>new TextEncoder().encode('%PDF-fixture').buffer}:{text:async()=>'<a href="https://example.org/notice.pdf">Integrated Tax (Rate)</a>'};
const result=await draftGst(ask,fetcher);assert.match(result,/1 row-matched proposals pending review/);assert.match(result,/2 AI items rejected/);const p=JSON.parse(fs.readFileSync('state/gst-proposal.json'));assert.equal(p.changes.length,1);assert.equal(p.changes[0].code,'1234');assert.equal(p.state,'manual_review_required');
const second=async u=>u.endsWith('.pdf')?{arrayBuffer:async()=>new TextEncoder().encode('%PDF-fixture').buffer}:{text:async()=>'<a href="https://example.org/second.pdf">Integrated Tax (Rate)</a>'};
await draftGst(async()=>[{code:'1234',rate:'5%',description:'goods'}],second);
const merged=JSON.parse(fs.readFileSync('state/gst-proposal.json'));assert.equal(merged.changes.length,1);assert.equal(merged.held.length,1);assert.equal(merged.sources.length,2);assert.equal(merged.changes[0].source,'https://example.org/notice.pdf');console.log(result);`;
try {const r=spawnSync(process.execPath,['--input-type=module','-e',script],{cwd:dir,env:{...process.env,PATH:bin+':'+process.env.PATH},encoding:'utf8'});assert.equal(r.status,0,r.stderr);console.log(r.stdout.trim());}finally{fs.rmSync(dir,{recursive:true,force:true});}
