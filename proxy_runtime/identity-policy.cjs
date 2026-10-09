'use strict';
// Socket peer is the boundary. Headers alone never create trust or authentication.
const {isIP}=require('node:net');
const {peerIdentity}=require('./rate-policy.cjs');
function normalized(value) {
 if(typeof value!=='string'||value.length>64||value.trim()!==value||!isIP(value))return null;
 return value.toLowerCase().startsWith('::ffff:')&&isIP(value.slice(7))===4?value.slice(7):value.toLowerCase();
}
function identityPolicy(env={}) {
 const raw=env.PROXY_TRUSTED_PEERS||'';
 if(typeof raw!=='string'||raw.length>4096)throw Error('Invalid proxy trust configuration');
 const peers=raw?raw.split(',').map(x=>normalized(x.trim())):[];
 if(peers.some(x=>!x)||new Set(peers).size!==peers.length||peers.length>32)throw Error('Invalid proxy trust configuration');
 if(peers.length&&env.PROXY_XFF_TOPOLOGY_VERIFIED!=='single_appended_hop')throw Error('Proxy topology must be verified');
 const trusted=new Set(peers);
 return req=>{
  const peer=peerIdentity(req);
  if(!trusted.has(peer))return peer;
  // Node joins duplicate headers. rawHeaders catches duplicates before parsing.
  const rawHeaders=req.rawHeaders;
  if(!Array.isArray(rawHeaders)||rawHeaders.length%2)return peer;
  let count=0;for(let i=0;i<rawHeaders.length;i+=2)if(String(rawHeaders[i]).toLowerCase()==='x-forwarded-for')count++;
  const x=req.headers&&req.headers['x-forwarded-for'];
  if(count!==1||typeof x!=='string'||x.length>1024)return peer;
  const chain=x.split(',').map(v=>normalized(v.trim()));
  if(!chain.length||chain.length>16||chain.some(v=>!v))return peer;
  // Verified proxy appends its observed client. Ignore attacker-supplied prefix.
  return chain[chain.length-1];
 };
}
function quotaPolicy(env={}) {
 function read(name,fallback,maximum){
  const v=env[name];if(v===undefined)return fallback;
  if(typeof v!=='string'||! /^[1-9][0-9]{0,4}$/.test(v)||Number(v)>maximum)throw Error('Invalid anonymous quota configuration');
  return Number(v);
 }
 const perPeer=read('PROXY_PER_PEER_LIMIT',20,1000),shared=read('PROXY_SHARED_LIMIT',60,1000);
 if(perPeer>shared)throw Error('Per-peer quota exceeds shared quota');
 return Object.freeze({perPeer,shared,attempts:60});
}
module.exports=Object.freeze({identityPolicy,quotaPolicy});
