import assert from 'node:assert/strict';import fs from 'node:fs';import os from 'node:os';import path from 'node:path';import {monitor}from '../../monitor.mjs';
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'monitor-pending-')),stateFile=path.join(dir,'state.json'),sourceList=[{id:'X',name:'Fixture',url:'https://example.invalid'}];const clock=()=>new Date('2026-01-01T00:00:00Z');
const save=x=>fs.writeFileSync(stateFile,JSON.stringify({X:x})),read=()=>JSON.parse(fs.readFileSync(stateFile)).X;
try{
 for(const state of['failed','uncertain','disabled']){
  save({sig:'old',pending_issues:[{title:'First',body:'B'}]});const order=[];
  const r=await monitor({stateFile,sourceList,clock,signature:async()=>{order.push('sig');throw Error('offline')},issueFn:async()=>{order.push('issue');return{state}}});assert.deepEqual(order,['issue','sig']);assert.equal(read().pending_issues.length,1);assert.equal(r.issue_health[0].state,state);
 }
 for(const state of['created','existing']){save({sig:'old',pending_issues:[{title:'First',body:'B'}]});await monitor({stateFile,sourceList,clock,signature:async()=> 'old',issueFn:async()=>({state})});assert.equal(read().pending_issues.length,0);}
 save({sig:'old',cand:'new',n:1,pending_issues:[{title:'First',body:'B'}]});await monitor({stateFile,sourceList,clock,signature:async()=> 'new',issueFn:async()=>({state:'failed'})});let x=read();assert.equal(x.sig,'new');assert.equal(x.changedAt,'2026-01-01');assert.equal(x.pending_issues.length,2);assert.equal(x.pending_issues[0].title,'First');
 const titles=[];await monitor({stateFile,sourceList,clock,signature:async()=> 'new',issueFn:async t=>{titles.push(t);return{state:'existing'}}});assert.equal(titles.length,2);assert.equal(read().pending_issues.length,0);
 save({sig:'old',fails:6,pending_issues:[{title:'First',body:'B'}]});const bad=await monitor({stateFile,sourceList,clock,signature:async()=>{throw Error('offline')},issueFn:async()=>{throw Error('bad repo')}});assert.equal(bad.unreachable.length,1);assert.ok(bad.issue_health.every(r=>r.reason==='invalid_issue_request'));assert.equal(read().pending_issues.length,2);
 save({sig:'old',pending_issue:{title:'Legacy',body:'B'}});await monitor({stateFile,sourceList,clock,signature:async()=> 'old',issueFn:async()=>({state:'disabled'})});assert.equal(read().pending_issues[0].title,'Legacy');assert.equal(read().pending_issue,undefined);
}finally{fs.rmSync(dir,{recursive:true,force:true});}
console.log('Monitor pending array/retention/retry/advanced-sig/invalid-config tests pass');
