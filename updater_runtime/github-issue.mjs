const headers=token=>({Authorization:'Bearer '+token,Accept:'application/vnd.github+json','User-Agent':'hsn-finder-updater'});
export async function ensureIssue(title,body,{token=process.env.GITHUB_TOKEN,repo=process.env.GITHUB_REPOSITORY,fetchFn=fetch}={}){
 if(!token||!repo)return {state:'disabled',reason:'missing_issue_credentials'};
 if(!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repo)||typeof title!=='string'||!title.trim()||typeof body!=='string')throw new Error('Invalid issue request');
 const root='https://api.github.com/repos/'+repo+'/issues',h=headers(token);
 try{
  for(let page=1;page<=100;page++){
   const r=await fetchFn(root+'?state=open&per_page=100&page='+page,{headers:h,signal:AbortSignal.timeout(20000)});
   if(!r.ok)return {state:'failed',phase:'list',status:r.status,retry_safe:true};
   const list=await r.json();if(!Array.isArray(list)||list.length>100||list.some(i=>!i||!Number.isInteger(i.number)||typeof i.title!=='string'))return {state:'failed',phase:'list',reason:'malformed_issue_page',retry_safe:true};
   const found=list.find(i=>!i.pull_request&&i.title===title);if(found)return {state:'existing',number:found.number};
   if(list.length<100){
    let post;try{post=await fetchFn(root,{method:'POST',headers:{...h,'Content-Type':'application/json'},body:JSON.stringify({title,body}),signal:AbortSignal.timeout(20000)});}catch{return {state:'uncertain',phase:'create',retry_safe:false};}
    if(post.status!==201)return {state:post.status>=500?'uncertain':'failed',phase:'create',status:post.status,retry_safe:post.status<500};
    let item;try{item=await post.json();}catch{return {state:'uncertain',phase:'create',reason:'malformed_ack',retry_safe:false};}
    if(!item||!Number.isInteger(item.number)||item.title!==title||typeof item.html_url!=='string')return {state:'uncertain',phase:'create',reason:'malformed_ack',retry_safe:false};
    return {state:'created',number:item.number,url:item.html_url};
   }
  }
  return {state:'failed',phase:'list',reason:'pagination_cap',retry_safe:true};
 }catch{return {state:'failed',phase:'list',reason:'list_transport_or_json_failed',retry_safe:true};}
}
