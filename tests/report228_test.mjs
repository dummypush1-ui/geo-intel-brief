// Realm/late-font/idempotence tests for exact production helper, synthetic DOM.
import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';
const source=fs.readFileSync('src/app.js','utf8');
const helper=source.slice(source.indexOf('function setupTemplateReportWindow'),source.indexOf('async function openTemplateReport'));
async function probe(mode){
 const kids=Array.from({length:2},()=>({classList:{contains:c=>c==='tpl-sec'},offsetHeight:200,style:{},children:[],appendChild(e){this.children.push(e)}}));
 const listeners=[],loads=[],timers=[];let resolveFonts,prints=0;
 const fonts=new Promise(resolve=>resolveFonts=resolve);
 const doc={readyState:mode==='load'?'loading':'complete',body:{children:kids},fonts:{ready:fonts},getElementById(){return {addEventListener(name,fn){listeners.push(fn)}}},createElement(){return {style:{}}}};
 const w={document:doc,closed:false,print(){prints++},addEventListener(event,fn,opts){assert.equal(event,'load');assert.equal(opts.once,true);loads.push(fn)}};
 const realm={TPL_PAGE_H:994,Promise,Array,Object,setTimeout(fn,ms){assert.equal(ms,1500);timers.push(fn);return 1},clearTimeout(){},};vm.createContext(realm);vm.runInContext(helper,realm);
 realm.setupTemplateReportWindow(w);realm.setupTemplateReportWindow(w);assert.equal(listeners.length,1);assert.equal(kids[0].children.length,0);
 if(mode==='load'){assert.equal(loads.length,1);loads[0]();loads[0]();}
 if(mode==='closed')w.closed=true;
 if(mode==='deadline')timers[0]();else resolveFonts();
 await new Promise(resolve=>setImmediate(resolve));
 assert.equal(kids[0].children.length,mode==='closed'?0:1);
 if(mode!=='closed'){assert.equal(doc.__templateReport228.complete,true);assert.equal(kids[0].children[0].textContent,'Page 1 of 2');assert.equal(kids[1].children[0].textContent,'Page 2 of 2');}
 listeners[0]();assert.equal(prints,1);w.print=()=>{throw Error('print unsupported')};assert.doesNotThrow(()=>listeners[0]());
 realm.setupTemplateReportWindow(w);assert.equal(listeners.length,1);
}
for(const mode of ['ready','load','deadline','closed'])await probe(mode);
console.log('PASS report228 opener realm/late fonts/deadline/load/idempotence/closed/print throw');
