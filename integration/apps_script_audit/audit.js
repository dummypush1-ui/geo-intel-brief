'use strict';
// Trusted-source harness, NOT isolation. Host mock constructors expose process. No no-I/O guarantee.
const fs=require('fs'),vm=require('vm'),crypto=require('crypto'),assert=require('assert');
const source=fs.readFileSync('intelligence/geo/apps_script/Code.gs','utf8');
const PIN='d4d3da4f6b44d962e1c59e88baa9e4c54b786a723dc4ce7f1c5cb2289eb85c67';
assert.equal(crypto.createHash('sha256').update(source).digest('hex'),PIN,'source pin changed');
function harness(opts={}) {
 const events=[],props={RENDER_BASE_URL:'https://fixture.invalid',TRIGGER_SECRET:'DUMMY_NON_SECRET',EMAIL_TO:'fixture@example.invalid',...(opts.props||{})};
 let fetchIndex=0,creates=0,deletes=0;
 const context={
  PropertiesService:{getScriptProperties:()=>({getProperty:k=>props[k]??null})},
  UrlFetchApp:{fetch:(url,options)=>{
   if(!url.startsWith('https://fixture.invalid/'))throw Error('UNMOCKED_IO');
   const parsed=new URL(url),route=parsed.pathname;
   assert.equal(parsed.searchParams.size,0);assert.equal(options.headers['X-Trigger-Secret'],'DUMMY_NON_SECRET');assert.equal(options.followRedirects,false);
   if(route==='/mark-emailed'){assert.equal(options.method,'post');assert.equal(options.contentType,'application/json');const p=JSON.parse(options.payload);assert(Array.isArray(p.article_ids));assert(p.article_ids.every(x=>/^fixture-\d+$/.test(x)));}
   else assert(options.method===undefined||['get','post'].includes(options.method));
   assert.equal(options.muteHttpExceptions,true);
   if(!['/digest-data','/mark-emailed','/dashboard','/health','/collect','/critical','/weekly'].includes(route))throw Error('UNMOCKED_IO');
   events.push({kind:'fetch',route,bodyBytes:options.payload?Buffer.byteLength(options.payload):0});
   const response=(opts.responses||[])[fetchIndex++];
   if(!response)throw Error('UNMOCKED_IO');
   if(response.throw)throw Error('synthetic transport failure');
   return {getResponseCode:()=>response.code,getContentText:encoding=>{
    assert.equal(encoding,'UTF-8');return response.body;
   }};
  }},
  GmailApp:{sendEmail:(to,subject,plain,body)=>{assert.equal(to,'fixture@example.invalid');events.push({kind:'gmail',htmlBytes:Buffer.byteLength(body.htmlBody)});if(opts.gmailError)throw Error('synthetic quota failure');}},
  Logger:{log:text=>{events.push({kind:'log',label:text});}},
  Session:{getScriptTimeZone:()=> 'UTC'},Utilities:{formatDate:()=> 'FIXTURE_DATE'},
  ScriptApp:{WeekDay:{MONDAY:1,TUESDAY:2,WEDNESDAY:3,THURSDAY:4,FRIDAY:5,SATURDAY:6,SUNDAY:7},getProjectTriggers:()=>opts.triggers||[{getHandlerFunction:()=> 'unrelated'},{getHandlerFunction:()=> 'keepAlive'}],deleteTrigger:t=>{deletes++;if(opts.failDeleteAt===deletes)throw Error('synthetic deletion failure');events.push({kind:'delete_trigger',handler:t.getHandlerFunction()});},newTrigger:name=>{
   const chain={};for(const key of ['timeBased','everyMinutes','everyHours','atHour','nearMinute','everyDays','onWeekDay','onMonthDay'])chain[key]=()=>chain;
   chain.create=()=>{creates++;if(opts.failCreateAt===creates)throw Error('synthetic trigger failure');events.push({kind:'create_trigger',handler:name});return {getHandlerFunction:()=> name};};return chain;
  }},HtmlService:{XFrameOptionsMode:{ALLOWALL:1},createHtmlOutput:()=>({setXFrameOptionsMode:()=>({})})}
 };
 vm.createContext(context,{codeGeneration:{strings:false,wasm:false}});vm.runInContext(source,context,{timeout:1000});
 function run(script){return vm.runInContext(script,context,{timeout:1000});}
 return {events,run};
}
const reports=[];
function check(name,fn){fn();reports.push({scope:'offline_not_production_not_receipt_proof',case:name,status:'pass'});}
function resp(data,code=200){return {code,body:JSON.stringify(data)};}
const article={html:'தமிழ் fixture',critical_count:0,article_ids:['fixture-1']};
check('trusted_harness_direct_globals_absent_but_host_escape_exists',()=>{
 const h=harness();assert.equal(h.run('typeof require+":"+typeof process+":"+typeof fetch'),'undefined:undefined:undefined');assert.equal(h.run('Logger.log.constructor("return typeof process")()'),'object');assert.throws(()=>h.run('UrlFetchApp.fetch("https://outside.invalid",{})'));});
