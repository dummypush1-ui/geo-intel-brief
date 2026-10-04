/* Preserved BRICS60s news-refresh cadence, dormant and capability-injected.
 * No module side effect/timer. Current workspace never calls start().
 * Production polling requires explicit owner approval and reviewed cadence.
 */
export function newsRefreshController({refreshNews,setTimer,clearTimer,pollingApproved=false}){
 if(typeof refreshNews!=='function'||typeof setTimer!=='function'||typeof clearTimer!=='function')throw new Error('Exact refresh dependencies required');
 let timer=null,inflight=false,closed=false;
 async function refresh(){if(inflight||closed)return false;inflight=true;try{await refreshNews();return true;}finally{inflight=false;}}
 return Object.freeze({manual:refresh,start(){if(pollingApproved!==true)throw new Error('Polling disabled pending approval');if(closed)throw new Error('Controller closed');if(timer===null)timer=setTimer(()=>{refresh().catch(()=>{});},60000);},stop(){if(timer!==null)clearTimer(timer);timer=null;closed=true;}});
}
