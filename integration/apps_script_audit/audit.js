'use strict';
// Trusted-source harness, NOT isolation. Host mock constructors expose process. No no-I/O guarantee.
const fs=require('fs'),vm=require('vm'),crypto=require('crypto'),assert=require('assert');
const source=fs.readFileSync('intelligence/geo/apps_script/Code.gs','utf8');
const PIN='a5db615b74bb21c4bcfac59cde71edd97379621914421d3ea2b3ab765c7bc62b';
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
   else assert(options.method===undefined||options.method==='get');
   assert.equal(options.muteHttpExceptions,true);
   if(!['/digest-data','/mark-emailed','/dashboard'].includes(route))throw Error('UNMOCKED_IO');
   events.push({kind:'fetch',route,bodyBytes:options.payload?Buffer.byteLength(options.payload):0});
   const response=(opts.responses||[])[fetchIndex++];
   if(!response)throw Error('UNMOCKED_IO');
   if(response.throw)throw Error('synthetic transport failure');
   return {getResponseCode:()=>response.code,getContentText:encoding=>{
    assert.equal(encoding,'UTF-8');return response.body;
   }};
  }},
  GmailApp:{sendEmail:(to,subject,plain,body)=>{assert.equal(to,'fixture@example.invalid');events.push({kind:'gmail',htmlBytes:Buffer.byteLength(body.htmlBody)});if(opts.gmailError)throw Error('synthetic quota failure');}},
  Logger:{log:text=>{events.push({kind:'log'});}},
  Session:{getScriptTimeZone:()=> 'UTC'},Utilities:{formatDate:()=> 'FIXTURE_DATE'},
  ScriptApp:{WeekDay:{MONDAY:1},getProjectTriggers:()=>[{fixture:'unrelated'},{fixture:'owned'}],deleteTrigger:()=>{deletes++;if(opts.failDeleteAt===deletes)throw Error('synthetic deletion failure');events.push({kind:'delete_trigger'});},newTrigger:name=>{
   const chain={};for(const key of ['timeBased','everyMinutes','everyHours','atHour','nearMinute','everyDays','onWeekDay','onMonthDay'])chain[key]=()=>chain;
   chain.create=()=>{creates++;if(opts.failCreateAt===creates)throw Error('synthetic trigger failure');events.push({kind:'create_trigger',handler:name});};return chain;
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
check('digest_non200_no_send',()=>{const h=harness({responses:[resp({},500)]});h.run('sendDigest()');assert(!h.events.some(e=>e.kind==='gmail'));});
for(const [name,body] of [['truncated_JSON','{"html":'],['invalid_UTF8_decoded_JSON','\ufffd{"html":1}']])check(name,()=>{const h=harness({responses:[{code:200,body}]});assert.throws(()=>h.run('sendDigest()'));assert(!h.events.some(e=>e.kind==='gmail'));});
check('replacement_character_HTML_is_not_rejected_by_original',()=>{const h=harness({responses:[resp({...article,html:'\ufffd fixture'}),resp({})]});h.run('sendDigest()');assert(h.events.some(e=>e.kind==='gmail'));});
check('Gmail_quota_throw_no_mark',()=>{const h=harness({responses:[resp(article)],gmailError:true});assert.throws(()=>h.run('sendDigest()'));assert(!h.events.some(e=>e.route==='/mark-emailed'));});
check('two_cycles_mark_never200_duplicate_send',()=>{const h=harness({responses:[resp(article),resp({},500),resp(article),resp({},500)]});h.run('sendDigest();sendDigest()');assert.equal(h.events.filter(e=>e.kind==='gmail').length,2);});
check('mark_transport_error_after_send_logged',()=>{const h=harness({responses:[resp(article),{throw:true}]});h.run('sendDigest()');assert(h.events.some(e=>e.kind==='log'));});
check('large_mark_body_no_original_bound',()=>{const ids=Array.from({length:10000},(_,i)=>'fixture-'+i);const h=harness({responses:[resp({...article,article_ids:ids}),resp({})]});h.run('sendDigest()');assert(h.events.find(e=>e.route==='/mark-emailed').bodyBytes>100000);});
check('trigger_rebuild_deletes_unrelated_and_partial_failure',()=>{const h=harness({failCreateAt:3});assert.throws(()=>h.run('setupTriggers()'));assert.equal(h.events.filter(e=>e.kind==='delete_trigger').length,2);assert.equal(h.events.filter(e=>e.kind==='create_trigger').length,2);});
check('partial_trigger_deletion_failure',()=>{const h=harness({failDeleteAt:2});assert.throws(()=>h.run('setupTriggers()'));assert.equal(h.events.filter(e=>e.kind==='delete_trigger').length,1);assert.equal(h.events.filter(e=>e.kind==='create_trigger').length,0);});
check('parse_time_edge_cases',()=>{const h=harness();assert.equal(h.run('_parseTime("25:99").hour'),25);assert.equal(h.run('_parseTime("9:5abc").minute'),5);assert.equal(h.run('_parseTime("")'),null);assert.throws(()=>h.run('_parseTime(null)'));});
check('read_int_partial_numeric',()=>{for(const [text,n] of [['12abc',12],['-1',-1],['1e3',1]]){const h=harness({props:{TEST:text}});assert.equal(h.run('_readInt("TEST",0)'),n);}});
check('doGet_dummy_secret_only',()=>{const h=harness({responses:[{code:200,body:'fixture dashboard'}]});h.run('doGet({})');assert.equal(h.events[0].route,'/dashboard');});
console.log(JSON.stringify({scope:'offline_not_production_not_receipt_proof',source_sha256:PIN,source_state:'preserved_local_copy_source_commit_not_independently_verified',cases:reports,docs_not_tested:['GmailApp real message identity','actual Apps Script timezone','provider UTF8 decoding/quota/trigger limits']}));
