'use strict';
const vm=require('node:vm'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..');let handler,sockets=[],timers=new Map(),id=0,intervals=[];
class FakeSocket{constructor(){sockets.push(this);}send(x){this.subscribed=JSON.parse(x);}close(){this.closed=true;}}
const ctx={require:n=>n==='http'?{createServer:f=>{handler=f;return {listen:()=>{}};}}:require(path.resolve(root,n)),
 process:{env:{AISSTREAM_KEY:'fixture-only'},on:()=>{},exit:()=>{}},WebSocket:FakeSocket,Buffer,ArrayBuffer,
 setTimeout:(f,d)=>{timers.set(++id,{f,d});return id;},clearTimeout:i=>timers.delete(i),
 setInterval:(f,d)=>{intervals.push({f,d});return ++id;},clearInterval:()=>{},console:{log:()=>{},warn:()=>{}},Date,URL,fetch:()=>{throw Error('network forbidden');}};
vm.runInNewContext(fs.readFileSync(path.join(root,'proxy.js'),'utf8'),ctx);
function health(){let body;handler({method:'GET',url:'/health',headers:{},socket:{}},{setHeader:()=>{},writeHead:()=>{},end:x=>{body=JSON.parse(x);}});return body.ais;}
assert.equal(sockets.length,1);assert.equal(sockets[0].binaryType,'arraybuffer');sockets[0].onopen();assert(health().connected);
(async()=>{
 await sockets[0].onmessage({data:'bad json'});assert.equal(health().errorFrames,1);assert(health().connected);
 await sockets[0].onmessage({data:'x'.repeat(262145)});assert.equal(health().payloadRejects,1);assert(!health().connected);assert(sockets[0].closed);
 const retry=[...timers.entries()].find(([,v])=>v.d===1000);assert(retry);timers.delete(retry[0]);retry[1].f();
 assert.equal(sockets.length,2);const handshake=[...timers.entries()].find(([,v])=>v.d===30000);assert(handshake);timers.delete(handshake[0]);handshake[1].f();assert.equal(health().handshakeTimeouts,1);
 console.log('fake proxy health/adapter integration assertions passed; zero network');
})().catch(e=>{console.error(e);process.exitCode=1;});
