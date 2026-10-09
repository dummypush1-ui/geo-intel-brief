// Copyright (c) 2026 Push. All rights reserved.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),crypto=require('crypto');
const source=fs.readFileSync(__dirname+'/handlers216.gs','utf8');
const bridge=fs.readFileSync(__dirname+'/bridge.gs','utf8');
const names=['mailV1Digest216','mailV1Critical216','mailV1Weekly216'],kinds=['digest','critical','weekly'];
const services=['PropertiesService','GmailApp','MailApp','UrlFetchApp','LockService','ScriptApp','CacheService','Session','Utilities','SpreadsheetApp','DriveApp','Logger','console'];
function trapped(){const c={};for(const s of services.concat(['runMailV1']))Object.defineProperty(c,s,{get(){throw Error('SERVICE_CANARY')}});vm.createContext(c);vm.runInContext(source,c);return c;}
for(const name of names){
 const c=trapped(),extra=new Proxy({},{get(){throw Error('EXTRA_CANARY')}});
 for(const args of [[],[false],[undefined],[false,extra]]){const r=c[name](...args);assert.equal(r.state,'off');assert(Object.isFrozen(r));assert.equal(JSON.stringify(r),'{"state":"off","scope":"no_send_attempt"}');}
 for(const value of [1,'true','TRUE',[],{}, {triggerUid:'CANARY'},null,new Boolean(true)])assert.throws(()=>c[name](value),e=>e.message==='mail216_refused');
}
for(let i=0;i<names.length;i++){
 let calls=0;const c={runMailV1(...args){calls++;assert.equal(args.length,1);assert.equal(args[0],kinds[i]);return {state:'acknowledged',recipient:'CANARY',subject:'CANARY',id:'CANARY',count:'CANARY',text:'CANARY'};}};
 vm.createContext(c);vm.runInContext(source,c);assert.deepEqual(JSON.parse(JSON.stringify(c[names[i]](true))),{state:'acknowledged',scope:'send_returned_not_delivery'});assert.equal(calls,1);
 for(const state of ['off','skipped']){c.runMailV1=()=>({state,secret:'CANARY'});assert.equal(c[names[i]](true).scope,'no_send_attempt');}
 for(const r of [null,undefined,[],{}, {state:'sent_CANARY'}, {get state(){throw Error('CANARY')}}]){c.runMailV1=()=>r;assert.throws(()=>c[names[i]](true),e=>e.message==='mail216_unknown'&&!String(e.stack).includes('CANARY'));}
 let logged=0;c.Logger={log(){logged++}};c.runMailV1=()=>{let e=Error('CANARY');e.name='CANARY';e.stack='CANARY';throw e;};assert.throws(()=>c[names[i]](true),e=>e.message==='mail216_possibly_sent'&&!String(e.stack).includes('CANARY'));assert.equal(logged,0);
 delete c.runMailV1;assert.throws(()=>c[names[i]](true),e=>e.message==='mail216_possibly_sent');
}
function fixture(kind,mode='ok',enabled='true'){
 const channel=crypto.createHash('sha256').update(JSON.stringify({sender:'sender@example.invalid',recipients:['fixture@example.invalid']})).digest('hex'),receipt='e'.repeat(64),hash='f'.repeat(64);
 const p={MAIL_V1_ENABLED:enabled,MAIL_V1_BASE:'https://fixture.invalid',MAIL_V1_HEADER_SECRET:'s'.repeat(48),MAIL_V1_EMAIL_TO:'fixture@example.invalid',MAIL_V1_CHANNEL:channel};let sent=0,claimed=false,requests=0;
 const c={PropertiesService:{getScriptProperties:()=>({getProperty:k=>p[k]||null,setProperty:(k,v)=>{if(mode==='persistAfterSend'&&JSON.parse(v).phase==='send_returned')throw Error('CANARY');p[k]=v},deleteProperty:k=>delete p[k]})},LockService:{getScriptLock:()=>({tryLock:()=>true,releaseLock(){}})},Session:{getEffectiveUser:()=>({getEmail:()=> 'sender@example.invalid'})},Utilities:{getUuid:()=> '00000000-0000-0000-0000-000000000001',DigestAlgorithm:{SHA_256:'sha256'},Charset:{UTF_8:'utf8'},computeDigest:(a,s)=>Array.from(crypto.createHash('sha256').update(s).digest())},GmailApp:{sendEmail(){sent++;if(mode==='gmail')throw Error('CANARY')}},UrlFetchApp:{fetch(url,opt){requests++;assert.equal(opt.followRedirects,false);let out;
 if(url.endsWith('/prepare')){assert.equal(JSON.parse(opt.payload).kind,kind);out={receipt,hash,channel_id:channel,state:claimed?'started':'prepared',payload:{kind,skip:false,subject:'Fixture',html:'<p>Fixture</p>'}};}
 else if(url.endsWith('/claim')){assert(!claimed);claimed=true;if(mode==='claimLost')throw Error('CANARY');out={receipt,state:'started',permit:true};}
 else if(url.endsWith('/ack')){if(mode==='ack')throw Error('CANARY');out={receipt,state:'acknowledged',scope:'bridge_send_returned_not_delivery'};}
 else throw Error('Unexpected');return {getResponseCode:()=>200,getContentText:()=>JSON.stringify(out)};
 }}};
 vm.createContext(c);vm.runInContext(bridge+'\n'+source,c);return {c,p,run:()=>c[names[kinds.indexOf(kind)]](true),get sent(){return sent},get requests(){return requests},setMode(m){mode=m}};
}
for(const kind of kinds){let f=fixture(kind);assert.equal(f.run().state,'acknowledged');assert.equal(f.sent,1);
 f=fixture(kind,'ok','false');assert.equal(f.run().state,'off');assert.equal(f.sent,0);assert.equal(f.requests,0);
 for(const mode of ['claimLost','gmail','persistAfterSend']){f=fixture(kind,mode);assert.throws(f.run,e=>e.message==='mail216_possibly_sent');const n=f.sent;f.setMode('ok');assert.throws(f.run,e=>e.message==='mail216_possibly_sent');assert.equal(f.sent,n);}
 f=fixture(kind,'ack');assert.throws(f.run,e=>e.message==='mail216_possibly_sent');assert.equal(f.sent,1);f.setMode('ok');assert.equal(f.run().state,'acknowledged');assert.equal(f.sent,1);
}
assert(!/216\s*\(\s*true\b/.test(source));assert.deepEqual(source.match(/runMailV1\([^)]*\)/g),["runMailV1('digest')","runMailV1('critical')","runMailV1('weekly')"]);
assert(!/Logger|console|MAIL_V1_ENABLED|ScriptApp|PropertiesService/.test(source));
const c={};vm.createContext(c);vm.runInContext(bridge+'\n'+source,c);for(const n of names){assert.equal(Object.keys(c).filter(k=>k===n).length,1);assert.equal((source.match(new RegExp('function '+n+'\\(','g'))||[]).length,1);assert(!n.endsWith('_'));}
console.log('PASS216: hostile OFF, exact booleans, literal mapping, fixed errors, property second gate, mocked bridge holds/ack-only, no installation');
