const fs=require('fs'),vm=require('vm'),assert=require('assert');
const crypto=require('crypto');
const values={COLLECTION_BASE_URL:'https://fixture.onrender.com',COLLECTION_HEADER_SECRET:'x'.repeat(48)};
let posts=[],reply=202,phase='accepted',locks=0;
const ctx={PropertiesService:{getScriptProperties:()=>({getProperty:k=>values[k],setProperty:(k,v)=>{values[k]=v}})},LockService:{getScriptLock:()=>({tryLock:()=>true,releaseLock:()=>{locks++;}})},Utilities:{getUuid:()=> '00000000-0000-0000-0000-000000000000',DigestAlgorithm:{SHA_256:'sha256'},Charset:{UTF_8:'utf8'},computeDigest:(a,s)=>Array.from(crypto.createHash('sha256').update(s).digest())},Date,
 UrlFetchApp:{fetch:(url,options)=>{posts.push({url,options});return {getResponseCode:()=>url.endsWith('/health')?200:reply,getContentText:()=>JSON.stringify({job:crypto.createHash('sha256').update('geo108\n00000000-0000-0000-0000-000000000000').digest('hex'),phase,counts:{}})};}}};
vm.createContext(ctx);vm.runInContext(fs.readFileSync('collection_only.gs','utf8'),ctx);
ctx.keepAliveCollection108();assert.equal(posts[0].url,'https://fixture.onrender.com/health');assert(!posts[0].url.includes('?'));
ctx.submitCollection108();ctx.submitCollection108();assert.equal(posts[1].options.payload,posts[2].options.payload);assert.equal(posts[1].options.headers.Authorization,'Bearer '+'x'.repeat(48));assert.equal(locks,2);assert(values.COLLECTION_PENDING108);
reply=500;assert.throws(()=>ctx.submitCollection108());assert.equal(locks,3);assert(values.COLLECTION_PENDING108);
values.COLLECTION_BASE_URL='http://127.0.0.1';let n=posts.length;assert.throws(()=>ctx.submitCollection108());assert.equal(posts.length,n);assert.equal(locks,4);
values.COLLECTION_BASE_URL='https://fixture.onrender.com';values.COLLECTION_HEADER_SECRET='';assert.throws(()=>ctx.keepAliveCollection108());assert.equal(posts.length,n);
console.log('PASS: original-global isolation, separate ping/header, nonce retry, failedreply preservation, unlock-onerror, invalidconfig nofetch');

values.COLLECTION_HEADER_SECRET='x'.repeat(48);reply=202;phase='unknown';assert.throws(()=>ctx.submitCollection108());console.log('PASS: receiptphase and SHA256noncebinding');
