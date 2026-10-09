// Publication is complete only relative to the installed API reference scope.
// It does not prove a country's underlying source data is accurate/available.
import fs from 'fs';
export function coverage(expected, completed, throttled=false) {
  if (!Array.isArray(expected)||!expected.length||new Set(expected).size!==expected.length||!Array.isArray(completed)) throw new Error('Comtrade coverage shape');
  const done=new Set(completed),missing=expected.filter(x=>!done.has(x));
  return {complete:missing.length===0,expected:expected.length,completed:expected.length-missing.length,missing,throttled,published:false};
}
export function checkpoint(path,state) {
  fs.mkdirSync('state',{recursive:true});const tmp=path+'.pending';
  fs.writeFileSync(tmp,JSON.stringify(state)+'\n');fs.renameSync(tmp,path);
}
export function publish(path,text) {
  const tmp=path+'.pending';fs.writeFileSync(tmp,text);fs.renameSync(tmp,path);
}
export function completeRows(d) {
  if (!d||!Array.isArray(d.data)||d.data.length>=100000||('count'in d&&(!Number.isSafeInteger(d.count)||d.count<0||d.count>d.data.length))) throw new Error('Comtrade truncated or invalid table');
  return d.data;
}
