'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync(__dirname+'/scheduler217.gs','utf8');let count=0;
function test(name,fn){fn();count++;console.log('PASS '+name);}
const entry=['installMailV1Schedules217','removeMailV1Schedules217','scheduledMailV1Weekly217','scheduledMailV1Critical217'];
function fixture(options={}){
 const props={MAIL_V1_SCHEDULER_ENABLED:'true',MAIL_V1_ENABLED:'true',MAIL217_WEEKLY_DAY:'THURSDAY',MAIL217_WEEKLY_TIME:'11:23',MAIL217_CRITICAL_MINUTES:'10',MAIL217_TIMEZONE:'Etc/UTC'};
 let ts=(options.triggers||[]).map(x=>({...x})),seq=0,creates=0,deletes=0,held=false,calls=0;const log=[];
 const trigger=x=>({getUniqueId:()=>x.id,getHandlerFunction:()=>x.name});
 const p={getProperty:k=>options.failReadback&&k==='MAIL217_OWNED'&&props[k]&&JSON.parse(props[k]).staged.length===2?'{}':Object.hasOwn(props,k)?props[k]:null,setProperty(k,v){log.push('write:'+k);props[k]=v;if(options.failWrite&&options.failWrite(k,v))throw Error('write_crash');},deleteProperty(k){delete props[k];}};
 const c={PropertiesService:{getScriptProperties:()=>p},LockService:{getScriptLock:()=>({tryLock(){assert(!held);held=true;return true;},releaseLock(){assert(held);held=false;}})},
 Utilities:{formatDate:(d,z)=>{if(z==='Invalid/Zone')throw Error('bad_zone');return d.toISOString().slice(0,10);}},ScriptApp:{WeekDay:{THURSDAY:'THURSDAY'},getProjectTriggers:()=>ts.map(trigger),deleteTrigger(t){deletes++;log.push('delete');if(options.failDelete)throw Error('delete_crash');ts=ts.filter(x=>x.id!==t.getUniqueId());},newTrigger(name){log.push('builder');const b={};for(const k of ['timeBased','onWeekDay','atHour','nearMinute','inTimezone','everyMinutes'])b[k]=()=>b;b.create=()=>{creates++;log.push('create');const x={id:'id'+(++seq),name};ts.push(x);if(options.failCreate===creates)throw Error('create_crash_unknown_id');return trigger(x);};return b;}},
 mailV1Weekly216:()=>{assert(!held,'nested_lock');assert(props.MAIL217_OCCURRENCES,'dedup_missing_before_call');calls++;if(options.failCall)throw Error('send_crash');return {state:'fake_return'};},mailV1Critical216:()=>{assert(!held,'nested_lock');assert(props.MAIL217_OCCURRENCES,'dedup_missing_before_call');calls++;return {state:'fake_return'};}};
 vm.createContext(c);vm.runInContext(source,c);
 return {c,props,log,get calls(){return calls;},get creates(){return creates;},get deletes(){return deletes;},get triggers(){return ts;}};
}
function owned(f,ids){f.props.MAIL217_OWNED=JSON.stringify({active:ids,inactive:[],staged:[]});}
for(const name of entry)test(name+' exact arg OFF before service',()=>{
 const c={};for(const k of ['PropertiesService','LockService','Utilities','ScriptApp','mailV1Weekly216','mailV1Critical216'])Object.defineProperty(c,k,{get(){throw Error('SERVICE_SPY');}});
 vm.createContext(c);vm.runInContext(source,c);for(const arg of [undefined,false,'true',1,{},new Boolean(true)])assert.equal(c[name](arg,{triggerUid:'id1'}).state,'off');
});
for(const name of entry)test(name+' property OFF before other services',()=>{
 const c={PropertiesService:{getScriptProperties:()=>({getProperty:()=> 'false'})}};
 for(const k of ['LockService','Utilities','ScriptApp','mailV1Weekly216','mailV1Critical216'])Object.defineProperty(c,k,{get(){throw Error('SERVICE_SPY');}});
 vm.createContext(c);vm.runInContext(source,c);assert.equal(c[name](true,{triggerUid:'id1'}).state,'off');
});
test('missing each config refuses before create/delete',()=>{for(const key of ['MAIL217_WEEKLY_DAY','MAIL217_WEEKLY_TIME','MAIL217_CRITICAL_MINUTES','MAIL217_TIMEZONE']){const f=fixture();delete f.props[key];assert.throws(()=>f.c.installMailV1Schedules217(true));assert.equal(f.creates+f.deletes,0);}});
test('invalid config and timezone refuse',()=>{for(const [k,v] of [['MAIL217_WEEKLY_DAY','MON'],['MAIL217_WEEKLY_TIME','25:00'],['MAIL217_CRITICAL_MINUTES','2'],['MAIL217_TIMEZONE','Invalid/Zone']]){const f=fixture();f.props[k]=v;assert.throws(()=>f.c.installMailV1Schedules217(true));assert.equal(f.creates,0);}});
test('same handler unowned refuses adoption',()=>{const f=fixture({triggers:[{id:'foreign',name:'scheduledMailV1Weekly217'}]});assert.throws(()=>f.c.installMailV1Schedules217(true));assert.equal(f.deletes+f.creates,0);});
test('quota includes unrelated triggers',()=>{const f=fixture({triggers:Array.from({length:19},(_,i)=>({id:'other'+i,name:'unrelated'}))});assert.throws(()=>f.c.installMailV1Schedules217(true));assert.equal(f.creates,0);});
test('creates both before retiring only owned old',()=>{const f=fixture({triggers:[{id:'old',name:'scheduledMailV1Weekly217'},{id:'foreign',name:'unrelated'}]});owned(f,['old']);f.c.installMailV1Schedules217(true);assert(f.log.lastIndexOf('create')<f.log.indexOf('delete'));assert.equal(f.deletes,1);assert(f.triggers.some(x=>x.id==='foreign'));assert.equal(f.props.MAIL217_OPERATION,undefined);});
for(const n of [1,2])test('unknown created ID crash '+n+' holds operation/old',()=>{const f=fixture({failCreate:n,triggers:[{id:'old',name:'scheduledMailV1Weekly217'}]});owned(f,['old']);assert.throws(()=>f.c.installMailV1Schedules217(true));assert(f.props.MAIL217_OPERATION);assert(f.triggers.some(x=>x.id==='old'));assert.equal(f.deletes,0);assert.throws(()=>f.c.installMailV1Schedules217(true));assert.equal(f.creates,n);});
test('after staged persist before readback crash holds',()=>{const f=fixture({failWrite:(k,v)=>k==='MAIL217_OWNED'&&JSON.parse(v).staged.length===2});assert.throws(()=>f.c.installMailV1Schedules217(true));assert(f.props.MAIL217_OPERATION);const s=JSON.parse(f.props.MAIL217_OWNED);assert.equal(s.staged.length,2);assert.equal(s.active.length,0);assert.equal(f.c.scheduledMailV1Weekly217(true,{triggerUid:'id1'}).state,'held_event');});
test('staged readback mismatch holds operation',()=>{const f=fixture({failReadback:true});assert.throws(()=>f.c.installMailV1Schedules217(true));assert(f.props.MAIL217_OPERATION);assert.equal(f.deletes,0);});
test('active flip before delete crash never sends while operation held',()=>{const f=fixture({failDelete:true,triggers:[{id:'old',name:'scheduledMailV1Weekly217'}]});owned(f,['old']);assert.throws(()=>f.c.installMailV1Schedules217(true));assert.equal(JSON.parse(f.props.MAIL217_OWNED).active.length,2);for(const id of ['old','id1','id2'])assert.equal(f.c.scheduledMailV1Weekly217(true,{triggerUid:id}).state,'held_event');assert.equal(f.calls,0);});
test('no event and unknown UID never call',()=>{const f=fixture();owned(f,['id1']);assert.equal(f.c.scheduledMailV1Weekly217(true).state,'unowned_event');assert.equal(f.c.scheduledMailV1Weekly217(true,{triggerUid:'unknown'}).state,'held_event');assert.equal(f.calls,0);});
test('durable occurrence precedes call, duplicate held, no nested lock',()=>{const f=fixture();owned(f,['id1']);f.c.scheduledMailV1Weekly217(true,{triggerUid:'id1'});assert(f.props.MAIL217_OCCURRENCES);assert.equal(f.c.scheduledMailV1Weekly217(true,{triggerUid:'id1'}).state,'occurrence_held_no_retry');assert.equal(f.calls,1);});
test('send failure after occurrence write never auto-retries',()=>{const f=fixture({failCall:true});owned(f,['id1']);assert.throws(()=>f.c.scheduledMailV1Weekly217(true,{triggerUid:'id1'}));assert.equal(f.c.scheduledMailV1Weekly217(true,{triggerUid:'id1'}).state,'occurrence_held_no_retry');assert.equal(f.calls,1);});
test('critical duplicate same bucket held',()=>{const f=fixture();owned(f,['id1']);f.c.scheduledMailV1Critical217(true,{triggerUid:'id1'});assert.equal(f.c.scheduledMailV1Critical217(true,{triggerUid:'id1'}).state,'occurrence_held_no_retry');assert.equal(f.calls,1);});
test('removal only owned and inactive before deletes',()=>{const f=fixture({triggers:[{id:'own',name:'scheduledMailV1Weekly217'},{id:'foreign',name:'scheduledMailV1Weekly217'}]});owned(f,['own']);f.c.removeMailV1Schedules217(true);assert.equal(f.deletes,1);assert.equal(f.triggers[0].id,'foreign');assert(f.log.indexOf('write:MAIL217_OWNED')<f.log.indexOf('delete'));});
test('removal failure holds operation and no active ids',()=>{const f=fixture({failDelete:true,triggers:[{id:'own',name:'scheduledMailV1Weekly217'}]});owned(f,['own']);assert.throws(()=>f.c.removeMailV1Schedules217(true));assert(f.props.MAIL217_OPERATION);assert.equal(JSON.parse(f.props.MAIL217_OWNED).active.length,0);});

