'use strict';
// Separate non-billable snapshot read budget; AI budgets/attempts unchanged.
const {createLimiter}=require('./rate-policy.cjs');
function shipsReads({clock=()=>performance.now(),maxKeys=64}={}) {
 const peers=createLimiter({max:20,clock}),shared=createLimiter({capacity:1,max:60,clock});
 const cache=new Map();
 return Object.freeze({allow:peer=>peers.allow(peer)&&shared.allow('ships'),
  snapshot:(key,build)=>{const now=clock();for(const[k,v]of cache)if(now-v.at>=30000)cache.delete(k);let v=cache.get(key);if(v)return v.body;if(cache.size>=maxKeys)throw Error('Ships snapshot capacity');const body=build();cache.set(key,{at:now,body});return body;},size:()=>cache.size});
}
module.exports=Object.freeze({shipsReads});
