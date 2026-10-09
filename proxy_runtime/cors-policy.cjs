'use strict';
function canonical(value){
 if(typeof value!=='string'||value.length>256)return false;
 try{const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password&&!u.search&&!u.hash&&u.origin===value&&u.hostname===u.hostname.toLowerCase();}catch{return false;}
}
function policy(raw=''){
 if(typeof raw!=='string'||raw.length>2048)throw new Error('Invalid CORS configuration');
 const origins=raw?raw.split(','):[];
 if(origins.length>10||new Set(origins).size!==origins.length||origins.some(x=>!canonical(x)))throw new Error('Invalid CORS configuration');
 const allowed=new Set(origins);
 function single(req,key){
  const h=req.headers||{},v=h[key];let count=0;
  const raw=req.rawHeaders||[];for(let i=0;i<raw.length;i+=2)if(String(raw[i]).toLowerCase()===key)count++;
  if(count>1||Array.isArray(v))return {bad:true};
  return {value:v};
 }
 return {check(req,res){
  res.setHeader('Vary','Origin');
  const origin=single(req,'origin');
  if(origin.bad)return {status:403,error:'Origin not allowed'};
  if(origin.value===undefined){
   if(req.method==='OPTIONS')return {status:403,error:'Origin required for preflight'};
   return null;
  }
  if(!canonical(origin.value)||!allowed.has(origin.value))return {status:403,error:'Origin not allowed'};
  if(req.method==='OPTIONS'){
   const method=single(req,'access-control-request-method'),headers=single(req,'access-control-request-headers');
   if(method.bad||headers.bad||!['GET','POST'].includes(method.value)||typeof headers.value==='string'&&headers.value.length>200)return {status:403,error:'Preflight not allowed'};
   const fields=headers.value===undefined?[]:typeof headers.value==='string'?headers.value.split(',').map(x=>x.trim().toLowerCase()):['invalid'];
   if(new Set(fields).size!==fields.length||fields.some(x=>!['content-type','x-app-token'].includes(x)))return {status:403,error:'Preflight not allowed'};
   res.setHeader('Access-Control-Allow-Origin',origin.value);res.setHeader('Access-Control-Allow-Methods',method.value);if(fields.length)res.setHeader('Access-Control-Allow-Headers',fields.join(', '));res.setHeader('Access-Control-Max-Age','600');
   return {status:204};
  }
  res.setHeader('Access-Control-Allow-Origin',origin.value);return null;
 }};
}
module.exports={policy,canonical};
