import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';import {webcrypto,createHash}from'node:crypto';
const raw='public fixture',digest=createHash('sha256').update(raw).digest('hex'),base='/workspace/finder/device/'+digest+'/',cfg={base,digest,size:Buffer.byteLength(raw),cache:'geo-finder-device-f10-'+digest};
const source=fs.readFileSync(new URL('../integration/finder_device_f10/worker.js',import.meta.url),'utf8').replace('/*F10_CONFIG*/','const CFG='+JSON.stringify(cfg)+';');
function fixture(response=()=>good()){
 const events={},store=new Map(),ops=[];store.set('unrelated',new Map([['secret','untouched']]));
 const caches={async open(name){ops.push(['open',name]);if(!store.has(name))store.set(name,new Map());return{async put(url,response){ops.push(['put',url]);store.get(name).set(url,response.clone());},async match(url){return store.get(name).get(url)?.clone();}};}};
 const self={location:{origin:'https://example.test'},addEventListener:(name,fn)=>events[name]=fn,async skipWaiting(){ops.push(['skip']);},clients:{async claim(){ops.push(['claim']);}}};
 vm.runInNewContext(source,{URL,Response,Uint8Array,crypto:webcrypto,self,caches,fetch:async(...args)=>{ops.push(['fetch',args[0],args[1]]);return response();},Error});
 return{events,store,ops,async install(){let job;events.install({waitUntil:p=>job=p});await job;},async request(url='https://example.test'+base+'snapshot.html',method='GET'){let job;events.fetch({request:new Request(url,{method}),respondWith:p=>job=p});return job;}};
}
function good(body=raw,options={}){return new Response(body,{status:200,headers:{'X-Finder-Device-Snapshot':digest,'Content-Type':'text/html'},...options});}
const a=fixture();assert.equal(a.ops.length,0);await a.install();assert.equal(a.store.get('unrelated').get('secret'),'untouched');assert.equal(await(await a.request()).text(),raw);assert.equal(await a.request('https://example.test/api/news'),undefined);assert.equal(await a.request('https://evil.test'+base+'snapshot.html'),undefined);assert.equal(await a.request(undefined,'POST'),undefined);assert.equal(a.ops[0][0],'fetch');assert.equal(a.ops[0][2].credentials,'omit');assert.equal(a.ops[0][2].redirect,'error');
for(const response of [()=>good('x'.repeat(raw.length)),()=>good('wrong'),()=>good(raw+'x'),()=>good(raw.slice(1)),()=>good(raw,{status:201}),()=>good(raw,{headers:{'Content-Type':'text/html'}}),()=>good(raw,{headers:{'X-Finder-Device-Snapshot':digest,'Content-Type':'text/plain'}}),()=>{const r=good();Object.defineProperty(r,'redirected',{value:true});return r;},()=>{const r=good();Object.defineProperty(r,'type',{value:'opaque'});return r;}]){
 const f=fixture(response);await assert.rejects(f.install());assert.equal(f.store.has(cfg.cache),false);assert.equal(f.store.get('unrelated').get('secret'),'untouched');assert.ok(!f.ops.some(x=>x[0]==='skip'));
}
// Corrupted existing cache is not returned as a verified offline page.
a.store.get(cfg.cache).set('https://example.test'+base+'snapshot.html',good('x'.repeat(raw.length)));await assert.rejects(a.request());
// A failed new install cannot erase a prior usable edition or unrelated cache.
const failed=fixture(()=>good('wrong'));failed.store.set('prior-edition',new Map([['snapshot',good()]]));await assert.rejects(failed.install());assert.equal(await failed.store.get('prior-edition').get('snapshot').text(),raw);
console.log('F10 worker: no automatic IO, install guards, exact fetch allowlist, cache drift, failed install preservation passed');

// Empty cache fallback is verified before it can be returned.
const fallback=fixture(()=>good('x'.repeat(raw.length)));await assert.rejects(fallback.request());
const validFallback=fixture();assert.equal(await(await validFallback.request()).text(),raw);
