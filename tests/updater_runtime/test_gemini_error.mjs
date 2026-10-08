import assert from 'node:assert/strict';
import {classifyGeminiError as classify} from '../../updater_runtime/gemini-error.mjs';
assert.equal(classify(400,{error:{message:'API invalid request key field missing'}}),'invalid_request');
assert.equal(classify(400,{error:{details:[{'@type':'type.googleapis.com/google.rpc.ErrorInfo',reason:'API_KEY_INVALID'}]}}),'invalid_key');
assert.equal(classify(403,{error:{message:'API key valid, IAM lacks permission'}}),'permission_denied');
assert.equal(classify(404,{}),'model_missing');assert.equal(classify(429,{}),'quota');assert.equal(classify(503,{}),'service_unavailable');
assert.equal(classify(400,{error:{message:'model unavailable',details:'bad shape'}}),'invalid_request');
assert.equal(classify(401,{}),'request_failed');console.log('8 structured error assertions pass');
let calls=0;globalThis.fetch=async()=>{calls++;return {ok:false,status:400,json:async()=>({error:{message:'API key request validation PRIVATE'}})}};
const {geminiPost}=await import('../../gemini.mjs');await assert.rejects(geminiPost('fixture-key',{}),/request validation failed/);assert.equal(calls,1);
calls=0;globalThis.fetch=async()=>{calls++;return {ok:calls===2,status:calls===2?200:404,json:async()=>({})}};
assert.equal((await geminiPost('fixture-key',{})).model,'gemini-3.7-flash');assert.equal(calls,2);console.log('2 fake fetch chain tests pass; no network');

calls=0;globalThis.fetch=async()=>{calls++;return {ok:calls===2,status:calls===2?200:503,json:async()=>({})}};assert.equal((await geminiPost('fixture-key',{})).model,'gemini-3.7-flash');assert.equal(calls,2);
calls=0;globalThis.fetch=async()=>{calls++;return {ok:false,status:503,json:async()=>({error:{message:'PRIVATE overload'}})}};await assert.rejects(geminiPost('fixture-key',{}),/^Error: Gemini service unavailable$/);assert.equal(calls,7);console.log('2 additional 5xx chain tests pass');
