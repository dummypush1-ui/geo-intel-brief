import {createHash} from 'node:crypto';
export function validateSanctionsRows(rows,list){
 if(!Array.isArray(rows)||rows.length===0||rows.length>200000)throw new Error('Empty or oversized sanctions list');
 if(rows.some(r=>!Array.isArray(r)||r.length!==3||r.some(v=>typeof v!=='string'||!v.trim()||v.length>4096)||r[1]!==list))throw new Error('Malformed sanctions rows');
 return rows.map(r=>r.slice());
}
export function sanctionsDecision(previous,proposal,list,reviewedHash){
 const rows=validateSanctionsRows(proposal,list);
 const hash=createHash('sha256').update(JSON.stringify({list,rows})).digest('hex');
 const reason=previous.length===0?'bootstrap':rows.length*100<previous.length*85||rows.length*100>previous.length*115?'outlier':null;
 const mismatch=reviewedHash!==undefined&&(typeof reviewedHash!=='string'||reviewedHash!==hash);
 return {state:mismatch||reason&&reviewedHash!==hash?'review_required':'updated',reason:mismatch?'review_hash_mismatch':reason,previous_count:previous.length,candidate_count:rows.length,candidate_sha256:hash,rows};
}
