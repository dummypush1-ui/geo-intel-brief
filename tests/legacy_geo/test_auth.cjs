'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('intelligence/geo/apps_script/Code.gs','utf8');
function fixture(secret='fixture-secret') {
 const seen=[];const props={RENDER_BASE_URL:'https://fixture.invalid',TRIGGER_SECRET:secret};
 const context={PropertiesService:{getScriptProperties:()=>({getProperty:k=>props[k]})},UrlFetchApp:{fetch:(url,opts)=>{seen.push({url,opts});return {};}},Logger:{log:()=>{}}};
 vm.createContext(context);vm.runInContext(source,context,{timeout:1000});return {context,seen,props};
}
for(const path of ['/health','/collect','/digest-data','/mark-emailed','/critical','/weekly','/dashboard']){
 const f=fixture();f.context._renderFetch(path,{method:'post',muteHttpExceptions:true});
 assert.equal(f.seen[0].url,'https://fixture.invalid'+path);assert.equal(f.seen[0].opts.headers['X-Trigger-Secret'],'fixture-secret');assert.equal(f.seen[0].opts.followRedirects,false);
}
for(const secret of [undefined,'',' ']){const f=fixture(secret===undefined?'':secret);assert.throws(()=>f.context._renderFetch('/collect'));assert.equal(f.seen.length,0);}
for(const path of ['https://outside.invalid','//outside.invalid','/collect?key=x','/../collect']){const f=fixture();assert.throws(()=>f.context._renderFetch(path));assert.equal(f.seen.length,0);}
for(const base of ['http://fixture.invalid','https://user@fixture.invalid','https://fixture.invalid/path','https://fixture.invalid?key=x']){const f=fixture();f.props.RENDER_BASE_URL=base;assert.throws(()=>f.context._renderFetch('/collect'));assert.equal(f.seen.length,0);}
const f=fixture();f.context.cleanupOld();assert.equal(f.seen.length,0);
assert(!source.includes("newTrigger('cleanupOld')"));assert(!source.includes('key='));
console.log('PASS header migration7routes,missing auth,redirect refusal,origin/path guards,cleanup held');
