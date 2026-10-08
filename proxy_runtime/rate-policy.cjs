'use strict';
// Pure candidate. No sockets/server/env. Untrusted forwarded headers ignored.
const {isIP}=require('node:net');
const {performance}=require('node:perf_hooks');
function peerIdentity(req) {
 const peer=req && req.socket && req.socket.remoteAddress;
 if(typeof peer!=='string'||!isIP(peer))return 'unknown-peer';
 return peer.startsWith('::ffff:')&&isIP(peer.slice(7))===4?peer.slice(7):peer;
}
function createLimiter({windowMs=600000,max=60,capacity=5000,clock=()=>performance.now()}={}) {
 if(!Number.isSafeInteger(windowMs)||windowMs<1||!Number.isSafeInteger(max)||max<1||!Number.isSafeInteger(capacity)||capacity<1||typeof clock!=='function')throw Error('Invalid fixed policy');
 const hits=new Map();let last=-Infinity;
 function allow(key) {
  if(typeof key!=='string'||!key||key.length>100)return false;
  const now=clock();if(!Number.isFinite(now)||now<last)return false;last=now;
  // Expiry only. Never clear active counters to admit another identity.
  for(const [k,v]of hits)if(now-v.t>=windowMs)hits.delete(k);
  let row=hits.get(key);
  if(!row) {
   if(hits.size>=capacity)return false;
   row={t:now,n:0};hits.set(key,row);
  }
  if(row.n>=max)return false;
  row.n++;return true;
 }
 return Object.freeze({allow,size:()=>hits.size});
}
module.exports=Object.freeze({peerIdentity,createLimiter});
