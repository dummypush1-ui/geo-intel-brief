const fs=require('fs'),vm=require('vm'),assert=require('assert'),crypto=require('crypto');
const pending={profile:'geo108',nonce:'n'.repeat(24),created_at:100};
const key=crypto.createHash('sha256').update('geo108\n'+pending.nonce).digest('hex');
const values={COLLECTION_BASE_URL:'https://fixture.onrender.com',COLLECTION_HEADER_SECRET:'x'.repeat(48),COLLECTION_PENDING108:JSON.stringify(pending)};
let calls=[],phase='accepted',released=0,code=200,corrupt=false,receiptBad=false;
const ctx={PropertiesService:{getScriptProperties:()=>({getProperty:k=>values[k],setProperty:()=>{throw Error('Unexpected property write')}})},LockService:{getScriptLock:()=>({tryLock:()=>true,releaseLock:()=>{released++}})},Utilities:{DigestAlgorithm:{SHA_256:'sha256'},Charset:{UTF_8:'utf8'},computeDigest:(a,s)=>Array.from(crypto.createHash('sha256').update(s).digest())},UrlFetchApp:{fetch:(url,options)=>{
 calls.push({url,options});let body;
 if(url.endsWith('/drive')){phase='prepare_complete';body={job:key,state:receiptBad?'completed':'held_before_write',phase};}
 else body={job:corrupt?'0'.repeat(64):key,phase,counts:{fetched:1,prepared:1}};
 return {getResponseCode:()=>code,getContentText:()=>JSON.stringify(body)};
}}};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync('collection_only.gs','utf8'),ctx);
vm.runInContext(fs.readFileSync('collection_drive109.gs','utf8'),ctx);
let out=ctx.pollDriveCollection109();assert.equal(out.phase,'prepare_complete');assert.equal(calls.length,3);assert.equal(calls[1].options.payload,'{}');assert.equal(calls[1].options.followRedirects,false);assert.equal(released,1);assert.equal(values.COLLECTION_PENDING108,JSON.stringify(pending));
for(const terminal of ['write_started','uncertain_after_write','completed','failed_before_write']){phase=terminal;calls=[];assert.equal(ctx.pollDriveCollection109().phase,terminal);assert.equal(calls.length,1);}
phase='accepted';corrupt=true;calls=[];assert.throws(()=>ctx.pollDriveCollection109());assert.equal(calls.length,1);corrupt=false;
phase='accepted';receiptBad=true;calls=[];assert.throws(()=>ctx.pollDriveCollection109());assert.equal(calls.length,2);receiptBad=false;
phase='accepted';code=500;calls=[];assert.throws(()=>ctx.pollDriveCollection109());assert.equal(calls.length,1);code=200;
values.COLLECTION_PENDING108='{"profile":"geo108","nonce":"short","created_at":100}';calls=[];assert.throws(()=>ctx.pollDriveCollection109());assert.equal(calls.length,0);
assert.equal(released,9);console.log('PASS: bound status, hold-only drive, no terminal replay, no nonce/property mutation, malformed/uncertain fail closed, lock always released');