check('empty_digest_skipped',()=>{const h=harness({responses:[resp({...article,article_ids:[]})]});h.run('sendDigest()');assert(!h.events.some(e=>e.kind==='gmail'));});
check('critical_only_sends_no_mark',()=>{const h=harness({responses:[resp({...article,article_ids:[],critical_count:1})]});h.run('sendDigest()');assert.equal(h.events.filter(e=>e.kind==='gmail').length,1);assert.equal(h.events.filter(e=>e.route==='/mark-emailed').length,0);});
check('send_then_mark_UTF8_fixture',()=>{const h=harness({responses:[resp(article),resp({},200)]});h.run('sendDigest()');assert.deepEqual(h.events.filter(e=>e.kind!=='log').map(e=>e.kind==='fetch'?e.route:e.kind),['/digest-data','gmail','/mark-emailed']);});
check('digest_non200_no_send',()=>{const h=harness({responses:[resp({},500)]});assert.throws(()=>h.run('sendDigest()'));assert(!h.events.some(e=>e.kind==='gmail'));});
for(const [name,body] of [['truncated_JSON','{"html":'],['invalid_UTF8_decoded_JSON','\ufffd{"html":1}']])check(name,()=>{const h=harness({responses:[{code:200,body}]});assert.throws(()=>h.run('sendDigest()'));assert(!h.events.some(e=>e.kind==='gmail'));});
check('replacement_character_HTML_is_not_rejected_by_original',()=>{const h=harness({responses:[resp({...article,html:'\ufffd fixture'}),resp({})]});h.run('sendDigest()');assert(h.events.some(e=>e.kind==='gmail'));});
check('Gmail_quota_throw_no_mark',()=>{const h=harness({responses:[resp(article)],gmailError:true});assert.throws(()=>h.run('sendDigest()'));assert(!h.events.some(e=>e.route==='/mark-emailed'));});
check('two_cycles_mark_never200_duplicate_send',()=>{const h=harness({responses:[resp(article),resp({},500),resp(article),resp({},500)]});assert.throws(()=>h.run('sendDigest()'));assert.throws(()=>h.run('sendDigest()'));assert.equal(h.events.filter(e=>e.kind==='gmail').length,2);});
check('mark_transport_error_after_send_logged',()=>{const h=harness({responses:[resp(article),{throw:true}]});assert.throws(()=>h.run('sendDigest()'));assert(h.events.some(e=>e.kind==='log'));assert(h.events.filter(e=>e.kind==='log').every(e=>!e.label.includes('synthetic')));});
check('large_mark_body_no_original_bound',()=>{const ids=Array.from({length:10000},(_,i)=>'fixture-'+i);const h=harness({responses:[resp({...article,article_ids:ids}),resp({})]});h.run('sendDigest()');assert(h.events.find(e=>e.route==='/mark-emailed').bodyBytes>100000);});
check('trigger_staging_preserves_unrelated_and_rolls_back_creation_failure',()=>{const h=harness({failCreateAt:3});assert.throws(()=>h.run('setupTriggers()'));assert.equal(h.events.filter(e=>e.kind==='delete_trigger').length,2);assert(h.events.filter(e=>e.kind==='delete_trigger').every(e=>['keepAlive','runCollect'].includes(e.handler)));assert.equal(h.events.filter(e=>e.kind==='create_trigger').length,2);});
check('partial_old_deletion_failure_is_reported_no_false_rollback',()=>{const h=harness({failDeleteAt:1});assert.throws(()=>h.run('setupTriggers()'));assert.equal(h.events.filter(e=>e.kind==='create_trigger').length,6);assert.equal(h.events.filter(e=>e.kind==='delete_trigger').length,0);assert(h.events.find(e=>e.kind==='log').label.includes('incomplete'));});
check('strict_time_edge_cases',()=>{const h=harness();for(const text of ['25:99','9:5abc','09:5','24:00','',' 09:00',null])assert.equal(h.run('_parseTime('+JSON.stringify(text)+')'),null);assert.equal(h.run('_parseTime("23:59").hour'),23);});
check('strict_int_rejects_partial_numeric',()=>{for(const text of ['12abc','-1','1e3','','01',' 1','999999999999999999999']){const h=harness({props:{TEST:text}});assert.throws(()=>h.run('_readInt("TEST",0)'));}});
check('all_schedule_validation_precedes_trigger_changes',()=>{for(const props of [{KEEPALIVE_INTERVAL_MIN:'2'},{COLLECT_INTERVAL_MIN:'60'},{CRITICAL_CHECK_INTERVAL_MIN:'-1'},{DIGEST_INTERVAL_HOURS:'3'},{DIGEST_INTERVAL_HOURS:'0'},{DIGEST_TIMES:'09:00,09:00'},{DIGEST_TIMES:'09:00,'},{DIGEST_TIMES:'25:01'},{WEEKLY_TIME:'9:00'},{WEEKLY_DAY:'MOON'},{DIGEST_TIMES:Array.from({length:17},(_,i)=>('0'+i).slice(-2)+':00').join(',')}]){const h=harness({props});assert.throws(()=>h.run('setupTriggers()'));assert(!h.events.some(e=>/trigger/.test(e.kind)));}});
check('trigger_success_preserves_unrelated_and_removes_managed',()=>{const h=harness();h.run('setupTriggers()');assert.equal(h.events.filter(e=>e.kind==='create_trigger').length,6);assert.deepEqual(h.events.filter(e=>e.kind==='delete_trigger').map(e=>e.handler),['keepAlive']);assert(h.events.findIndex(e=>e.kind==='delete_trigger')>h.events.map(e=>e.kind).lastIndexOf('create_trigger'));});
check('interval_mode_ignores_unused_digest_times',()=>{const h=harness({props:{DIGEST_INTERVAL_HOURS:'1',DIGEST_TIMES:'bad'}});h.run('setupTriggers()');assert.equal(h.events.filter(e=>e.kind==='create_trigger').length,5);});
check('staging_capacity_preserves_existing',()=>{const h=harness({triggers:Array.from({length:15},()=>({getHandlerFunction:()=> 'unrelated'}))});assert.throws(()=>h.run('setupTriggers()'));assert(!h.events.some(e=>/trigger/.test(e.kind)));});
check('creation_cleanup_failure_is_visible',()=>{const h=harness({failCreateAt:3,failDeleteAt:1});assert.throws(()=>h.run('setupTriggers()'));assert(h.events.find(e=>e.kind==='log').label.includes('cleanup incomplete'));});
check('held403_all_jobs_visible_no_mail_no_retry',()=>{for(const fn of ['keepAlive','runCollect','sendDigest','checkCritical','sendWeekly']){const h=harness({responses:[{code:403,body:'private untrusted response'}]});assert.throws(()=>h.run(fn+'()'),/held/);assert.equal(h.events.filter(e=>e.kind==='fetch').length,1);assert(!h.events.some(e=>e.kind==='gmail'));assert(h.events.filter(e=>e.kind==='log').every(e=>e.label==='Render route held: HTTP 403'));}});
check('non200_critical_weekly_collect_health_visible',()=>{for(const fn of ['keepAlive','runCollect','checkCritical','sendWeekly']){const h=harness({responses:[resp({},500)]});assert.throws(()=>h.run(fn+'()'));assert.equal(h.events.filter(e=>e.kind==='fetch').length,1);}});
check('mark403_after_send_unknown_receipt_no_retry',()=>{const h=harness({responses:[resp(article),resp({},403)]});assert.throws(()=>h.run('sendDigest()'),/receipt state unknown/);assert.equal(h.events.filter(e=>e.kind==='gmail').length,1);assert.equal(h.events.filter(e=>e.kind==='fetch').length,2);});
check('doGet_dummy_secret_only',()=>{const h=harness({responses:[{code:200,body:'fixture dashboard'}]});h.run('doGet({})');assert.equal(h.events[0].route,'/dashboard');});
console.log(JSON.stringify({scope:'offline_not_production_not_receipt_proof',source_sha256:PIN,source_state:'preserved_local_copy_source_commit_not_independently_verified',cases:reports,docs_not_tested:['GmailApp real message identity','actual Apps Script timezone','provider UTF8 decoding/quota/trigger limits']}));
