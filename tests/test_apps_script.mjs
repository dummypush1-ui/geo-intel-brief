import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const code=fs.readFileSync(new URL('../geonews/apps_script/Code.gs',import.meta.url),'utf8');
function harness(){
 const props=new Map([['RENDER_BASE_URL','https://example.onrender.com'],['TRIGGER_SECRET','test-secret'],['EMAIL_TO','owner@example.test']]);
 const calls=[], emails=[], triggers=[], deleted=[];
 let failAck=false, noNews=false, sendFails=false;
 const existing=['runCollect','sendDigest','checkCritical','unrelatedTask'].map(name=>({getHandlerFunction:()=>name}));
 const context={console:{log(){}},PropertiesService:{getScriptProperties:()=>({getProperty:k=>props.get(k)||null,setProperty:(k,v)=>props.set(k,v),deleteProperty:k=>props.delete(k)})},
 LockService:{getScriptLock:()=>({tryLock:()=>true,releaseLock(){}})},Utilities:{sleep(){},formatDate:()=> '02 Nov 2026 10:00'},
 GmailApp:{sendEmail:(...args)=>{if(sendFails)throw Error('Gmail quota');emails.push(args);}},
 UrlFetchApp:{fetch:(url,opts)=>{calls.push([url,opts]);let status=200;let body={ok:true};
 if(url.endsWith('/digest')) body={count:noNews?0:2,html:'<h1>Brief</h1>',article_ids:{brics:noNews?[]:['a'.repeat(64)],geo:noNews?[]:['b'.repeat(24)]}};
 if(url.endsWith('/api/intel/mark-emailed')&&failAck)status=503;
 return{getResponseCode:()=>status,getContentText:()=>JSON.stringify(body)};}},
 ScriptApp:{getProjectTriggers:()=>existing,deleteTrigger:t=>deleted.push(t.getHandlerFunction()),newTrigger:name=>{const t={name};triggers.push(t);const b={};for(const method of ['timeBased','everyMinutes','atHour','nearMinute','everyDays','inTimezone','create'])b[method]=v=>{t[method]=v;return b;};return b;}}};
 vm.createContext(context);vm.runInContext(code,context);
 return{context,props,calls,emails,triggers,deleted,setFailAck:v=>failAck=v,setNoNews:v=>noNews=v,setSendFails:v=>sendFails=v};
}
{
 const h=harness();h.context.runCollect();assert(h.calls.some(([u])=>u.endsWith('/api/trigger/collect')));
 h.context.sendDigest();assert.equal(h.emails.length,1);assert.equal(h.props.has('PENDING_COMBINED_IDS'),false);
 const ack=h.calls.find(([u])=>u.endsWith('/api/intel/mark-emailed'));
 assert.equal(JSON.parse(ack[1].payload).article_ids.brics.length,1);
 assert(h.calls.every(([u])=>!u.includes('test-secret')));
}
{
 const h=harness();h.setFailAck(true);assert.throws(()=>h.context.sendDigest(),/HTTP 503/);
 assert.equal(h.emails.length,1);assert(h.props.has('PENDING_COMBINED_IDS'));
 h.setFailAck(false);h.setNoNews(true);h.context.sendDigest();assert.equal(h.emails.length,1);assert(!h.props.has('PENDING_COMBINED_IDS'));
}
{
 const h=harness();h.setSendFails(true);assert.throws(()=>h.context.sendDigest(),/Gmail quota/);
 assert(!h.calls.some(([u])=>u.endsWith('/api/intel/mark-emailed')));
}
{
 const h=harness();h.props.set('PENDING_EMAIL_IDS',JSON.stringify(['b'.repeat(24)]));h.setNoNews(true);h.context.sendDigest();
 assert(h.calls.some(([u])=>u.endsWith('/geo/mark-emailed')));assert(!h.props.has('PENDING_EMAIL_IDS'));
}
{
 const h=harness();h.context.setupTriggers();assert.equal(h.triggers.length,4);assert(!h.deleted.includes('unrelatedTask'));
 assert.deepEqual(h.triggers.filter(t=>t.name==='sendDigest').map(t=>t.atHour),[10,22]);
}
{
 const h=harness();h.props.set('DIGEST_TIMES','25:99');assert.throws(()=>h.context.setupTriggers(),/HH:MM/);assert.equal(h.deleted.length,0);
}
console.log('Apps Script: 6 workflow scenarios passed (mocked Google services).');
