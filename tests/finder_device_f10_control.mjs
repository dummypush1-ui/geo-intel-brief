import fs from'node:fs';import vm from'node:vm';import assert from'node:assert/strict';import{webcrypto,createHash}from'node:crypto';
const body='public fixture',digest=createHash('sha256').update(body).digest('hex'),origin='https://example.test',base='/workspace/finder/device/'+digest+'/',cfg={base,digest,size:body.length,cache:'geo-finder-device-f10-'+digest},scriptURL=origin+base+'worker.js';
const source=fs.readFileSync(new URL('../integration/finder_device_f10/control.js',import.meta.url),'utf8').replace('/*F10_CONFIG*/','const CFG='+JSON.stringify(cfg)+';');
function fixture({stored=body,scope=origin+base,script=scriptURL,secure=true,remove=true,foreign=false}={}){
 const elements={status:{textContent:''},save:{disabled:false},clear:{disabled:false}},ops=[],stores=new Map([['unrelated','secret']]);let regs=[];
 const reg={scope,active:{scriptURL:script,state:'activated'},async unregister(){ops.push(['unregister',scope]);if(remove)regs=regs.filter(r=>r!==reg);return remove;}};
 if(foreign){regs=[reg];reg.active.scriptURL=origin+'/other.js';}
 const navigator={serviceWorker:{async register(url,options){ops.push(['register',url,options]);regs=[reg];stores.set(cfg.cache,stored);return reg;},async getRegistrations(){ops.push(['registrations']);return regs;}}};
 const caches={async open(name){ops.push(['open',name]);return{async match(){return stores.has(name)?new Response(stores.get(name),{headers:{'X-Finder-Device-Snapshot':digest}}):undefined;}};},async delete(name){ops.push(['delete',name]);return stores.delete(name);},async keys(){return [...stores.keys()];}};
 vm.runInNewContext(source,{document:{getElementById:id=>elements[id]},location:{origin},URL,Response,Uint8Array,crypto:webcrypto,navigator,caches,isSecureContext:secure,Error});
 return{elements,ops,stores,regs:()=>regs,async save(){await elements.save.onclick();},async clear(){await elements.clear.onclick();}};
}
const f=fixture();assert.equal(f.ops.length,0);await f.save();assert.match(f.elements.status.textContent,/is saved/);assert.equal(f.ops[0][0],'register');assert.equal(f.ops[0][1],scriptURL);assert.equal(f.ops[0][2].scope,origin+base);assert.equal(f.ops[0][2].updateViaCache,'none');await f.clear();assert.match(f.elements.status.textContent,/was cleared/);assert.equal(f.stores.get('unrelated'),'secret');assert.equal(f.regs().length,0);assert.ok(f.ops.filter(x=>x[0]==='delete').every(x=>x[1]===cfg.cache));
for(const args of[{stored:'x'.repeat(body.length)},{stored:'short'},{scope:origin+'/wrong/'},{script:origin+'/wrong.js'},{secure:false}]){
 const x=fixture(args);await x.save();assert.match(x.elements.status.textContent,/unavailable/);assert.equal(x.elements.save.disabled,false);assert.equal(x.elements.clear.disabled,false);
}
const foreign=fixture({foreign:true});await foreign.clear();assert.match(foreign.elements.status.textContent,/Different worker/);assert.ok(!foreign.ops.some(x=>x[0]==='delete'||x[0]==='unregister'));
const refused=fixture({remove:false});await refused.save();await refused.clear();assert.match(refused.elements.status.textContent,/removal not confirmed/);assert.ok(!refused.ops.some(x=>x[0]==='delete'));
console.log('F10 control: no automatic IO, exact manual register, digest/size/identity refusal, scoped clear and unrelated preservation passed');
