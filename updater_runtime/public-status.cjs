'use strict';
const {randomUUID}=require('node:crypto');
// Closed output schema: never copy arbitrary refresh results/errors to HTTP.
function publicResult(value,failed=false){
 const correlationId=randomUUID();
 if(failed)return {state:'failed',correlationId};
 if(!value||typeof value!=='object'||Array.isArray(value))return {state:'unknown',correlationId};
 const state=value.skipped?'skipped':value.dry===true?'dry_run':value.changed===false?'unchanged':value.committed===true?'committed':value.changed===true?'changed':'unknown';
 const out={state,correlationId};
 if(Number.isInteger(value.year)&&value.year>=1900&&value.year<=2200)out.year=value.year;
 if(typeof value.sha==='string'&&/^[a-f0-9]{40}$/.test(value.sha))out.commit=value.sha;
 return out;
}
module.exports=Object.freeze({publicResult});