for(const name of entry)test(name+' independent mail flag false/absent OFF',()=>{
 for(const mail of [undefined,'false']){
 const props={MAIL_V1_SCHEDULER_ENABLED:'true'};if(mail!==undefined)props.MAIL_V1_ENABLED=mail;
 const c={PropertiesService:{getScriptProperties:()=>({getProperty:k=>Object.hasOwn(props,k)?props[k]:null})}};
 for(const k of ['LockService','Utilities','ScriptApp','mailV1Weekly216','mailV1Critical216'])Object.defineProperty(c,k,{get(){throw Error('SERVICE_SPY');}});
 vm.createContext(c);vm.runInContext(source,c);assert.equal(c[name](true,{triggerUid:'id1'}).state,'off');
 }
});
test('128 occurrence capacity holds and 129 refused',()=>{for(const n of [128,129]){const f=fixture();owned(f,['id1']);f.props.MAIL217_OCCURRENCES=JSON.stringify(Array.from({length:n},(_,i)=>'synthetic:'+i));assert.throws(()=>f.c.scheduledMailV1Weekly217(true,{triggerUid:'id1'}));assert.equal(f.calls,0);}});
test('staged/inactive recovery without operation refuses installation',()=>{for(const key of ['staged','inactive']){const f=fixture();const s={active:[],inactive:[],staged:[]};s[key]=['recover'];f.props.MAIL217_OWNED=JSON.stringify(s);assert.equal(f.props.MAIL217_OPERATION,undefined);assert.throws(()=>f.c.installMailV1Schedules217(true));assert.equal(f.creates+f.deletes,0);}});


for(const name of entry)test(name+' converse scheduler flag false/absent OFF',()=>{
 for(const scheduler of [undefined,'false']){
 const props={MAIL_V1_ENABLED:'true'};if(scheduler!==undefined)props.MAIL_V1_SCHEDULER_ENABLED=scheduler;
 const c={PropertiesService:{getScriptProperties:()=>({getProperty:k=>Object.hasOwn(props,k)?props[k]:null})}};
 for(const k of ['LockService','Utilities','ScriptApp','mailV1Weekly216','mailV1Critical216'])Object.defineProperty(c,k,{get(){throw Error('SERVICE_SPY');}});
 vm.createContext(c);vm.runInContext(source,c);assert.equal(c[name](true,{triggerUid:'id1'}).state,'off');
 }
});

console.log(count+' source-only tests PASS; Apps Script not executed');
