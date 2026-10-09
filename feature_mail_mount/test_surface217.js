const fs=require('fs'),vm=require('vm'),assert=require('assert'),crypto=require('crypto');
const src=fs.readFileSync(__dirname+'/bridge.gs','utf8')+'\n'+fs.readFileSync(__dirname+'/handlers216.gs','utf8');
for(const held of ['prepare','claim','ack']){
 const channel=crypto.createHash('sha256').update(JSON.stringify({sender:'sender@example.invalid',recipients:['fixture@example.invalid']})).digest('hex'),key='a'.repeat(64),hash='b'.repeat(64);
 const props={MAIL_V1_ENABLED:'true',MAIL_V1_BASE:'https://fixture.invalid',MAIL_V1_HEADER_SECRET:'s'.repeat(48),MAIL_V1_EMAIL_TO:'fixture@example.invalid',MAIL_V1_CHANNEL:channel};let sent=0,calls=[];
 const c={PropertiesService:{getScriptProperties:()=>({getProperty:k=>props[k]||null,setProperty:(k,v)=>props[k]=v,deleteProperty:k=>delete props[k]})},Session:{getEffectiveUser:()=>({getEmail:()=> 'sender@example.invalid'})},LockService:{getScriptLock:()=>({tryLock:()=>true,releaseLock(){}})},Utilities:{getUuid:()=> '00000000-0000-0000-0000-000000000001',DigestAlgorithm:{SHA_256:'sha256'},Charset:{UTF_8:'utf8'},computeDigest:(a,s)=>Array.from(crypto.createHash('sha256').update(s).digest())},GmailApp:{sendEmail(){sent++}},UrlFetchApp:{fetch(url,opt){const action=url.split('/').pop();calls.push(action);let out;
 if(action===held)return {getResponseCode:()=>503,getContentText:()=>'{"state":"mail_integration_held","retry_send":false}'};
 if(action==='prepare')out={receipt:key,hash,channel_id:channel,state:'prepared',payload:{kind:'digest',skip:false,subject:'Fixture',html:'<p>Fixture</p>'}};
 else if(action==='claim')out={receipt:key,state:'started',permit:true};else throw Error('Unexpected');return {getResponseCode:()=>200,getContentText:()=>JSON.stringify(out)};
 }}};vm.createContext(c);vm.runInContext(src,c);
 assert.throws(()=>c.mailV1Digest216(true),e=>e.message==='mail216_possibly_sent');assert.equal(calls.filter(x=>x===held).length,1);assert.equal(sent,held==='ack'?1:0);assert(props.MAIL_V1_PENDING_DIGEST);
 const phase=JSON.parse(props.MAIL_V1_PENDING_DIGEST).phase;assert.equal(phase,{prepare:'pending',claim:'claiming',ack:'send_returned'}[held]);
 if(held==='claim'){assert.throws(()=>c.mailV1Digest216(true));assert.equal(sent,0);assert.equal(calls.filter(x=>x==='claim').length,1);}
}
console.log('PASS217 mocked held prepare/claim/ack bridge retains pending and never retries send');
