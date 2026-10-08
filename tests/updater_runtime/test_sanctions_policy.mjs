import assert from 'node:assert/strict';import fs from 'node:fs';import os from 'node:os';import path from 'node:path';
import {sanctionsDecision as decide}from '../../updater_runtime/sanctions-policy.mjs';import {refreshSanctions}from '../../sanctions-refresh.mjs';
const rows=(n,l='OFAC')=>Array.from({length:n},(_,i)=>['Name '+i,l,'P']);
for(const n of[85,100,115])assert.equal(decide(rows(100),rows(n),'OFAC').state,'updated');
for(const n of[84,116,500])assert.equal(decide(rows(100),rows(n),'OFAC').state,'review_required');
const bootstrap=decide([],rows(1),'OFAC');assert.equal(bootstrap.reason,'bootstrap');assert.equal(bootstrap.state,'review_required');
assert.equal(decide([],rows(1),'OFAC',bootstrap.candidate_sha256).state,'updated');
assert.equal(decide([],rows(2),'OFAC',bootstrap.candidate_sha256).reason,'review_hash_mismatch');
for(const bad of[[],[['','OFAC','P']],[['X','EU','P']],null])assert.throws(()=>decide(rows(10),bad,'OFAC'));
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'sanctions-policy-'));try{
 const file=path.join(dir,'sanctions.ts'),reviewFile=path.join(dir,'review.json');
 const meta={sources:{OFAC:'ofac',EU:'eu'},checked:'2026-01-01',ofac:'old OFAC',eu:'old EU'};
 fs.writeFileSync(file,'//fixture\nexport const SANCTIONS_META = '+JSON.stringify(meta)+';\nexport const SANCTIONS: [string, string, string][] = '+JSON.stringify([...rows(100),...rows(100,'EU'),['U','UFLPA','P']])+';\n');
 const xml=n=>'<sdnList>'+Array.from({length:n},(_,i)=>'<sdnEntry><lastName>Name '+i+'</lastName></sdnEntry>').join('')+'</sdnList>';
 let r=await refreshSanctions({file,reviewFile,clock:new Date('2026-02-01T00:00:00Z'),fetchText:async u=>u==='ofac'?xml(200):'wrong;columns\n'});
 assert.equal(r.OFAC.state,'review_required');assert.equal(r.EU.state,'kept_old');let text=fs.readFileSync(file,'utf8');assert.ok(text.includes('"checked":"2026-01-01"'));assert.ok(text.includes('old OFAC'));assert.ok(text.includes('"stale":true'));
 const saved=JSON.parse(fs.readFileSync(reviewFile));assert.equal(saved.candidates.OFAC.rows.length,200);assert.equal(saved.candidates.OFAC.candidate_sha256,r.OFAC.candidate_sha256);
 let failed=await refreshSanctions({file,reviewFile,clock:new Date('2026-02-01T12:00:00Z'),fetchText:async()=>{throw new Error('offline')}});
 assert.equal(failed.OFAC.state,'kept_old');assert.equal(JSON.parse(fs.readFileSync(reviewFile)).candidates.OFAC.candidate_sha256,r.OFAC.candidate_sha256);
 const mismatch=await refreshSanctions({file,reviewFile,clock:new Date('2026-02-01T13:00:00Z'),reviewedHashes:{OFAC:r.OFAC.candidate_sha256},fetchText:async u=>u==='ofac'?xml(201):'wrong;columns\n'});
 assert.equal(mismatch.OFAC.reason,'review_hash_mismatch');assert.equal(JSON.parse(fs.readFileSync(reviewFile)).candidates.OFAC.rows.length,201);
 assert.notEqual(mismatch.OFAC.candidate_sha256,r.OFAC.candidate_sha256);
 assert.ok(JSON.parse(fs.readFileSync(reviewFile)).candidate_history.OFAC[r.OFAC.candidate_sha256]);
 r=await refreshSanctions({file,reviewFile,clock:new Date('2026-02-02T00:00:00Z'),reviewedHashes:{OFAC:r.OFAC.candidate_sha256},fetchText:async u=>u==='ofac'?xml(200):'NameAlias_WholeName;Entity_Regulation_Programme\n'+rows(100,'EU').map(x=>x[0]+';P').join('\n')});
 assert.equal(r.OFAC.state,'updated');assert.equal(r.EU.state,'updated');assert.ok(fs.readFileSync(file,'utf8').includes('"checked":"2026-02-02"'));assert.ok(JSON.parse(fs.readFileSync(reviewFile)).candidate_history.OFAC[mismatch.OFAC.candidate_sha256]);
 assert.ok(!JSON.parse(fs.readFileSync(reviewFile)).candidate_history.OFAC[r.OFAC.candidate_sha256]);
 const prior=fs.readFileSync(file,'utf8');
 for(const payload of['<sdnList></sdnList>','<sdnList><sdnEntry><lastName>X</lastName></sdnEntry>','<!DOCTYPE sdnList><sdnList><sdnEntry><lastName>X</lastName></sdnEntry></sdnList>']){
  const held=await refreshSanctions({file,reviewFile,clock:new Date('2026-02-03T00:00:00Z'),fetchText:async()=>payload});assert.equal(held.OFAC.state,'kept_old');assert.ok(fs.readFileSync(file,'utf8').includes('"checked":"2026-02-02"'));
 }
 fs.writeFileSync(file,'//fixture\nexport const SANCTIONS_META = '+JSON.stringify(meta)+';\nexport const SANCTIONS: [string, string, string][] = [];\n');
 const zero=await refreshSanctions({file,reviewFile,clock:new Date('2026-02-04T00:00:00Z'),fetchText:async u=>u==='ofac'?xml(1):'NameAlias_WholeName;Entity_Regulation_Programme\nE;P'});
 assert.equal(zero.OFAC.state,'review_required');assert.equal(zero.OFAC.reason,'bootstrap');assert.ok(fs.readFileSync(file,'utf8').includes(' = [];'));
}finally{fs.rmSync(dir,{recursive:true,force:true});}
console.log('sanctions policy edges, bootstrap, exact review, malformed and retained-old cases pass');
