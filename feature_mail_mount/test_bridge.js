// Copyright (c) 2026 Push. All rights reserved.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),crypto=require('crypto');
const source=fs.readFileSync(__dirname+'/bridge.gs','utf8');
const key='e'.repeat(64),hash='f'.repeat(64),channel=crypto.createHash('sha256').update(JSON.stringify({sender:'sender@example.invalid',recipients:['fixture@example.invalid']})).digest('hex');
function fixture(mode='ok') {
 const props={MAIL_V1_ENABLED:'true',MAIL_V1_BASE:'https://fixture.invalid',MAIL_V1_HEADER_SECRET:'s'.repeat(48),MAIL_V1_EMAIL_TO:'fixture@example.invalid',MAIL_V1_CHANNEL:channel};
 let sent=0,claimed=false,acked=false,released=0,calls=[];
 const ctx={PropertiesService:{getScriptProperties:()=>({getProperty:k=>props[k]||null,setProperty:(k,v)=>{if(mode==='persistAfterSend'&&JSON.parse(v).phase==='send_returned')throw Error('storage');props[k]=v},deleteProperty:k=>{delete props[k]}})},LockService:{getScriptLock:()=>({tryLock:()=>true,releaseLock:()=>released++})},Session:{getEffectiveUser:()=>({getEmail:()=> 'sender@example.invalid'})},Utilities:{getUuid:()=> '00000000-0000-0000-0000-000000000001',DigestAlgorithm:{SHA_256:'sha256'},Charset:{UTF_8:'utf8'},computeDigest:(a,s)=>Array.from(crypto.createHash('sha256').update(s).digest())},GmailApp:{sendEmail:()=>{sent++;if(mode==='gmail')throw Error('unknown')}},UrlFetchApp:{fetch:(url,opt)=>{
  assert.equal(opt.followRedirects,false);assert.equal(opt.headers.Authorization,'Bearer '+'s'.repeat(48));calls.push(url);
  let out;
  if(url.endsWith('/prepare'))out={receipt:key,hash,channel_id:channel,state:claimed?'started':'prepared',payload:{kind:'digest',skip:false,subject:'Fixture',html:'<p>Fixture</p>'}};
  else if(url.endsWith('/claim')){assert(!claimed);claimed=true;if(mode==='claimLost')throw Error('lost');out={receipt:key,state:'started',permit:true};}
  else if(url.endsWith('/ack')){if(mode==='ack')throw Error('ack lost');acked=true;out={receipt:key,state:'acknowledged',scope:'bridge_send_returned_not_delivery'};}
  else throw Error('unexpected');return {getResponseCode:()=>200,getContentText:()=>JSON.stringify(out)};
 }}};
 vm.createContext(ctx);vm.runInContext(source,ctx);
 return {run:()=>ctx.runMailV1('digest'),props,get sent(){return sent},get claimed(){return claimed},get acked(){return acked},get released(){return released},calls,setMode:x=>{mode=x}};
}
let f=fixture();assert.equal(f.run().state,'acknowledged');assert.equal(f.sent,1);assert(f.acked);assert.equal(f.released,1);assert(!f.props.MAIL_V1_PENDING_DIGEST);
for(const mode of ['claimLost','gmail','persistAfterSend']) {
 f=fixture(mode);assert.throws(f.run);const n=f.sent;f.setMode('ok');assert.throws(f.run);assert.equal(f.sent,n);assert(!f.acked);
}
f=fixture('ack');assert.throws(f.run);assert.equal(f.sent,1);f.setMode('ok');assert.equal(f.run().state,'acknowledged');assert.equal(f.sent,1);
f=fixture();f.props.MAIL_V1_ENABLED='false';assert.equal(f.run().state,'off');assert.equal(f.calls.length,0);
f=fixture();f.props.MAIL_V1_EMAIL_TO='attacker\n@example.invalid';assert.throws(f.run);assert.equal(f.calls.length,0);
console.log('PASS bridge acceptance-only receipt, ack-only retry, unknown outcome holds, gates, no timers');
