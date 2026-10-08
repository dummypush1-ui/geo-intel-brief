import assert from 'node:assert/strict';import {ensureIssue}from '../../updater_runtime/github-issue.mjs';
const o={token:'synthetic',repo:'fixture/repo'},r=(status,body)=>({ok:status>=200&&status<300,status,json:async()=>body});
for(const status of[401,403,429,500]){let n=0;const x=await ensureIssue('T','B',{...o,fetchFn:async()=>{n++;return r(status,{})}});assert.equal(x.state,'failed');assert.equal(n,1);}
let calls=[];let x=await ensureIssue('T','B',{...o,fetchFn:async(u,p)=>{calls.push([u,p.method]);return r(200,u.endsWith('page=1')?Array.from({length:100},(_,i)=>({number:i+1,title:'other'})):[{number:101,title:'T'}]);}});assert.equal(x.state,'existing');assert.equal(calls.length,2);assert.ok(calls[1][0].endsWith('page=2'));
for(const body of[{},[{number:1}],null]){x=await ensureIssue('T','B',{...o,fetchFn:async()=>r(200,body)});assert.equal(x.phase,'list');assert.equal(x.state,'failed');}
let items=[],posts=0;const fake=async(u,p)=>{if(p.method==='POST'){posts++;items=[{number:1,title:'T',html_url:'https://example.invalid/issue'}];return r(500,{});}return r(200,items);};
x=await ensureIssue('T','B',{...o,fetchFn:fake});assert.equal(x.state,'uncertain');x=await ensureIssue('T','B',{...o,fetchFn:fake});assert.equal(x.state,'existing');assert.equal(posts,1);
for(const ack of[{},null,{number:1,title:'wrong'}]){x=await ensureIssue('T','B',{...o,fetchFn:async(u,p)=>p.method==='POST'?r(201,ack):r(200,[])});assert.equal(x.state,'uncertain');}
x=await ensureIssue('T','B',{...o,fetchFn:async(u,p)=>p.method==='POST'?r(201,{number:2,title:'T',html_url:'https://example.invalid/2'}):r(200,[])});assert.equal(x.state,'created');
console.log('Issue status/pagination/malformed/uncertain-retry/no-duplicate tests pass');
