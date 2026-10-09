'use strict';
const vm=require('node:vm'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..');
function server(env){let handler,fetches=0;const ctx={require:n=>n==='http'?{createServer:f=>{handler=f;return{listen(){}};}}:require(path.resolve(root,n)),process:{env:{APP_SECRET:'public-fixture',...env},on(){},exit(){}},Buffer,ArrayBuffer,setTimeout:()=>1,clearTimeout(){},setInterval:()=>1,clearInterval(){},console:{log(){},warn(){}},Date,URL,AbortController,fetch:async()=>{fetches++;return{status:401,headers:{get:()=>null},text:async()=>'{"error":"fixture"}'};}};vm.runInNewContext(fs.readFileSync(path.join(root,'proxy.js'),'utf8'),ctx);return{handler,count:()=>fetches};}
async function call(s,peer,token='public-fixture',method='GET',url='/ships'){let status,body,end;const req={method,url,headers:{'x-app-token':token,'x-forwarded-for':'203.0.113.'+Math.floor(Math.random()*255),'cf-connecting-ip':'198.51.100.2'},rawHeaders:[],socket:{remoteAddress:peer},on(n,f){if(n==='end')end=f;},destroy(){throw Error('unexpected destroy');}};await s.handler(req,{setHeader(){},writeHead(c){status=c;},end(x){body=JSON.parse(x);}});if(end)await end();return{status,body};}
(async()=>{
 let s=server({});for(let i=0;i<20;i++)assert.equal((await call(s,'192.0.2.1')).status,503);assert.equal((await call(s,'192.0.2.1')).status,429);assert.equal((await call(s,'192.0.2.2')).status,503);assert.equal(s.count(),0);
 s=server({});assert.equal((await call(s,'192.0.2.1','bad')).status,401);assert.equal((await call(s,'192.0.2.1','public-fixture','POST','/admin')).status,404);assert.equal(s.count(),0);
 s=server({GROQ_KEYS:'fixture-a,fixture-b'});for(let i=0;i<30;i++)assert.equal((await call(s,i<15?'192.0.2.1':'192.0.2.2','public-fixture','POST','/groq/openai/v1/chat/completions')).status,401);assert.equal(s.count(),60);assert.equal((await call(s,'192.0.2.3','public-fixture','POST','/groq/openai/v1/chat/completions')).status,429);assert.equal(s.count(),60);
 console.log('3 fake proxy identity/shared-request/shared-attempt scenarios passed; zero real network');
})().catch(e=>{console.error(e);process.exitCode=1;});
