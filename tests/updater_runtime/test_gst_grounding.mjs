import assert from 'node:assert/strict';import fs from 'node:fs';import os from 'node:os';import path from 'node:path';
import {spawnSync}from 'node:child_process';
import {groundGst}from '../../updater_runtime/gst-grounding.mjs';import {extractNotificationPdf}from '../../updater_runtime/pdf-extract.mjs';
const c={code:'1234',rate:'18%',description:'goods'};
assert.equal(groundGst(c,'1234 goods 18%').state,'row_matched_pending_review');
for(const t of['12 chapter goods 18%','91234 goods 18%','1234 other goods 18%','1234 goods 5%\n5678 toys 18%','1234 goods 5% 18%','1234 goods exempt 18%','1234 goods 18%\nSubject to conditions','1234 goods 18%\n1234 goods 18%','1234 goods\n18%'])assert.equal(groundGst(c,t).state,'held_ambiguous',t);
assert.throws(()=>extractNotificationPdf(Buffer.from('%PDF-x'),{tool:'/missing-pdftotext'}),/missing/);
for(const b of[Buffer.from('bad'),Buffer.alloc(10*1024*1024+1)])assert.throws(()=>extractNotificationPdf(b),/format or size/);
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'pdf-extract-test-'));try{
 const tool=path.join(dir,'pdftotext');const write=s=>{fs.writeFileSync(tool,s);fs.chmodSync(tool,0o700);};
 write('#!/bin/sh\nif [ "$1" = -v ]; then echo "pdftotext version 22.02.0"; exit 0; fi\necho "1234 goods 18%"\n');assert.equal(extractNotificationPdf(Buffer.from('%PDF-x'),{tool}).trim(),'1234 goods 18%');
 write('#!/bin/sh\nif [ "$1" = -v ]; then echo "pdftotext version 22.02.0"; exit 0; fi\nexit 1\n');assert.throws(()=>extractNotificationPdf(Buffer.from('%PDF-x'),{tool}),/extraction failed/);
 write('#!/bin/sh\nif [ "$1" = -v ]; then echo "pdftotext version 22.02.0"; exit 0; fi\nsleep 1\n');assert.throws(()=>extractNotificationPdf(Buffer.from('%PDF-x'),{tool,timeout:10}),/extraction failed/);
 write('#!/bin/sh\necho "pdftotext version 99.0.0"\n');assert.throws(()=>extractNotificationPdf(Buffer.from('%PDF-x'),{tool}),/version/);
 const state=path.join(dir,'state');fs.mkdirSync(state);fs.writeFileSync(path.join(state,'gst-proposal.json'),JSON.stringify({state:'manual_review_required',changes:[c],sources:['https://example.com']}));
 const run=spawnSync(process.execPath,[path.resolve('apply-gst.mjs')],{cwd:dir,encoding:'utf8'});assert.notEqual(run.status,0);assert.match(run.stderr,/operator must review/);assert.equal(fs.existsSync(path.join(dir,'src/gstmap.ts')),false);
 for(const state of[undefined,'manual_review_required','unknown']){
  fs.writeFileSync(path.join(dir,'state/gst-proposal.json'),JSON.stringify({state,changes:[c],sources:['https://example.com']}));const refusal=spawnSync(process.execPath,[path.resolve('apply-gst.mjs')],{cwd:dir,encoding:'utf8'});assert.notEqual(refusal.status,0);assert.match(refusal.stderr,/operator must review/);
 }
}finally{fs.rmSync(dir,{recursive:true,force:true});}
console.log('GST row/rate/context/scope and PDF input/tool/error/timeout tests pass');
