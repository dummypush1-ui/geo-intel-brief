import assert from 'node:assert/strict';import {newsRefreshController} from '../integration/news_refresh.js';
let calls=0,timers=0,callback,cleared=0;const deps={refreshNews:async()=>{calls++},setTimer:(fn,ms)=>{assert.equal(ms,60000);timers++;callback=fn;return 1},clearTimer:()=>cleared++};
const off=newsRefreshController(deps);assert.equal(timers,0);assert.throws(()=>off.start(),/Polling disabled/);assert.equal(timers,0);await off.manual();assert.equal(calls,1);
const enabled=newsRefreshController({...deps,pollingApproved:true});enabled.start();enabled.start();assert.equal(timers,1);await callback();await new Promise(r=>setImmediate(r));assert.equal(calls,2);enabled.stop();assert.equal(cleared,1);assert.throws(()=>enabled.start(),/closed/);
let release;const serial=newsRefreshController({...deps,refreshNews:()=>new Promise(r=>release=r)});const first=serial.manual();assert.equal(await serial.manual(),false);release();await first;
console.log('default off, exact original60s fixture timer, once-only start, serial requests, stop PASS');
