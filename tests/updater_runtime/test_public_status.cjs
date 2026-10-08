'use strict';
const assert=require('node:assert/strict');const {publicResult}=require('../../updater_runtime/public-status.cjs');
const secret='mongodb://user:password@private/token=PRIVATE';
for(const value of [null,[],{error:secret},{skipped:secret},{changed:true,cleanup:{uri:secret}},{committed:true,sha:secret,year:secret}]){
 const r=publicResult(value);assert(!JSON.stringify(r).includes(secret));assert.deepEqual(Object.keys(r).filter(k=>!['state','correlationId','year','commit'].includes(k)),[]);assert.match(r.correlationId,/^[a-f0-9-]{36}$/);
}
assert.equal(publicResult(new Error(secret),true).state,'failed');
assert.equal(publicResult({changed:false}).state,'unchanged');assert.equal(publicResult({dry:true}).state,'dry_run');
assert.equal(publicResult({committed:true,sha:'a'.repeat(40),year:2025}).commit,'a'.repeat(40));
assert.equal(publicResult({year:NaN}).year,undefined);console.log('11 typed-status assertions passed');
