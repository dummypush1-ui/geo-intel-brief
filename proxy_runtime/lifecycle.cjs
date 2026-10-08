'use strict';
const {performance}=require('node:perf_hooks');
// Inert until explicitly constructed. Supplied socket/timer factories only.
function createLifecycle({makeSocket,subscribe,decode,onMessage,validateFrame=()=>true,onState=()=>{},setTimer,clearTimer,clock=()=>performance.now(),handshakeMs=30000,maxQueued=16,decodeMs=10000}) {
 if([makeSocket,subscribe,decode,onMessage,validateFrame,onState,setTimer,clearTimer,clock].some(f=>typeof f!=='function'))throw Error('Fixed lifecycle callbacks required');
 if(!Number.isSafeInteger(decodeMs)||decodeMs<1||decodeMs>60000)throw Error('Bounded decode deadline');
 if(!Number.isSafeInteger(handshakeMs)||handshakeMs<1||!Number.isSafeInteger(maxQueued)||maxQueued<1||maxQueued>64)throw Error('Bounded policy');
 let generation=0,socket=null,retry=null,handshake=null,decodeTimer=null,abortDecode=null,stopped=false,connected=false,lastFrame=null,backoff=1000,lastClock=-Infinity,busy=false,queue=[];
 function now(){const n=clock();if(!Number.isFinite(n)||n<lastClock)throw Error('Invalid monotonic clock');lastClock=n;return n;}
 function report(state,detail){try{onState(state,detail);}catch{}}
 function current(ws,g){return !stopped&&socket===ws&&generation===g;}
 function cancelRetry(){if(retry!==null){clearTimer(retry);retry=null;}}
 function drop(){
  generation++;const old=socket;socket=null;connected=false;lastFrame=null;queue=[];
  if(abortDecode){abortDecode();abortDecode=null;}
  if(decodeTimer!==null){clearTimer(decodeTimer);decodeTimer=null;}
  if(handshake!==null){clearTimer(handshake);handshake=null;}
  if(old){old.onopen=old.onmessage=old.onclose=null;old.onerror=()=>{};if(typeof old.on==='function')old.on('error',()=>{});try{old.close();}catch{}}
 }
 function scheduleRetry(){
  if(stopped||retry!==null)return;
  const g=generation;const delay=backoff;backoff=Math.min(backoff*2,60000);
  retry=setTimer(()=>{retry=null;if(!stopped&&generation===g)connect();},delay);
 }
 function fail(ws,g,state,detail){if(!current(ws,g))return;drop();report(state,detail);scheduleRetry();}
 function connect(){
  if(stopped)return false;
  cancelRetry();drop();const g=generation;let ws;
  try{now();ws=makeSocket();socket=ws;}catch{report('create_failed');scheduleRetry();return false;}
  handshake=setTimer(()=>{handshake=null;fail(ws,g,'handshake_timeout');},handshakeMs);
  ws.onopen=()=>{
   if(!current(ws,g))return;
   try{subscribe(ws);}catch{return fail(ws,g,'subscribe_failed');}
   try{lastFrame=now();}catch{return fail(ws,g,'clock_invalid');}
   if(handshake!==null){clearTimer(handshake);handshake=null;}
   connected=true;backoff=1000;report('connected');
  };
  async function drain(){
   if(busy)return;busy=true;
   try{
    while(queue.length){
     const item=queue.shift();let message;
     if(!current(item.ws,item.g))continue;
     try{
      const result=Promise.resolve().then(()=>decode(item.ev));
      const deadline=new Promise((_,reject)=>{abortDecode=()=>reject(Error('decode_aborted'));decodeTimer=setTimer(()=>reject(Error('decode_timeout')),decodeMs);});
      message=await Promise.race([result,deadline]);
     }catch(e){if(current(item.ws,item.g))fail(item.ws,item.g,e&&e.message==='decode_timeout'?'decode_timeout':'decode_failed');continue;}
     finally{if(decodeTimer!==null){clearTimer(decodeTimer);decodeTimer=null;}abortDecode=null;}
     if(!current(item.ws,item.g))continue;
     try{lastFrame=now();}catch{fail(item.ws,item.g,'clock_invalid');continue;}
     try{onMessage(message);}catch{report('message_rejected');}
    }
   }finally{busy=false;}
  }
  ws.onmessage=ev=>{
   if(!current(ws,g))return Promise.resolve();
   try{if(!validateFrame(ev))throw Error('frame');}catch{fail(ws,g,'payload_rejected');return Promise.resolve();}
   if(queue.length>=maxQueued){fail(ws,g,'decode_queue_full');return Promise.resolve();}
   queue.push({ev,ws,g});return drain();
  };
  ws.onclose=ev=>fail(ws,g,'closed',{code:ev&&Number.isSafeInteger(ev.code)?ev.code:0});
  ws.onerror=()=>fail(ws,g,'error');
  return true;
 }
 function watchdog(silentMs=360000){
  let stamp;try{stamp=now();}catch{if(socket)fail(socket,generation,'clock_invalid');return false;}if(!Number.isSafeInteger(silentMs)||silentMs<1)return false;
  if(connected&&lastFrame!==null&&stamp-lastFrame>=silentMs){fail(socket,generation,'silent');return true;}
  return false;
 }
 function shutdown(){if(stopped)return;stopped=true;cancelRetry();drop();report('stopped');}
 return Object.freeze({connect,watchdog,shutdown,snapshot:()=>({connected,stopped,retryPending:retry!==null,generation,socketOwned:socket!==null})});
}
module.exports=Object.freeze({createLifecycle});
